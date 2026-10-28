"""
OmniBridge MCP: Model Context Protocol Server.
Supports multi-channel dispatch (Telegram, Discord, WhatsApp, Slack, Matrix, Webhooks),
SQLite WAL retry queue with active drain worker, and token-bucket rate limiting.
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from . import __version__
from .channels import (
    CustomWebhookChannel,
    DiscordChannel,
    MatrixChannel,
    SlackChannel,
    TelegramChannel,
    WhatsAppChannel,
)
from .core.rate_limiter import RateLimiter
from .core.resilient_queue import ResilientQueue

logger = logging.getLogger("OmniBridgeServer")


class OmniBridgeServer:
    def __init__(self, queue_db_path: Optional[str] = None):
        self.telegram = TelegramChannel()
        self.discord = DiscordChannel()
        self.whatsapp = WhatsAppChannel()
        self.slack = SlackChannel()
        self.matrix = MatrixChannel()
        self.webhook = CustomWebhookChannel()
        self.queue = ResilientQueue(queue_db_path)
        self.limiter = RateLimiter(default_rate=5.0, default_burst=10)
        self.server_name = "omnibridge-mcp"
        self.server_version = __version__

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "send_telegram_message",
                "description": "Send a notification or message to a Telegram chat or channel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "chat_id": {"type": "string", "description": "Telegram chat ID or @channel"},
                        "text": {"type": "string", "description": "Message body to send (Markdown supported)"},
                        "disable_notification": {"type": "boolean", "description": "Send silently (default: false)"},
                    },
                    "required": ["chat_id", "text"],
                },
            },
            {
                "name": "send_discord_alert",
                "description": "Send a webhook notification or embed to a Discord channel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Raw text content"},
                        "title": {"type": "string", "description": "Embed card title"},
                        "description": {"type": "string", "description": "Embed card detailed description"},
                        "color": {"type": "integer", "description": "Hex decimal color code"},
                        "webhook_url": {"type": "string", "description": "Optional Discord webhook URL override"},
                    },
                },
            },
            {
                "name": "send_whatsapp_message",
                "description": "Send a WhatsApp message to a phone number via WhatsApp Cloud API.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to_phone": {
                            "type": "string",
                            "description": "Recipient international phone number with country code (e.g. +14155552671)",
                        },
                        "text": {"type": "string", "description": "Message text"},
                        "preview_url": {"type": "boolean", "description": "Show link preview (default: false)"},
                    },
                    "required": ["to_phone", "text"],
                },
            },
            {
                "name": "send_slack_notification",
                "description": "Send a notification or structured Block Kit alert to a Slack channel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Fallback plain text message"},
                        "header": {"type": "string", "description": "Prominent header block text"},
                        "webhook_url": {"type": "string", "description": "Optional Slack webhook URL override"},
                    },
                    "required": ["text"],
                },
            },
            {
                "name": "send_matrix_message",
                "description": "Send a message to a Matrix protocol room.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "body": {"type": "string", "description": "Message text"},
                        "room_id": {"type": "string", "description": "Optional target Matrix room ID override"},
                    },
                    "required": ["body"],
                },
            },
            {
                "name": "send_custom_webhook",
                "description": "Send a structured JSON payload to an external HTTPS webhook with HMAC-SHA256 signing.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Destination webhook URL"},
                        "payload": {"type": "object", "description": "JSON payload object to send"},
                        "secret": {"type": "string", "description": "Optional secret key for HMAC signature generation"},
                    },
                    "required": ["url", "payload"],
                },
            },
            {
                "name": "get_queue_stats",
                "description": "Inspect persistent message queue statistics (pending, retrying, delivered, failed).",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "flush_queue",
                "description": "Process due pending and retrying messages in the persistent SQLite WAL queue.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "max_items": {
                            "type": "integer",
                            "description": "Maximum due messages to retry in this pass (default: 20)",
                        }
                    },
                },
            },
            {
                "name": "get_channel_status",
                "description": "Check configuration readiness of all connected notification channels.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def _dispatch_direct(self, channel: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if channel == "telegram":
            return self.telegram.send(
                chat_id=args.get("chat_id", ""),
                text=args.get("text", ""),
                disable_notification=bool(args.get("disable_notification", False)),
            )
        if channel == "discord":
            return self.discord.send(
                content=args.get("content", ""),
                title=args.get("title"),
                description=args.get("description"),
                color=args.get("color", 0x3498DB),
                webhook_url=args.get("webhook_url"),
            )
        if channel == "whatsapp":
            return self.whatsapp.send(
                to_phone=args.get("to_phone", ""),
                text=args.get("text", ""),
                preview_url=bool(args.get("preview_url", False)),
            )
        if channel == "slack":
            return self.slack.send(
                text=args.get("text", ""),
                header=args.get("header"),
                webhook_url=args.get("webhook_url"),
            )
        if channel == "matrix":
            return self.matrix.send(
                body=args.get("body", ""),
                room_id=args.get("room_id"),
            )
        if channel == "webhook":
            return self.webhook.send(
                url=args.get("url"),
                payload=args.get("payload", {}),
                secret=args.get("secret"),
            )
        raise ValueError(f"Unknown channel {channel}")

    def process_pending_queue(self, max_items: int = 20) -> Dict[str, Any]:
        """Attempt delivery of due messages in the SQLite WAL queue."""
        limit = max(1, min(int(max_items), 100))
        due_items = self.queue.fetch_pending(limit=limit)
        delivered = 0
        retried = 0
        for item in due_items:
            channel = item["channel"]
            if not self.limiter.acquire(channel):
                continue
            res = self._dispatch_direct(channel, item["payload"])
            if res.get("success", False):
                self.queue.mark_delivered(item["id"])
                delivered += 1
            else:
                self.queue.mark_retry(
                    item["id"],
                    current_retries=item["retries"],
                    max_retries=item["max_retries"],
                    error=str(res.get("error", "Delivery failed")),
                )
                retried += 1
        return {
            "success": True,
            "processed": delivered + retried,
            "delivered": delivered,
            "retried": retried,
            "stats": self.queue.get_stats(),
        }

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        channel_map = {
            "send_telegram_message": "telegram",
            "send_discord_alert": "discord",
            "send_whatsapp_message": "whatsapp",
            "send_slack_notification": "slack",
            "send_matrix_message": "matrix",
            "send_custom_webhook": "webhook",
        }

        if name in channel_map:
            channel = channel_map[name]
            if not self.limiter.acquire(channel):
                logger.warning("Rate limit exceeded for %s. Enqueuing in WAL queue.", channel)
                msg_id = self.queue.enqueue(channel, arguments)
                return {
                    "success": True,
                    "queued": True,
                    "queue_id": msg_id,
                    "message": f"Channel {channel} rate-limited. Message persisted in WAL queue for delivery.",
                }

            res = self._dispatch_direct(channel, arguments)
            if not res.get("success", False) and res.get("retryable", False):
                logger.warning("Transient failure on %s (%s). Enqueuing in WAL queue.", channel, res.get("error"))
                msg_id = self.queue.enqueue(channel, arguments)
                res["queued"] = True
                res["queue_id"] = msg_id
                res["queue_note"] = "Persisted in WAL queue; call flush_queue or retry after backoff."
            return res

        if name == "get_queue_stats":
            return {
                "queue_db": str(self.queue.db_path),
                "stats": self.queue.get_stats(),
            }

        if name == "flush_queue":
            max_items = arguments.get("max_items", 20)
            return self.process_pending_queue(max_items=max_items)

        if name == "get_channel_status":
            return {
                "version": self.server_version,
                "channels": {
                    "telegram": {"configured": self.telegram.is_configured()},
                    "discord": {"configured": self.discord.is_configured()},
                    "whatsapp": {"configured": self.whatsapp.is_configured()},
                    "slack": {"configured": self.slack.is_configured()},
                    "matrix": {"configured": self.matrix.is_configured()},
                    "webhook": {"configured": self.webhook.is_configured()},
                },
                "queue": self.queue.get_stats(),
            }

        raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(request, dict):
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request: expected JSON object"},
            }

        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params")
        if params is None:
            params = {}
        elif not isinstance(params, dict):
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": "Invalid params: expected JSON object"},
            }

        if req_id is None and "id" not in request:
            if method == "notifications/initialized":
                logger.info("Client completed initialization handshake.")
            return None

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": self.server_name,
                        "version": self.server_version,
                    },
                },
            }

        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_tools_definition()},
            }

        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments")
            if tool_args is None:
                tool_args = {}
            elif not isinstance(tool_args, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params: 'arguments' must be an object"},
                }
            try:
                output = self.handle_tool_call(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(output, indent=2, ensure_ascii=False),
                            }
                        ],
                        "isError": not output.get("success", True) if "success" in output else False,
                    },
                }
            except Exception as e:
                logger.error("Error calling tool %s: %s", tool_name, e)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)},
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    def run_stdio(self) -> None:
        if not logging.getLogger().handlers and not logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] [OmniBridge] %(message)s",
                stream=sys.stderr,
            )
        logger.info("Starting %s v%s stdio listener...", self.server_name, self.server_version)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except json.JSONDecodeError as e:
                logger.error("JSON parse error: %s", e)
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                logger.error("Error processing stdio line: %s", e)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="omnibridge-mcp",
        description="OmniBridge MCP stdio server for multi-channel notifications and signed webhooks",
    )
    parser.add_argument("-v", "--version", action="version", version=f"omnibridge-mcp {__version__}")
    parser.add_argument("--queue-db", default=None, help="Optional path to SQLite WAL queue file")
    args = parser.parse_args()
    server = OmniBridgeServer(queue_db_path=args.queue_db)
    server.run_stdio()


if __name__ == "__main__":
    main()
