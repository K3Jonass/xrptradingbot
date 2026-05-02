# Data Schemas

## `data/paper_state.json`
- `fake_balance` (float)
- `day_start_balance` (float)
- `realized_pnl` (float)
- `unrealized_pnl` (float)
- `trade_count` (int, optional)

## `data/paper_trades.jsonl`
Per line event includes:
- `interval`, `signal`, `signal_score`, `signal_explanation`, `market_regime`
- `atr`, `adx`, `support`, `resistance`, `stop_loss`, `take_profit`
- `higher_timeframe_confirmation`

## `data/trade_journal.jsonl`
Per closed trade:
- `timestamp`, `strategy_name`, `signal_label`, `signal_score`, `signal_explanation`
- `market_regime`, `entry_reason`, `exit_reason`
- `entry_price`, `exit_price`, `stop_loss`, `take_profit`
- `holding_duration`, `realized_pnl`, `risk_taken_pct`, `win_loss`, `notes`
- `analysis` object: `what_worked`, `what_failed`, `entry_quality`, `exit_timing`, `risk_management_respected`
- `decision_score` (0-100)
- `mistakes` (list)

## Backward Compatibility
- Missing journal fields are default-filled during load for older rows.
