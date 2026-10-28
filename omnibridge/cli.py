"""
OmniBridge CLI diagnostic and queue management tool.
Usage:
  omnibridge-cli status
  omnibridge-cli flush
  omnibridge-cli test --channel discord --webhook <URL> --message "Hello from OmniBridge"
"""

import argparse
import json
import sys

from . import __version__
from .channels import DiscordChannel, TelegramChannel
from .server import OmniBridgeServer


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="omnibridge-cli",
        description="OmniBridge CLI utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="version", version=f"omnibridge-cli {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    subparsers.add_parser("status", help="Check channel configuration and queue status")
    flush_parser = subparsers.add_parser("flush", help="Process due messages in the SQLite WAL queue")
    flush_parser.add_argument("--max-items", type=int, default=20, help="Maximum messages to process")

    test_parser = subparsers.add_parser("test", help="Send a test notification")
    test_parser.add_argument("--channel", choices=["telegram", "discord"], required=True, help="Target channel")
    test_parser.add_argument("--message", default="Test alert from OmniBridge CLI", help="Message to send")
    test_parser.add_argument("--token", help="Telegram bot token (optional, falls back to env)")
    test_parser.add_argument("--chat-id", help="Telegram chat ID")
    test_parser.add_argument("--webhook", help="Discord webhook URL (optional, falls back to env)")

    args = parser.parse_args()

    if args.command == "status":
        srv = OmniBridgeServer()
        print(json.dumps(srv.handle_tool_call("get_channel_status", {}), indent=2))
    elif args.command == "flush":
        srv = OmniBridgeServer()
        print(json.dumps(srv.process_pending_queue(max_items=args.max_items), indent=2))
    elif args.command == "test":
        if args.channel == "telegram":
            if not args.chat_id:
                print("Error: --chat-id is required for telegram test", file=sys.stderr)
                sys.exit(1)
            tg = TelegramChannel(bot_token=args.token)
            res = tg.send(chat_id=args.chat_id, text=args.message)
            print(json.dumps(res, indent=2))
        elif args.channel == "discord":
            dc = DiscordChannel(webhook_url=args.webhook)
            res = dc.send(title="OmniBridge Test", description=args.message)
            print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
