## XRP Trading Bot (Research + Paper Trading Only)


```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Dashboard (read-only)
- Preferred CLI: `xrp-dashboard`
- Alternative launcher (direct app file): `python -m streamlit run src/xrp_bot/dashboard.py`

Windows (PowerShell/CMD):
- Activate venv: `.venv\\Scripts\\activate`
- Run dashboard: `xrp-dashboard`
- Alternative: `python -m streamlit run src/xrp_bot/dashboard.py`

### Paper Trading Cycle (safe simulation only)
- Run one cycle: `xrp-paper --once`
- Run continuous loop (default): `xrp-paper`
- Explicit loop mode: `xrp-paper --loop`
- Loop pacing: `xrp-paper --sleep-seconds 30`
- Test bounded loop: `xrp-paper --loop --max-cycles 3 --sleep-seconds 0`
- `--once` prints a full cycle JSON payload with:
  - `current_price`, `signal_label`, `signal_score`, `signal_explanation`
  - `market_regime`, `support`, `resistance`
  - `atr_stop_loss`, `atr_take_profit`
  - `fake_balance`, `open_position`, `realized_pnl`, `unrealized_pnl`
  - `risk_status`, `event_type` (`OPEN`, `CLOSE`, `SKIP`)
- If no trade opens, payload includes:
  - `event_type: SKIP`
  - `reason: signal did not meet entry criteria`
- The cycle always persists files:
  - `data/paper_state.json`
  - `data/paper_trades.jsonl`
- Loop mode behavior:
  - If `--once` is set, exactly one paper cycle runs, then exits.
  - If `--loop` is set, continuous cycles run until Ctrl+C (or `--max-cycles` is reached).
  - If neither flag is set, default mode runs continuous loop.
  - Every cycle emits a heartbeat log line with cycle number, timestamp, price, signal, and event type.
  - Ctrl+C exits gracefully after the current cycle without any real trading side effects.
- Dashboard visibility for overnight runs:
  - Shows **Recent Paper Events** table sourced from `data/paper_trades.jsonl` (including HOLD/SKIP cycles).
  - Shows cycle counters: total cycles, SKIP/OPEN/CLOSE/HOLD, and BUY/SELL/STRONG_BUY/STRONG_SELL counts.
  - Shows combined chart for `signal_score` and `current_price` over time.
  - Shows **Prediction Research (Advisory Only)** as clean dashboard cards/tables, not raw JSON by default.
  - Prediction block displays: model name/version, accuracy, precision, recall, F1, and directional hit rate.
  - Includes a confusion matrix table and average forward return by predicted class table.
  - Shows explicit safeguards: `Advisory only`, `Not used for real trading`, and `No execution authority`.
  - Displays weak-model warning when model quality is low; raw report is available only under **Show raw model report** expander.
  - Sidebar filters support `event_type`, `signal_label`, and `market_regime`.
  - If no trades are opened yet, dashboard explicitly shows: `No trades yet, but paper cycles are being recorded.`
- Safety guarantees remain unchanged:
  - `PAPER_TRADING_ONLY = True`
  - No private Binance API usage
  - No real order execution


## Troubleshooting
- **pandas missing**: run `pip install pandas` (or reinstall with `pip install -r requirements-dev.txt`).
- **yaml missing**: run `pip install PyYAML`.
- **streamlit missing**: run `pip install streamlit`.
- **sklearn missing**: run `pip install scikit-learn`.
- **PYTHONPATH issue**: run commands with `PYTHONPATH=src` so `xrp_bot` imports resolve.
- **Windows activation issue**: use `.venv\\Scripts\\activate` in PowerShell or CMD.


## Stage 9 Telegram Institutional Signal Engine
- PAPER_TRADING_ONLY remains enforced. Telegram is advisory/monitoring and paper-control only.
- Secrets are loaded from `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) with placeholders in `.env.example`.
- Alerts include strong signals, paper OPEN/CLOSE, risk/system events, and daily summary. HOLD/SKIP are summarized every configurable N cycles (`telegram.hold_skip_summary_every`).
- Commands supported: `/status`, `/summary`, `/risk`, `/pause`, `/resume`, `/lastsignal` (paper mode only).
- Runtime state includes active/paused, cycle count, last alert timestamp, and last signal sent.
- CLI test command: `xrp-telegram-test` validates env config and sends a test message only.

## Stage 15: Paper Soak Testing + Strategy Validation
- Added a professional paper soak validation layer with readiness scoring and promotion gates.
- Paper-only remains enforced (`PAPER_TRADING_ONLY = True`), no live/testnet order placement.
