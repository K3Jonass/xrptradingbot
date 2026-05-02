from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data_fetcher import BinanceMarketDataFetcher
from .indicators import add_indicators
from .paper_trading import append_event_jsonl, build_paper_report, evaluate_paper_signal


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="XRP live paper trading loop (paper only)")
    p.add_argument("--symbol", default="XRPUSDT")
    p.add_argument("--interval", default="15m", choices=["15m", "1h", "4h"])
    p.add_argument("--limit", type=int, default=300)
    p.add_argument("--event-file", default="data/paper_events.jsonl")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    fetcher = BinanceMarketDataFetcher()
    entry_df = add_indicators(fetcher.fetch_klines(args.interval, args.limit, symbol=args.symbol))
    higher_tf_df = None
    if args.interval in {"15m", "1h"}:
        higher_tf_df = add_indicators(fetcher.fetch_klines("4h", min(args.limit, 300), symbol=args.symbol))
    decision = evaluate_paper_signal(entry_df, interval=args.interval, higher_tf_df=higher_tf_df)
    report = build_paper_report(decision)
    append_event_jsonl(Path(args.event_file), decision, interval=args.interval)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
