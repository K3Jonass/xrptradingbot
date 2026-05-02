from __future__ import annotations

from .safety import PAPER_TRADING_ONLY, ensure_paper_trading_only


def run_healthcheck() -> dict:
    ensure_paper_trading_only()
    return {
        "status": "ok",
        "config": "ok",
        "telegram": "disabled_or_unconfigured",
        "paper_trading_only": PAPER_TRADING_ONLY,
        "private_api_enabled": False,
        "order_execution_enabled": False,
    }
