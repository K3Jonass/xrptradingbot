# Architecture Overview

## Unified signal path
- `signal_engine.stage3_analysis()` remains the single source for Stage 3 scoring.
- Analyzer, paper signal evaluation, and Stage3 composite strategy consume this path.

## Prediction research layer (Stage 8)
- New module: `xrp_bot.prediction`.
- Ingests indicator-enriched candle data and performs feature engineering + labeling.
- Supports baseline classification models (`logistic_regression`, `random_forest`, `gradient_boosting`).
- Uses ordered time-series splits only.
- Writes report artifact to `data/models/model_report.json`.
- Produces advisory prediction payload (`direction`, `confidence`, model metadata, feature timestamp).

## Safety boundary
- Prediction layer is **not** wired to order execution.
- Prediction data can be used as analysis context only in research/paper mode.
- No private Binance APIs or live trading routes.

## Stage 8.1 Integration
- Optional prediction context can be attached to analyzer and paper reports.
- Dashboard can load model report artifact in a read-only advisory section.
