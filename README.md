## XRP Trading Bot (Research + Paper Trading Only)

This project analyzes XRP/USDT market data from Binance public candles and supports paper-trading simulation.

## Safety Constraints
- `PAPER_TRADING_ONLY = True`
- No private Binance API keys required.
- Public REST market data only (`/api/v3/klines` via `requests`).
- No live order execution.
- Prediction outputs are advisory-only context and have no execution authority.

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Commands
- `xrp-analyze` market analysis
- `xrp-backtest` offline strategy simulation
- `xrp-paper` live paper-trading simulator
- `xrp-research` strategy research lab
- `xrp-predict` ML research prediction (paper-only, advisory only)

## Prediction Research Layer
`xrp-predict` builds engineered features from candles:
- returns, volatility, RSI, MACD, EMA distance, volume ratio, ATR, ADX
- distance to support/resistance
- encoded market regime

Labels:
- future return over configurable horizon
- direction class: `UP`, `DOWN`, `FLAT`

Models:
- logistic regression
- random forest
- gradient boosting (if available)

Validation:
- time-series split only (no random split)

Metrics:
- accuracy, precision, recall, F1
- confusion matrix
- directional hit rate
- average forward return by predicted class

Report output:
- `data/models/model_report.json`

Prediction output fields:
- `predicted_direction`
- `confidence_score`
- `model_name`
- `model_version`
- `feature_timestamp`

## Tests
```bash
python -m compileall src
PYTHONPATH=src pytest -q
```

## Stage 8.1 Integration
- CLI audit includes: xrp-analyze, xrp-backtest, xrp-paper, xrp-dashboard, xrp-healthcheck, xrp-research, xrp-journal, xrp-predict.
- `xrp-predict` and prediction context are advisory-only and never execution authority.
- `xrp-analyze --include-prediction` and `xrp-paper --include-prediction` optionally include prediction context.

## Run locally in VS Code
1. Open project folder in VS Code.
2. Create and activate a virtual environment.
3. Install deps: `pip install -r requirements-dev.txt`.
4. Run offline deterministic checks first:
   - `PYTHONPATH=src python scripts/local_check.py`
5. Then run full tests:
   - `PYTHONPATH=src pytest -q`

## Troubleshooting
- **pandas missing**: run `pip install pandas` (or reinstall with `pip install -r requirements-dev.txt`).
- **yaml missing**: run `pip install PyYAML`.
- **streamlit missing**: run `pip install streamlit`.
- **sklearn missing**: run `pip install scikit-learn`.
- **PYTHONPATH issue**: run commands with `PYTHONPATH=src` so `xrp_bot` imports resolve.
- **Windows activation issue**: use `.venv\\Scripts\\activate` in PowerShell or CMD.
