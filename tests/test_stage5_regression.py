import json
from pathlib import Path

import pandas as pd

from xrp_bot.healthcheck import run_healthcheck
from xrp_bot.paper_trading import PaperState, run_paper_cycle, evaluate_paper_signal, append_event_jsonl
from xrp_bot.telegram import format_stage3_alert
from xrp_bot.dashboard import calculate_dashboard_metrics, load_trades_jsonl


def _df(n=50):
    rows=[]; px=1.0
    for i in range(n):
        px*=1.001
        rows.append({"close_time": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=i), "close": px, "high": px*1.01, "low": px*0.99, "volume": 200+i, "volume_ma_20": 180, "ema_20": px*1.001, "ema_50": px*0.999, "rsi_14": 55, "macd_hist": 0.03, "atr_14": px*0.01, "adx_14": 30, "bb_upper": px*1.02, "bb_lower": px*0.98})
    return pd.DataFrame(rows)


def test_paper_trading_cycle_and_event_shape(tmp_path: Path):
    state = PaperState(fake_balance=1000, day_start_balance=1000, last_reset_date="2026-01-01")
    event_file = tmp_path / "paper_trades.jsonl"
    out = run_paper_cycle(_df(), "1h", state, event_file)
    assert "signal" in out and "market_regime" in out
    payload = json.loads(event_file.read_text().strip())
    for k in ["signal_score", "signal_explanation", "market_regime", "atr", "adx", "support", "resistance", "stop_loss", "take_profit", "higher_timeframe_confirmation"]:
        assert k in payload


def test_telegram_alert_formatting_stage3_fields():
    msg = format_stage3_alert({"signal":"BUY","signal_score":66,"market_regime":"trend","stop_loss":1.0,"take_profit":1.2,"atr":0.02,"adx":30})
    assert "Score:" in msg and "Regime:" in msg and "ATR/ADX" in msg


def test_dashboard_metrics_from_real_event_shape(tmp_path: Path):
    decision = evaluate_paper_signal(_df(), interval="1h")
    f = tmp_path / "events.jsonl"
    append_event_jsonl(f, decision, interval="1h")
    df = load_trades_jsonl(f)
    metrics = calculate_dashboard_metrics({"fake_balance":1000,"realized_pnl":0,"unrealized_pnl":0,"day_start_balance":1000}, df)
    assert metrics["total_simulated_trades"] >= 0


def test_healthcheck_import_and_run():
    result = run_healthcheck()
    assert result["status"] == "ok"
    assert result["paper_trading_only"] is True
