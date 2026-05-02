from __future__ import annotations

import argparse
import json
import logging
import signal
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from .config import ALLOWED_SYMBOLS, DEFAULT_INTERVAL, PAPER_LOG_FILE, SUPPORTED_INTERVALS
from .data_fetcher import BinanceMarketDataFetcher
from .indicators import add_indicators
from .monitoring import format_alert, load_runtime_state, save_runtime_state, send_telegram_message, summarize_day
from .paper_trading import PaperTradeConfig, append_trade_event, generate_signal, load_state, risk_status, save_state
from .safety import block_private_keys, ensure_paper_trading_only


def paper_logger() -> logging.Logger:
    logger = logging.getLogger("xrp_paper")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    PAPER_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    h = RotatingFileHandler(PAPER_LOG_FILE, maxBytes=1_000_000, backupCount=3)
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(h)
    return logger


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="XRPUSDT")
    p.add_argument("--interval", default=DEFAULT_INTERVAL, choices=SUPPORTED_INTERVALS)
    p.add_argument("--balance", type=float, default=1000)
    p.add_argument("--once", action="store_true")
    p.add_argument("--loop", action="store_true")
    p.add_argument("--sleep-seconds", type=int, default=60)
    p.add_argument("--reset-state", action="store_true")
    p.add_argument("--command", default="")
    return p.parse_args()


def handle_command(command: str, runtime, state, price: float, risk: str) -> str:
    cmd = command.strip().lower()
    if cmd == "/pause":
        runtime.active = False
        return "Paper trading paused."
    if cmd == "/resume":
        runtime.active = True
        return "Paper trading resumed."
    if cmd == "/resetpaper":
        state.open_position = None
        state.trade_history = []
        state.realized_pnl = 0.0
        state.daily_realized_pnl = 0.0
        return "Paper state reset."
    if cmd == "/status":
        return f"Status: {'ACTIVE' if runtime.active else 'PAUSED'} | Balance: {state.fake_balance:.2f} | Price: {price:.6f}"
    if cmd == "/risk":
        return f"Risk: {risk} | Daily PnL: {state.daily_realized_pnl:.2f}"
    if cmd == "/summary":
        d = summarize_day(state)
        return f"Trades: {d['total_simulated_trades']} | Win rate: {d['win_rate']:.2f}% | PnL: {d['daily_pnl']:.2f}"
    return "Unsupported command."


def run_once(args, fetcher, cfg, logger, command: str | None = None):
    ensure_paper_trading_only()
    block_private_keys({})
    state = load_state(initial_balance=args.balance)
    runtime = load_runtime_state()
    today = datetime.now(timezone.utc).date().isoformat()
    state.reset_daily_if_needed(today)
    runtime.last_heartbeat = datetime.now(timezone.utc).isoformat()

    df = add_indicators(fetcher.fetch_klines(symbol=args.symbol, interval=args.interval, limit=120))
    row = df.iloc[-1]
    now_iso = datetime.now(timezone.utc).isoformat()
    candle_time = row["close_time"].isoformat()
    price = float(row["close"])
    signal = generate_signal(df)

    if command:
        msg = handle_command(command, runtime, state, price, risk_status(state, cfg))
        save_runtime_state(runtime)
        save_state(state, price)
        send_telegram_message(msg)
        print(msg)
        return

    if not runtime.active:
        save_runtime_state(runtime)
        save_state(state, price)
        send_telegram_message("Heartbeat: bot alive; paper trading paused.")
        return

    action = "SKIP"
    reason = "NO_SIGNAL"
    if state.open_position:
        low, high = float(row["low"]), float(row["high"])
        pos = state.open_position
        if low <= pos.stop_loss or high >= pos.take_profit:
            exit_price = pos.stop_loss if low <= pos.stop_loss else pos.take_profit
            reason = "STOP_LOSS" if low <= pos.stop_loss else "TAKE_PROFIT"
            pnl = (exit_price - pos.entry_price) * pos.size
            state.fake_balance += pnl
            state.realized_pnl += pnl
            state.daily_realized_pnl += pnl
            from .paper_trading import TradeRecord
            state.trade_history.append(TradeRecord(pos.opened_at, now_iso, pos.entry_price, exit_price, pos.size, pnl, (pnl / max(cfg.initial_balance, 1e-9)) * 100, reason))
            state.open_position = None
            action = "CLOSE"

    rstatus = risk_status(state, cfg)
    if action == "SKIP" and signal == "BUY" and rstatus == "OK":
        if state.open_position and state.open_position.entry_candle_time == candle_time:
            reason = "DUPLICATE_CANDLE"
        elif state.open_position is None:
            risk_amount = state.fake_balance * cfg.max_risk_per_trade
            stop_loss = price * (1 - cfg.stop_loss_pct)
            size = risk_amount / max(price - stop_loss, 1e-9)
            from .paper_trading import SimPosition
            state.open_position = SimPosition("LONG", price, size, stop_loss, price * (1 + cfg.take_profit_pct), now_iso, candle_time)
            action, reason = "OPEN", "BUY_SIGNAL"
    elif action == "SKIP" and signal == "BUY":
        reason = rstatus

    event = {
        "timestamp": now_iso, "symbol": args.symbol, "interval": args.interval, "event_type": action,
        "signal": signal, "signal_label": signal, "signal_score": 1.0 if signal == "BUY" else 0.2,
        "signal_explanation": reason, "market_regime": "bullish" if signal == "BUY" else "neutral",
        "support": float(row["bb_lower"]), "resistance": float(row["bb_upper"]), "price": price,
        "stop_loss": state.open_position.stop_loss if state.open_position else 0.0,
        "take_profit": state.open_position.take_profit if state.open_position else 0.0,
        "quantity": (state.open_position.size if state.open_position else 0.0), "fake_balance": state.fake_balance,
        "realized_pnl": state.realized_pnl, "unrealized_pnl": state.unrealized_pnl(price), "risk_status": rstatus, "reason": reason,
    }
    append_trade_event(event)
    logger.info(json.dumps(event))
    save_runtime_state(runtime)
    save_state(state, price)
    send_telegram_message(format_alert(event))


def main():
    should_run = {"value": True}

    def _shutdown_handler(signum, _frame):
        should_run["value"] = False

    signal.signal(signal.SIGINT, _shutdown_handler)
    signal.signal(signal.SIGTERM, _shutdown_handler)
    args = parse_args()
    if args.symbol not in ALLOWED_SYMBOLS:
        raise ValueError("Unsupported symbol")
    cfg = PaperTradeConfig(initial_balance=args.balance)
    fetcher = BinanceMarketDataFetcher()
    logger = paper_logger()
    if not args.once and not args.loop:
        args.once = True
    if args.loop:
        while should_run["value"]:
            try:
                run_once(args, fetcher, cfg, logger, args.command or None)
            except Exception as exc:
                logger.exception("Unhandled error in paper loop")
                send_telegram_message(f"SYSTEM ERROR: {exc}")
            time.sleep(max(1, args.sleep_seconds))
        logger.info("Graceful shutdown received; exiting paper loop")
    else:
        run_once(args, fetcher, cfg, logger, args.command or None)


if __name__ == "__main__":
    main()
