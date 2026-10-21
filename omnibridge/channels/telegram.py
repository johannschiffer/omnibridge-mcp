"""
Telegram Bot notification channel provider.
"""
import os
from typing import Dict, Any, Optional
import httpx
from .base import BaseChannel

class TelegramChannel(BaseChannel):
    channel_name = "telegram"

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    def is_configured(self) -> bool:
        return bool(self.bot_token)

    def send(self, chat_id: str, text: str, parse_mode: str = "Markdown", disable_notification: bool = False) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "TELEGRAM_BOT_TOKEN is not configured. Set environment variable or pass token."
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload)
                data = resp.json()
                if resp.status_code == 200 and data.get("ok"):
                    return {
                        "success": True,
                        "channel": "telegram",
                        "message_id": data.get("result", {}).get("message_id"),
                        "chat_id": chat_id
                    }
                else:
                    return {
                        "success": False,
                        "channel": "telegram",
                        "error": data.get("description", resp.text),
                        "status_code": resp.status_code
                    }
        except Exception as e:
            return {
                "success": False,
                "channel": "telegram",
                "error": f"Connection error: {str(e)}"
            }
