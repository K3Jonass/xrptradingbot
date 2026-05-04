# Data Schemas



## Stage 9 Telegram Institutional Signal Engine
- PAPER_TRADING_ONLY remains enforced. Telegram is advisory/monitoring and paper-control only.
- Secrets are loaded from `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) with placeholders in `.env.example`.
- Alerts include strong signals, paper OPEN/CLOSE, risk/system events, and daily summary. HOLD/SKIP are summarized every configurable N cycles (`telegram.hold_skip_summary_every`).
- Commands supported: `/status`, `/summary`, `/risk`, `/pause`, `/resume`, `/lastsignal` (paper mode only).
- Runtime state includes active/paused, cycle count, last alert timestamp, and last signal sent.
- CLI test command: `xrp-telegram-test` validates env config and sends a test message only.

## Validation Data Schema (Stage 15)
### `data/validation_health.json`
- `reconciliation_unresolved`: int
- `duplicate_order_incidents`: int
- `safety_bypass_incidents`: int
- `emergency_stop_incidents`: int

### Derived report fields
- `total_signals`, `total_trades`, `skipped_trades`, `win_rate`, `average_r_multiple`, `expectancy`, `max_drawdown`, `profit_factor`, `average_execution_quality`, `slippage_impact`, `false_breakout_rate`, `performance_by_market_regime`, `performance_by_strategy_module`, `journal_completeness`.
