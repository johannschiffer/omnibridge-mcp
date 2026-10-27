"""
OmniBridge MCP: Model Context Protocol Server
Includes multi-channel dispatch (Telegram, Discord, WhatsApp, Slack, Matrix, Webhooks),
persistent WAL offline queue, and adaptive token bucket rate-limiting.
"""

import sys
import json
import logging
from typing import Dict, Any, List, Optional
from .channels import (
    TelegramChannel, DiscordChannel, WhatsAppChannel,
    SlackChannel, MatrixChannel, CustomWebhookChannel
)
from .core.resilient_queue import ResilientQueue
from .core.rate_limiter import RateLimiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [OmniBridge] %(message)s",
    stream=sys.stderr
)
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
        self.server_version = "1.0.0"

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "send_telegram_message",
                "description": "Send a real-time notification or message to a Telegram chat or channel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "chat_id": {"type": "string", "description": "Telegram chat ID or @channel"},
                        "text": {"type": "string", "description": "Message body to send (Markdown supported)"},
                        "disable_notification": {"type": "boolean", "description": "Send silently (default: false)"}
                    },
                    "required": ["chat_id", "text"]
                }
            },
            {
                "name": "send_discord_alert",
                "description": "Send a rich webhook notification or embed to a Discord channel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Raw text content"},
                        "title": {"type": "string", "description": "Embed card title"},
                        "description": {"type": "string", "description": "Embed card detailed description"},
                        "color": {"type": "integer", "description": "Hex decimal color code"},
                        "webhook_url": {"type": "string", "description": "Optional Discord webhook URL override"}
                    }
                }
            },
            {
                "name": "send_whatsapp_message",
                "description": "Send an official WhatsApp message to a phone number via WhatsApp Cloud API.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to_phone": {"type": "string", "description": "Recipient international phone number with country code (e.g. +14155552671)"},
                        "text": {"type": "string", "description": "Message text"},
                        "preview_url": {"type": "boolean", "description": "Show link preview (default: false)"}
                    },
                    "required": ["to_phone", "text"]
                }
            },
            {
                "name": "send_slack_notification",
                "description": "Send a notification or structured Block Kit alert to a Slack channel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Fallback plain text message"},
                        "header": {"type": "string", "description": "Prominent header block text"},
                        "webhook_url": {"type": "string", "description": "Optional Slack webhook URL override"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "send_matrix_message",
                "description": "Send a message to a Matrix protocol room.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "body": {"type": "string", "description": "Message text"},
                        "room_id": {"type": "string", "description": "Optional target Matrix room ID override"}
                    },
                    "required": ["body"]
                }
            },
            {
                "name": "send_custom_webhook",
                "description": "Send a structured JSON payload to any external webhook with HMAC-SHA256 signature verification.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Destination webhook URL"},
                        "payload": {"type": "object", "description": "JSON payload object to send"},
                        "secret": {"type": "string", "description": "Optional secret key for HMAC signature generation"}
                    },
                    "required": ["url", "payload"]
                }
            },
            {
                "name": "get_queue_stats",
                "description": "Inspect persistent message queue statistics (pending, retrying, delivered, failed).",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_channel_status",
                "description": "Check configuration and operational readiness of all connected notification channels.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def _dispatch_direct(self, channel: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if channel == "telegram":
            return self.telegram.send(
                chat_id=args.get("chat_id", ""),
                text=args.get("text", ""),
                disable_notification=args.get("disable_notification", False)
            )
        elif channel == "discord":
            return self.discord.send(
                content=args.get("content", ""),
                title=args.get("title"),
                description=args.get("description"),
                color=args.get("color", 0x3498db),
                webhook_url=args.get("webhook_url")
            )
        elif channel == "whatsapp":
            return self.whatsapp.send(
                to_phone=args.get("to_phone", ""),
                text=args.get("text", ""),
                preview_url=args.get("preview_url", False)
            )
        elif channel == "slack":
            return self.slack.send(
                text=args.get("text", ""),
                header=args.get("header"),
                webhook_url=args.get("webhook_url")
            )
        elif channel == "matrix":
            return self.matrix.send(
                body=args.get("body", ""),
                room_id=args.get("room_id")
            )
        elif channel == "webhook":
            return self.webhook.send(
                url=args.get("url"),
                payload=args.get("payload", {}),
                secret=args.get("secret")
            )
        else:
            raise ValueError(f"Unknown channel {channel}")

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        channel_map = {
            "send_telegram_message": "telegram",
            "send_discord_alert": "discord",
            "send_whatsapp_message": "whatsapp",
            "send_slack_notification": "slack",
            "send_matrix_message": "matrix",
            "send_custom_webhook": "webhook"
        }

        if name in channel_map:
            channel = channel_map[name]
            # Check rate limiter
            if not self.limiter.acquire(channel):
                logger.warning(f"Rate limit exceeded for {channel}. Enqueuing in resilient queue.")
                msg_id = self.queue.enqueue(channel, arguments)
                return {
                    "success": True,
                    "queued": True,
                    "queue_id": msg_id,
                    "message": f"Channel {channel} rate-limited. Message persisted in WAL queue for delivery."
                }

            # Attempt direct delivery
            res = self._dispatch_direct(channel, arguments)
            if not res.get("success", False):
                # Auto-resilience: enqueue on network failure
                logger.warning(f"Delivery to {channel} failed ({res.get('error')}). Enqueuing in resilient queue.")
                msg_id = self.queue.enqueue(channel, arguments)
                res["queued"] = True
                res["queue_id"] = msg_id
                res["queue_note"] = "Persisted in WAL queue; will retry with exponential backoff."
            return res

        elif name == "get_queue_stats":
            return {
                
                "queue_db": str(self.queue.db_path),
                "stats": self.queue.get_stats()
            }

        elif name == "get_channel_status":
            return {
                "version": "1.0.0",
                "channels": {
                    "telegram": {"configured": self.telegram.is_configured()},
                    "discord": {"configured": self.discord.is_configured()},
                    "whatsapp": {"configured": self.whatsapp.is_configured()},
                    "slack": {"configured": self.slack.is_configured()},
                    "matrix": {"configured": self.matrix.is_configured()},
                    "webhook": {"configured": self.webhook.is_configured()}
                },
                "queue": self.queue.get_stats()
            }
        else:
            raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if req_id is None:
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
                        "version": self.server_version
                    }
                }
            }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_tools_definition()}
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                output = self.handle_tool_call(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(output, indent=2, ensure_ascii=False)
                            }
                        ],
                        "isError": not output.get("success", True) if "success" in output else False
                    }
                }
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)}
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    def run_stdio(self):
        logger.info(f"Starting {self.server_name} v{self.server_version} stdio listener...")
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
            except Exception as e:
                logger.error(f"Error processing stdio line: {e}")

def main():
    server = OmniBridgeServer()
    server.run_stdio()

if __name__ == "__main__":
    main()
