"""Terminal and file reporting helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from .config import DATA_DIR, REPORT_FILE, SYMBOL


def build_report_payload(interval: str, df: pd.DataFrame, analysis: dict, prediction_context: dict | None = None) -> dict:
    """Build a serializable analysis payload for console and file output."""
    latest = df.iloc[-1]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbol": SYMBOL,
        "interval": interval,
        "latest_candle_close_time": latest["close_time"].isoformat(),
        "latest_price": float(latest["close"]),
        "indicators": {
            "ema_20": float(latest["ema_20"]),
            "ema_50": float(latest["ema_50"]),
            "rsi_14": float(latest["rsi_14"]),
            "macd_line": float(latest["macd_line"]),
            "macd_signal": float(latest["macd_signal"]),
            "macd_hist": float(latest["macd_hist"]),
            "bb_upper": float(latest["bb_upper"]),
            "bb_mid": float(latest["bb_mid"]),
            "bb_lower": float(latest["bb_lower"]),
            "volume": float(latest["volume"]),
            "volume_ma_20": float(latest["volume_ma_20"]),
            "atr_14": float(latest["atr_14"]),
            "adx_14": float(latest["adx_14"]),
        },
        "market_conditions": analysis,
        "prediction_context": prediction_context,
    }


def print_report(report: dict) -> None:
    """Print a clean analysis report for terminal use."""
    cond = report["market_conditions"]
    ind = report["indicators"]

    print("\n=== XRP/USDT Market Analysis (Stage 1 - Analysis Only) ===")
    print(f"Generated at: {report['generated_at']}")
    print(f"Timeframe:    {report['interval']}")
    print(f"Last close:   {report['latest_candle_close_time']}")
    print(f"Last price:   {report['latest_price']:.6f}\n")

    print("Indicators")
    print(f"- EMA20 / EMA50: {ind['ema_20']:.6f} / {ind['ema_50']:.6f}")
    print(f"- RSI(14):       {ind['rsi_14']:.2f}")
    print(
        f"- MACD:          line={ind['macd_line']:.6f}, "
        f"signal={ind['macd_signal']:.6f}, hist={ind['macd_hist']:.6f}"
    )
    print(
        f"- Bollinger:     upper={ind['bb_upper']:.6f}, "
        f"mid={ind['bb_mid']:.6f}, lower={ind['bb_lower']:.6f}"
    )
    print(f"- Volume/MA20:   {ind['volume']:.2f} / {ind['volume_ma_20']:.2f}")
    print(f"- ATR(14):       {ind['atr_14']:.6f}")
    print(f"- ADX(14):       {ind['adx_14']:.2f}\n")

    print("Conditions")
    print(f"- Trend:               {cond['trend']}")
    print(f"- Regime:              {cond['regime']}")
    print(f"- Signal:              {cond['signal']} (score={cond['score']})")
    print(f"- Support/Resistance:  {cond['support']:.6f} / {cond['resistance']:.6f}")
    print(f"- ATR SL/TP:           {cond['stop_loss']:.6f} / {cond['take_profit']:.6f}")
    print(f"- High volume breakout:{' yes' if cond['breakout'] else ' no'}")
    print(f"- Overbought:          {'yes' if cond['overbought'] else 'no'}")
    print(f"- Oversold:            {'yes' if cond['oversold'] else 'no'}")
    print("- Notes:")
    for note in cond["notes"]:
        print(f"  * {note}")


def save_report(report: dict) -> None:
    """Persist the latest report to local storage."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with REPORT_FILE.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
