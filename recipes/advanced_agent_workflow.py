from omnibridge.core.resilient_queue import ResilientQueue
from omnibridge.channels.telegram import TelegramChannel

def main():
    queue = ResilientQueue()
    queue.enqueue(
        channel="telegram",
        payload={"chat_id": "123456", "text": "Deploy completed successfully! 🚀"}
    )
    print("Enqueued notification to persistent SQLite WAL buffer. Pending items:", queue.count())

if __name__ == "__main__":
    main()
