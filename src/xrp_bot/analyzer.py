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
    regime: str
    signal: str
    score: int
    support: float
    resistance: float
    stop_loss: float
    take_profit: float
    notes: list[str]
    signal_explanation: str

    @property
    def explanation(self) -> str:
        """Backward-compatible alias used by older code paths."""
        return self.signal_explanation

    @property
    def explanation_notes(self) -> str:
        """Backward-compatible alias for legacy payload names."""
        return self.signal_explanation

    def to_dict(self) -> dict:
        return asdict(self)


def detect_support_resistance(df: pd.DataFrame, lookback: int = 30, swing_window: int = 2) -> tuple[float, float]:
    recent = df.tail(lookback).reset_index(drop=True)
    highs, lows = [], []
    for i in range(swing_window, len(recent) - swing_window):
        h = recent.loc[i, "high"]
        l = recent.loc[i, "low"]
        if h >= recent.loc[i - swing_window:i + swing_window, "high"].max():
            highs.append(h)
        if l <= recent.loc[i - swing_window:i + swing_window, "low"].min():
            lows.append(l)
    resistance = max(highs) if highs else float(recent["high"].max())
    support = min(lows) if lows else float(recent["low"].min())
    return support, resistance


def _regime(row: pd.Series) -> str:
    if row["atr_14"] / row["close"] >= ANALYSIS["high_volatility_atr_ratio"]:
        return "high volatility"
    if row["atr_14"] / row["close"] <= ANALYSIS["low_volatility_atr_ratio"]:
        return "low volatility"
    if row["adx_14"] >= ANALYSIS["adx_trend_threshold"]:
        return "trending bullish" if row["ema_20"] > row["ema_50"] else "trending bearish"
    return "ranging"


def detect_market_conditions(df: pd.DataFrame, higher_tf_df: pd.DataFrame | None = None) -> MarketAnalysis:
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    support, resistance = detect_support_resistance(df, lookback=ANALYSIS["support_resistance_lookback"])

    score = 0
    trend = "bullish trend" if latest["ema_20"] > latest["ema_50"] else "bearish trend"
    score += 20 if trend == "bullish trend" else -20

    if latest["rsi_14"] < 35:
        score += 10
    elif latest["rsi_14"] > 70:
        score -= 10
    else:
        score += 5

    score += 10 if latest["macd_hist"] > 0 else -10
    score += 10 if latest["volume"] > latest["volume_ma_20"] else -5
    score += 10 if latest["adx_14"] >= ANALYSIS["adx_trend_threshold"] else -5

    regime = _regime(latest)
    regime_score_map = {"trending bullish": 15, "trending bearish": -15, "ranging": 0, "high volatility": -10, "low volatility": 5}
    score += regime_score_map[regime]

    close = float(latest["close"])
    near_support = (close - support) / close <= ANALYSIS["sr_proximity_pct"]
    near_resistance = (resistance - close) / close <= ANALYSIS["sr_proximity_pct"]
    score += 10 if near_support else 0
    score -= 10 if near_resistance else 0

    htf_confirm = False
    if higher_tf_df is not None and not higher_tf_df.empty:
        htf = higher_tf_df.iloc[-1]
        htf_confirm = bool(htf["ema_20"] > htf["ema_50"] and htf["macd_hist"] > 0)
        score += 20 if htf_confirm else -20

    score = max(-100, min(100, int(score)))
    if score >= 60:
        signal = "STRONG_BUY"
    elif score >= 20:
        signal = "BUY"
    elif score <= -60:
        signal = "STRONG_SELL"
    elif score <= -20:
        signal = "SELL"
    else:
        signal = "HOLD"

    atr = float(latest["atr_14"])
    stop_loss = close - ANALYSIS["atr_stop_loss_multiple"] * atr
    take_profit = close + ANALYSIS["atr_take_profit_multiple"] * atr

    breakout = bool(latest["volume"] > (ANALYSIS["volume_breakout_threshold"] * latest["volume_ma_20"]))
    overbought = bool(latest["rsi_14"] >= ANALYSIS["overbought_rsi"])
    oversold = bool(latest["rsi_14"] <= ANALYSIS["oversold_rsi"])
    notes = [
        f"{signal} because EMA trend is {'bullish' if trend == 'bullish trend' else 'bearish'}, RSI={latest['rsi_14']:.1f}, volume ratio={(latest['volume']/latest['volume_ma_20']):.2f}x.",
        f"4h confirmation: {'yes' if htf_confirm else 'no'}, regime={regime}, score={score}.",
        f"MACD histogram moved from {prev['macd_hist']:.6f} to {latest['macd_hist']:.6f}.",
    ]
    signal_explanation = " ".join(notes)
    return MarketAnalysis(
        trend,
        breakout,
        overbought,
        oversold,
        regime,
        signal,
        score,
        support,
        resistance,
        stop_loss,
        take_profit,
        notes,
        signal_explanation,
    )
