"""Application configuration loaded from YAML and .env (paper-only)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = BASE_DIR / "config" / "settings.yaml"
ENV_FILE = BASE_DIR / ".env"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
REPORT_FILE = DATA_DIR / "latest_report.json"
PAPER_STATE_FILE = DATA_DIR / "paper_state.json"
PAPER_TRADES_FILE = DATA_DIR / "paper_trades.jsonl"
LOG_FILE = LOG_DIR / "analyzer.log"
PAPER_LOG_FILE = LOG_DIR / "paper_trader.log"


def load_dotenv(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_settings() -> dict[str, Any]:
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def redact_secrets(payload: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    for key in ("bot_token", "chat_id"):
        if result.get(key):
            result[key] = "***REDACTED***"
    return result


load_dotenv()
SETTINGS = load_settings()
APP = SETTINGS["app"]
INDICATORS = SETTINGS["indicator_settings"]
ANALYSIS = SETTINGS["analysis"]
NETWORK = SETTINGS["network"]
TELEGRAM = SETTINGS.get("telegram", {})
TELEGRAM["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM.get("bot_token", ""))
TELEGRAM["chat_id"] = os.getenv("TELEGRAM_CHAT_ID", TELEGRAM.get("chat_id", ""))

SYMBOL = APP["symbol"]
ALLOWED_SYMBOLS = set(APP["allowed_symbols"])
SUPPORTED_INTERVALS = APP["supported_intervals"]
DEFAULT_INTERVAL = APP["default_interval"]
DEFAULT_LIMIT = APP["candle_limit"]["default"]
MIN_LIMIT = APP["candle_limit"]["min"]
MAX_LIMIT = APP["candle_limit"]["max"]

PAPER_TRADING = SETTINGS.get("paper_trading", {})
PAPER_TRADING_ONLY = True
