"""
Telegram Bot notification channel provider.
"""
import os
from typing import Any, Dict, Optional

import httpx

from .base import BaseChannel


class TelegramChannel(BaseChannel):
    channel_name = "telegram"

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token if bot_token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    def is_configured(self) -> bool:
        return bool(self.bot_token)

    def _scrub(self, text: str) -> str:
        if self.bot_token and self.bot_token in text:
            return text.replace(self.bot_token, "[REDACTED]")
        return text

    def send(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "Markdown",
        disable_notification: bool = False,
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "retryable": False,
                "error": "TELEGRAM_BOT_TOKEN is not configured. Set environment variable or pass token.",
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
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
                        "chat_id": chat_id,
                    }
                return {
                    "success": False,
                    "retryable": resp.status_code in (408, 429, 500, 502, 503, 504),
                    "channel": "telegram",
                    "error": self._scrub(str(data.get("description", resp.text[:500]))),
                    "status_code": resp.status_code,
                }
        except Exception as e:
            return {
                "success": False,
                "retryable": True,
                "channel": "telegram",
                "error": f"Connection error: {self._scrub(str(e))}",
            }
