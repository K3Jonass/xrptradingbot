"""Application configuration loaded from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = BASE_DIR / "config" / "settings.yaml"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
REPORT_FILE = DATA_DIR / "latest_report.json"
PAPER_STATE_FILE = DATA_DIR / "paper_state.json"
PAPER_TRADES_FILE = DATA_DIR / "paper_trades.jsonl"
LOG_FILE = LOG_DIR / "analyzer.log"
PAPER_LOG_FILE = LOG_DIR / "paper_trader.log"


def load_settings() -> dict[str, Any]:
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


SETTINGS = load_settings()
APP = SETTINGS["app"]
INDICATORS = SETTINGS["indicator_settings"]
ANALYSIS = SETTINGS["analysis"]
NETWORK = SETTINGS["network"]

SYMBOL = APP["symbol"]
ALLOWED_SYMBOLS = set(APP["allowed_symbols"])
SUPPORTED_INTERVALS = APP["supported_intervals"]
DEFAULT_INTERVAL = APP["default_interval"]
DEFAULT_LIMIT = APP["candle_limit"]["default"]
MIN_LIMIT = APP["candle_limit"]["min"]
MAX_LIMIT = APP["candle_limit"]["max"]

PAPER_TRADING = SETTINGS.get("paper_trading", {})
PAPER_TRADING_ONLY = True
