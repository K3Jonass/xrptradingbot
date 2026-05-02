from __future__ import annotations


def format_stage3_alert(event: dict) -> str:
    return (
        f"Signal: {event.get('signal','HOLD')}\n"
        f"Score: {event.get('signal_score', 0)}\n"
        f"Regime: {event.get('market_regime','unknown')}\n"
        f"SL/TP: {event.get('stop_loss', 0)} / {event.get('take_profit', 0)}\n"
        f"ATR/ADX: {event.get('atr', 0)} / {event.get('adx', 0)}"
    )
