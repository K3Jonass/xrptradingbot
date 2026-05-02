# XRP Trading Bot - Stage 4 (Paper Trading Monitoring + Telegram Control)

This project remains simulation-only:
- Uses Binance **public market data only**.
- Uses **no private API keys**.
- Places **no real orders**.
- Performs **no market/limit execution**.
- Telegram integration is **alerts + paper-control only** (no buy/sell execution commands).

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
xrp-paper --command /status --once
xrp-healthcheck
```

Options:
- `--symbol` (default: `XRPUSDT`)
- `--interval` (default from config)
- `--balance` starting fake balance (default: `1000`)
- `--once` run one cycle
- `--loop` run continuously
- `--sleep-seconds` loop delay
- `--reset-state` clear local paper state file before running
- `--command` issue a paper-only control command: `/status`, `/summary`, `/risk`, `/pause`, `/resume`, `/resetpaper`

## Telegram monitoring (alerts only)
Configure `config/settings.yaml`:
- `telegram.enabled`
- `telegram.bot_token`
- `telegram.chat_id`

Secrets are loaded from `.env`:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Use `.env.example` as a template.

## Deployment

### Local run
```bash
cp .env.example .env
xrp-healthcheck
xrp-paper --loop --sleep-seconds 60
```

### Docker run
```bash
docker build -t xrp-paper .
docker run --env-file .env -v $(pwd)/data:/app/data -v $(pwd)/logs:/app/logs xrp-paper
```

### Docker Compose
```bash
docker compose up -d xrp-paper
docker compose run --rm xrp-healthcheck
```

### systemd VPS run
```bash
sudo cp deploy/xrp-paper.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now xrp-paper
```

Alert types:
- analysis alerts
- paper trade open/close alerts
- risk warnings
- daily summary via `/summary`
- system error alerts

Forbidden / not implemented:
- no `/buy` command
- no `/sell` command
- no live order execution
- no private Binance API actions

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

### Local test run (full)
```bash
pip install -r requirements-dev.txt
python -m compileall src tests
PYTHONPATH=src python scripts/smoke_test.py
PYTHONPATH=src pytest -q
```

### Docker test run
```bash
docker compose run --rm test
```

### CI test flow
GitHub Actions workflow `.github/workflows/tests.yml` runs on push/PR with Python 3.11 and executes:
1. `pip install -r requirements-dev.txt`
2. `python -m compileall src tests`
3. `PYTHONPATH=src python scripts/smoke_test.py`
4. `PYTHONPATH=src pytest -q`


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
