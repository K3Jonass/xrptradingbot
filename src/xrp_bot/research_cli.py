from __future__ import annotations

import argparse
import json
from pathlib import Path

from xrp_bot.backtesting import BacktestConfig, batch_backtest, optimize_parameters, walk_forward_validation
from xrp_bot.data_fetcher import BinanceMarketDataFetcher
from xrp_bot.indicators import add_indicators
from xrp_bot.strategies import (
    BreakoutVolumeStrategy,
    EMACrossoverStrategy,
    RSIMeanReversionStrategy,
    Stage3CompositeStrategy,
)


def main() -> None:
    p = argparse.ArgumentParser(description="XRP strategy research lab (paper-only)")
    p.add_argument("--fixture", default="tests/fixtures/xrpusdt_1h_sample.json")
    args = p.parse_args()
    raw = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    df = add_indicators(BinanceMarketDataFetcher._normalize_klines(raw))
    cfg = BacktestConfig()
    strategies = [Stage3CompositeStrategy(), EMACrossoverStrategy(), RSIMeanReversionStrategy(), BreakoutVolumeStrategy()]
    results = batch_backtest(df, cfg, strategies)
    grid = [
        {"atr_stop_loss_multiple": 1.2, "atr_take_profit_multiple": 2.5, "adx_threshold": 18, "volume_breakout_threshold": 1.1},
        {"atr_stop_loss_multiple": 1.5, "atr_take_profit_multiple": 3.0, "adx_threshold": 20, "volume_breakout_threshold": 1.2},
        {"atr_stop_loss_multiple": 2.0, "atr_take_profit_multiple": 4.0, "adx_threshold": 25, "volume_breakout_threshold": 1.4},
    ]
    best = optimize_parameters(df, cfg, strategies, grid)
    wf = walk_forward_validation(df, cfg, Stage3CompositeStrategy(), train_size=80, test_size=40)
    print(json.dumps({"results": [r.to_dict() for r in results], "best": best, "walk_forward": wf}, indent=2))


if __name__ == "__main__":
    main()
