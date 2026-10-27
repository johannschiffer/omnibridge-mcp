"""
Slack Webhook and Block Kit channel provider.
"""
import os
from typing import Dict, Any, Optional, List
import httpx
from .base import BaseChannel

class SlackChannel(BaseChannel):
    channel_name = "slack"

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "").strip()

    def is_configured(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith("https://hooks.slack.com/"))

    def send(self, text: str, header: Optional[str] = None, blocks: Optional[List[Dict[str, Any]]] = None,
             webhook_url: Optional[str] = None) -> Dict[str, Any]:
        target_url = webhook_url or self.webhook_url
        if not target_url:
            return {
                "success": False,
                "error": "SLACK_WEBHOOK_URL is not configured."
            }

        payload: Dict[str, Any] = {"text": text}

        if blocks:
            payload["blocks"] = blocks
        elif header:
            payload["blocks"] = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": header[:150]
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
                }
            ]

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(target_url, json=payload)
                if resp.status_code == 200 and resp.text.strip() == "ok":
                    return {
                        "success": True,
                        "channel": "slack",
                        "status_code": 200
                    }
                else:
                    return {
                        "success": False,
                        "channel": "slack",
                        "status_code": resp.status_code,
                        "error": resp.text
                    }
        except Exception as e:
            return {
                "success": False,
                "channel": "slack",
                "error": f"Slack request error: {str(e)}"
            }
