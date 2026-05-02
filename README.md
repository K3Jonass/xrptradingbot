# XRP Trading Bot - Stage 1 (Analysis Only)

Still analysis-only: no private keys, no order execution, no live trading.

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

### Dev/Test install
```bash
pip install -r requirements-dev.txt
# or
pip install -e .[dev]
```

## Run analyzer
```bash
xrp-analyze
xrp-analyze --interval 1h --limit 300 --output text
xrp-analyze --interval 15m --output json --no-save
xrp-analyze --symbol XRPUSDT --interval 5m --limit 200
```

## Run offline backtest (simulation-only)
```bash
xrp-backtest --fixture tests/fixtures/xrpusdt_1h_sample.json
xrp-backtest --initial-balance 2000 --max-risk 0.01 --stop-loss 0.015 --take-profit 0.03
```

Backtest strategy uses EMA20/EMA50 trend, RSI filter, and volume breakout filter with risk controls (max risk per trade, stop loss, take profit, max open position = 1).

## Run tests
```bash
python -m compileall src
python scripts/smoke_test.py
PYTHONPATH=src pytest -q
```

## Offline smoke test
- Uses `tests/fixtures/xrpusdt_1h_sample.json`.
- Does not call Binance.
- Loads `config/settings.yaml`, runs indicators + analysis pipeline, and prints `SMOKE TEST PASSED`.
