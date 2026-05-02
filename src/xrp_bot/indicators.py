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

    prev_close = out["close"].shift(1)
    tr = pd.concat([
        out["high"] - out["low"],
        (out["high"] - prev_close).abs(),
        (out["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    out["atr_14"] = tr.ewm(alpha=1 / INDICATORS["atr_period"], min_periods=INDICATORS["atr_period"], adjust=False).mean()

    up_move = out["high"].diff()
    down_move = -out["low"].diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    tr_smooth = tr.ewm(alpha=1 / INDICATORS["adx_period"], min_periods=INDICATORS["adx_period"], adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1 / INDICATORS["adx_period"], min_periods=INDICATORS["adx_period"], adjust=False).mean() / tr_smooth)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / INDICATORS["adx_period"], min_periods=INDICATORS["adx_period"], adjust=False).mean() / tr_smooth)
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA)) * 100
    out["adx_14"] = dx.ewm(alpha=1 / INDICATORS["adx_period"], min_periods=INDICATORS["adx_period"], adjust=False).mean()
    out["plus_di_14"] = plus_di
    out["minus_di_14"] = minus_di
    return out
