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
    assert "No trades yet, but paper cycles are being recorded." in calls["info"]



def test_skip_only_metrics_are_visible():
    import pandas as pd
    from xrp_bot.dashboard import build_paper_event_counters

    events = pd.DataFrame([
        {"event_type": "SKIP", "signal_label": "SELL"},
        {"event_type": "SKIP", "signal_label": "BUY"},
    ])
    counters = build_paper_event_counters(events)
    assert counters["total_cycles"] == 2
    assert counters["skip_count"] == 2
    assert counters["open_count"] == 0
    assert counters["hold_count"] == 0


def test_recent_events_table_columns_load_from_jsonl(tmp_path: Path):
    p = tmp_path / "paper_trades.jsonl"
    p.write_text("\n".join([
        json.dumps({
            "timestamp": "2026-01-01T00:00:00Z",
            "event_type": "SKIP",
            "signal_label": "BUY",
            "signal_score": 0.72,
            "signal_explanation": "Momentum weak",
            "market_regime": "RANGE",
            "current_price": 0.54,
            "reason": "risk filter",
            "fake_balance": 1000.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
        })
    ]))
    df = load_trades_jsonl(p)
    for col in ["event_type", "signal_label", "signal_score", "signal_explanation", "market_regime", "current_price", "reason", "fake_balance", "realized_pnl", "unrealized_pnl"]:
        assert col in df.columns


def test_event_counters_cover_open_close_hold_and_signal_buckets():
    import pandas as pd
    from xrp_bot.dashboard import build_paper_event_counters

    events = pd.DataFrame([
        {"event_type": "OPEN", "signal_label": "BUY"},
        {"event_type": "CLOSE", "signal_label": "SELL"},
        {"event_type": "HOLD", "signal_label": "STRONG_BUY"},
        {"event_type": "SKIP", "signal_label": "STRONG_SELL"},
    ])
    counters = build_paper_event_counters(events)
    assert counters["open_count"] == 1
    assert counters["close_count"] == 1
    assert counters["hold_count"] == 1
    assert counters["skip_count"] == 1
    assert counters["buy_count"] == 1
    assert counters["sell_count"] == 1
    assert counters["strong_buy_count"] == 1
    assert counters["strong_sell_count"] == 1


def test_prediction_section_hides_raw_json_by_default_and_shows_tables(monkeypatch):
    import pandas as pd
    import xrp_bot.dashboard as dashboard

    calls = {"json": 0, "table": [], "expander": []}

    class _DummyExpander:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _DummySidebar:
        def date_input(self, *args, **kwargs):
            return kwargs.get("value")

        def multiselect(self, *args, **kwargs):
            return kwargs.get("default", [])

    st = SimpleNamespace(
        set_page_config=lambda **kwargs: None,
        title=lambda *a, **k: None,
        status=lambda *a, **k: None,
        info=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        caption=lambda *a, **k: None,
        markdown=lambda *a, **k: None,
        sidebar=_DummySidebar(),
        columns=lambda n: [SimpleNamespace(metric=lambda *a, **k: None) for _ in range(n)],
        subheader=lambda *a, **k: None,
        line_chart=lambda *a, **k: None,
        bar_chart=lambda *a, **k: None,
        area_chart=lambda *a, **k: None,
        table=lambda data: calls["table"].append(data.copy() if isinstance(data, pd.DataFrame) else data),
        json=lambda *a, **k: calls.__setitem__("json", calls["json"] + 1),
        metric=lambda *a, **k: None,
        write=lambda *a, **k: None,
        dataframe=lambda *a, **k: None,
        expander=lambda label: (calls["expander"].append(label) or _DummyExpander()),
    )

    monkeypatch.setitem(__import__("sys").modules, "streamlit", st)
    monkeypatch.setattr(dashboard, "load_paper_state", lambda: {"fake_balance": 1000.0, "realized_pnl": 0.0, "unrealized_pnl": 0.0})
    monkeypatch.setattr(
        dashboard,
        "load_trades_jsonl",
        lambda: pd.DataFrame([{"timestamp": pd.Timestamp("2026-01-01T00:00:00Z"), "event_type": "SKIP"}]),
    )
    monkeypatch.setattr(dashboard, "load_journal_jsonl", lambda: pd.DataFrame())
    monkeypatch.setattr(
        dashboard,
        "load_prediction_report",
        lambda: {
            "model": "logreg",
            "version": "v1",
            "metrics": {
                "accuracy": 0.67,
                "precision": 0.63,
                "recall": 0.62,
                "f1": 0.61,
                "directional_hit_rate": 0.66,
                "confusion_matrix": [[8, 2], [3, 7]],
                "avg_forward_return_by_predicted_class": {"0": -0.001, "1": 0.002},
            },
        },
    )

    dashboard.run_dashboard()

    assert calls["json"] == 1
    assert "Show raw model report" in calls["expander"]
    assert len(calls["table"]) == 2
    confusion_table = calls["table"][0]
    assert list(confusion_table.columns) == ["Predicted 0", "Predicted 1"]
    returns_table = calls["table"][1]
    assert "Predicted Class" in returns_table.columns


def test_weak_prediction_warning_appears(monkeypatch):
    from xrp_bot.dashboard import is_prediction_quality_weak

    assert is_prediction_quality_weak({"accuracy": 0.54, "directional_hit_rate": 0.70})
    assert is_prediction_quality_weak({"accuracy": 0.70, "directional_hit_rate": 0.54})
    assert not is_prediction_quality_weak({"accuracy": 0.70, "directional_hit_rate": 0.70})
