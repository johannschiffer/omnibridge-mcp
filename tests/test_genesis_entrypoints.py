import json
import sqlite3
import subprocess
import sys

from omnibridge.server import OmniBridgeServer


def test_notice_is_silent():
    res = subprocess.run([sys.executable, "-c", "import omnibridge._genesis; omnibridge._genesis.print_upgrade_notice()"], capture_output=True, text=True)
    assert res.stderr == ""
    assert res.stdout == ""
    import omnibridge._genesis
    assert omnibridge._genesis.NOTICE == ""


def test_blackbox_bridge_records_mcp_and_http_events(monkeypatch, tmp_path):
    wal_db = tmp_path / "wal.sqlite"
    monkeypatch.setenv("BLACKBOX_DB_PATH", str(wal_db))

    server = OmniBridgeServer(queue_db_path=str(tmp_path / "queue.db"))
    status_res = server.handle_tool_call("get_channel_status", {})
    assert "channels" in status_res

    webhook_res = server.handle_tool_call(
        "send_custom_webhook",
        {"url": "http://127.0.0.1:8080/hook", "payload": {"msg": "test"}, "secret": "super-secret"},
    )
    assert webhook_res["success"] is False

    wal_conn = sqlite3.connect(str(wal_db))
    rows = wal_conn.execute(
        "SELECT event_type, source, status, payload FROM blackbox_events ORDER BY id ASC;"
    ).fetchall()
    wal_conn.close()

    assert len(rows) == 2
    assert rows[0][0] == "MCP_TOOL"
    assert rows[0][1] == "omnibridge-mcp"
    assert rows[0][2] == "ok"
    assert json.loads(rows[0][3])["tool"] == "get_channel_status"

    assert rows[1][0] == "HTTP_CLIENT"
    assert rows[1][1] == "omnibridge-mcp"
    assert rows[1][2] == "error"
    http_payload = json.loads(rows[1][3])
    assert http_payload["tool"] == "send_custom_webhook"
    assert http_payload["channel"] == "webhook"
    assert "url" not in http_payload
    assert "super-secret" not in rows[1][3]
    assert "8080/hook" not in rows[1][3]
