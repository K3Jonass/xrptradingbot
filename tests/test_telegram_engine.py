from __future__ import annotations

import importlib

from xrp_bot.paper_cli import handle_command
from xrp_bot.telegram import TelegramRuntimeState, format_alert_message, should_send_alert


def test_alert_formatting_contains_required_fields():
    msg = format_alert_message({"symbol": "XRPUSDT", "current_price": 2.0, "signal_label": "BUY", "signal_score": 80, "signal_explanation": "momentum", "market_regime": "trend", "support": 1.9, "resistance": 2.1, "atr_stop_loss": 1.8, "atr_take_profit": 2.4, "fake_balance": 1000, "realized_pnl": 20, "unrealized_pnl": 3, "risk_status": "OK", "prediction_context": "bullish", "timestamp": "2026-01-01T00:00:00Z"}, "OPEN")
    assert "Symbol: XRPUSDT" in msg and "Risk: OK" in msg and "Prediction:" in msg


def test_no_spam_on_hold_skip():
    rt = TelegramRuntimeState()
    assert should_send_alert("HOLD", "SKIP", rt, 3) is False
    assert should_send_alert("HOLD", "SKIP", rt, 3) is False
    assert should_send_alert("HOLD", "SKIP", rt, 3) is True


def test_command_handling():
    class S:
        fake_balance = 1000.0
        realized_pnl = 1.0
        unrealized_pnl = 2.0

    rt = TelegramRuntimeState()
    assert "paused" in handle_command("/pause", rt, S(), 2.0, "OK").lower()
    assert rt.active is False
    assert "resumed" in handle_command("/resume", rt, S(), 2.0, "OK").lower()
    assert "Risk status" in handle_command("/risk", rt, S(), 2.0, "OK")


def test_env_secret_loading(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    cfg = importlib.reload(importlib.import_module("xrp_bot.config"))
    assert cfg.TELEGRAM["bot_token"] == "abc"


def test_missing_token_behavior():
    from xrp_bot.telegram import TelegramAlertEngine

    e = TelegramAlertEngine({"enabled": True, "bot_token": "", "chat_id": ""})
    assert e.is_config_valid() is False


def test_xrp_telegram_test_import():
    assert importlib.import_module("xrp_bot.telegram_test_cli")
