import json
from pathlib import Path

import pandas as pd

from xrp_bot.dashboard import calculate_dashboard_metrics, load_journal_jsonl, load_paper_state, load_trades_jsonl
from xrp_bot.journal import append_journal_entry, weekly_summary
from xrp_bot.paper_trading import PaperState, run_paper_cycle
from xrp_bot.telegram import format_weekly_journal_summary


def _df(n=50):
    rows = []
    px = 1.0
    for i in range(n):
        px *= 1.001
        rows.append({"close_time": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=i), "close": px, "high": px*1.01, "low": px*0.99, "volume": 200+i, "volume_ma_20": 180, "ema_20": px*1.001, "ema_50": px*0.999, "rsi_14": 55, "macd_hist": 0.03, "atr_14": px*0.01, "adx_14": 30, "bb_upper": px*1.02, "bb_lower": px*0.98})
    return pd.DataFrame(rows)


def test_end_to_end_journal_dashboard_summary(tmp_path: Path):
    state_file = tmp_path / "paper_state.json"
    state_file.write_text(json.dumps({"fake_balance": 1000.0, "day_start_balance": 1000.0, "realized_pnl": 0.0, "unrealized_pnl": 0.0}))
    trades_file = tmp_path / "paper_trades.jsonl"
    journal_file = tmp_path / "trade_journal.jsonl"

    state = PaperState(fake_balance=1000, day_start_balance=1000, last_reset_date="2026-01-01")
    close_trade = {
        "timestamp": "2026-01-02T00:00:00Z", "strategy_name": "ema_rsi", "signal_label": "BUY", "signal_score": 75,
        "signal_explanation": "breakout confirmation", "market_regime": "trend", "entry_reason": "breakout", "exit_reason": "tp",
        "entry_price": 1.0, "exit_price": 1.08, "stop_loss": 0.97, "take_profit": 1.08, "holding_duration": "3h",
        "realized_pnl": 0.08, "risk_taken_pct": 1.0, "notes": "clean setup", "higher_timeframe_confirmation": True,
    }
    out = run_paper_cycle(_df(), "1h", state, trades_file, close_trade=close_trade)
    assert out["journal_written"] is True

    append_journal_entry(close_trade, journal_file)
    trades_df = load_trades_jsonl(trades_file)
    journal_df = load_journal_jsonl(journal_file)
    summary = weekly_summary(journal_df)
    telegram_msg = format_weekly_journal_summary(summary)
    metrics = calculate_dashboard_metrics(load_paper_state(state_file), trades_df)

    assert "signal_score" in trades_df.columns
    assert not journal_df.empty
    assert "best_decisions" in summary
    assert "Weekly Review" in telegram_msg
    assert "total_simulated_trades" in metrics
