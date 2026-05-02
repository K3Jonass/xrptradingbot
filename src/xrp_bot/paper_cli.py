from __future__ import annotations

import argparse

from .monitoring import RuntimeState
from .paper_trading import PaperState


def handle_command(command: str, runtime: RuntimeState, state: PaperState, current_price: float, risk_status: str) -> str:
    cmd = command.strip().lower()
    if cmd == "/pause":
        runtime.active = False
        return "Paper trading paused."
    if cmd == "/resume":
        runtime.active = True
        return "Paper trading resumed."
    if cmd == "/status":
        return (
            f"Status: {'active' if runtime.active else 'paused'} | "
            f"Balance={state.fake_balance:.2f} | Price={current_price:.6f} | Risk={risk_status}"
        )
    if cmd == "/resetpaper":
        state.trade_history.clear()
        state.realized_pnl = 0.0
        state.daily_realized_pnl = 0.0
        return "Paper state reset."
    return "Unknown command."


def main() -> None:
    p = argparse.ArgumentParser(description="Paper simulator command utility")
    p.add_argument("--command", default="/status")
    p.parse_args()


if __name__ == "__main__":
    main()
