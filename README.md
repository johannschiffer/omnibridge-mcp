# omnibridge-mcp

[![PyPI version](https://img.shields.io/pypi/v/omnibridge-mcp.svg)](https://pypi.org/project/omnibridge-mcp/)
[![CI](https://github.com/johannschiffer/omnibridge-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/johannschiffer/omnibridge-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![MCP Compliant](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io)

<a href="https://glama.ai/mcp/servers/@johannschiffer/omnibridge-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@johannschiffer/omnibridge-mcp/badge" alt="omnibridge-mcp MCP server" />
</a>

**OmniBridge MCP** is a Model Context Protocol (2024-11-05) notification and webhook gateway that lets AI agents send alerts across Telegram, Discord, Slack, WhatsApp Cloud API, Matrix, and HMAC-signed webhooks with per-channel rate limiting and a persistent SQLite WAL retry queue.

## Features

- **6 Outbound Channels**: Telegram Bot API, Discord Webhooks, Slack Block Kit Webhooks, WhatsApp Cloud API, Matrix rooms, and HMAC-SHA256 custom webhooks.
- **Outbound SSRF & Prefix Guards**: Enforces official `https://discord.com/api/webhooks/` and `https://hooks.slack.com/` prefixes even on per-call overrides, blocks loopback/RFC1918/link-local (`169.254.169.254`) webhook targets, URL-encodes Matrix room IDs, and redacts bot tokens from transport errors.
- **Persistent SQLite WAL Queue & Flush Worker**: Rate-limited and transient 5xx/network failures are stored in `~/.omnibridge/queue.db` (`0600` permissions) and retried with exponential backoff via `flush_queue` or `omnibridge-cli flush`.

## Quickstart

### Run with `uvx`

```bash
uvx omnibridge-mcp
```

### Claude Desktop / Cursor Configuration

```json
{
  "mcpServers": {
    "omnibridge-mcp": {
      "command": "uvx",
      "args": ["omnibridge-mcp"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_bot_token_here",
        "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/..."
      }
    }
  }
}
```

### CLI Diagnostics

```bash
omnibridge-cli status
omnibridge-cli flush
omnibridge-cli test --channel discord --message "OmniBridge test alert"
```

## MCP Tools Available

| Tool | Parameters | Description |
|---|---|---|
| `send_telegram_message` | `chat_id`, `text`, `disable_notification` | Send a Telegram notification with Markdown formatting |
| `send_discord_alert` | `content`, `title`, `description`, `color`, `webhook_url` | Send a Discord webhook message or rich embed |
| `send_whatsapp_message` | `to_phone`, `text`, `preview_url` | Send a WhatsApp Cloud API text message |
| `send_slack_notification` | `text`, `header`, `webhook_url` | Send a Slack Block Kit webhook notification |
| `send_matrix_message` | `body`, `room_id` | Send a Matrix room event (`m.room.message`) |
| `send_custom_webhook` | `url`, `payload`, `secret` | Deliver a JSON webhook signed with `X-OmniBridge-Signature` (`sha256=...`) |
| `get_queue_stats` | *(none)* | Return pending, retrying, delivered, and failed counts in the SQLite WAL queue |
| `flush_queue` | `max_items` | Process due messages in the SQLite WAL retry queue |
| `get_channel_status` | *(none)* | Return configuration status for all 6 channels and current queue counts |

## Genesis MCP Ecosystem

| Module | Description | Repository |
|---|---|---|
| **CrawlEngine MCP** | HTTP web extraction to clean Markdown, JSON-LD parsing, and proxy rotation | [GitHub](https://github.com/johannschiffer/crawlengine-mcp) |
| **BrowserBridge MCP** | Lightweight HTTP/DOM session automation with SHA-256 action receipts | [GitHub](https://github.com/johannschiffer/browserbridge-mcp) |
| **PgSafe MCP** | Read-only PostgreSQL/SQLite query guard, PII masking, and dry-run mutations | [GitHub](https://github.com/johannschiffer/pgsafe-mcp) |
| **OmniBridge MCP** | Multi-channel notification bus with SQLite retry queue | [GitHub](https://github.com/johannschiffer/omnibridge-mcp) |
| **SysFlow MCP** | Linux systemd inspection, confined log tailing, and port auditing | [GitHub](https://github.com/johannschiffer/sysflow-mcp) |
| **FastMCP Forge** | Zero-dependency FastMCP framework, CLI scaffolder, and SSE middleware | [GitHub](https://github.com/johannschiffer/fastmcp-forge) |

## Support

If you find this project useful, you can support maintenance on [Ko-fi](https://ko-fi.com/johannschiffer).

## License

MIT (c) 2026 [Johann Schiffer](https://github.com/johannschiffer)
