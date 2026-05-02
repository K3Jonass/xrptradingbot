from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data_fetcher import BinanceMarketDataFetcher
from .indicators import add_indicators
from .paper_trading import load_state, run_paper_cycle, save_state


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
    if args.once:
        state = load_state(Path(args.state_path))
        fetcher = BinanceMarketDataFetcher()
        df = add_indicators(fetcher.fetch_klines(interval="1h", limit=200, symbol="XRPUSDT"))
        current_price = float(df.iloc[-1]["close"])
        result = run_paper_cycle(df, "1h", state, Path("data/paper_trades.jsonl"))
        event = result["event"]
        signal = str(event.get("signal", "HOLD"))
        if signal in {"BUY", "STRONG_BUY"} and state.open_position is None:
            state.open_position = {
                "entry_price": current_price,
                "size": 1.0,
                "opened_at": event.get("timestamp"),
            }
            event_type = "OPEN"
            reason = "signal met entry criteria"
        elif signal in {"SELL", "STRONG_SELL"} and state.open_position is not None:
            entry_price = float(state.open_position.get("entry_price", current_price))
            size = float(state.open_position.get("size", 1.0))
            pnl = (current_price - entry_price) * size
            state.realized_pnl += pnl
            state.fake_balance += pnl
            state.open_position = None
            state.unrealized_pnl = 0.0
            event_type = "CLOSE"
            reason = "exit signal met"
        else:
            event_type = "SKIP"
            reason = "signal did not meet entry criteria"

        if state.open_position is not None:
            entry_price = float(state.open_position.get("entry_price", current_price))
            size = float(state.open_position.get("size", 1.0))
            state.unrealized_pnl = (current_price - entry_price) * size
        save_state(state, current_price=current_price, path=Path(args.state_path))

        payload.update({
            "current_price": current_price,
            "signal_label": event.get("signal_label", signal),
            "signal_score": float(event.get("signal_score", 0.0)),
            "signal_explanation": event.get("signal_explanation", ""),
            "market_regime": event.get("market_regime", "unknown"),
            "support": float(event.get("support", 0.0)),
            "resistance": float(event.get("resistance", 0.0)),
            "atr_stop_loss": float(event.get("stop_loss", 0.0)),
            "atr_take_profit": float(event.get("take_profit", 0.0)),
            "fake_balance": float(state.fake_balance),
            "open_position": state.open_position,
            "realized_pnl": float(state.realized_pnl),
            "unrealized_pnl": float(state.unrealized_pnl),
            "risk_status": "OK",
            "event_type": event_type,
            "reason": reason,
        })

    if args.include_prediction:
        pred_path = Path("data/models/model_report.json")
        payload["prediction_context"] = json.loads(pred_path.read_text()) if pred_path.exists() else None
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
