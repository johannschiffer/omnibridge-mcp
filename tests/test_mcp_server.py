"""
Unit tests for OmniBridge Pro MCP server JSON-RPC protocol compliance.
"""
import pytest
import json
from omnibridge.server import OmniBridgeProServer

def test_mcp_initialize(tmp_path):
    server = OmniBridgeProServer(queue_db_path=str(tmp_path / "queue.db"))
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    resp = server.handle_request(req)
    assert resp["id"] == 1
    assert "capabilities" in resp["result"]
    assert resp["result"]["serverInfo"]["name"] == "omnibridge-mcp-pro"

def test_mcp_tools_list(tmp_path):
    server = OmniBridgeProServer(queue_db_path=str(tmp_path / "queue.db"))
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    resp = server.handle_request(req)
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "send_telegram_message" in tool_names
    assert "send_discord_alert" in tool_names
    assert "send_whatsapp_message" in tool_names
    assert "send_slack_notification" in tool_names
    assert "send_matrix_message" in tool_names
    assert "send_custom_webhook" in tool_names
    assert "get_queue_stats" in tool_names
    assert "get_channel_status" in tool_names

def test_mcp_tools_call_get_channel_status(tmp_path):
    server = OmniBridgeProServer(queue_db_path=str(tmp_path / "queue.db"))
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_channel_status",
            "arguments": {}
        }
    }
    resp = server.handle_request(req)
    assert resp["id"] == 3
    content_text = resp["result"]["content"][0]["text"]
    data = json.loads(content_text)
    assert data["edition"] == "Enterprise Pro (All Channels Active)"
    assert "telegram" in data["channels"]
    assert "whatsapp" in data["channels"]
