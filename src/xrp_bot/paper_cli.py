from __future__ import annotations

import argparse
import json
from pathlib import Path


def handle_command(command: str, runtime, state, current_price: float, risk_status: str) -> str:
    cmd = (command or "").strip().lower()
    if cmd == "/pause":
        runtime.active = False
        return "Bot paused."
    if cmd == "/resume":
        runtime.active = True
        return "Bot resumed."
    if cmd == "/status":
        return (
            f"Status: {'active' if runtime.active else 'paused'} | "
            f"Balance: {getattr(state, 'fake_balance', 0):.2f} | "
            f"Price: {current_price:.6f} | Risk: {risk_status}"
        )
    return "Unknown command."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Paper trading CLI placeholder (simulation-only).")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--state-path", default="data/paper_state.json")
    parser.add_argument("--include-prediction", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = {
        "mode": "paper",
        "paper_trading_only": True,
        "advisory_only": True,
        "state_path": str(Path(args.state_path)),
        "once": bool(args.once),
    }
    if args.include_prediction:
        pred_path = Path("data/models/model_report.json")
        payload["prediction_context"] = json.loads(pred_path.read_text()) if pred_path.exists() else None
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
