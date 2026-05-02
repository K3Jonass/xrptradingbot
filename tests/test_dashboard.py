import json
from pathlib import Path

from xrp_bot.dashboard import calculate_dashboard_metrics, load_paper_state, load_trades_jsonl


def test_load_paper_state(tmp_path: Path):
    p = tmp_path / "paper_state.json"
    p.write_text(json.dumps({"fake_balance": 1100, "realized_pnl": 50, "unrealized_pnl": 10}))
    state = load_paper_state(p)
    assert state["fake_balance"] == 1100


def test_load_jsonl_trades(tmp_path: Path):
    p = tmp_path / "paper_trades.jsonl"
    p.write_text('\n'.join([
        json.dumps({"timestamp": "2026-01-01T00:00:00Z", "pnl": 10.0, "signal": "BUY"}),
        json.dumps({"timestamp": "2026-01-02T00:00:00Z", "pnl": -3.0, "signal": "SELL"}),
    ]))
    df = load_trades_jsonl(p)
    assert len(df) == 2
    assert "timestamp" in df.columns


def test_calculate_dashboard_metrics():
    import pandas as pd

    state = {"fake_balance": 1200.0, "realized_pnl": 200.0, "unrealized_pnl": -5.0, "day_start_balance": 1000.0}
    trades = pd.DataFrame([
        {"pnl": 100.0},
        {"pnl": -20.0},
        {"pnl": 50.0},
    ])
    metrics = calculate_dashboard_metrics(state, trades)
    assert metrics["total_simulated_trades"] == 3
    assert metrics["best_trade"] == 100.0
    assert metrics["worst_trade"] == -20.0
    assert metrics["win_rate"] > 0
