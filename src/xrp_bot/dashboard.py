from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


STATE_FILE = Path("data/paper_state.json")
TRADES_FILE = Path("data/paper_trades.jsonl")
JOURNAL_FILE = Path("data/trade_journal.jsonl")
SIGNAL_LABELS = ["BUY", "SELL", "STRONG_BUY", "STRONG_SELL"]


def load_prediction_report(path: Path | str = Path("data/models/model_report.json")) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text())


def load_paper_state(path: Path | str = STATE_FILE) -> dict:
    p = Path(path)
    if not p.exists():
        return {"fake_balance": 0.0, "realized_pnl": 0.0, "unrealized_pnl": 0.0}
    return json.loads(p.read_text())


def load_trades_jsonl(path: Path | str = TRADES_FILE) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    rows = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    elif "exit_time" in df.columns:
        df["timestamp"] = pd.to_datetime(df["exit_time"], utc=True, errors="coerce")
    return df


def load_journal_jsonl(path: Path | str = JOURNAL_FILE) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    rows = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    return pd.DataFrame(rows)


def build_paper_event_counters(events_df: pd.DataFrame) -> dict:
    counters = {
        "total_cycles": int(len(events_df)),
        "skip_count": 0,
        "open_count": 0,
        "close_count": 0,
        "hold_count": 0,
    }
    for label in SIGNAL_LABELS:
        counters[f"{label.lower()}_count"] = 0

    if events_df.empty:
        return counters

    event_counts = events_df.get("event_type", pd.Series(dtype=str)).value_counts()
    counters["skip_count"] = int(event_counts.get("SKIP", 0))
    counters["open_count"] = int(event_counts.get("OPEN", 0))
    counters["close_count"] = int(event_counts.get("CLOSE", 0))
    counters["hold_count"] = int(event_counts.get("HOLD", 0))

    signal_counts = events_df.get("signal_label", pd.Series(dtype=str)).value_counts()
    for label in SIGNAL_LABELS:
        counters[f"{label.lower()}_count"] = int(signal_counts.get(label, 0))
    return counters


def filter_paper_events(events_df: pd.DataFrame, event_types: list[str], signal_labels: list[str], market_regimes: list[str]) -> pd.DataFrame:
    filtered = events_df.copy()
    if "event_type" in filtered.columns and event_types:
        filtered = filtered[filtered["event_type"].isin(event_types)]
    if "signal_label" in filtered.columns and signal_labels:
        filtered = filtered[filtered["signal_label"].isin(signal_labels)]
    if "market_regime" in filtered.columns and market_regimes:
        filtered = filtered[filtered["market_regime"].isin(market_regimes)]
    return filtered


def calculate_dashboard_metrics(state: dict, trades_df: pd.DataFrame) -> dict:
    if "pnl" in trades_df.columns:
        pnl = trades_df["pnl"]
    elif "realized_pnl" in trades_df.columns:
        pnl = trades_df["realized_pnl"].diff().fillna(trades_df["realized_pnl"])
    elif "pnl_change" in trades_df.columns:
        pnl = trades_df["pnl_change"]
    else:
        pnl = pd.Series(dtype=float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    total_trades = int(len(pnl))
    win_rate = float((len(wins) / total_trades) * 100) if total_trades else 0.0
    profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) else (float("inf") if len(wins) else 0.0)

    equity = pd.Series([float(state.get("day_start_balance", state.get("fake_balance", 0.0)))] + pnl.cumsum().tolist())
    running_max = equity.cummax()
    drawdown = (equity - running_max)
    max_drawdown = float(drawdown.min()) if len(drawdown) else 0.0

    return {
        "current_paper_balance": float(state.get("fake_balance", 0.0)),
        "realized_pnl": float(state.get("realized_pnl", wins.sum() + losses.sum())),
        "unrealized_pnl": float(state.get("unrealized_pnl", 0.0)),
        "total_simulated_trades": total_trades,
        "win_rate": win_rate,
        "max_drawdown": max_drawdown,
        "profit_factor": profit_factor,
        "best_trade": float(pnl.max()) if total_trades else 0.0,
        "worst_trade": float(pnl.min()) if total_trades else 0.0,
    }


def run_dashboard() -> None:
    import streamlit as st

    st.set_page_config(page_title="XRP Paper Trading Dashboard", layout="wide")
    st.title("XRP Paper Trading Dashboard (Read-only)")

    state = load_paper_state()
    trades = load_trades_jsonl()
    journal = load_journal_jsonl()

    st.status("Dashboard loaded in read-only paper trading mode.", state="complete")

    if trades.empty:
        st.info("No trades yet, but paper cycles are being recorded.")

    if "timestamp" in trades.columns and not trades.empty:
        min_dt = trades["timestamp"].min().date()
        max_dt = trades["timestamp"].max().date()
        date_range = st.sidebar.date_input("Date range", value=(min_dt, max_dt), min_value=min_dt, max_value=max_dt)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            trades = trades[(trades["timestamp"].dt.date >= date_range[0]) & (trades["timestamp"].dt.date <= date_range[1])]

    event_options = sorted(trades["event_type"].dropna().unique().tolist()) if "event_type" in trades.columns else []
    signal_options = sorted(trades["signal_label"].dropna().unique().tolist()) if "signal_label" in trades.columns else []
    regime_options = sorted(trades["market_regime"].dropna().unique().tolist()) if "market_regime" in trades.columns else []

    selected_events = st.sidebar.multiselect("Event type", options=event_options, default=event_options)
    selected_signals = st.sidebar.multiselect("Signal label", options=signal_options, default=signal_options)
    selected_regimes = st.sidebar.multiselect("Market regime", options=regime_options, default=regime_options)

    filtered_events = filter_paper_events(trades, selected_events, selected_signals, selected_regimes)

    metrics = calculate_dashboard_metrics(state, filtered_events)
    prediction_report = load_prediction_report()
    cols = st.columns(3)
    for idx, (k, v) in enumerate(metrics.items()):
        cols[idx % 3].metric(k.replace("_", " ").title(), f"{v:.2f}" if isinstance(v, float) else v)

    st.subheader("Paper Cycle Summary")
    counters = build_paper_event_counters(filtered_events)
    counter_cols = st.columns(5)
    counter_cols[0].metric("Total Cycles", counters["total_cycles"])
    counter_cols[1].metric("SKIP", counters["skip_count"])
    counter_cols[2].metric("OPEN", counters["open_count"])
    counter_cols[3].metric("CLOSE", counters["close_count"])
    counter_cols[4].metric("HOLD", counters["hold_count"])
    sig_cols = st.columns(4)
    sig_cols[0].metric("BUY", counters["buy_count"])
    sig_cols[1].metric("SELL", counters["sell_count"])
    sig_cols[2].metric("STRONG_BUY", counters["strong_buy_count"])
    sig_cols[3].metric("STRONG_SELL", counters["strong_sell_count"])

    if not filtered_events.empty and "timestamp" in filtered_events.columns:
        chart_data = filtered_events.sort_values("timestamp").set_index("timestamp")
        selected_cols = [c for c in ["signal_score", "current_price"] if c in chart_data.columns]
        if selected_cols:
            st.subheader("Signal Score & Current Price Over Time")
            st.line_chart(chart_data[selected_cols])

    st.subheader("Recent Paper Events")
    event_columns = [
        "timestamp",
        "event_type",
        "signal_label",
        "signal_score",
        "signal_explanation",
        "market_regime",
        "current_price",
        "reason",
        "fake_balance",
        "realized_pnl",
        "unrealized_pnl",
    ]
    existing = [c for c in event_columns if c in filtered_events.columns]
    if existing:
        st.dataframe(filtered_events.sort_values("timestamp", ascending=False)[existing], use_container_width=True)
    else:
        st.info("No paper events found in data/paper_trades.jsonl yet.")

    if prediction_report:
        st.subheader("Prediction Research (Advisory Only)")
        st.json({"model": prediction_report.get("model"), "version": prediction_report.get("version"), "metrics": prediction_report.get("metrics", {})})

    if not journal.empty:
        st.subheader("Trading Journal Intelligence (Read-only)")
        if "decision_score" in journal.columns:
            st.metric("Average Decision Score", f"{journal['decision_score'].mean():.2f}")
            st.bar_chart(journal["decision_score"])
        if "mistakes" in journal.columns:
            mistakes = {}
            for arr in journal["mistakes"].dropna().tolist():
                for m in arr:
                    mistakes[m] = mistakes.get(m, 0) + 1
            if mistakes:
                st.write("Repeated Mistakes", mistakes)


if __name__ == "__main__":
    run_dashboard()
