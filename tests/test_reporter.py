import pandas as pd

from xrp_bot.reporter import build_report_payload


def test_report_payload_keys():
    df = pd.DataFrame([{
        "close_time": pd.Timestamp("2026-01-01", tz="UTC"),
        "close": 2.0,
        "ema_20": 1.9,
        "ema_50": 1.8,
        "rsi_14": 55,
        "macd_line": 0.1,
        "macd_signal": 0.05,
        "macd_hist": 0.05,
        "bb_upper": 2.2,
        "bb_mid": 2.0,
        "bb_lower": 1.8,
        "volume": 200,
        "volume_ma_20": 150,
        "atr_14": 0.03,
        "adx_14": 27,
    }])
    rpt = build_report_payload("1h", df, {"trend": "bullish trend"})
    assert rpt["interval"] == "1h"
    assert "indicators" in rpt
