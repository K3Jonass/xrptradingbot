"""Offline smoke test for Stage 1 analysis pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from xrp_bot.analyzer import detect_market_conditions
from xrp_bot.config import CONFIG_FILE, load_settings
from xrp_bot.data_fetcher import BinanceMarketDataFetcher
from xrp_bot.indicators import add_indicators
from xrp_bot.reporter import build_report_payload


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture = root / "tests" / "fixtures" / "xrpusdt_1h_sample.json"

    settings = load_settings()
    assert CONFIG_FILE.exists()
    assert settings["app"]["symbol"] == "XRPUSDT"

    with fixture.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    df = BinanceMarketDataFetcher._normalize_klines(raw)
    df = add_indicators(df)
    analysis = detect_market_conditions(df).to_dict()
    report = build_report_payload("1h", df, analysis)

    assert report["symbol"] == "XRPUSDT"
    assert "indicators" in report and "market_conditions" in report
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
