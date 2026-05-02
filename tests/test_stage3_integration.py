import json
from pathlib import Path

import pandas as pd

from xrp_bot.backtesting import BacktestConfig, run_backtest
from xrp_bot.paper_trading import append_event_jsonl, evaluate_paper_signal
from xrp_bot.signal_engine import stage3_analysis


def _df(n=80):
    rows=[]
    px=1.0
    for i in range(n):
        px*=1.002
        rows.append({
            "close_time": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=i),
            "close": px,
            "high": px*1.01,
            "low": px*0.99,
            "volume": 200+i,
            "volume_ma_20": 180,
            "ema_20": px*1.002,
            "ema_50": px*0.998,
            "rsi_14": 56,
            "macd_hist": 0.04,
            "atr_14": px*0.015,
            "adx_14": 28,
            "bb_upper": px*1.03,
            "bb_lower": px*0.97,
        })
    return pd.DataFrame(rows)


def test_analyzer_path_uses_stage3_engine():
    analysis = stage3_analysis(_df(), interval="1h")
    assert -100 <= analysis.score <= 100
    assert analysis.signal in {"STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"}


def test_backtest_uses_stage3_engine_outputs():
    result = run_backtest(_df(), BacktestConfig())
    assert isinstance(result.total_trades, int)


def test_paper_trading_uses_stage3_context_and_events(tmp_path: Path):
    decision = evaluate_paper_signal(_df(), interval="1h", higher_tf_df=_df())
    assert decision.signal in {"STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"}
    assert decision.regime
    event_file = tmp_path / "events.jsonl"
    append_event_jsonl(event_file, decision, interval="1h")
    payload = json.loads(event_file.read_text().strip())
    for key in [
        "signal_score", "signal_explanation", "market_regime", "atr", "adx",
        "support", "resistance", "stop_loss", "take_profit", "higher_timeframe_confirmation"
    ]:
        assert key in payload
