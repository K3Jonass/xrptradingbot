from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib import parse, request

from .config import DATA_DIR, TELEGRAM

RUNTIME_FILE = DATA_DIR / "runtime_state.json"


@dataclass
class RuntimeState:
    active: bool = True
    last_heartbeat: str = ""

    def to_dict(self) -> dict:
        return {"active": self.active, "last_heartbeat": self.last_heartbeat}

    @classmethod
    def from_dict(cls, payload: dict) -> "RuntimeState":
        return cls(active=bool(payload.get("active", True)), last_heartbeat=payload.get("last_heartbeat", ""))


def load_runtime_state(path: Path = RUNTIME_FILE) -> RuntimeState:
    if not path.exists():
        return RuntimeState(active=True, last_heartbeat=datetime.now(timezone.utc).isoformat())
    return RuntimeState.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_runtime_state(state: RuntimeState, path: Path = RUNTIME_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def telegram_enabled() -> bool:
    return bool(TELEGRAM.get("enabled") and TELEGRAM.get("bot_token") and TELEGRAM.get("chat_id"))


def send_telegram_message(text: str) -> None:
    if not telegram_enabled():
        return
    token = TELEGRAM["bot_token"]
    chat_id = TELEGRAM["chat_id"]
    base_url = TELEGRAM.get("base_url", "https://api.telegram.org")
    payload = parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = request.Request(f"{base_url}/bot{token}/sendMessage", data=payload)
    with request.urlopen(req, timeout=10) as _:
        pass


def format_alert(payload: dict) -> str:
    return (
        f"[{payload.get('event_type', 'ANALYSIS')}] {payload.get('symbol', 'XRPUSDT')} {payload.get('interval', '')}\n"
        f"Price: {payload.get('price', 0):.6f}\n"
        f"Signal: {payload.get('signal_label', payload.get('signal', 'HOLD'))} (score={payload.get('signal_score', 0):.2f})\n"
        f"Why: {payload.get('signal_explanation', 'N/A')}\n"
        f"Regime: {payload.get('market_regime', 'unknown')}\n"
        f"S/R: {payload.get('support', 0):.6f} / {payload.get('resistance', 0):.6f}\n"
        f"SL/TP: {payload.get('stop_loss', 0):.6f} / {payload.get('take_profit', 0):.6f}\n"
        f"Balance: {payload.get('fake_balance', 0):.2f}\n"
        f"PnL R/U: {payload.get('realized_pnl', 0):.2f} / {payload.get('unrealized_pnl', 0):.2f}\n"
        f"Risk: {payload.get('risk_status', 'OK')}"
    )


def summarize_day(state) -> dict:
    trades = state.trade_history
    wins = [t for t in trades if t.pnl > 0]
    total = len(trades)
    win_rate = (len(wins) / total * 100) if total else 0.0
    best = max([t.pnl for t in trades], default=0.0)
    worst = min([t.pnl for t in trades], default=0.0)
    peak = state.day_start_balance
    equity = state.fake_balance
    drawdown = min(0.0, equity - peak)
    return {
        "total_simulated_trades": total,
        "win_rate": win_rate,
        "daily_pnl": state.daily_realized_pnl,
        "best_trade": best,
        "worst_trade": worst,
        "current_balance": state.fake_balance,
        "drawdown": drawdown,
    }
