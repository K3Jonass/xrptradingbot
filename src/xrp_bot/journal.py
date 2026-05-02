from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean

import pandas as pd

JOURNAL_FILE = Path("data/trade_journal.jsonl")


@dataclass
class JournalEntry:
    timestamp: str
    strategy_name: str
    signal_label: str
    signal_score: float
    signal_explanation: str
    market_regime: str
    entry_reason: str
    exit_reason: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    holding_duration: str
    realized_pnl: float
    risk_taken_pct: float
    win_loss: str
    notes: str
    analysis: dict
    decision_score: int
    mistakes: list[str]


def _decision_score(signal_score: float, discipline: float, compliance: float, risk_quality: float) -> int:
    score = 0.35 * signal_score + 0.25 * discipline + 0.20 * compliance + 0.20 * risk_quality
    return int(max(0, min(100, round(score))))


def analyze_closed_trade(trade: dict) -> dict:
    entry_price = float(trade.get("entry_price", 0.0))
    exit_price = float(trade.get("exit_price", entry_price))
    stop_loss = float(trade.get("stop_loss", entry_price))
    take_profit = float(trade.get("take_profit", exit_price))
    pnl = float(trade.get("realized_pnl", exit_price - entry_price))
    signal_score = float(trade.get("signal_score", 50.0))
    direction = str(trade.get("signal_label", trade.get("signal", "BUY"))).upper()

    risk_amount = abs(entry_price - stop_loss) if entry_price else 0.0
    reward_amount = abs(take_profit - entry_price) if entry_price else 0.0
    rr = (reward_amount / risk_amount) if risk_amount > 0 else 0.0

    hit_stop = (direction == "BUY" and exit_price <= stop_loss) or (direction == "SELL" and exit_price >= stop_loss)
    hit_tp = (direction == "BUY" and exit_price >= take_profit) or (direction == "SELL" and exit_price <= take_profit)

    entry_quality = "high" if signal_score >= 70 else ("medium" if signal_score >= 50 else "low")
    exit_timing = "correct" if (hit_stop or hit_tp) else ("early" if pnl > 0 else "late")
    risk_respected = not trade.get("ignored_stop_loss", False)

    discipline = 100.0 if risk_respected else 30.0
    compliance = 90.0 if not trade.get("rule_violation", False) else 25.0
    risk_quality = 85.0 if rr >= 1.5 and risk_respected else 40.0

    mistakes: list[str] = []
    if not trade.get("higher_timeframe_confirmation", True):
        mistakes.append("entering_against_higher_timeframe")
    if signal_score < 45:
        mistakes.append("weak_signal_entries")
    if trade.get("ignored_stop_loss", False):
        mistakes.append("ignoring_stop_loss_logic")
    if trade.get("revenge_trade", False):
        mistakes.append("revenge_trading_behavior")

    return {
        "what_worked": "Signal alignment and risk planning" if pnl > 0 else "Risk cap limited downside",
        "what_failed": "None material" if pnl > 0 else "Trade thesis failed or timing was weak",
        "entry_quality": entry_quality,
        "exit_timing": exit_timing,
        "risk_management_respected": risk_respected,
        "decision_score": _decision_score(signal_score, discipline, compliance, risk_quality),
        "mistakes": mistakes,
    }


def append_journal_entry(trade: dict, path: Path | str = JOURNAL_FILE) -> dict:
    analysis = analyze_closed_trade(trade)
    pnl = float(trade.get("realized_pnl", 0.0))
    signal_explanation = (
        trade.get("signal_explanation")
        or trade.get("explanation")
        or trade.get("explanation_notes")
        or ""
    )
    payload = JournalEntry(
        timestamp=trade.get("timestamp", datetime.now(timezone.utc).isoformat()),
        strategy_name=trade.get("strategy_name", "unknown"),
        signal_label=trade.get("signal_label", trade.get("signal", "HOLD")),
        signal_score=float(trade.get("signal_score", 0.0)),
        signal_explanation=signal_explanation,
        market_regime=trade.get("market_regime", "unknown"),
        entry_reason=trade.get("entry_reason", ""),
        exit_reason=trade.get("exit_reason", ""),
        entry_price=float(trade.get("entry_price", 0.0)),
        exit_price=float(trade.get("exit_price", 0.0)),
        stop_loss=float(trade.get("stop_loss", 0.0)),
        take_profit=float(trade.get("take_profit", 0.0)),
        holding_duration=trade.get("holding_duration", "0m"),
        realized_pnl=pnl,
        risk_taken_pct=float(trade.get("risk_taken_pct", 0.0)),
        win_loss=trade.get("win_loss", "win" if pnl > 0 else "loss"),
        notes=trade.get("notes", ""),
        analysis={k: analysis[k] for k in ["what_worked", "what_failed", "entry_quality", "exit_timing", "risk_management_respected"]},
        decision_score=analysis["decision_score"],
        mistakes=analysis["mistakes"],
    ).__dict__
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
    return payload


def load_journal(path: Path | str = JOURNAL_FILE) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "signal_explanation" not in df.columns:
        if "explanation" in df.columns:
            df["signal_explanation"] = df["explanation"].fillna("")
        elif "explanation_notes" in df.columns:
            df["signal_explanation"] = df["explanation_notes"].fillna("")
    defaults = {
        "strategy_name": "unknown",
        "signal_label": "HOLD",
        "signal_score": 0.0,
        "signal_explanation": "",
        "market_regime": "unknown",
        "entry_reason": "",
        "exit_reason": "",
        "entry_price": 0.0,
        "exit_price": 0.0,
        "stop_loss": 0.0,
        "take_profit": 0.0,
        "holding_duration": "0m",
        "realized_pnl": 0.0,
        "risk_taken_pct": 0.0,
        "win_loss": "loss",
        "notes": "",
        "analysis": {},
        "decision_score": 0,
        "mistakes": [],
    }
    for k, v in defaults.items():
        if k not in df.columns:
            df[k] = v
    df["decision_score"] = pd.to_numeric(df["decision_score"], errors="coerce").fillna(0)
    return df


def detect_repeated_mistakes(journal_df: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    if journal_df.empty or "mistakes" not in journal_df.columns:
        return counts
    for arr in journal_df["mistakes"].dropna().tolist():
        if not isinstance(arr, list):
            continue
        for m in arr:
            counts[m] = counts.get(m, 0) + 1
    if len(journal_df) >= 10 and len(journal_df) / 7 > 1.5:
        counts["overtrading"] = counts.get("overtrading", 0) + 1
    return counts


def weekly_summary(journal_df: pd.DataFrame) -> dict:
    if journal_df.empty:
        return {"best_decisions": [], "worst_decisions": [], "repeated_mistakes": {}, "strategy_comparison": {}, "improvement_suggestions": [], "avg_decision_score": 0.0}

    safe_df = load_journal_from_df(journal_df)
    decisions = safe_df.sort_values("decision_score", ascending=False)
    best = decisions.head(3)[["timestamp", "strategy_name", "decision_score"]].to_dict("records")
    worst = decisions.tail(3)[["timestamp", "strategy_name", "decision_score"]].to_dict("records")
    repeated = detect_repeated_mistakes(safe_df)
    strat = safe_df.groupby("strategy_name").agg(avg_pnl=("realized_pnl", "mean"), win_rate=("win_loss", lambda s: float((s == "win").mean() * 100)), avg_decision=("decision_score", "mean")).round(2).to_dict("index")
    suggestions = []
    if repeated.get("weak_signal_entries", 0) > 0:
        suggestions.append("Raise minimum signal threshold for entries.")
    if repeated.get("ignoring_stop_loss_logic", 0) > 0:
        suggestions.append("Enforce stop-loss adherence with automatic veto.")
    if safe_df["decision_score"].mean() < 65:
        suggestions.append("Focus on rule compliance and fewer discretionary trades.")
    return {
        "best_decisions": best,
        "worst_decisions": worst,
        "repeated_mistakes": repeated,
        "strategy_comparison": strat,
        "improvement_suggestions": suggestions,
        "avg_decision_score": round(float(mean(safe_df["decision_score"])), 2),
    }


def load_journal_from_df(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    for c, d in {"strategy_name": "unknown", "timestamp": "", "decision_score": 0, "realized_pnl": 0.0, "win_loss": "loss", "mistakes": []}.items():
        if c not in temp.columns:
            temp[c] = d
    temp["decision_score"] = pd.to_numeric(temp["decision_score"], errors="coerce").fillna(0)
    return temp
