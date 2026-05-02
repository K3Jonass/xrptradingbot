from __future__ import annotations

import argparse
import json
from pathlib import Path

from xrp_bot.backtesting import BacktestConfig, run_backtest
from xrp_bot.data_fetcher import BinanceMarketDataFetcher
from xrp_bot.indicators import add_indicators


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="XRP offline backtest (simulation-only)")
    p.add_argument("--fixture", default="tests/fixtures/xrpusdt_1h_sample.json")
    p.add_argument("--initial-balance", type=float, default=1000)
    p.add_argument("--max-risk", type=float, default=0.02)
    p.add_argument("--stop-loss", type=float, default=0.02)
    p.add_argument("--take-profit", type=float, default=0.04)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    raw = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    df = BinanceMarketDataFetcher._normalize_klines(raw)
    df = add_indicators(df)
    cfg = BacktestConfig(
        initial_balance=args.initial_balance,
        max_risk_per_trade=args.max_risk,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
    )
    result = run_backtest(df, cfg).to_dict()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
