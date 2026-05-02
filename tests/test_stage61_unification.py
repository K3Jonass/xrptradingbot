import importlib
import json
from pathlib import Path

import pandas as pd

from xrp_bot.paper_trading import normalize_event_payload
from xrp_bot.strategies import Stage3CompositeStrategy


def test_backward_compat_old_event_schema():
    old = {"signal": "BUY", "score": 55, "regime": "trending bullish", "explanation": "legacy"}
    norm = normalize_event_payload(old)
    for k in ["signal_label", "signal_score", "signal_explanation", "market_regime", "event_type"]:
        assert k in norm


def test_unified_signal_engine_usage(monkeypatch):
    calls = {"count": 0}

    def fake_stage3(df, interval, higher_tf_df=None):
        calls["count"] += 1
        class A:
            signal = "BUY"
        return A()

    import xrp_bot.strategies as s
    monkeypatch.setattr(s, "stage3_analysis", fake_stage3)
    df = pd.DataFrame([{"close": 1}])
    sig = Stage3CompositeStrategy().generate_signal(df)
    assert sig.action == "BUY"
    assert calls["count"] == 1


def test_cli_import_integrity():
    for mod in [
        "xrp_bot.cli",
        "xrp_bot.backtest_cli",
        "xrp_bot.paper_cli",
        "xrp_bot.healthcheck_cli",
        "xrp_bot.research_cli",
    ]:
        assert importlib.import_module(mod)
