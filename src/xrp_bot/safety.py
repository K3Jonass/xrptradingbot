"""Hard safety guardrails to enforce paper-trading-only behavior."""

from __future__ import annotations

PAPER_TRADING_ONLY = True


class SafetyViolation(RuntimeError):
    pass


BLOCKED_FUNCTIONS = {
    "place_market_order",
    "place_limit_order",
    "create_order",
    "new_order",
    "futures_create_order",
    "margin_create_order",
    "get_account",
    "get_my_trades",
}

BLOCKED_ENV_KEYS = {
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "BINANCE_KEY",
    "BINANCE_SECRET",
}


def ensure_paper_trading_only() -> None:
    if not PAPER_TRADING_ONLY:
        raise SafetyViolation("PAPER_TRADING_ONLY must remain True.")


def block_private_keys(env: dict[str, str]) -> None:
    ensure_paper_trading_only()
    present = [k for k in BLOCKED_ENV_KEYS if env.get(k)]
    if present:
        raise SafetyViolation(f"Private Binance key usage is blocked: {sorted(present)}")


def block_private_endpoint(endpoint_name: str) -> None:
    ensure_paper_trading_only()
    if endpoint_name in BLOCKED_FUNCTIONS:
        raise SafetyViolation(f"Blocked private or order endpoint: {endpoint_name}")
