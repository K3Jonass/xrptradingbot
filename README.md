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
