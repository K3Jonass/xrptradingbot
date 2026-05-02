from __future__ import annotations

import pandas as pd

from .analyzer import MarketAnalysis, detect_market_conditions


ENTRY_CONFIRMATION_INTERVALS = {"15m", "1h"}


def stage3_analysis(entry_df: pd.DataFrame, interval: str, higher_tf_df: pd.DataFrame | None = None) -> MarketAnalysis:
    """Unified Stage 3 scoring path used by analyzer/backtest/paper modes."""
    use_htf = higher_tf_df if interval in ENTRY_CONFIRMATION_INTERVALS else None
    return detect_market_conditions(entry_df, higher_tf_df=use_htf)
