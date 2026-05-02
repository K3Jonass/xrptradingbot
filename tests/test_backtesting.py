import json
from pathlib import Path

from xrp_bot.backtesting import BacktestConfig, run_backtest
from xrp_bot.data_fetcher import BinanceMarketDataFetcher
from xrp_bot.indicators import add_indicators


def test_backtest_outputs_metrics():
    fixture = Path(__file__).parent / "fixtures" / "xrpusdt_1h_sample.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    df = add_indicators(BinanceMarketDataFetcher._normalize_klines(raw))
    result = run_backtest(df, BacktestConfig())
    assert result.total_trades >= 0
    assert isinstance(result.win_rate, float)
    assert isinstance(result.total_return_pct, float)
    assert hasattr(result, "profit_factor")
