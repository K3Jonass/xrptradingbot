import json
from pathlib import Path


from xrp_bot.backtesting import BacktestConfig, batch_backtest, optimize_parameters, walk_forward_validation
from xrp_bot.data_fetcher import BinanceMarketDataFetcher
from xrp_bot.indicators import add_indicators
from xrp_bot.strategies import (
    BaseStrategy,
    BreakoutVolumeStrategy,
    EMACrossoverStrategy,
    RSIMeanReversionStrategy,
    Stage3CompositeStrategy,
)


def _df():
    fixture = Path(__file__).parent / "fixtures" / "xrpusdt_1h_sample.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    return add_indicators(BinanceMarketDataFetcher._normalize_klines(raw))


def test_strategy_interface_shape():
    assert issubclass(Stage3CompositeStrategy, BaseStrategy)


def test_each_strategy_generates_action():
    df = _df()
    for strat in [Stage3CompositeStrategy(), EMACrossoverStrategy(), RSIMeanReversionStrategy(), BreakoutVolumeStrategy()]:
        sig = strat.generate_signal(df)
        assert sig.action in {"BUY", "HOLD"}


def test_batch_backtesting_outputs_results():
    df = _df()
    results = batch_backtest(df, BacktestConfig(), [Stage3CompositeStrategy(), EMACrossoverStrategy()])
    assert len(results) == 2
    assert all(hasattr(r, "sharpe_ratio") for r in results)


def test_optimization_output():
    df = _df()
    best = optimize_parameters(df, BacktestConfig(), [Stage3CompositeStrategy()], [{"adx_threshold": 10}, {"adx_threshold": 30}])
    assert "params" in best


def test_walk_forward_split_logic():
    df = _df()
    out = walk_forward_validation(df, BacktestConfig(), Stage3CompositeStrategy(), train_size=60, test_size=30)
    assert out
    assert all(w["test"] == 30 for w in out)
