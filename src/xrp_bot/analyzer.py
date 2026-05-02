from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from .config import ANALYSIS


@dataclass
class MarketAnalysis:
    trend: str
    breakout: bool
    overbought: bool
    oversold: bool
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def detect_market_conditions(df: pd.DataFrame) -> MarketAnalysis:
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    if latest["ema_20"] > latest["ema_50"] and latest["rsi_14"] >= ANALYSIS["trend_rsi_midpoint"]:
        trend = "bullish trend"
    elif latest["ema_20"] < latest["ema_50"] and latest["rsi_14"] <= ANALYSIS["trend_rsi_midpoint"]:
        trend = "bearish trend"
    else:
        trend = "sideways market"

    breakout = bool(
        latest["volume"] > (ANALYSIS["volume_breakout_threshold"] * latest["volume_ma_20"])
        and (latest["close"] > latest["bb_upper"] or latest["close"] < latest["bb_lower"])
    )
    overbought = bool(latest["rsi_14"] >= ANALYSIS["overbought_rsi"])
    oversold = bool(latest["rsi_14"] <= ANALYSIS["oversold_rsi"])
    notes = [
        f"MACD histogram moved from {prev['macd_hist']:.6f} to {latest['macd_hist']:.6f}.",
        f"Volume ratio vs MA20: {(latest['volume'] / latest['volume_ma_20']):.2f}x.",
    ]
    return MarketAnalysis(trend, breakout, overbought, oversold, notes)
