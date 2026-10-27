"""
Resilient WAL-backed Queue Engine (OmniBridge Pro Core).
Ensures zero message loss during transient network partitions, API outages, or rate-limiting.
"""
import os
import json
import sqlite3
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

DEFAULT_QUEUE_DB = Path.home() / ".omnibridge" / "queue.db"

class ResilientQueue:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_QUEUE_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS message_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    retries INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 5,
                    next_retry_at REAL NOT NULL,
                    last_error TEXT,
                    created_at REAL NOT NULL,
                    delivered_at REAL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_status_retry ON message_queue(status, next_retry_at);")
            conn.commit()

    def enqueue(self, channel: str, payload: Dict[str, Any], max_retries: int = 5) -> int:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO message_queue (channel, payload_json, status, retries, max_retries, next_retry_at, created_at)
                VALUES (?, ?, 'pending', 0, ?, ?, ?)
            """, (channel, json.dumps(payload), max_retries, now, now))
            conn.commit()
            return cursor.lastrowid

    def fetch_pending(self, limit: int = 20) -> List[Dict[str, Any]]:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, channel, payload_json, retries, max_retries
                FROM message_queue
                WHERE status IN ('pending', 'retrying') AND next_retry_at <= ?
                ORDER BY next_retry_at ASC
                LIMIT ?
            """, (now, limit))
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "channel": r["channel"],
                    "payload": json.loads(r["payload_json"]),
                    "retries": r["retries"],
                    "max_retries": r["max_retries"]
                }
                for r in rows
            ]

    def mark_delivered(self, msg_id: int):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE message_queue
                SET status = 'delivered', delivered_at = ?
                WHERE id = ?
            """, (time.time(), msg_id))
            conn.commit()

    def mark_retry(self, msg_id: int, current_retries: int, max_retries: int, error: str):
        next_retries = current_retries + 1
        if next_retries >= max_retries:
            status = 'failed'
            next_retry = time.time() + 86400 * 365 # Never retry automatically
        else:
            status = 'retrying'
            backoff_seconds = (2 ** next_retries) * 5 # 10s, 20s, 40s, 80s
            next_retry = time.time() + backoff_seconds

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE message_queue
                SET status = ?, retries = ?, next_retry_at = ?, last_error = ?
                WHERE id = ?
            """, (status, next_retries, next_retry, str(error)[:500], msg_id))
            conn.commit()

    def get_stats(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as c
                FROM message_queue
                GROUP BY status
            """)
            counts = {r["status"]: r["c"] for r in cursor.fetchall()}
            return {
                "pending": counts.get("pending", 0),
                "retrying": counts.get("retrying", 0),
                "delivered": counts.get("delivered", 0),
                "failed": counts.get("failed", 0)
            }
