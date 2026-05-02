"""Paper trading helpers and local persistence (read/write simulation only)."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import pandas as pd
from .signal_engine import stage3_analysis
from .journal import append_journal_entry

@dataclass
class PaperTradeConfig:
    initial_balance: float = 1000.0

@dataclass
class PaperState:
    fake_balance: float
    day_start_balance: float
    last_reset_date: str
    realized_pnl: float = 0.0
    daily_realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    trade_count: int = 0
    open_position: dict | None = None
    trade_history: list[dict] = field(default_factory=list)
    def reset_daily_if_needed(self, today: str) -> None:
        if self.last_reset_date != today:
            self.last_reset_date = today
            self.day_start_balance = self.fake_balance
            self.daily_realized_pnl = 0.0

@dataclass
class PaperDecision:
    signal: str
    score: float
    explanation: str
    regime: str
    atr: float
    adx: float
    support: float
    resistance: float
    stop_loss: float
    take_profit: float
    higher_timeframe_confirmation: bool

def load_state(path: Path | str = Path("data/paper_state.json"), initial_balance: float = 1000.0) -> PaperState:
    p = Path(path)
    if not p.exists():
        return PaperState(fake_balance=initial_balance, day_start_balance=initial_balance, last_reset_date="1970-01-01")
    payload = json.loads(p.read_text())
    return PaperState(**{**PaperState(fake_balance=initial_balance, day_start_balance=initial_balance, last_reset_date="1970-01-01").__dict__, **payload})

def save_state(state: PaperState, current_price: float | None = None, path: Path | str = Path("data/paper_state.json")) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(state)
    if current_price is not None: payload["current_price"] = float(current_price)
    p.write_text(json.dumps(payload, indent=2))

def generate_signal(df: pd.DataFrame) -> str:
    if df.empty: return "HOLD"
    row = df.iloc[-1]
    if float(row.get("ema_20", 0)) > float(row.get("ema_50", 0)) and 50 <= float(row.get("rsi_14", 50)) <= 70 and float(row.get("volume", 0)) >= float(row.get("volume_ma_20", 1)):
        return "BUY"
    if float(row.get("ema_20", 0)) < float(row.get("ema_50", 0)) and float(row.get("rsi_14", 50)) >= 35:
        return "SELL"
    return "HOLD"

def evaluate_paper_signal(df: pd.DataFrame, interval: str, higher_tf_df: pd.DataFrame | None = None) -> PaperDecision:
    analysis = stage3_analysis(df, interval=interval, higher_tf_df=higher_tf_df)
    last = df.iloc[-1]; close = float(last.get("close", 0.0)); atr = float(last.get("atr_14", 0.0))
    return PaperDecision(signal=analysis.signal, score=float(analysis.score), explanation=analysis.explanation, regime=analysis.regime, atr=atr, adx=float(last.get("adx_14", 0.0)), support=float(last.get("bb_lower", close-atr)), resistance=float(last.get("bb_upper", close+atr)), stop_loss=max(close-1.5*atr,0.0), take_profit=close+3.0*atr, higher_timeframe_confirmation=higher_tf_df is not None)

def append_event_jsonl(path: Path | str, decision: PaperDecision, interval: str) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"interval": interval, "signal": decision.signal, "signal_score": decision.score, "signal_explanation": decision.explanation, "market_regime": decision.regime, "atr": decision.atr, "adx": decision.adx, "support": decision.support, "resistance": decision.resistance, "stop_loss": decision.stop_loss, "take_profit": decision.take_profit, "higher_timeframe_confirmation": decision.higher_timeframe_confirmation}
    with p.open("a", encoding="utf-8") as f: f.write(json.dumps(payload)+"\n")

def run_paper_cycle(df: pd.DataFrame, interval: str, state: PaperState, event_path: Path | str, close_trade: dict | None = None) -> dict:
    decision = evaluate_paper_signal(df, interval=interval)
    state.trade_count += 1
    append_event_jsonl(event_path, decision, interval)
    journal_entry = append_journal_entry(close_trade) if close_trade else None
    return {"signal": decision.signal, "market_regime": decision.regime, "signal_score": decision.score, "journal_written": bool(journal_entry)}
