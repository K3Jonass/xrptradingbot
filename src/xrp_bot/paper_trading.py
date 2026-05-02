from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import PAPER_TRADING_ONLY
from .signal_engine import stage3_analysis


@dataclass
class TradeRecord:
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    reason: str


@dataclass
class PaperTradeConfig:
    initial_balance: float = 1000.0


@dataclass
class PaperState:
    fake_balance: float
    day_start_balance: float
    last_reset_date: str
    daily_realized_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    trade_history: list[TradeRecord] = field(default_factory=list)

    def reset_daily_if_needed(self, current_date: str) -> None:
        if self.last_reset_date != current_date:
            self.last_reset_date = current_date
            self.day_start_balance = self.fake_balance
            self.daily_realized_pnl = 0.0

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["trade_history"] = [asdict(t) for t in self.trade_history]
        return payload

    @classmethod
    def from_dict(cls, payload: dict, initial_balance: float) -> "PaperState":
        history = [TradeRecord(**t) for t in payload.get("trade_history", [])]
        return cls(
            fake_balance=float(payload.get("fake_balance", initial_balance)),
            day_start_balance=float(payload.get("day_start_balance", initial_balance)),
            last_reset_date=payload.get("last_reset_date", datetime.now(timezone.utc).date().isoformat()),
            daily_realized_pnl=float(payload.get("daily_realized_pnl", 0.0)),
            realized_pnl=float(payload.get("realized_pnl", 0.0)),
            unrealized_pnl=float(payload.get("unrealized_pnl", 0.0)),
            trade_history=history,
        )


@dataclass
class PaperSignalDecision:
    signal: str
    score: int
    regime: str
    explanation: str
    support: float
    resistance: float
    stop_loss: float
    take_profit: float
    atr: float
    adx: float
    higher_timeframe_confirmation: bool


def generate_signal(df: pd.DataFrame) -> str:
    row = df.iloc[-1]
    if float(row.get("ema_20", 0)) > float(row.get("ema_50", 0)) and float(row.get("rsi_14", 100)) < 70 and float(row.get("volume", 0)) >= float(row.get("volume_ma_20", 0)):
        return "BUY"
    return "HOLD"


def evaluate_paper_signal(df: pd.DataFrame, interval: str, higher_tf_df: pd.DataFrame | None = None) -> PaperSignalDecision:
    a = stage3_analysis(df, interval=interval, higher_tf_df=higher_tf_df)
    return PaperSignalDecision(
        signal=a.signal,
        score=a.score,
        regime=a.regime,
        explanation="; ".join(a.notes[:2]),
        support=a.support,
        resistance=a.resistance,
        stop_loss=a.stop_loss,
        take_profit=a.take_profit,
        atr=float(df.iloc[-1].get("atr_14", 0.0)),
        adx=float(df.iloc[-1].get("adx_14", 0.0)),
        higher_timeframe_confirmation=bool(higher_tf_df is not None),
    )


def append_event_jsonl(path: Path, decision: PaperSignalDecision, interval: str, extra: dict | None = None) -> None:
    payload = {
        "event_type": "ANALYSIS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "interval": interval,
        "signal": decision.signal,
        "signal_label": decision.signal,
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
    if extra:
        payload.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def normalize_event_payload(payload: dict) -> dict:
    # backward compatibility for old jsonl schema variants
    out = dict(payload)
    out.setdefault("signal_label", out.get("signal", "HOLD"))
    out.setdefault("signal_score", out.get("score", 0))
    out.setdefault("signal_explanation", out.get("explanation", "N/A"))
    out.setdefault("market_regime", out.get("regime", "unknown"))
    out.setdefault("event_type", "ANALYSIS")
    return out


def save_state(state: PaperState, current_price: float, path: Path) -> None:
    if not PAPER_TRADING_ONLY:
        raise RuntimeError("Paper mode only")
    state.unrealized_pnl = 0.0 if not state.trade_history else state.unrealized_pnl
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def load_state(path: Path, initial_balance: float) -> PaperState:
    if not path.exists():
        return PaperState(
            fake_balance=initial_balance,
            day_start_balance=initial_balance,
            last_reset_date=datetime.now(timezone.utc).date().isoformat(),
        )
    return PaperState.from_dict(json.loads(path.read_text(encoding="utf-8")), initial_balance)
