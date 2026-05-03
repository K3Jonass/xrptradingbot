from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

SIGNAL_ALERTS = {"STRONG_BUY", "BUY", "SELL", "STRONG_SELL"}


@dataclass
class TelegramRuntimeState:
    active: bool = True
    paused: bool = False
    last_alert_timestamp: str | None = None
    last_signal_sent: str | None = None
    cycle_count: int = 0
    hold_skip_count: int = 0
    update_offset: int = 0


class TelegramAlertEngine:
    def __init__(self, config: dict[str, Any]):
        self.enabled = bool(config.get("enabled", False))
        self.bot_token = str(config.get("bot_token", ""))
        self.chat_id = str(config.get("chat_id", ""))
        self.base_url = str(config.get("base_url", "https://api.telegram.org"))
        self.hold_skip_summary_every = int(config.get("hold_skip_summary_every", 10))

    def is_config_valid(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def _url(self, method: str) -> str:
        return f"{self.base_url}/bot{self.bot_token}/{method}"

    def send_message(self, text: str) -> bool:
        if not self.enabled or not self.is_config_valid():
            return False
        resp = requests.post(self._url("sendMessage"), json={"chat_id": self.chat_id, "text": text}, timeout=10)
        return resp.status_code == 200

    def poll_commands(self, runtime: TelegramRuntimeState) -> list[str]:
        if not self.enabled or not self.is_config_valid():
            return []
        resp = requests.get(self._url("getUpdates"), params={"offset": runtime.update_offset + 1, "timeout": 0}, timeout=10)
        if resp.status_code != 200:
            return []
        payload = resp.json()
        commands: list[str] = []
        for item in payload.get("result", []):
            runtime.update_offset = max(runtime.update_offset, int(item.get("update_id", 0)))
            text = (((item.get("message") or {}).get("text")) or "").strip()
            if text.startswith("/"):
                commands.append(text.lower())
        return commands


def format_alert_message(payload: dict[str, Any], event_type: str) -> str:
    ts = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    return (
        f"Event: {event_type}\n"
        f"Symbol: {payload.get('symbol', 'XRPUSDT')}\n"
        f"Price: {payload.get('current_price', 0):.6f}\n"
        f"Signal: {payload.get('signal_label', payload.get('signal', 'HOLD'))}\n"
        f"Score: {payload.get('signal_score', 0):.2f}\n"
        f"Why: {payload.get('signal_explanation', '')}\n"
        f"Regime: {payload.get('market_regime', 'unknown')}\n"
        f"Support/Resistance: {payload.get('support', 0):.6f} / {payload.get('resistance', 0):.6f}\n"
        f"SL/TP: {payload.get('atr_stop_loss', 0):.6f} / {payload.get('atr_take_profit', 0):.6f}\n"
        f"Fake Balance: {payload.get('fake_balance', 0):.2f}\n"
        f"Realized PnL: {payload.get('realized_pnl', 0):.2f}\n"
        f"Unrealized PnL: {payload.get('unrealized_pnl', 0):.2f}\n"
        f"Risk: {payload.get('risk_status', 'OK')}\n"
        f"Prediction: {payload.get('prediction_context', 'n/a')}\n"
        f"Timestamp: {ts}"
    )


def should_send_alert(signal: str, event_type: str, runtime: TelegramRuntimeState, hold_skip_every: int) -> bool:
    if event_type in {"OPEN", "CLOSE", "RISK_WARNING", "SYSTEM_ERROR", "DAILY_SUMMARY"}:
        return True
    if signal in SIGNAL_ALERTS:
        return True
    if signal in {"HOLD", "SKIP"}:
        runtime.hold_skip_count += 1
        return runtime.hold_skip_count % max(1, hold_skip_every) == 0
    return False
