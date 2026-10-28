"""
Matrix Protocol room message provider.
"""
import os
import urllib.parse
import uuid
from typing import Any, Dict, Optional

import httpx

from ..core.url_guard import validate_outbound_url
from .base import BaseChannel


class MatrixChannel(BaseChannel):
    channel_name = "matrix"

    def __init__(
        self,
        homeserver_url: Optional[str] = None,
        access_token: Optional[str] = None,
        room_id: Optional[str] = None,
    ):
        self.homeserver = (
            homeserver_url or os.getenv("MATRIX_HOMESERVER_URL", "https://matrix.org").strip()
        ).rstrip("/")
        self.access_token = access_token or os.getenv("MATRIX_ACCESS_TOKEN", "").strip()
        self.room_id = room_id or os.getenv("MATRIX_ROOM_ID", "").strip()

    def is_configured(self) -> bool:
        return bool(self.access_token and self.room_id)

    def send(self, body: str, room_id: Optional[str] = None, msgtype: str = "m.text") -> Dict[str, Any]:
        target_room = (room_id or self.room_id or "").strip()
        if not target_room or not self.access_token:
            return {
                "success": False,
                "retryable": False,
                "error": "Matrix access token or room ID not configured.",
            }

        ok_url, reason = validate_outbound_url(self.homeserver)
        if not ok_url:
            return {
                "success": False,
                "retryable": False,
                "channel": "matrix",
                "error": reason,
            }

        encoded_room = urllib.parse.quote(target_room, safe="")
        txn_id = f"m_{uuid.uuid4().hex}"
        url = f"{self.homeserver}/_matrix/client/v3/rooms/{encoded_room}/send/m.room.message/{txn_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"msgtype": msgtype, "body": body}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.put(url, json=payload, headers=headers)
                data = resp.json()
                if resp.status_code in (200, 201) and "event_id" in data:
                    return {
                        "success": True,
                        "channel": "matrix",
                        "event_id": data["event_id"],
                    }
                return {
                    "success": False,
                    "retryable": resp.status_code in (408, 429, 500, 502, 503, 504),
                    "channel": "matrix",
                    "status_code": resp.status_code,
                    "error": data.get("error", resp.text[:500]),
                }
        except Exception as e:
            return {
                "success": False,
                "retryable": True,
                "channel": "matrix",
                "error": f"Matrix connection error: {str(e)}",
            }
