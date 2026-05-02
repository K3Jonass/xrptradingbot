# XRP Trading Bot - Stage 3 (Paper Trading Intelligence)

PAPER_TRADING_ONLY = True. No private keys, no order execution, and no live trading.

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
xrp-backtest --initial-balance 2000 --max-risk 0.01 --stop-loss 1.5 --take-profit 3.0
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


## Stage 3 strategy upgrades
- Market regime detection: trending bullish/bearish, ranging, high volatility, low volatility.
- Added ATR(14) and ADX(14).
- Support/resistance from recent swing highs/lows.
- ATR-based stop loss and take profit planning.
- Multi-timeframe confirmation: 15m/1h entries validated with 4h trend.
- Signal scoring engine (-100 to +100) combining EMA, RSI, MACD, volume, ADX, regime, support/resistance, and HTF confirmation.
- Signal outputs: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL with explanation notes.
- Backtest now uses the same signal scoring for paper-only entries with ATR SL/TP.


## Run live paper mode (no execution)
```bash
xrp-paper --interval 15m --limit 300 --event-file data/paper_events.jsonl
```

## Unified Stage 3 signal architecture
- A single Stage 3 signal engine is shared by `xrp-analyze`, `xrp-backtest`, and `xrp-paper`.
- Shared context includes score, label, explanation, regime, ATR/ADX, support/resistance, ATR SL/TP, and 4h confirmation for 15m/1h entries.
- JSONL paper events include the same Stage 3 context for downstream auditability.
- PAPER_TRADING_ONLY = True remains enforced; no private keys and no order execution.
