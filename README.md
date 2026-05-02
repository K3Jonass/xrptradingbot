## Install (pip)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Commands audit (Stage 7.1)
- `xrp-analyze`: public data market analyzer.
- `xrp-backtest`: offline simulation backtest.
- `xrp-paper`: paper trading simulator only.
- `xrp-dashboard`: read-only dashboard.
- `xrp-healthcheck`: safety/runtime check.
- `xrp-research`: analyzer alias for research workflows.
- `xrp-journal`: weekly decision-intelligence summary.

## Stage 7 journal intelligence
- Closed paper trades write events to `data/paper_trades.jsonl` and journal records to `data/trade_journal.jsonl`.
- Journal supports post-trade analysis, decision scoring, repeated-mistake detection, and weekly summary generation.
- Dashboard reads `paper_state.json`, `paper_trades.jsonl`, and `trade_journal.jsonl` for read-only analytics.
- Telegram weekly summary formatting uses journal weekly summary payload.

## Safety constraints
- `PAPER_TRADING_ONLY = True`.
- No private Binance API.
- No order execution.
- Journal is analysis-only/review-only.
