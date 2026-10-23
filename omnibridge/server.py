"""
OmniBridge MCP: Model Context Protocol Server (Lite Edition)
Implements standard JSON-RPC 2.0 stdio transport compatible with
Claude Desktop, Cursor, Zed, Windsurf, and Antigravity.
"""

import sys
import json
import logging
from typing import Dict, Any, List
from .channels import TelegramChannel, DiscordChannel

# Configure logging to stderr so stdout remains purely JSON-RPC messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [OmniBridge] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("OmniBridgeServer")

class OmniBridgeMCPServer:
    def __init__(self):
        self.telegram = TelegramChannel()
        self.discord = DiscordChannel()
        self.server_name = "omnibridge-mcp"
        self.server_version = "1.0.0"

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "send_telegram_message",
                "description": "Send a real-time notification or message to a Telegram chat, user, or channel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "chat_id": {
                            "type": "string",
                            "description": "Telegram chat ID, user ID or @channelusername"
                        },
                        "text": {
                            "type": "string",
                            "description": "Message body to send (supports Markdown)"
                        },
                        "disable_notification": {
                            "type": "boolean",
                            "description": "Send silently without sound alert (default: false)"
                        }
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
                        "content": {
                            "type": "string",
                            "description": "Optional raw text message"
                        },
                        "title": {
                            "type": "string",
                            "description": "Embed card title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Embed card detailed description or body"
                        },
                        "color": {
                            "type": "integer",
                            "description": "Hex decimal color code (default: 3447003 / 0x3498db Blue, 0x2ecc71 Green, 0xe74c3c Red)"
                        },
                        "webhook_url": {
                            "type": "string",
                            "description": "Optional target Discord webhook URL if overriding default"
                        }
                    }
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

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "send_telegram_message":
            chat_id = arguments.get("chat_id", "")
            text = arguments.get("text", "")
            disable_notification = arguments.get("disable_notification", False)
            res = self.telegram.send(chat_id=chat_id, text=text, disable_notification=disable_notification)
            return res

        elif name == "send_discord_alert":
            res = self.discord.send(
                content=arguments.get("content", ""),
                title=arguments.get("title"),
                description=arguments.get("description"),
                color=arguments.get("color", 0x3498db),
                webhook_url=arguments.get("webhook_url")
            )
            return res

        elif name == "get_channel_status":
            return {
                "edition": "Lite (Open-Source)",
                "channels": {
                    "telegram": {
                        "configured": self.telegram.is_configured(),
                        "bot_token_set": bool(self.telegram.bot_token)
                    },
                    "discord": {
                        "configured": self.discord.is_configured(),
                        "webhook_set": bool(self.discord.webhook_url)
                    },
                    "whatsapp": {
                        "configured": False,
                        "note": "Available in OmniBridge Pro ($14.99): WhatsApp Cloud API, Slack BlockKit, Matrix, and Resilient WAL Queue"
                    },
                    "slack": {
                        "configured": False,
                        "note": "Available in OmniBridge Pro ($14.99)"
                    }
                }
            }
        else:
            raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        # Handle notifications (no response needed)
        if req_id is None:
            if method == "notifications/initialized":
                logger.info("Client completed initialization handshake.")
            return None

        # 1. Initialize
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": self.server_name,
                        "version": self.server_version
                    }
                }
            }

        # 2. Ping
        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }

        # 3. List tools
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": self.get_tools_definition()
                }
            }

        # 4. Call tool
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
                    "error": {
                        "code": -32000,
                        "message": str(e)
                    }
                }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    def run_stdio(self):
        """Standard IO event loop reading JSON-RPC lines from stdin and writing to stdout."""
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
            except json.JSONDecodeError as e:
                logger.error(f"Malformed JSON: {e}")
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog="omnibridge-mcp",
        description="OmniBridge MCP: Resilient Multi-Channel Notification and Webhook Server for AI Agents"
    )
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.0.0")
    args, unknown = parser.parse_known_args()
    server = OmniBridgeMCPServer()
    server.run_stdio()

if __name__ == "__main__":
    main()
