# Safety Audit (Stage 6.1)

- `PAPER_TRADING_ONLY` remains hardcoded `True` in config.
- No private Binance API order endpoints are used.
- Backtesting/research paths are simulation-only and do not execute trades.
- Paper event schema is normalized with backward compatibility support via `normalize_event_payload()`.
- Stage 3 signal flow is centralized via `signal_engine.stage3_analysis()`.
