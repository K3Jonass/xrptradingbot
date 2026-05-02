from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import xrp_bot.paper_cli as paper_cli


def _df(n=80, *, buy_signal: bool) -> pd.DataFrame:
    rows = []
    px = 1.0
    for i in range(n):
        px *= 1.001
        rows.append({
            "open_time": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=i),
            "close_time": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=i + 1),
            "open": px * 0.999,
            "close": px,
            "high": px * 1.01,
            "low": px * 0.99,
            "volume": 200 + i,
            "volume_ma_20": 180,
            "ema_20": px * (1.002 if buy_signal else 0.998),
            "ema_50": px * (0.998 if buy_signal else 1.002),
            "rsi_14": 56 if buy_signal else 40,
            "macd_hist": 0.04 if buy_signal else -0.04,
            "atr_14": px * 0.015,
            "adx_14": 28,
            "bb_upper": px * 1.03,
            "bb_lower": px * 0.97,
        })
    return pd.DataFrame(rows)


def test_xrp_paper_once_outputs_stage3_fields(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    class _Fetcher:
        def fetch_klines(self, interval: str, limit: int, symbol: str):
            return _df(buy_signal=True)

    monkeypatch.setattr(paper_cli, "BinanceMarketDataFetcher", lambda: _Fetcher())
    monkeypatch.setattr(paper_cli, "add_indicators", lambda df: df)
    monkeypatch.setattr("sys.argv", ["xrp-paper", "--once"])

    paper_cli.main()
    out = json.loads(capsys.readouterr().out)

    for k in [
        "current_price", "signal_label", "signal_score", "signal_explanation", "market_regime",
        "support", "resistance", "atr_stop_loss", "atr_take_profit", "fake_balance", "open_position",
        "realized_pnl", "unrealized_pnl", "risk_status", "event_type",
    ]:
        assert k in out
    assert Path("data/paper_state.json").exists()
    assert Path("data/paper_trades.jsonl").exists()


def test_skip_event_when_no_trade_happens(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    class _Fetcher:
        def fetch_klines(self, interval: str, limit: int, symbol: str):
            return _df(buy_signal=False)

    monkeypatch.setattr(paper_cli, "BinanceMarketDataFetcher", lambda: _Fetcher())
    monkeypatch.setattr(paper_cli, "add_indicators", lambda df: df)
    monkeypatch.setattr("sys.argv", ["xrp-paper", "--once"])

    paper_cli.main()
    out = json.loads(capsys.readouterr().out)
    assert out["event_type"] == "SKIP"
    assert out["reason"] == "signal did not meet entry criteria"


def test_dashboard_can_read_skip_events_safely(tmp_path: Path):
    from xrp_bot.dashboard import calculate_dashboard_metrics, load_trades_jsonl

    events = tmp_path / "paper_trades.jsonl"
    events.write_text(json.dumps({
        "timestamp": "2026-01-01T00:00:00Z",
        "event_type": "SKIP",
        "signal": "HOLD",
        "signal_score": 10,
        "market_regime": "range",
    }) + "\n")
    df = load_trades_jsonl(events)
    metrics = calculate_dashboard_metrics({"fake_balance": 1000.0, "day_start_balance": 1000.0}, df)
    assert metrics["total_simulated_trades"] == 0

