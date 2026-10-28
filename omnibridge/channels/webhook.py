"""
Custom webhook provider with HMAC-SHA256 signature support and SSRF protection.
"""
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

import httpx

from .. import __version__
from ..core.url_guard import validate_outbound_url
from .base import BaseChannel


class CustomWebhookChannel(BaseChannel):
    channel_name = "webhook"

    def __init__(self, default_url: Optional[str] = None, secret_key: Optional[str] = None):
        self.default_url = default_url or os.getenv("WEBHOOK_ENDPOINT_URL", "").strip()
        self.secret_key = secret_key or os.getenv("WEBHOOK_SECRET_KEY", "").strip()

    def is_configured(self) -> bool:
        return bool(self.default_url)

    def send(
        self,
        payload: Dict[str, Any],
        url: Optional[str] = None,
        secret: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        target_url = (url or self.default_url or "").strip()
        if not target_url:
            return {
                "success": False,
                "retryable": False,
                "error": "Target webhook URL is required.",
            }

        ok_url, reason = validate_outbound_url(target_url)
        if not ok_url:
            return {
                "success": False,
                "retryable": False,
                "channel": "webhook",
                "error": reason,
            }

        signing_secret = secret or self.secret_key
        raw_body = json.dumps(payload, ensure_ascii=False)
        timestamp = str(int(time.time()))

        headers: Dict[str, str] = {}
        if custom_headers:
            for k, v in custom_headers.items():
                headers[str(k)] = str(v)

        headers["Content-Type"] = "application/json"
        headers["X-OmniBridge-Timestamp"] = timestamp
        headers["User-Agent"] = f"OmniBridge-Webhook/{__version__}"

        if signing_secret:
            signature_data = f"{timestamp}:{raw_body}".encode("utf-8")
            digest = hmac.new(signing_secret.encode("utf-8"), signature_data, hashlib.sha256).hexdigest()
            headers["X-OmniBridge-Signature"] = f"sha256={digest}"

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(target_url, content=raw_body, headers=headers)
                succeeded = resp.status_code in (200, 201, 202, 204)
                return {
                    "success": succeeded,
                    "retryable": (not succeeded) and resp.status_code in (408, 429, 500, 502, 503, 504),
                    "channel": "webhook",
                    "status_code": resp.status_code,
                    "response_body": resp.text[:500],
                }
        except Exception as e:
            return {
                "success": False,
                "retryable": True,
                "channel": "webhook",
                "error": f"Webhook delivery error: {str(e)}",
            }
