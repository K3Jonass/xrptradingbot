from __future__ import annotations

import pandas as pd

from .config import INDICATORS


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema_20"] = out["close"].ewm(span=INDICATORS["ema_fast"], adjust=False).mean()
    out["ema_50"] = out["close"].ewm(span=INDICATORS["ema_slow"], adjust=False).mean()

    delta = out["close"].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / INDICATORS["rsi_period"], min_periods=INDICATORS["rsi_period"], adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / INDICATORS["rsi_period"], min_periods=INDICATORS["rsi_period"], adjust=False).mean()
    out["rsi_14"] = 100 - (100 / (1 + (avg_gain / avg_loss)))

    ema_fast = out["close"].ewm(span=INDICATORS["macd_fast"], adjust=False).mean()
    ema_slow = out["close"].ewm(span=INDICATORS["macd_slow"], adjust=False).mean()
    out["macd_line"] = ema_fast - ema_slow
    out["macd_signal"] = out["macd_line"].ewm(span=INDICATORS["macd_signal"], adjust=False).mean()
    out["macd_hist"] = out["macd_line"] - out["macd_signal"]

    bb_mid = out["close"].rolling(window=INDICATORS["bollinger_period"]).mean()
    bb_std = out["close"].rolling(window=INDICATORS["bollinger_period"]).std()
    out["bb_mid"] = bb_mid
    out["bb_upper"] = bb_mid + (INDICATORS["bollinger_std_dev"] * bb_std)
    out["bb_lower"] = bb_mid - (INDICATORS["bollinger_std_dev"] * bb_std)
    out["volume_ma_20"] = out["volume"].rolling(window=INDICATORS["volume_ma_period"]).mean()
    return out
