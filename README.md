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


## Troubleshooting
- **pandas missing**: run `pip install pandas` (or reinstall with `pip install -r requirements-dev.txt`).
- **yaml missing**: run `pip install PyYAML`.
- **streamlit missing**: run `pip install streamlit`.
- **sklearn missing**: run `pip install scikit-learn`.
- **PYTHONPATH issue**: run commands with `PYTHONPATH=src` so `xrp_bot` imports resolve.
- **Windows activation issue**: use `.venv\\Scripts\\activate` in PowerShell or CMD.
