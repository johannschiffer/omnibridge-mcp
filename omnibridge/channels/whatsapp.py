"""
WhatsApp Cloud API channel provider.
Supports direct messaging to phone numbers via Meta Graph API.
"""
import os
from typing import Dict, Any, Optional
import httpx
from .base import BaseChannel

class WhatsAppChannel(BaseChannel):
    channel_name = "whatsapp"

    def __init__(self, phone_number_id: Optional[str] = None, access_token: Optional[str] = None):
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v19.0").strip()

    def is_configured(self) -> bool:
        return bool(self.phone_number_id and self.access_token)

    def send(self, to_phone: str, text: str, preview_url: bool = False) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "WHATSAPP_PHONE_NUMBER_ID or WHATSAPP_ACCESS_TOKEN is not configured."
            }

        clean_phone = "".join(filter(str.isdigit, to_phone))
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text
            }
        }

        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, json=payload, headers=headers)
                data = resp.json()
                if resp.status_code in (200, 201):
                    msg_id = data.get("messages", [{}])[0].get("id")
                    return {
                        "success": True,
                        "channel": "whatsapp",
                        "message_id": msg_id,
                        "recipient": clean_phone
                    }
                else:
                    return {
                        "success": False,
                        "channel": "whatsapp",
                        "status_code": resp.status_code,
                        "error": data.get("error", {}).get("message", resp.text)
                    }
        except Exception as e:
            return {
                "success": False,
                "channel": "whatsapp",
                "error": f"WhatsApp API connection error: {str(e)}"
            }
