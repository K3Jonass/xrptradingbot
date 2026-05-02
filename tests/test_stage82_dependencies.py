import importlib
import json
from pathlib import Path

import pytest

from xrp_bot.data_fetcher import BinanceMarketDataFetcher
from xrp_bot.safety import SafetyViolation, block_private_endpoint, ensure_paper_trading_only


def test_public_candle_fetch_via_requests(monkeypatch):
    class Resp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return [[1, "1", "2", "0.5", "1.5", "100", 2, "0", 1, "0", "0", "0"]]

    monkeypatch.setattr("xrp_bot.data_fetcher.requests.get", lambda *args, **kwargs: Resp())
    df = BinanceMarketDataFetcher().fetch_klines("1h", 1, symbol="XRPUSDT")
    assert len(df) == 1
    assert float(df.iloc[0]["close"]) == 1.5


def test_no_python_binance_import_required():
    src = Path("src/xrp_bot/data_fetcher.py").read_text(encoding="utf-8")
    assert "binance.client" not in src
    assert "python-binance" not in src


def test_all_cli_imports_without_python_binance():
    for mod in [
        "xrp_bot.cli",
        "xrp_bot.backtest_cli",
        "xrp_bot.paper_cli",
        "xrp_bot.dashboard_cli",
        "xrp_bot.healthcheck_cli",
        "xrp_bot.research_cli",
        "xrp_bot.predict_cli",
        "xrp_bot.journal_cli",
    ]:
        assert importlib.import_module(mod)


def test_safety_guard_blocks_private_endpoints():
    ensure_paper_trading_only()
    with pytest.raises(SafetyViolation):
        block_private_endpoint("create_order")
