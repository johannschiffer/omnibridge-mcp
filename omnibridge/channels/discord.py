"""
Discord Webhook notification channel provider.
"""
import os
from typing import Any, Dict, Optional

import httpx

from .base import BaseChannel

_DISCORD_PREFIXES = (
    "https://discord.com/api/webhooks/",
    "https://discordapp.com/api/webhooks/",
)


class DiscordChannel(BaseChannel):
    channel_name = "discord"

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    def is_configured(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith(_DISCORD_PREFIXES))

    def send(
        self,
        content: str = "",
        username: str = "OmniBridge AI",
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: int = 0x3498DB,
        webhook_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_url = (webhook_url or self.webhook_url or "").strip()
        if not target_url:
            return {
                "success": False,
                "retryable": False,
                "error": "DISCORD_WEBHOOK_URL is not configured.",
            }
        if not target_url.startswith(_DISCORD_PREFIXES):
            return {
                "success": False,
                "retryable": False,
                "error": "Invalid Discord webhook URL: must start with https://discord.com/api/webhooks/.",
            }

        payload: Dict[str, Any] = {"username": username}
        if content:
            payload["content"] = content

        if title or description:
            payload["embeds"] = [
                {
                    "title": title or "Notification",
                    "description": description or "",
                    "color": color,
                }
            ]

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(target_url, json=payload)
                if resp.status_code in (200, 204):
                    return {
                        "success": True,
                        "channel": "discord",
                        "status_code": resp.status_code,
                    }
                return {
                    "success": False,
                    "retryable": resp.status_code in (408, 429, 500, 502, 503, 504),
                    "channel": "discord",
                    "status_code": resp.status_code,
                    "error": resp.text[:500],
                }
        except Exception as e:
            return {
                "success": False,
                "retryable": True,
                "channel": "discord",
                "error": f"Discord request failed: {str(e)}",
            }
