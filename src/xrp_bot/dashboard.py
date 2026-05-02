from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


STATE_FILE = Path("data/paper_state.json")
TRADES_FILE = Path("data/paper_trades.jsonl")
JOURNAL_FILE = Path("data/trade_journal.jsonl")


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
    st.set_page_config(page_title="XRP Paper Trading Dashboard", layout="wide")
    st.title("XRP Paper Trading Dashboard (Read-only)")

    state = load_paper_state()
    trades = load_trades_jsonl()
    journal = load_journal_jsonl()

    if trades.empty:
        st.warning("No trade data found. Expected data/paper_trades.jsonl")

    if "timestamp" in trades.columns and not trades.empty:
        min_dt = trades["timestamp"].min().date()
        max_dt = trades["timestamp"].max().date()
        date_range = st.sidebar.date_input("Date range", value=(min_dt, max_dt), min_value=min_dt, max_value=max_dt)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            trades = trades[(trades["timestamp"].dt.date >= date_range[0]) & (trades["timestamp"].dt.date <= date_range[1])]

    if "signal" in trades.columns:
        signals = sorted(trades["signal"].dropna().unique().tolist())
        chosen = st.sidebar.multiselect("Signal type", options=signals, default=signals)
        trades = trades[trades["signal"].isin(chosen)] if chosen else trades

    if "market_regime" in trades.columns:
        regimes = sorted(trades["market_regime"].dropna().unique().tolist())
        chosen_regimes = st.sidebar.multiselect("Market regime", options=regimes, default=regimes)
        trades = trades[trades["market_regime"].isin(chosen_regimes)] if chosen_regimes else trades

    metrics = calculate_dashboard_metrics(state, trades)
    prediction_report = load_prediction_report()
    cols = st.columns(3)
    for idx, (k, v) in enumerate(metrics.items()):
        cols[idx % 3].metric(k.replace("_", " ").title(), f"{v:.2f}" if isinstance(v, float) else v)

    if not trades.empty and "pnl" in trades.columns:
        st.subheader("Equity Curve")
        base = float(state.get("day_start_balance", 0.0))
        curve = trades.sort_values("timestamp").copy() if "timestamp" in trades.columns else trades.copy()
        curve["equity"] = base + curve["pnl"].cumsum()
        st.line_chart(curve.set_index("timestamp")["equity"] if "timestamp" in curve.columns else curve["equity"])

        st.subheader("Daily PnL")
        if "timestamp" in curve.columns:
            daily = curve.groupby(curve["timestamp"].dt.date)["pnl"].sum()
            st.bar_chart(daily)

        st.subheader("Trade PnL Distribution")
        st.bar_chart(curve["pnl"])

    if prediction_report:
        st.subheader("Prediction Research (Advisory Only)")
        st.json({"model": prediction_report.get("model"), "version": prediction_report.get("version"), "metrics": prediction_report.get("metrics", {})})

    if not trades.empty and "signal_score" in trades.columns and "timestamp" in trades.columns:
        st.subheader("Signal Score Over Time")
        st.line_chart(trades.sort_values("timestamp").set_index("timestamp")["signal_score"])

    if not trades.empty and "market_regime" in trades.columns and "timestamp" in trades.columns:
        st.subheader("Market Regime Over Time")
        regime_counts = trades.groupby([trades["timestamp"].dt.date, "market_regime"]).size().unstack(fill_value=0)
        st.area_chart(regime_counts)

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
