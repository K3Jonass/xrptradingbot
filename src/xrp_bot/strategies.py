from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from .signal_engine import stage3_analysis


@dataclass
class StrategySignal:
    action: str  # BUY|HOLD
    reason: str


class BaseStrategy(ABC):
    name: str = "base"

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> StrategySignal:
        raise NotImplementedError


class Stage3CompositeStrategy(BaseStrategy):
    name = "stage3_composite"

    def generate_signal(self, df: pd.DataFrame) -> StrategySignal:
        analysis = stage3_analysis(df, interval="1h")
        action = "BUY" if analysis.signal in {"BUY", "STRONG_BUY"} else "HOLD"
        return StrategySignal(action=action, reason=f"stage3:{analysis.signal}")


class EMACrossoverStrategy(BaseStrategy):
    name = "ema_crossover"

    def __init__(self, fast_period: int = 20, slow_period: int = 50) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signal(self, df: pd.DataFrame) -> StrategySignal:
        row = df.iloc[-1]
        fast = float(row.get(f"ema_{self.fast_period}", row.get("ema_20", 0.0)))
        slow = float(row.get(f"ema_{self.slow_period}", row.get("ema_50", 0.0)))
        return StrategySignal("BUY" if fast > slow else "HOLD", f"ema_fast={fast:.4f},ema_slow={slow:.4f}")


class RSIMeanReversionStrategy(BaseStrategy):
    name = "rsi_mean_reversion"

    def __init__(self, buy_below: float = 35.0, sell_above: float = 65.0) -> None:
        self.buy_below = buy_below
        self.sell_above = sell_above

    def generate_signal(self, df: pd.DataFrame) -> StrategySignal:
        rsi = float(df.iloc[-1].get("rsi_14", 50.0))
        action = "BUY" if rsi <= self.buy_below else "HOLD"
        return StrategySignal(action, f"rsi={rsi:.2f},buy_below={self.buy_below},sell_above={self.sell_above}")


class BreakoutVolumeStrategy(BaseStrategy):
    name = "breakout_volume"

    def __init__(self, volume_breakout_threshold: float = 1.2, lookback: int = 20) -> None:
        self.volume_breakout_threshold = volume_breakout_threshold
        self.lookback = lookback

    def generate_signal(self, df: pd.DataFrame) -> StrategySignal:
        row = df.iloc[-1]
        recent_high = float(df["high"].tail(self.lookback).max())
        close = float(row["close"])
        volume = float(row.get("volume", 0.0))
        vol_ma = float(row.get("volume_ma_20", max(df["volume"].tail(self.lookback).mean(), 1e-9)))
        vol_ratio = volume / max(vol_ma, 1e-9)
        action = "BUY" if close >= recent_high and vol_ratio >= self.volume_breakout_threshold else "HOLD"
        return StrategySignal(action, f"close={close:.4f},high={recent_high:.4f},vol_ratio={vol_ratio:.2f}")
