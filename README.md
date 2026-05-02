## Install (pip)

### Option A: requirements files
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Option B: editable package install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Commands

### Market analyzer
```bash
xrp-analyze --symbol XRPUSDT --interval 1h --limit 300
```

### Offline backtest (simulation-only)
```bash
xrp-backtest --fixture tests/fixtures/xrpusdt_1h_sample.json
```

### Live paper trading simulator (simulation-only)
```bash


The dashboard reads local artifacts only:
- `data/paper_state.json`
- `data/paper_trades.jsonl`
- `logs/paper_trader.log` (optional for future extensions)

Dashboard features:
- metrics: balance, realized/unrealized PnL, total trades, win rate, max drawdown, profit factor, best/worst trade
- charts: equity curve, daily PnL, trade PnL distribution, signal score over time, market regime over time
- filters: date range, signal type, market regime

Safety constraints:
- `PAPER_TRADING_ONLY = True`
- no Binance private API use
- no live order execution
- dashboard is read-only

## Run tests
```bash
python -m compileall src
PYTHONPATH=src pytest -q
```


