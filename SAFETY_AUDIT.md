# SAFETY AUDIT (Stage 5.1)

## Paper-only guarantees
- `PAPER_TRADING_ONLY` is enforced and must remain `True`.
- Safety checks explicitly block private-key usage and private/order endpoints.

## Forbidden paths
- No code path may call Binance private endpoints (`create_order`, `get_account`, etc.).
- No path may read API keys for trading actions.

## Binance private API usage
- Public market data access is allowed.
- Private account/trade/order endpoints are forbidden.

## Order execution
- No real order execution is implemented.
- All trade artifacts are simulated/local (`data/*.json`, `data/*.jsonl`).

## Telegram command limitations
- Telegram formatting is informational only.
- No command/action supports executing trades.

## Dashboard read-only status
- Dashboard only reads local state/event files.
- It does not write orders or call private exchange APIs.
