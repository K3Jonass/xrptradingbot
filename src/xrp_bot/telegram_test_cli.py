from __future__ import annotations

from .config import TELEGRAM, load_dotenv
from .telegram import TelegramAlertEngine


def main() -> None:
    load_dotenv()
    engine = TelegramAlertEngine(TELEGRAM)
    if not engine.is_config_valid():
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
    ok = engine.send_message("xrp-telegram-test: paper trading monitor online (no real trading).")
    if not ok:
        raise SystemExit("Failed to send Telegram test message")
    print("Telegram test message sent successfully.")


if __name__ == "__main__":
    main()
