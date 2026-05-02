import pandas as pd

from xrp_bot.analyzer import detect_market_conditions, detect_support_resistance


def _mk_df(n=60, trend=0.01):
    rows=[]
    price=1.0
    for i in range(n):
        price *= (1+trend)
        rows.append({
            "close": price,
            "high": price*1.01,
            "low": price*0.99,
            "volume": 100+i,
            "volume_ma_20": 100,
            "ema_20": price*1.001,
            "ema_50": price*0.999,
            "rsi_14": 55,
            "macd_hist": 0.1,
            "atr_14": price*0.02,
            "adx_14": 30,
            "bb_upper": price*1.02,
            "bb_lower": price*0.98,
        })
    return pd.DataFrame(rows)


def test_regime_and_signal_detected():
    df = _mk_df()
    analysis = detect_market_conditions(df)
    assert analysis.regime in {"trending bullish", "high volatility", "low volatility", "ranging", "trending bearish"}
    assert analysis.signal in {"STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"}


def test_support_resistance_swings():
    df = pd.DataFrame({"high": [1, 2, 3, 2, 1, 2, 4, 2, 1], "low": [0.5, 0.4, 0.6, 0.3, 0.2, 0.4, 0.5, 0.4, 0.3]})
    support, resistance = detect_support_resistance(df, lookback=9, swing_window=1)
    assert support <= 0.3
    assert resistance >= 3


def test_higher_timeframe_confirmation_affects_score():
    df = _mk_df()
    htf = _mk_df(trend=-0.005)
    htf["ema_20"] = htf["close"] * 0.998
    htf["ema_50"] = htf["close"] * 1.002
    htf["macd_hist"] = -0.1
    base = detect_market_conditions(df)
    with_htf = detect_market_conditions(df, higher_tf_df=htf)
    assert with_htf.score <= base.score
