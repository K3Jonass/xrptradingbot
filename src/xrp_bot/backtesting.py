"""Offline backtesting engine (simulation-only, no real trading)."""

from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd

from .signal_engine import stage3_analysis


@dataclass
class BacktestConfig:
    initial_balance: float = 1000.0
    max_risk_per_trade: float = 0.02
    atr_stop_loss_multiple: float = 1.5
    atr_take_profit_multiple: float = 3.0
    rsi_buy_min: float = 50
    rsi_buy_max: float = 70
    volume_breakout_threshold: float = 1.2


@dataclass
class Trade:
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float


@dataclass
class BacktestResult:
    initial_balance: float
    final_balance: float
    total_trades: int
    win_rate: float
    total_return_pct: float
    max_drawdown_pct: float
    average_win: float
    average_loss: float
    profit_factor: float
    trades: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)


def run_backtest(df: pd.DataFrame, cfg: BacktestConfig) -> BacktestResult:
    balance = cfg.initial_balance
    peak_balance = balance
    max_drawdown = 0.0
    open_trade: dict | None = None
    trades: list[Trade] = []

    for i in range(1, len(df)):
        row = df.iloc[i]
        if open_trade is None:
            analysis = stage3_analysis(df.iloc[: i + 1], interval="1h")
            long_signal = analysis.signal in {"BUY", "STRONG_BUY"}
            if long_signal:
                entry = float(row["close"])
                risk_amount = balance * cfg.max_risk_per_trade
                atr = max(float(row.get("atr_14", 0.0)), 1e-9)
                stop = entry - (cfg.atr_stop_loss_multiple * atr)
                risk_per_unit = max(entry - stop, 1e-9)
                size = risk_amount / risk_per_unit
                open_trade = {
                    "entry_price": entry,
                    "entry_time": row["close_time"].isoformat(),
                    "size": size,
                    "stop": stop,
                    "take": entry + (cfg.atr_take_profit_multiple * atr),
                }
        else:
            low = float(row["low"])
            high = float(row["high"])
            exit_price = None
            if low <= open_trade["stop"]:
                exit_price = open_trade["stop"]
            elif high >= open_trade["take"]:
                exit_price = open_trade["take"]

            if exit_price is not None:
                pnl = (exit_price - open_trade["entry_price"]) * open_trade["size"]
                balance += pnl
                peak_balance = max(peak_balance, balance)
                dd = (peak_balance - balance) / peak_balance if peak_balance > 0 else 0.0
                max_drawdown = max(max_drawdown, dd)
                trades.append(
                    Trade(
                        entry_time=open_trade["entry_time"],
                        exit_time=row["close_time"].isoformat(),
                        entry_price=open_trade["entry_price"],
                        exit_price=exit_price,
                        size=open_trade["size"],
                        pnl=pnl,
                        pnl_pct=(pnl / max(cfg.initial_balance, 1e-9)) * 100,
                    )
                )
                open_trade = None

    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl < 0]
    total_trades = len(trades)
    win_rate = (len(wins) / total_trades * 100) if total_trades else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    profit_factor = (sum(wins) / abs(sum(losses))) if losses else float("inf") if wins else 0.0

    return BacktestResult(
        initial_balance=cfg.initial_balance,
        final_balance=balance,
        total_trades=total_trades,
        win_rate=win_rate,
        total_return_pct=((balance - cfg.initial_balance) / cfg.initial_balance) * 100,
        max_drawdown_pct=max_drawdown * 100,
        average_win=avg_win,
        average_loss=avg_loss,
        profit_factor=profit_factor,
        trades=[asdict(t) for t in trades],
    )
