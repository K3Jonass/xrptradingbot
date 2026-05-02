# Safety Audit

## Hard Safety Rules
- `PAPER_TRADING_ONLY = True` is enforced in config/module layer.
- No private Binance API endpoints are used.
- No live order placement code paths exist.
- ML prediction layer is strictly research/paper context.
- Predictions are advisory only and never execution authority.

## Stage 8 Prediction Controls
- Prediction command: `xrp-predict`.
- Output is informational and includes confidence/model metadata.
- Minimum confidence threshold is configurable; low confidence collapses to `FLAT` advisory state.
- Model report persisted to `data/models/model_report.json` for auditability.

## Operational Notes
- Public candle data only.
- Strategy + paper modules remain simulation-only.

## Integration Audit (Stage 8.1)
- Prediction is read-only context in analyze/paper/dashboard flows.
- No order functions are called by prediction code paths.
