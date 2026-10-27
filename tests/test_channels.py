"""
Unit tests for OmniBridge notification channel providers.
"""
import pytest
import hmac
import hashlib
import json
from unittest.mock import patch, MagicMock
from omnibridge.channels.telegram import TelegramChannel
from omnibridge.channels.discord import DiscordChannel
from omnibridge.channels.whatsapp import WhatsAppChannel
from omnibridge.channels.slack import SlackChannel
from omnibridge.channels.matrix import MatrixChannel
from omnibridge.channels.webhook import CustomWebhookChannel

def test_telegram_unconfigured():
    tg = TelegramChannel(bot_token="")
    res = tg.send(chat_id="123", text="Hello")
    assert res["success"] is False
    assert "not configured" in res["error"]

@patch("httpx.Client.post")
def test_telegram_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True, "result": {"message_id": 42}}
    mock_post.return_value = mock_resp

    tg = TelegramChannel(bot_token="fake_token")
    res = tg.send(chat_id="999", text="Deployment successful")
    assert res["success"] is True
    assert res["message_id"] == 42

@patch("httpx.Client.post")
def test_discord_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 204
    mock_post.return_value = mock_resp

    dc = DiscordChannel(webhook_url="https://discord.com/api/webhooks/123/abc")
    res = dc.send(title="Alert", description="System nominal")
    assert res["success"] is True

@patch("httpx.Client.post")
def test_whatsapp_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"messages": [{"id": "wamid.HBgL"}]}
    mock_post.return_value = mock_resp

    wa = WhatsAppChannel(phone_number_id="109283", access_token="wa_token")
    res = wa.send(to_phone="+14155552671", text="Production deployment complete.")
    assert res["success"] is True
    assert res["message_id"] == "wamid.HBgL"

@patch("httpx.Client.post")
def test_slack_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "ok"
    mock_post.return_value = mock_resp

    sl = SlackChannel(webhook_url="https://hooks.slack.com/services/T00/B00/X00")
    res = sl.send(text="Backup verified", header="Backup Alert")
    assert res["success"] is True

@patch("httpx.Client.put")
def test_matrix_success(mock_put):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"event_id": "$event_12345"}
    mock_put.return_value = mock_resp

    mx = MatrixChannel(access_token="mx_tok", room_id="!room:matrix.org")
    res = mx.send(body="Server rebooted")
    assert res["success"] is True
    assert res["event_id"] == "$event_12345"

@patch("httpx.Client.post")
def test_custom_webhook_hmac_signature(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "OK"
    mock_post.return_value = mock_resp

    secret = "my_super_secret"
    wh = CustomWebhookChannel()
    payload = {"event": "model_trained", "accuracy": 0.98}
    res = wh.send(url="https://api.example.com/webhook", payload=payload, secret=secret)
    assert res["success"] is True

    # Validate that signature header was passed
    args, kwargs = mock_post.call_args
    headers = kwargs["headers"]
    assert "X-OmniBridge-Signature" in headers
    assert headers["X-OmniBridge-Signature"].startswith("sha256=")
