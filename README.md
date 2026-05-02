

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



## Strategy research lab (paper-only)
Run multi-strategy simulation, optimization, and walk-forward validation:
```bash
xrp-research --fixture tests/fixtures/xrpusdt_1h_sample.json
```

Included strategies:
- `Stage3CompositeStrategy`
- EMA crossover
- RSI mean reversion
- Breakout + volume confirmation

Outputs are saved under `data/backtests/`.

Safety guarantees:
- `PAPER_TRADING_ONLY = True`
- no real trading
- no private Binance API keys
- no order execution

## Stage 6.1 conflict resolution
- Unified Stage 3 signal flow through `signal_engine.stage3_analysis`.
- Standardized paper event schema with backward compatibility normalization for legacy JSONL records.
- Added architecture and safety audit docs: `docs/ARCHITECTURE.md`, `SAFETY_AUDIT.md`.
