"""Offline backtesting engine (simulation-only, no real trading)."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json

import numpy as np
import pandas as pd

from .config import DATA_DIR, PAPER_TRADING_ONLY
from .strategies import BaseStrategy, Stage3CompositeStrategy


@dataclass
class BacktestConfig:
    initial_balance: float = 1000.0
    max_risk_per_trade: float = 0.02
    atr_stop_loss_multiple: float = 1.5
    atr_take_profit_multiple: float = 3.0
    adx_threshold: float = 20.0
    ema_fast_period: int = 20
    ema_slow_period: int = 50
    rsi_buy_threshold: float = 35.0
    rsi_sell_threshold: float = 65.0
    volume_breakout_threshold: float = 1.2


@dataclass
class BacktestResult:
    strategy: str
    initial_balance: float
    final_balance: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    average_trade_duration_hours: float
    number_of_trades: int
    trades: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)
    @property
    def total_trades(self) -> int:
        return self.number_of_trades



def run_backtest(df: pd.DataFrame, cfg: BacktestConfig, strategy: BaseStrategy | None = None) -> BacktestResult:
    if not PAPER_TRADING_ONLY:
        raise RuntimeError("Research mode requires PAPER_TRADING_ONLY=True")
    strategy = strategy or Stage3CompositeStrategy()
    balance = cfg.initial_balance
    peak = balance
    open_trade = None
    equity_curve = [balance]
    trades: list[dict] = []

    for i in range(30, len(df)):
        row = df.iloc[i]
        w = df.iloc[: i + 1]
        if open_trade is None:
            sig = strategy.generate_signal(w)
            if sig.action == "BUY" and float(row.get("adx_14", 0.0)) >= cfg.adx_threshold:
                entry = float(row["close"])
                atr = max(float(row.get("atr_14", 0.0)), 1e-9)
                risk_amount = balance * cfg.max_risk_per_trade
                stop = entry - cfg.atr_stop_loss_multiple * atr
                size = risk_amount / max(entry - stop, 1e-9)
                open_trade = {
                    "entry_time": row["close_time"], "entry_price": entry, "size": size,
                    "stop": stop, "take": entry + cfg.atr_take_profit_multiple * atr,
                }
        else:
            low, high = float(row["low"]), float(row["high"])
            exit_price = open_trade["stop"] if low <= open_trade["stop"] else open_trade["take"] if high >= open_trade["take"] else None
            if exit_price is not None:
                pnl = (exit_price - open_trade["entry_price"]) * open_trade["size"]
                balance += pnl
                dur = (row["close_time"] - open_trade["entry_time"]).total_seconds() / 3600
                trades.append({"pnl": pnl, "duration_hours": dur})
                open_trade = None
        peak = max(peak, balance)
        equity_curve.append(balance)

    return _metrics(cfg.initial_balance, balance, trades, equity_curve, strategy.name)


def _metrics(initial: float, final: float, trades: list[dict], equity_curve: list[float], strategy: str) -> BacktestResult:
    pnls = [t["pnl"] for t in trades]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    rets = pd.Series(equity_curve).pct_change().fillna(0)
    sharpe = float((rets.mean() / rets.std()) * np.sqrt(252)) if rets.std() > 0 else 0.0
    dd = (pd.Series(equity_curve).cummax() - pd.Series(equity_curve)) / pd.Series(equity_curve).cummax()
    avg_dur = float(np.mean([t["duration_hours"] for t in trades])) if trades else 0.0
    return BacktestResult(
        strategy=strategy,
        initial_balance=initial,
        final_balance=final,
        total_return_pct=((final - initial) / initial) * 100,
        max_drawdown_pct=float(dd.max() * 100) if len(dd) else 0.0,
        sharpe_ratio=sharpe,
        win_rate=(len(wins) / len(pnls) * 100) if pnls else 0.0,
        profit_factor=(sum(wins) / abs(sum(losses))) if losses else (float("inf") if wins else 0.0),
        average_trade_duration_hours=avg_dur,
        number_of_trades=len(trades),
        trades=trades,
    )


def batch_backtest(df: pd.DataFrame, cfg: BacktestConfig, strategies: list[BaseStrategy]) -> list[BacktestResult]:
    results = [run_backtest(df, cfg, s) for s in strategies]
    outdir = DATA_DIR / "backtests"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "batch_report.json").write_text(json.dumps([r.to_dict() for r in results], indent=2), encoding="utf-8")
    return results


def optimize_parameters(df: pd.DataFrame, cfg: BacktestConfig, strategies: list[BaseStrategy], grid: list[dict]) -> dict:
    best = {"score": float("-inf")}
    for params in grid:
        c = BacktestConfig(**{**asdict(cfg), **{k: v for k, v in params.items() if hasattr(cfg, k)}})
        res = batch_backtest(df, c, strategies)
        score = max(r.total_return_pct for r in res)
        if score > best["score"]:
            best = {"score": score, "params": params}
    return best


def walk_forward_validation(df: pd.DataFrame, cfg: BacktestConfig, strategy: BaseStrategy, train_size: int, test_size: int) -> list[dict]:
    windows = []
    start = 0
    while start + train_size + test_size <= len(df):
        train = df.iloc[start:start + train_size]
        test = df.iloc[start + train_size:start + train_size + test_size]
        # strategy is rule-based; "train" reserved for optimization workflows
        _ = train
        r = run_backtest(test, cfg, strategy)
        windows.append({"start": start, "train": train_size, "test": test_size, "return": r.total_return_pct})
        start += test_size
    return windows
