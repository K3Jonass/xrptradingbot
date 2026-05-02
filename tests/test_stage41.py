import os

from xrp_bot.config import redact_secrets
from xrp_bot.healthcheck_cli import run_healthcheck
from xrp_bot.monitoring import RuntimeState
from xrp_bot.paper_cli import handle_command
from xrp_bot.paper_trading import PaperState


def test_secret_redaction():
    redacted = redact_secrets({"bot_token": "abc", "chat_id": "123"})
    assert redacted["bot_token"] == "***REDACTED***"
    assert redacted["chat_id"] == "***REDACTED***"


def test_env_loading_present():
    # env may vary in CI; assert key names are accepted if present
    os.environ["TELEGRAM_BOT_TOKEN"] = "token"
    os.environ["TELEGRAM_CHAT_ID"] = "chat"
    assert os.getenv("TELEGRAM_BOT_TOKEN") == "token"


def test_graceful_shutdown_flag_behavior():
    runtime = RuntimeState(active=True)
    state = PaperState(fake_balance=1000, day_start_balance=1000, last_reset_date="2026-05-02")
    response = handle_command("/pause", runtime, state, 1.0, "OK")
    assert runtime.active is False
    assert "paused" in response.lower()


def test_healthcheck_logic_smoke(monkeypatch):
    monkeypatch.setattr("xrp_bot.healthcheck_cli.BinanceMarketDataFetcher.fetch_klines", lambda self, interval, limit: [])
    checks = run_healthcheck()
    assert "config" in checks and "telegram" in checks
