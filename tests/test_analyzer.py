import pandas as pd
from xrp_bot.analyzer import detect_market_conditions


def test_bullish_detection():
    df = pd.DataFrame([
        {"ema_20": 1, "ema_50": 2, "rsi_14": 40, "volume": 10, "volume_ma_20": 10, "close": 1, "bb_upper": 2, "bb_lower": 0, "macd_hist": -1},
        {"ema_20": 3, "ema_50": 2, "rsi_14": 60, "volume": 20, "volume_ma_20": 10, "close": 3, "bb_upper": 2.5, "bb_lower": 1, "macd_hist": 1},
    ])
    analysis = detect_market_conditions(df)
    assert analysis.trend == "bullish trend"
    assert analysis.overbought is False
