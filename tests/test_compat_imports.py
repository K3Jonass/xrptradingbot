import importlib


def test_paper_trading_exports_exist():
    mod = importlib.import_module("xrp_bot.paper_trading")
    assert hasattr(mod, "append_event_jsonl")
    assert hasattr(mod, "run_paper_cycle")


def test_dashboard_import_without_streamlit_dependency():
    mod = importlib.import_module("xrp_bot.dashboard")
    assert hasattr(mod, "calculate_dashboard_metrics")
