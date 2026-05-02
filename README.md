# XRP Trading Bot - Stage 2 (Paper Trading Simulation Only)

This project remains simulation-only:
- Uses Binance **public market data only**.
- Uses **no private API keys**.
- Places **no real orders**.
- Performs **no market/limit execution**.

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
xrp-paper --symbol XRPUSDT --interval 1h --balance 1000 --once
xrp-paper --loop --sleep-seconds 60
xrp-paper --reset-state --once
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


## Stage 2 Safety Guards
- Global guard: `PAPER_TRADING_ONLY = True`.
- Any attempt to use private endpoints or order placement functions is blocked by `xrp_bot.safety`.
- Loading Binance private API keys is blocked.

## Paper Trading Logs
- Event log file: `logs/paper_trader.log`
- Structured events: `data/paper_trades.jsonl`

Each paper event includes: timestamp, symbol, interval, event type (`OPEN`/`CLOSE`/`SKIP`), signal, price, quantity, fake balance, realized PnL, reason.

## Paper Risk Config
Paper trading risk defaults now come from `config/settings.yaml` under `paper_trading:`.
