"""
Discord Webhook notification channel provider.
"""
import os
from typing import Dict, Any, Optional
import httpx
from .base import BaseChannel

class DiscordChannel(BaseChannel):
    channel_name = "discord"

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    def is_configured(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith("https://discord.com/api/webhooks/"))

    def send(self, content: str = "", username: str = "OmniBridge AI", 
             title: Optional[str] = None, description: Optional[str] = None, 
             color: int = 0x3498db, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        
        target_url = webhook_url or self.webhook_url
        if not target_url:
            return {
                "success": False,
                "error": "DISCORD_WEBHOOK_URL is not configured."
            }

        payload: Dict[str, Any] = {"username": username}
        if content:
            payload["content"] = content

        if title or description:
            embed = {
                "title": title or "Notification",
                "description": description or "",
                "color": color
            }
            payload["embeds"] = [embed]

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(target_url, json=payload)
                if resp.status_code in (200, 204):
                    return {
                        "success": True,
                        "channel": "discord",
                        "status_code": resp.status_code
                    }
                else:
                    return {
                        "success": False,
                        "channel": "discord",
                        "status_code": resp.status_code,
                        "error": resp.text
                    }
        except Exception as e:
            return {
                "success": False,
                "channel": "discord",
                "error": f"Discord request failed: {str(e)}"
            }
