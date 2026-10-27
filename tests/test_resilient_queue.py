"""
Unit tests for OmniBridge resilient WAL queue.
"""
import pytest
import time
from omnibridge.core.resilient_queue import ResilientQueue

def test_queue_enqueue_and_fetch(tmp_path):
    db_file = tmp_path / "test_queue.db"
    queue = ResilientQueue(str(db_file))

    # Initial stats empty
    stats = queue.get_stats()
    assert stats["pending"] == 0

    # Enqueue 2 items
    id1 = queue.enqueue("telegram", {"chat_id": "1", "text": "Msg 1"})
    id2 = queue.enqueue("whatsapp", {"to_phone": "2", "text": "Msg 2"})
    assert id1 is not None and id2 is not None

    items = queue.fetch_pending(limit=10)
    assert len(items) == 2
    assert items[0]["channel"] == "telegram"
    assert items[1]["channel"] == "whatsapp"

    # Mark first item delivered
    queue.mark_delivered(id1)
    stats = queue.get_stats()
    assert stats["delivered"] == 1
    assert stats["pending"] == 1

    # Mark second item retry
    queue.mark_retry(id2, current_retries=0, max_retries=3, error="Rate limit")
    stats = queue.get_stats()
    assert stats["retrying"] == 1

    # Max retries exceeded marks as failed
    queue.mark_retry(id2, current_retries=2, max_retries=3, error="Permanent failure")
    stats = queue.get_stats()
    assert stats["failed"] == 1
