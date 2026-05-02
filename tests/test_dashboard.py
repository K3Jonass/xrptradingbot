import json
from types import SimpleNamespace
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


def test_dashboard_has_executable_entrypoint():
    content = Path("src/xrp_bot/dashboard.py").read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in content
    assert "run_dashboard()" in content


def test_dashboard_shows_fallback_message_when_data_missing(monkeypatch):
    import xrp_bot.dashboard as dashboard

    calls = {"title": [], "info": []}

    class _DummySidebar:
        def date_input(self, *args, **kwargs):
            return kwargs.get("value")

        def multiselect(self, *args, **kwargs):
            return kwargs.get("default", [])

    st = SimpleNamespace(
        set_page_config=lambda **kwargs: None,
        title=lambda msg: calls["title"].append(msg),
        status=lambda *args, **kwargs: None,
        info=lambda msg: calls["info"].append(msg),
        warning=lambda msg: None,
        sidebar=_DummySidebar(),
        columns=lambda n: [SimpleNamespace(metric=lambda *a, **k: None) for _ in range(n)],
        subheader=lambda *a, **k: None,
        line_chart=lambda *a, **k: None,
        bar_chart=lambda *a, **k: None,
        area_chart=lambda *a, **k: None,
        json=lambda *a, **k: None,
        metric=lambda *a, **k: None,
        write=lambda *a, **k: None,
    )

    monkeypatch.setitem(__import__("sys").modules, "streamlit", st)
    monkeypatch.setattr(dashboard, "load_paper_state", lambda: {"fake_balance": 0.0, "realized_pnl": 0.0, "unrealized_pnl": 0.0})
    monkeypatch.setattr(dashboard, "load_trades_jsonl", lambda: __import__("pandas").DataFrame())
    monkeypatch.setattr(dashboard, "load_journal_jsonl", lambda: __import__("pandas").DataFrame())
    monkeypatch.setattr(dashboard, "load_prediction_report", lambda: None)

    dashboard.run_dashboard()

    assert calls["title"]
    assert "No paper trading data yet. Run xrp-paper --once first." in calls["info"]
