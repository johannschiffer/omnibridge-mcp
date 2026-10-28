"""
OmniBridge MCP workflow recipe.
Demonstrates WAL queue persistence, queue statistics, and active queue flush.
"""
import json
import tempfile
from pathlib import Path

from omnibridge.core.resilient_queue import ResilientQueue


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_file = Path(tmp) / "queue.db"
        queue = ResilientQueue(str(db_file))
        msg_id = queue.enqueue(
            channel="telegram",
            payload={"chat_id": "123456", "text": "Deploy completed."},
        )
        print(
            json.dumps(
                {
                    "queued_id": msg_id,
                    "pending_count": queue.count(),
                    "stats": queue.get_stats(),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
