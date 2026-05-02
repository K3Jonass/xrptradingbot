from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .signal_engine import stage3_analysis


PAPER_TRADING_ONLY = True


@dataclass
class PaperTradeDecision:
    signal: str
    score: int
    explanation: str
    regime: str
    atr: float
    adx: float
    support: float
    resistance: float
    stop_loss: float
    take_profit: float
    higher_timeframe_confirmation: bool

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def evaluate_paper_signal(entry_df: pd.DataFrame, interval: str, higher_tf_df: pd.DataFrame | None = None) -> PaperTradeDecision:
    analysis = stage3_analysis(entry_df, interval=interval, higher_tf_df=higher_tf_df)
    latest = entry_df.iloc[-1]
    htf_confirmed = any("4h confirmation: yes" in n for n in analysis.notes)
    return PaperTradeDecision(
        signal=analysis.signal,
        score=analysis.score,
        explanation=analysis.notes[0],
        regime=analysis.regime,
        atr=float(latest["atr_14"]),
        adx=float(latest["adx_14"]),
        support=float(analysis.support),
        resistance=float(analysis.resistance),
        stop_loss=float(analysis.stop_loss),
        take_profit=float(analysis.take_profit),
        higher_timeframe_confirmation=htf_confirmed,
    )


def build_paper_report(decision: PaperTradeDecision) -> dict:
    return {
        "paper_trading_only": PAPER_TRADING_ONLY,
        "signal": decision.signal,
        "signal_score": decision.score,
        "signal_explanation": decision.explanation,
        "market_regime": decision.regime,
        "atr": decision.atr,
        "adx": decision.adx,
        "support": decision.support,
        "resistance": decision.resistance,
        "stop_loss": decision.stop_loss,
        "take_profit": decision.take_profit,
        "higher_timeframe_confirmation": decision.higher_timeframe_confirmation,
    }


def append_event_jsonl(event_path: Path, decision: PaperTradeDecision, interval: str) -> None:
    payload = {
        "event": "paper_signal",
        "interval": interval,
        **build_paper_report(decision),
    }
    event_path.parent.mkdir(parents=True, exist_ok=True)
    with event_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
