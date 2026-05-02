

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

```

Options:
- `--symbol` (default: `XRPUSDT`)
- `--interval` (default from config)
- `--balance` starting fake balance (default: `1000`)
- `--once` run one cycle
- `--loop` run continuously
- `--sleep-seconds` loop delay
- `--reset-state` clear local paper state file before running

## Paper state persistence
Paper trading state is stored in:
- `data/paper_state.json`

Stored fields include:
- current fake balance
- open simulated position
- trade history
- realized PnL
- unrealized PnL

## Risk controls in paper engine
- max risk per trade
- stop loss %
- take profit %
- max daily loss %
- max trades per day
- max open positions = 1

## Terminal report
Each run shows:
- current price
- signal
- fake balance
- open position
- realized PnL
- unrealized PnL
- number of trades today
- risk status

## Run tests
```bash
python -m compileall src
PYTHONPATH=src pytest -q
```

