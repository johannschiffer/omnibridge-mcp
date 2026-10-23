"""
OmniBridge CLI testing tool.
Usage:
  python -m omnibridge.cli status
  python -m omnibridge.cli test --channel discord --webhook <URL> --message "Hello from OmniBridge"
  python -m omnibridge.cli test --channel telegram --token <TOKEN> --chat-id <ID> --message "Hello"
"""

import argparse
import json
import sys
from .channels import TelegramChannel, DiscordChannel

def main():
    parser = argparse.ArgumentParser(description="OmniBridge CLI utility")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Status command
    subparsers.add_parser("status", help="Check channels configuration")

    # Test command
    test_parser = subparsers.add_parser("test", help="Send a test notification")
    test_parser.add_argument("--channel", choices=["telegram", "discord"], required=True, help="Target channel")
    test_parser.add_argument("--message", default="Test alert from OmniBridge CLI", help="Message to send")
    test_parser.add_argument("--token", help="Telegram bot token (optional, falls back to env)")
    test_parser.add_argument("--chat-id", help="Telegram chat ID")
    test_parser.add_argument("--webhook", help="Discord webhook URL (optional, falls back to env)")

    args = parser.parse_args()

    if args.command == "status":
        tg = TelegramChannel()
        dc = DiscordChannel()
        status = {
            "telegram": {"configured": tg.is_configured()},
            "discord": {"configured": dc.is_configured()}
        }
        print(json.dumps(status, indent=2))

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



_main_impl = main


def main():
    from ._genesis import print_upgrade_notice
    try:
        return _main_impl()
    finally:
        print_upgrade_notice()

if __name__ == "__main__":
    main()
