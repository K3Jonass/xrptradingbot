from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from .config import ALLOWED_SYMBOLS, DEFAULT_INTERVAL, PAPER_LOG_FILE, SUPPORTED_INTERVALS
from .data_fetcher import BinanceMarketDataFetcher
from .indicators import add_indicators
from .paper_trading import (
    PaperTradeConfig,
    append_trade_event,
    generate_signal,
    load_state,
    risk_status,
    save_state,
)
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
    return p.parse_args()


def run_once(args, fetcher, cfg, logger):
    ensure_paper_trading_only()
    block_private_keys({})
    state = load_state(initial_balance=args.balance)
    today = datetime.now(timezone.utc).date().isoformat()
    state.reset_daily_if_needed(today)

    df = add_indicators(fetcher.fetch_klines(symbol=args.symbol, interval=args.interval, limit=120))
    row = df.iloc[-1]
    now_iso = datetime.now(timezone.utc).isoformat()
    candle_time = row["close_time"].isoformat()
    price = float(row["close"])
    signal = generate_signal(df)
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

    event = {"timestamp": now_iso, "symbol": args.symbol, "interval": args.interval, "event_type": action, "signal": signal, "price": price, "quantity": (state.open_position.size if state.open_position else 0.0), "fake_balance": state.fake_balance, "realized_pnl": state.realized_pnl, "reason": reason}
    append_trade_event(event)
    logger.info(json.dumps(event))
    save_state(state, price)

    print(f"Current price: {price:.6f}\nSignal: {signal}\nFake balance: {state.fake_balance:.2f}\nOpen position: {state.open_position.side if state.open_position else 'NONE'}\nRealized PnL: {state.realized_pnl:.2f}\nUnrealized PnL: {state.unrealized_pnl(price):.2f}\nNumber of trades today: {state.trades_today}\nRisk status: {risk_status(state, cfg)}")


def main():
    args = parse_args()
    if args.symbol not in ALLOWED_SYMBOLS:
        raise ValueError("Unsupported symbol")
    cfg = PaperTradeConfig(initial_balance=args.balance)
    fetcher = BinanceMarketDataFetcher()
    logger = paper_logger()
    if not args.once and not args.loop:
        args.once = True
    if args.loop:
        while True:
            run_once(args, fetcher, cfg, logger)
            time.sleep(max(1, args.sleep_seconds))
    else:
        run_once(args, fetcher, cfg, logger)


if __name__ == "__main__":
    main()
