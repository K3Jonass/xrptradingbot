import json
from pathlib import Path

from xrp_bot.journal import append_journal_entry, analyze_closed_trade, detect_repeated_mistakes, load_journal, weekly_summary


def sample_trade(**kwargs):
    base = {
        "timestamp": "2026-05-01T00:00:00Z",
        "strategy_name": "ema_rsi",
        "signal_label": "BUY",
        "signal_score": 72,
        "signal_explanation": "trend + momentum",
        "market_regime": "trend",
        "entry_reason": "breakout",
        "exit_reason": "take profit",
        "entry_price": 1.0,
        "exit_price": 1.1,
        "stop_loss": 0.97,
        "take_profit": 1.1,
        "holding_duration": "2h",
        "realized_pnl": 0.1,
        "risk_taken_pct": 1.0,
        "higher_timeframe_confirmation": True,
    }
    base.update(kwargs)
    return base


def test_journal_writing(tmp_path: Path):
    p = tmp_path / "trade_journal.jsonl"
    row = append_journal_entry(sample_trade(), p)
    assert row["decision_score"] > 0
    lines = p.read_text().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["signal_explanation"] == "trend + momentum"


def test_post_trade_analysis_and_scoring():
    out = analyze_closed_trade(sample_trade(signal_score=30, ignored_stop_loss=True, higher_timeframe_confirmation=False))
    assert out["entry_quality"] == "low"
    assert 0 <= out["decision_score"] <= 100
    assert "ignoring_stop_loss_logic" in out["mistakes"]


def test_repeated_mistake_detection_and_weekly_summary(tmp_path: Path):
    p = tmp_path / "trade_journal.jsonl"
    for _ in range(3):
        append_journal_entry(sample_trade(signal_score=35, higher_timeframe_confirmation=False), p)
    for _ in range(2):
        append_journal_entry(sample_trade(realized_pnl=-0.05, signal_score=40), p)

    df = load_journal(p)
    mistakes = detect_repeated_mistakes(df)
    assert mistakes.get("weak_signal_entries", 0) >= 1
    assert mistakes.get("entering_against_higher_timeframe", 0) >= 1

    summary = weekly_summary(df)
    assert "best_decisions" in summary
    assert "strategy_comparison" in summary
    assert isinstance(summary["improvement_suggestions"], list)
