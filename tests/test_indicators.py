import pandas as pd

from xrp_bot.indicators import add_indicators


def test_indicator_columns_added():
    df = pd.DataFrame({"close": [1 + i * 0.1 for i in range(80)], "volume": [100 + i for i in range(80)]})
    out = add_indicators(df)
    for col in ["ema_20", "ema_50", "rsi_14", "macd_line", "bb_upper", "bb_lower", "volume_ma_20"]:
        assert col in out.columns
