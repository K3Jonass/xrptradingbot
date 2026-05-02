from __future__ import annotations

import argparse
import json

from .data_fetcher import BinanceMarketDataFetcher
from .indicators import add_indicators
from .prediction import train_and_predict


def main() -> None:
    parser = argparse.ArgumentParser(description="XRP direction prediction research (paper-only)")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    fetcher = BinanceMarketDataFetcher()
    df = add_indicators(fetcher.fetch_klines(args.interval, args.limit, symbol="XRPUSDT"))
    pred, report = train_and_predict(df)
    print(
        json.dumps(
            {
                "predicted_direction": pred.predicted_direction,
                "confidence_score": pred.confidence_score,
                "model_name": pred.model_name,
                "model_version": pred.model_version,
                "feature_timestamp": pred.feature_timestamp,
                "paper_trading_only": True,
                "advisory_only": True,
                "no_execution_authority": True,
                "report_summary": report.get("metrics", {}),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
