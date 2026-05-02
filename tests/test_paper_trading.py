from xrp_bot.paper_trading import PaperState, PaperTradeConfig, generate_signal, load_state, save_state
from xrp_bot.safety import SafetyViolation, block_private_endpoint, block_private_keys, ensure_paper_trading_only


def test_state_persistence_roundtrip(tmp_path):
    p = tmp_path / "paper_state.json"
    state = PaperState(fake_balance=1000.0, day_start_balance=1000.0, last_reset_date="2026-05-02")
    save_state(state, current_price=1.0, path=p)
    loaded = load_state(path=p, initial_balance=500)
    assert loaded.fake_balance == 1000.0


def test_daily_reset():
    state = PaperState(fake_balance=900, day_start_balance=1000, last_reset_date="2026-05-01", daily_realized_pnl=-100)
    state.reset_daily_if_needed("2026-05-02")
    assert state.daily_realized_pnl == 0.0
    assert state.day_start_balance == 900


def test_signal_defaults_hold():
    import pandas as pd
    df = pd.DataFrame({"ema_20": [1], "ema_50": [2], "rsi_14": [40], "volume": [1], "volume_ma_20": [2]})
    assert generate_signal(df) == "HOLD"


def test_private_trading_guards_blocked():
    ensure_paper_trading_only()
    try:
        block_private_endpoint("create_order")
        assert False
    except SafetyViolation:
        assert True
    try:
        block_private_keys({"BINANCE_API_KEY": "x"})
        assert False
    except SafetyViolation:
        assert True
