# omnibridge-mcp (v1.0.0)

[![PyPI version](https://img.shields.io/badge/PyPI-v1.0.0-blue.svg)](https://pypi.org/project/omnibridge-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Support on Ko-fi](https://img.shields.io/badge/Support%20on-Ko--fi-ff5e5b.svg)](https://ko-fi.com/johannschiffer)

<a href="https://glama.ai/mcp/servers/@johannschiffer/omnibridge-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@johannschiffer/omnibridge-mcp/badge" alt="omnibridge-mcp MCP server" />
</a>

[![PyPI](https://img.shields.io/pypi/v/omnibridge-mcp.svg)](https://pypi.org/project/omnibridge-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![MCP Compliant](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io)

**OmniBridge MCP** is a lightweight, zero-latency Model Context Protocol server that gives AI agents (in **Claude Desktop**, **Cursor**, **Windsurf**, and **Antigravity**) direct, controlled access to send real-time alerts, operational notifications, and webhooks without exposing your primary API keys or relying on bloated middleware.

---

## Run without cloning

```bash
uvx omnibridge-mcp
```

Claude Desktop / Cursor config entry:

```json
{
  "mcpServers": {
    "omnibridge-mcp": {
      "command": "uvx",
      "args": [
        "omnibridge-mcp"
      ]
    }
  }
}
```

[![CI](https://github.com/johannschiffer/omnibridge-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/johannschiffer/omnibridge-mcp/actions/workflows/ci.yml)

## Features

- 📱 **Telegram Bot API**: Direct message and alert delivery.
- 💬 **Discord Webhooks**: Embedded message alerts with custom colors and titles.
- 💬 **WhatsApp Cloud API & Slack Block Kit**: Multi-channel business messaging support.
- 🌐 **Matrix Protocol Rooms**: Decentralized notification dispatching.
- 🔐 **Custom Webhooks with HMAC**: Cryptographic signature validation for webhook buses.
- 💾 **Offline WAL Resilient Queue**: SQLite WAL persistent queue with zero message loss.
- ⚡ **Adaptive Rate Limiting**: Anti-ban protection and exponential backoff.
- 🐳 **Production Docker & Compose**: Containerized multi-channel gateway.
---

## 🚀 Quick Setup in 2 Minutes

### 1. Installation

```bash
git clone https://github.com/johannschiffer/omnibridge-mcp.git
cd omnibridge-mcp
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file or export variables in your shell:

```bash
# Telegram Bot Token (from @BotFather)
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"

# Discord Webhook URL (from Channel Settings -> Integrations -> Webhooks)
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

### 3. Verify with CLI

```bash
# Check channels configuration
python -m omnibridge.cli status

# Send a test alert to Discord
python -m omnibridge.cli test --channel discord --message "OmniBridge is live!"
```

---

## 🖥️ Client Configuration

### Claude Desktop (`claude_desktop_config.json`)

On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`  
On Windows: `%APPDATA%\Claude\claude_desktop_config.json`  
On Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "omnibridge": {
      "command": "python",
      "args": ["-m", "omnibridge.server"],
      "cwd": "/path/to/omnibridge-mcp",
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_bot_token_here",
        "DISCORD_WEBHOOK_URL": "your_discord_webhook_url_here"
      }
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "omnibridge": {
      "command": "python -m omnibridge.server",
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_bot_token_here",
        "DISCORD_WEBHOOK_URL": "your_discord_webhook_url_here"
      }
    }
  }
}
```

---

## 🛠️ MCP Tools Available

| Tool | Parameters | Description |
|---|---|---|
| `send_telegram_message` | `chat_id`, `text`, `disable_notification` | Sends Telegram notification with Markdown support |
| `send_discord_alert` | `content`, `title`, `description`, `color`, `webhook_url` | Sends Discord rich embed card |
| `get_channel_status` | *(none)* | Returns connectivity and health of all channels |

---

## Genesis MCP Ecosystem

| Module | Description | Repository |
|---|---|---|
| **CrawlEngine MCP** | Anti-bot web scraping, clean Markdown, proxy rotation, and TLS evasion | [GitHub](https://github.com/johannschiffer/crawlengine-mcp) |
| **BrowserBridge MCP** | Deterministic headless browser automation with cryptographic action receipts | [GitHub](https://github.com/johannschiffer/browserbridge-mcp) |
| **PgSafe MCP** | Zero-trust PostgreSQL/SQLite guard, live PII masking, and schema inspection | [GitHub](https://github.com/johannschiffer/pgsafe-mcp) |
| **OmniBridge MCP** | Multi-channel notification bus with persistent SQLite queue | [GitHub](https://github.com/johannschiffer/omnibridge-mcp) |
| **SysFlow MCP** | Safe Linux administration, systemd automation, and port auditing | [GitHub](https://github.com/johannschiffer/sysflow-mcp) |
| **FastMCP Forge** | Production FastMCP server scaffolder with stdio and SSE middleware | [GitHub](https://github.com/johannschiffer/fastmcp-forge) |

## Support

If you find this project helpful, you can support its ongoing maintenance on [Ko-fi](https://ko-fi.com/johannschiffer).

## License

MIT © 2026 [Johann Schiffer](https://github.com/johannschiffer)
