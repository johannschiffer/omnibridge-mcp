# omnibridge-mcp (v2.0.0)

[![PyPI version](https://img.shields.io/badge/PyPI-v2.0.0-blue.svg)](https://pypi.org/project/omnibridge-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Support on Ko-fi](https://img.shields.io/badge/Support%20on-Ko--fi-ff5e5b.svg)](https://ko-fi.com/johannschiffer)

> **100% Free & Open Source (MIT)**: All features, proxy rotation, migration simulation, Docker stacks, and recipes are completely unlocked. Support open development on [Ko-fi](https://ko-fi.com/johannschiffer).


> 

> ### ⚡ Enterprise Infrastructure & Tooling
> | Component | Pricing | Delivery / Direct Access |
> |---|---|---|
> | **Starter Kit** | **Free ($0+)** | 25+ `.cursorrules`, `CLAUDE.md` stack rules & MCP config templates. [Download Free](https://github.com/johannschiffer) |
> | **Enterprise Suite Pro** | **$9 Early Access** ~~$19~~ | 6 Pro MCP Servers, Zero-Downtime DB migrations, Residential Proxies, Docker Compose Stack & Commercial License. [Get Early Access ($9)](https://github.com/johannschiffer) |
> | **Config Generator** | **Free Web Tool** | Interactive visual config generator for Claude Desktop & Cursor. [Open Generator](https://johannschiffer.github.io/) |


<a href="https://glama.ai/mcp/servers/@johannschiffer/omnibridge-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@johannschiffer/omnibridge-mcp/badge" alt="omnibridge-mcp MCP server" />
</a>



[![PyPI](https://img.shields.io/pypi/v/omnibridge-mcp.svg)](https://pypi.org/project/omnibridge-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![MCP Compliant](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io)


> ### ⚡ Enterprise Infrastructure & Tooling
> | Package | Access | Features |
> |---|---|---|
> | **Starter Kit** | **Free ($0+)** | 25+ `.cursorrules`, `CLAUDE.md` stack rules & MCP config templates. [Download Free](https://github.com/johannschiffer) |
> | **Enterprise Suite Pro** | **Free MIT** | 6 Pro MCP Servers, Zero-Downtime DB migrations, Residential Proxies, Docker Compose Stack & Commercial License. [Get Pro License](https://github.com/johannschiffer) |
> | **Config Generator** | **Free Web Tool** | Interactive visual config generator for Claude Desktop & Cursor. [Open Generator](https://johannschiffer.github.io/) |

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

## ⚡ Key Features (Open Source v2.0)

- 🚀 **Zero Heavy Dependencies**: Pure Python implementation with minimal footprint (`httpx`).
- 💬 **Telegram Bot API**: Send markdown-formatted alerts, silent notifications, and direct messages.
- 🎮 **Discord Webhooks**: Send rich embed cards with custom colors, titles, and timestamps.
- 🔌 **Universal Compatibility**: Works out of the box with any MCP-compliant client via standard IO (`stdio`).
- 🧪 **Built-in CLI**: Interactive test tool to verify credentials and channel delivery in seconds.

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

## 💎 Need Enterprise Features? Upgrade to OmniBridge Pro

Looking for production-grade reliability, business messaging, and fault tolerance?

| Feature | v1.0 (Legacy) | v2.0 (Open Source) |
|---|:---:|:---:|
| **Telegram Bot API** | ✅ | ✅ |
| **Discord Webhooks** | ✅ | ✅ |
| **WhatsApp Cloud API** | ❌ | ✅ |
| **Slack Block Kit & Webhooks** | ❌ | ✅ |
| **Matrix Protocol Rooms** | ❌ | ✅ |
| **Custom Webhooks with HMAC** | ❌ | ✅ |
| **Offline WAL Resilient Queue** *(Zero Message Loss)* | ❌ | ✅ |
| **Adaptive Rate Limiting** *(Anti-ban protection)* | ❌ | ✅ |
| **Production Docker & Compose** | ❌ | ✅ |
| **Full Pytest Suite & Architecture PDF** | ❌ | ✅ |



---


## Solución Enterprise (Genesis Suite)

Para despliegues en producción y cargas intensivas con bypass de rate limits, soporte multi-tenant y configuraciones Docker precompiladas:

- **Bypass de Rate Limits & IP Rotation:** Bus de notificaciones y webhooks multi-tenant con cola SQLite WAL de alta disponibilidad y reintentos.
- **Soporte Multi-Tenant & RBAC:** Control de accesos granular, gestión de secretos y auditoría criptográfica.
- **Docker Compose Stacks:** Contenedores precompilados y configuraciones listas para producción con orquestación autónoma.

  



## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

## Genesis MCP Ecosystem

| Module | What it does | Repo |
|---|---|---|
| **CrawlEngine MCP** | Anti-bot web scraping, clean Markdown, proxy rotation and TLS evasion | [GitHub](https://github.com/johannschiffer/crawlengine-mcp) |
| **BrowserBridge MCP** | Deterministic headless browser automation with cryptographic action receipts | [GitHub](https://github.com/johannschiffer/browserbridge-mcp) |
| **PgSafe MCP** | Zero-trust PostgreSQL/SQLite guard, live PII masking, zero-downtime migration checks | [GitHub](https://github.com/johannschiffer/pgsafe-mcp) |
| **OmniBridge MCP** (this repo) | Multi-channel notification and webhook bus with a persistent SQLite WAL queue | [GitHub](https://github.com/johannschiffer/omnibridge-mcp) |
| **SysFlow MCP** | Safe Linux administration plane: systemd, port audit, isolated execution | [GitHub](https://github.com/johannschiffer/sysflow-mcp) |
| **FastMCP Forge** | Production MCP server scaffolder: stdio, SSE and auth middleware | [GitHub](https://github.com/johannschiffer/fastmcp-forge) |

[Live config builder](https://johannschiffer.github.io) | [GitHub Profile](https://github.com/johannschiffer) | [Support on Ko-fi ☕](https://ko-fi.com/johannschiffer)

## Recommended Infrastructure & Sponsorship

- **Sponsorship & Corporate Support**: Support continued maintenance and priority feature requests via [GitHub Sponsors](https://github.com/sponsors/johannschiffer).
- **Verified Cloud & Network Infrastructure**:
  - **High-Performance VPS & Nodes**: [Hetzner Cloud](https://www.hetzner.com/cloud) & [DigitalOcean](https://m.do.co/c/johannschiffer)
  - **Reliable Proxy Pool & IP Rotation**: [Webshare](https://www.webshare.io/) & [Bright Data](https://brightdata.com/)
  - **Documentation & Setup Guides**: [johannschiffer.github.io](https://johannschiffer.github.io/)