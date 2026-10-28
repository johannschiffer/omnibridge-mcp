"""
Security and queue reliability tests for omnibridge-mcp v2.0.1.
"""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from omnibridge import __version__
from omnibridge.channels.discord import DiscordChannel
from omnibridge.channels.matrix import MatrixChannel
from omnibridge.channels.slack import SlackChannel
from omnibridge.channels.telegram import TelegramChannel
from omnibridge.channels.webhook import CustomWebhookChannel
from omnibridge.core.resilient_queue import ResilientQueue
from omnibridge.server import OmniBridgeServer


def test_ssrf_blocked_on_webhook_and_override_prefixes():
    wh = CustomWebhookChannel()
    for blocked in (
        "http://127.0.0.1:8080/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:9000/hook",
        "file:///etc/passwd",
        "http://2130706433/secret",
    ):
        res = wh.send(payload={"x": 1}, url=blocked)
        assert res["success"] is False
        assert res["retryable"] is False

    dc = DiscordChannel()
    bad_dc = dc.send(content="hi", webhook_url="http://169.254.169.254/steal")
    assert bad_dc["success"] is False
    assert "discord.com/api/webhooks" in bad_dc["error"]

    sl = SlackChannel()
    bad_sl = sl.send(text="hi", webhook_url="https://evil.example.com/hook")
    assert bad_sl["success"] is False
    assert "hooks.slack.com" in bad_sl["error"]


@patch("httpx.Client.put")
def test_matrix_room_id_url_encoded(mock_put):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"event_id": "$ev1"}
    mock_put.return_value = mock_resp

    mx = MatrixChannel(access_token="tok", room_id="!abc:matrix.org")
    res = mx.send(body="hello", room_id="!room/../../admin:matrix.org")
    assert res["success"] is True
    called_url = mock_put.call_args[0][0]
    assert "%21room%2F..%2F..%2Fadmin%3Amatrix.org" in called_url


@patch("httpx.Client.post")
def test_telegram_exception_scrubs_bot_token(mock_post):
    secret_token = "999888777:SECRET_BOT_TOKEN_ABC"
    mock_post.side_effect = RuntimeError(f"Failed POST https://api.telegram.org/bot{secret_token}/sendMessage")

    tg = TelegramChannel(bot_token=secret_token)
    res = tg.send(chat_id="123", text="ping")
    assert res["success"] is False
    assert secret_token not in res["error"]
    assert "[REDACTED]" in res["error"]


def test_queue_permissions_and_flush_worker(tmp_path):
    db_file = tmp_path / "secure_queue.db"
    srv = OmniBridgeServer(queue_db_path=str(db_file))
    mode = stat.S_IMODE(os.stat(db_file).st_mode)
    assert mode == 0o600

    # Permanent configuration failure must NOT be queued
    unconf = srv.handle_tool_call("send_telegram_message", {"chat_id": "1", "text": "hello"})
    assert unconf["success"] is False
    assert srv.queue.count() == 0

    # Enqueue a message and flush it via mocked Discord transport
    srv.queue.enqueue(
        "discord",
        {
            "content": "Queued alert",
            "webhook_url": "https://discord.com/api/webhooks/111/222",
        },
    )
    assert srv.queue.count() == 1

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_post.return_value = mock_resp

        flush_res = srv.handle_tool_call("flush_queue", {"max_items": 10})
        assert flush_res["delivered"] == 1
        assert srv.queue.count() == 0
        assert srv.queue.get_stats()["delivered"] == 1


def test_cli_version_and_parse_error(tmp_path):
    repo_root = str(Path(__file__).resolve().parents[1])
    env = {**os.environ, "PYTHONPATH": repo_root, "OMNIBRIDGE_QUEUE_DB": str(tmp_path / "q.db")}

    ver = subprocess.run(
        [sys.executable, "-m", "omnibridge.server", "--version"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert ver.returncode == 0
    assert __version__ in ver.stdout

    proc = subprocess.run(
        [sys.executable, "-m", "omnibridge.server"],
        input="{not-valid-json\n",
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    err = json.loads(proc.stdout.strip())
    assert err["error"]["code"] == -32700
