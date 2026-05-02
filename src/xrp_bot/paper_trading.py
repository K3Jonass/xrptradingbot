from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from .config import PAPER_STATE_FILE, PAPER_TRADES_FILE, PAPER_TRADING


@dataclass
class PaperTradeConfig:
    initial_balance: float = float(PAPER_TRADING.get("initial_balance", 1000.0))
    max_risk_per_trade: float = float(PAPER_TRADING.get("max_risk_per_trade", 0.02))
    stop_loss_pct: float = float(PAPER_TRADING.get("stop_loss_pct", 0.02))
    take_profit_pct: float = float(PAPER_TRADING.get("take_profit_pct", 0.04))
    max_daily_loss_pct: float = float(PAPER_TRADING.get("max_daily_loss_pct", 0.05))
    max_trades_per_day: int = int(PAPER_TRADING.get("max_trades_per_day", 5))
    max_open_position: int = int(PAPER_TRADING.get("max_open_position", 1))


@dataclass
class SimPosition:
    side: str
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    opened_at: str
    entry_candle_time: str


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
class PaperState:
    fake_balance: float
    open_position: SimPosition | None = None
    trade_history: list[TradeRecord] = field(default_factory=list)
    realized_pnl: float = 0.0
    daily_realized_pnl: float = 0.0
    day_start_balance: float = 0.0
    last_reset_date: str = ""

    def reset_daily_if_needed(self, today: str) -> None:
        if self.last_reset_date != today:
            self.daily_realized_pnl = 0.0
            self.day_start_balance = self.fake_balance
            self.last_reset_date = today

    @property
    def trades_today(self) -> int:
        return sum(1 for t in self.trade_history if t.exit_time.startswith(self.last_reset_date))

    def unrealized_pnl(self, current_price: float) -> float:
        if not self.open_position:
            return 0.0
        return (current_price - self.open_position.entry_price) * self.open_position.size

    def to_dict(self) -> dict:
        return {
            "fake_balance": self.fake_balance,
            "open_position": asdict(self.open_position) if self.open_position else None,
            "trade_history": [asdict(t) for t in self.trade_history],
            "realized_pnl": self.realized_pnl,
            "daily_realized_pnl": self.daily_realized_pnl,
            "day_start_balance": self.day_start_balance,
            "last_reset_date": self.last_reset_date,
            "unrealized_pnl": 0.0,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "PaperState":
        return cls(
            fake_balance=float(payload.get("fake_balance", 0.0)),
            open_position=SimPosition(**payload["open_position"]) if payload.get("open_position") else None,
            trade_history=[TradeRecord(**t) for t in payload.get("trade_history", [])],
            realized_pnl=float(payload.get("realized_pnl", 0.0)),
            daily_realized_pnl=float(payload.get("daily_realized_pnl", 0.0)),
            day_start_balance=float(payload.get("day_start_balance", payload.get("fake_balance", 0.0))),
            last_reset_date=payload.get("last_reset_date", ""),
        )


def load_state(path: Path = PAPER_STATE_FILE, initial_balance: float = 1000.0) -> PaperState:
    if not path.exists():
        today = date.today().isoformat()
        return PaperState(fake_balance=initial_balance, day_start_balance=initial_balance, last_reset_date=today)
    return PaperState.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_state(state: PaperState, current_price: float, path: Path = PAPER_STATE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = state.to_dict()
    payload["unrealized_pnl"] = state.unrealized_pnl(current_price)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def append_trade_event(event: dict, path: Path = PAPER_TRADES_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def generate_signal(df: pd.DataFrame) -> str:
    row = df.iloc[-1]
    return "BUY" if row["ema_20"] > row["ema_50"] and 50 <= row["rsi_14"] <= 70 and row["volume"] > row["volume_ma_20"] else "HOLD"


def risk_status(state: PaperState, cfg: PaperTradeConfig) -> str:
    if state.trades_today >= cfg.max_trades_per_day:
        return "MAX_TRADES_REACHED"
    if state.daily_realized_pnl <= -(state.day_start_balance * cfg.max_daily_loss_pct):
        return "DAILY_LOSS_LIMIT"
    if state.open_position is not None and cfg.max_open_position <= 1:
        return "POSITION_OPEN"
    return "OK"
