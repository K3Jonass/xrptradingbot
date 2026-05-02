from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import DATA_DIR, LOG_DIR, PAPER_STATE_FILE, SETTINGS, TELEGRAM
from .data_fetcher import BinanceMarketDataFetcher
from .monitoring import load_runtime_state, telegram_enabled
from .paper_trading import load_state


def _is_writable(path: Path) -> bool:
    path.mkdir(parents=True, exist_ok=True)
    test_file = path / ".write_test"
    test_file.write_text("ok", encoding="utf-8")
    test_file.unlink()
    return True


def run_healthcheck() -> list[str]:
    checks: list[str] = []
    assert SETTINGS.get("app"), "Config not loaded"
    checks.append("config")
    assert _is_writable(DATA_DIR), "data dir not writable"
    checks.append("data")
    assert _is_writable(LOG_DIR), "logs dir not writable"
    checks.append("logs")
    fetcher = BinanceMarketDataFetcher()
    fetcher.fetch_klines(interval="1m", limit=1)
    checks.append("binance")
    if TELEGRAM.get("enabled"):
        assert TELEGRAM.get("bot_token") and TELEGRAM.get("chat_id"), "telegram enabled but missing env secrets"
    checks.append("telegram")
    load_state(path=PAPER_STATE_FILE, initial_balance=1000)
    load_runtime_state()
    checks.append("state")
    return checks


def main() -> None:
    argparse.ArgumentParser(description="Paper bot healthcheck").parse_args()
    checks = run_healthcheck()
    print("healthcheck ok:", ", ".join(checks))


if __name__ == "__main__":
    main()
