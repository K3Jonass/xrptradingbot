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

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Paper trading CLI placeholder (simulation-only).")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--state-path", default="data/paper_state.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = {
        "mode": "paper",
        "paper_trading_only": True,
        "state_path": str(Path(args.state_path)),
        "once": bool(args.once),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
