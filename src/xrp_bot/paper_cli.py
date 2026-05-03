from __future__ import annotations

import argparse
import json
import signal
import time
from pathlib import Path

from .data_fetcher import BinanceMarketDataFetcher
from .indicators import add_indicators
from .paper_trading import load_state, run_paper_cycle, save_state
from .config import TELEGRAM, SYMBOL
from .telegram import TelegramAlertEngine, TelegramRuntimeState, format_alert_message, should_send_alert


def handle_command(command: str, runtime, state, current_price: float, risk_status: str) -> str:
    cmd = (command or "").strip().lower()
    if cmd == "/pause":
        runtime.active = False
        runtime.paused = True
        return "Paper bot paused."
    if cmd == "/resume":
        runtime.active = True
        runtime.paused = False
        return "Paper bot resumed."
    if cmd == "/status":
        return f"Status: {'active' if runtime.active else 'paused'} | Balance: {state.fake_balance:.2f} | Price: {current_price:.6f}"
    if cmd == "/summary":
        return f"Cycle: {runtime.cycle_count} | Realized: {state.realized_pnl:.2f} | Unrealized: {state.unrealized_pnl:.2f}"
    if cmd == "/risk":
        return f"Risk status: {risk_status}"
    if cmd == "/lastsignal":
        return f"Last signal sent: {runtime.last_signal_sent or 'none'}"
    return "Unknown command."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Paper trading CLI placeholder (simulation-only).")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=30.0)
    parser.add_argument("--max-cycles", type=int, default=None)
    parser.add_argument("--state-path", default="data/paper_state.json")
    parser.add_argument("--include-prediction", action="store_true")
    return parser.parse_args()


def _run_single_cycle(args: argparse.Namespace, state, fetcher: BinanceMarketDataFetcher) -> dict:
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
    return {
        "current_price": current_price,
        "event": event,
        "event_type": event_type,
        "reason": reason,
        "signal": signal,
    }


def main() -> None:
    args = parse_args()
    should_loop = bool(args.loop or not args.once)
    stop_requested = False

    def _handle_sigint(_signum, _frame):
        nonlocal stop_requested
        stop_requested = True
        print("Received Ctrl+C, finishing current cycle and shutting down gracefully.")

    signal.signal(signal.SIGINT, _handle_sigint)

    payload = {
        "symbol": SYMBOL,
        "mode": "paper",
        "paper_trading_only": True,
        "advisory_only": True,
        "state_path": str(Path(args.state_path)),
        "once": bool(args.once),
        "loop": bool(should_loop),
        "sleep_seconds": float(args.sleep_seconds),
    }
    state = load_state(Path(args.state_path))
    fetcher = BinanceMarketDataFetcher()
    telegram = TelegramAlertEngine(TELEGRAM)
    runtime = TelegramRuntimeState()
    cycle_count = 0
    while True:
        try:
            cycle_count += 1
            runtime.cycle_count = cycle_count
            for cmd in telegram.poll_commands(runtime):
                reply = handle_command(cmd, runtime, state, 0.0, "OK")
                telegram.send_message(reply)
            if not runtime.active:
                time.sleep(max(0.0, float(args.sleep_seconds)))
                if args.max_cycles is not None and cycle_count >= args.max_cycles:
                    break
                continue
            cycle_result = _run_single_cycle(args, state, fetcher)
            event = cycle_result["event"]
            payload.update({
            "timestamp": event.get("timestamp"),
            "current_price": cycle_result["current_price"],
            "signal_label": event.get("signal_label", cycle_result["signal"]),
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
            "event_type": cycle_result["event_type"],
            "reason": cycle_result["reason"],
            "cycle": cycle_count,
        })
            if should_send_alert(cycle_result["signal"], cycle_result["event_type"], runtime, telegram.hold_skip_summary_every):
                text = format_alert_message(payload, cycle_result["event_type"])
                if telegram.send_message(text):
                    runtime.last_alert_timestamp = payload.get("timestamp")
                    runtime.last_signal_sent = cycle_result["signal"]

            print(json.dumps({
                "heartbeat": True,
                "cycle": cycle_count,
                "timestamp": event.get("timestamp"),
                "price": cycle_result["current_price"],
                "signal": cycle_result["signal"],
                "event_type": cycle_result["event_type"],
            }))
            if not should_loop:
                break
            if args.max_cycles is not None and cycle_count >= args.max_cycles:
                break
            if stop_requested:
                break
            time.sleep(max(0.0, float(args.sleep_seconds)))
        except KeyboardInterrupt:
            print("Received Ctrl+C, shutting down gracefully.")
            break

    if args.include_prediction:
        pred_path = Path("data/models/model_report.json")
        payload["prediction_context"] = json.loads(pred_path.read_text()) if pred_path.exists() else None
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
