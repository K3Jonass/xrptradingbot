"""Deterministic offline local validation for VS Code workflows."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from xrp_bot.analyzer import detect_market_conditions
from xrp_bot.backtesting import BacktestConfig, run_backtest
from xrp_bot.config import load_settings
from xrp_bot.dashboard import calculate_dashboard_metrics
from xrp_bot.data_fetcher import BinanceMarketDataFetcher
from xrp_bot.indicators import add_indicators
from xrp_bot.journal_cli import main as journal_main
from xrp_bot.paper_trading import evaluate_paper_signal, load_state, save_state
from xrp_bot.prediction import train_and_predict


def _load_fixture_df() -> tuple[Path, object]:
    root = Path(__file__).resolve().parents[1]
    fixture = root / "tests" / "fixtures" / "xrpusdt_1h_sample.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    df = add_indicators(BinanceMarketDataFetcher._normalize_klines(raw))
    return root, df


def main() -> None:
    # config load
    settings = load_settings()
    assert settings["app"]["symbol"] == "XRPUSDT"

    # module imports
    for mod in [
        "xrp_bot.cli",
        "xrp_bot.backtest_cli",
        "xrp_bot.paper_cli",
        "xrp_bot.dashboard_cli",
        "xrp_bot.healthcheck_cli",
        "xrp_bot.research_cli",
        "xrp_bot.predict_cli",
        "xrp_bot.journal_cli",
    ]:
        importlib.import_module(mod)

    root, df = _load_fixture_df()

    # fixture-based analysis
    analysis = detect_market_conditions(df)
    assert analysis.signal in {"STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"}

    # fixture-based backtest
    backtest = run_backtest(df, BacktestConfig())
    assert backtest.initial_balance > 0

    # fixture-based paper cycle
    state_file = root / "data" / "local_check_paper_state.json"
    state = load_state(path=state_file, initial_balance=1000.0)
    decision = evaluate_paper_signal(df, interval="1h")
    assert decision.signal in {"BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"}
    save_state(state, current_price=float(df.iloc[-1]["close"]), path=state_file)

    # fixture-based journal summary
    journal_file = root / "data" / "paper_trades.jsonl"
    if not journal_file.exists():
        journal_file.parent.mkdir(parents=True, exist_ok=True)
        journal_file.write_text("", encoding="utf-8")
    journal_main()

    # fixture-based dashboard metrics
    import pandas as pd

    trades = pd.DataFrame([{"pnl": 10.0}, {"pnl": -4.0}, {"pnl": 2.0}])
    metrics = calculate_dashboard_metrics({"fake_balance": 1008.0, "day_start_balance": 1000.0, "realized_pnl": 8.0}, trades)
    assert metrics["total_simulated_trades"] == 3

    # prediction report shape check
    pred, report = train_and_predict(df)
    assert pred.predicted_direction in {"UP", "DOWN", "FLAT"}
    assert "metrics" in report

    print("LOCAL CHECK PASSED")


if __name__ == "__main__":
    main()
