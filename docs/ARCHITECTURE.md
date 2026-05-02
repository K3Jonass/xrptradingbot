# Architecture

## Components
- `xrp-analyze`: public-market analysis pipeline only.
- `xrp-backtest`: offline simulation backtesting.
- `xrp-paper`: paper-trading cycle/event logger.
- `xrp-dashboard`: read-only Streamlit analytics.
- `xrp-healthcheck`: runtime + safety checks.
- `xrp-research`: alias entrypoint for analysis workflow.
- `xrp-journal`: journal intelligence weekly summary.

## Data Flow (Paper Only)
1. Market signal decision is produced from indicator dataframe.
2. Paper event snapshot is appended to `data/paper_trades.jsonl`.
3. Closed trade context is appended to `data/trade_journal.jsonl`.
4. Weekly summary is generated from journal records.
5. Telegram summary uses journal weekly summary formatter.
6. Dashboard reads `paper_state.json`, `paper_trades.jsonl`, and `trade_journal.jsonl`.

## Safety
- `PAPER_TRADING_ONLY = True` remains required.
- No private Binance API endpoints.
- No order execution paths.
