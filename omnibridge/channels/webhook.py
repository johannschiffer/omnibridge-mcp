"""
Custom enterprise webhook provider with HMAC-SHA256 signature support (Pro Feature).
"""
import os
import time
import hmac
import hashlib
import json
from typing import Dict, Any, Optional
import httpx
from .base import BaseChannel

class CustomWebhookChannel(BaseChannel):
    channel_name = "webhook"

    def __init__(self, default_url: Optional[str] = None, secret_key: Optional[str] = None):
        self.default_url = default_url or os.getenv("WEBHOOK_ENDPOINT_URL", "").strip()
        self.secret_key = secret_key or os.getenv("WEBHOOK_SECRET_KEY", "").strip()

    def is_configured(self) -> bool:
        return bool(self.default_url)

    def send(self, payload: Dict[str, Any], url: Optional[str] = None, 
             secret: Optional[str] = None, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        target_url = url or self.default_url
        if not target_url:
            return {
                "success": False,
                "error": "Target webhook URL is required."
            }

        signing_secret = secret or self.secret_key
        raw_body = json.dumps(payload, ensure_ascii=False)
        timestamp = str(int(time.time()))

        headers = {
            "Content-Type": "application/json",
            "X-OmniBridge-Timestamp": timestamp,
            "User-Agent": "OmniBridge-Webhook/1.0"
        }

        if signing_secret:
            signature_data = f"{timestamp}:{raw_body}".encode("utf-8")
            digest = hmac.new(signing_secret.encode("utf-8"), signature_data, hashlib.sha256).hexdigest()
            headers["X-OmniBridge-Signature"] = f"sha256={digest}"

        if custom_headers:
            headers.update(custom_headers)

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(target_url, content=raw_body, headers=headers)
                return {
                    "success": resp.status_code in (200, 201, 202, 204),
                    "channel": "webhook",
                    "status_code": resp.status_code,
                    "response_body": resp.text[:500]
                }
        except Exception as e:
            return {
                "success": False,
                "channel": "webhook",
                "error": f"Webhook delivery error: {str(e)}"
            }
