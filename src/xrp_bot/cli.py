from __future__ import annotations

import argparse
import json
import sys

from .analyzer import detect_market_conditions
from .config import ALLOWED_SYMBOLS, DEFAULT_INTERVAL, DEFAULT_LIMIT, MAX_LIMIT, MIN_LIMIT, SUPPORTED_INTERVALS
from .data_fetcher import BinanceMarketDataFetcher, DataFetchError
from .indicators import add_indicators
from .logger import setup_logger
from .reporter import build_report_payload, print_report, save_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="XRP/USDT market analyzer (no trading).")
    parser.add_argument("--symbol", default="XRPUSDT")
    parser.add_argument("--interval", default=DEFAULT_INTERVAL, choices=SUPPORTED_INTERVALS)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--no-save", action="store_true", help="Do not write output files.")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    return parser.parse_args()


def validate_inputs(symbol: str, interval: str, limit: int) -> None:
    if symbol not in ALLOWED_SYMBOLS:
        raise ValueError(f"Unsupported symbol '{symbol}'. Allowed: {sorted(ALLOWED_SYMBOLS)}")
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(f"Unsupported interval '{interval}'.")
    if not (MIN_LIMIT <= limit <= MAX_LIMIT):
        raise ValueError(f"Candle limit must be between {MIN_LIMIT} and {MAX_LIMIT}.")


def main() -> None:
    args = parse_args()
    logger = setup_logger()
    try:
        validate_inputs(args.symbol, args.interval, args.limit)
        df = BinanceMarketDataFetcher().fetch_klines(args.interval, args.limit, symbol=args.symbol)
        df = add_indicators(df)
        report = build_report_payload(args.interval, df, detect_market_conditions(df).to_dict())
        if args.output == "json":
            print(json.dumps(report, indent=2))
        else:
            print_report(report)
        if not args.no_save:
            save_report(report)
        logger.info("Analysis complete.")
    except (ValueError, DataFetchError) as exc:
        logger.exception("Analyzer failed: %s", exc)
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
