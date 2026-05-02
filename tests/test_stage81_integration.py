import importlib
import json
from pathlib import Path

from xrp_bot.dashboard import load_prediction_report
from xrp_bot.paper_cli import main as paper_main
from xrp_bot.prediction import train_and_predict
from xrp_bot.reporter import build_report_payload


def test_all_cli_imports():
    for mod in [
        "xrp_bot.cli",
        "xrp_bot.backtest_cli",
        "xrp_bot.paper_cli",
        "xrp_bot.dashboard_cli",
        "xrp_bot.healthcheck_cli",
        "xrp_bot.research_cli",
        "xrp_bot.predict_cli",
    ]:
        assert importlib.import_module(mod)


def test_prediction_advisory_only_guard():
    src = Path("src/xrp_bot/predict_cli.py").read_text(encoding="utf-8")
    assert "advisory_only" in src
    assert "no_execution_authority" in src


def test_model_report_backward_compatibility_shape(tmp_path):
    p = tmp_path / "model_report.json"
    p.write_text(json.dumps({"model": "logistic_regression", "metrics": {}, "version": "v0"}))
    loaded = load_prediction_report(p)
    assert loaded["model"] == "logistic_regression"
    assert "metrics" in loaded


def test_dashboard_prediction_report_loading(tmp_path):
    p = tmp_path / "model_report.json"
    p.write_text(json.dumps({"model": "random_forest", "version": "v1", "metrics": {"accuracy": 0.5}}))
    loaded = load_prediction_report(p)
    assert loaded["model"] == "random_forest"


def test_analyze_report_includes_prediction_context_when_enabled():
    import pandas as pd

    df = pd.DataFrame([
        {"close_time": pd.Timestamp("2026-01-01T00:00:00Z"), "close": 1.0, "ema_20": 1.0, "ema_50": 1.0, "rsi_14": 50.0, "macd_line": 0.0, "macd_signal": 0.0, "macd_hist": 0.0, "bb_upper": 1.1, "bb_mid": 1.0, "bb_lower": 0.9, "volume": 10.0, "volume_ma_20": 10.0, "atr_14": 0.01, "adx_14": 20.0}
    ])
    report = build_report_payload("1h", df, {"signal": "HOLD"}, prediction_context={"predicted_direction": "FLAT"})
    assert report["prediction_context"]["predicted_direction"] == "FLAT"


def test_paper_payload_can_include_prediction_context(tmp_path, monkeypatch, capsys):
    pred = tmp_path / "model_report.json"
    pred.write_text(json.dumps({"model": "logistic_regression"}))
    monkeypatch.chdir(tmp_path)
    import sys
    sys.argv = ["xrp-paper", "--include-prediction"]
    paper_main()
    out = json.loads(capsys.readouterr().out)
    assert "prediction_context" in out
