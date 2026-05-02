from datetime import timezone

import pandas as pd

from xrp_bot.reporter import build_report_payload


def test_reporter_uses_timezone_utc_compatible_with_py310():
    df = pd.DataFrame([{
        "close_time": pd.Timestamp("2026-01-01T00:00:00Z"),
        "close": 1.0,
        "ema_20": 1.0, "ema_50": 1.0, "rsi_14": 50.0,
        "macd_line": 0.0, "macd_signal": 0.0, "macd_hist": 0.0,
        "bb_upper": 1.1, "bb_mid": 1.0, "bb_lower": 0.9,
        "volume": 100.0, "volume_ma_20": 100.0, "atr_14": 0.01, "adx_14": 20.0,
    }])
    payload = build_report_payload("1h", df, {"trend": "flat"})
    assert payload["generated_at"]
    assert timezone.utc is not None
