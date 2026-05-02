from __future__ import annotations


def format_stage3_alert(event: dict) -> str:
    return (
        f"Signal: {event.get('signal','HOLD')}\n"
        f"Score: {event.get('signal_score', 0)}\n"
        f"Regime: {event.get('market_regime','unknown')}\n"
        f"SL/TP: {event.get('stop_loss', 0)} / {event.get('take_profit', 0)}\n"
        f"ATR/ADX: {event.get('atr', 0)} / {event.get('adx', 0)}"
    )


def format_weekly_journal_summary(summary: dict) -> str:
    return (
        "Weekly Review (Paper Trading Only)\n"
        f"Avg decision score: {summary.get('avg_decision_score', 0)}\n"
        f"Best decisions: {len(summary.get('best_decisions', []))}\n"
        f"Worst decisions: {len(summary.get('worst_decisions', []))}\n"
        f"Repeated mistakes: {summary.get('repeated_mistakes', {})}\n"
        f"Suggestions: {summary.get('improvement_suggestions', [])}"
    )
