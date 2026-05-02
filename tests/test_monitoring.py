from xrp_bot.monitoring import RuntimeState, format_alert, summarize_day
from xrp_bot.paper_cli import handle_command
from xrp_bot.paper_trading import PaperState, TradeRecord


def test_alert_format_contains_required_fields():
    msg = format_alert({"event_type":"OPEN","symbol":"XRPUSDT","interval":"1h","price":2.0,"signal_label":"BUY","signal_score":0.9,"signal_explanation":"test","market_regime":"bull","support":1.9,"resistance":2.1,"stop_loss":1.8,"take_profit":2.2,"fake_balance":1000,"realized_pnl":10,"unrealized_pnl":5,"risk_status":"OK"})
    assert "Price:" in msg and "Signal:" in msg and "Risk:" in msg


def test_paused_state_behavior():
    runtime = RuntimeState(active=True)
    state = PaperState(fake_balance=1000, day_start_balance=1000, last_reset_date="2026-05-02")
    resp = handle_command("/pause", runtime, state, 2.0, "OK")
    assert "paused" in resp.lower()
    assert runtime.active is False


def test_summary_generation():
    state = PaperState(fake_balance=1010, day_start_balance=1000, last_reset_date="2026-05-02", daily_realized_pnl=10)
    state.trade_history.append(TradeRecord("a","b",1,2,1,1,1,"TP"))
    s = summarize_day(state)
    assert s["total_simulated_trades"] == 1
    assert s["win_rate"] == 100.0


def test_command_handling_status():
    runtime = RuntimeState(active=True)
    state = PaperState(fake_balance=1000, day_start_balance=1000, last_reset_date="2026-05-02")
    resp = handle_command("/status", runtime, state, 2.0, "OK")
    assert "Status:" in resp
