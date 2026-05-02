import json
from pathlib import Path

from xrp_bot.data_fetcher import BinanceMarketDataFetcher
from xrp_bot.indicators import add_indicators
import xrp_bot.prediction as pred_mod
from xrp_bot.prediction import add_labels, build_features, time_series_splits, train_and_predict


def _df():
    fixture = Path(__file__).parent / "fixtures" / "xrpusdt_1h_sample.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    return add_indicators(BinanceMarketDataFetcher._normalize_klines(raw))


def test_feature_generation_columns():
    feat = build_features(_df())
    for col in [
        "returns",
        "volatility",
        "ema_distance",
        "volume_ratio",
        "dist_to_support",
        "dist_to_resistance",
        "market_regime",
    ]:
        assert col in feat.columns


def test_label_generation_columns():
    labeled = add_labels(_df(), horizon=4, flat_threshold=0.001)
    assert "future_return" in labeled.columns
    assert "direction_label" in labeled.columns
    assert set(labeled["direction_label"].dropna().unique()).issubset({"UP", "DOWN", "FLAT"})


def test_time_series_split_ordered_non_overlapping():
    splits = time_series_splits(120, n_splits=3)
    assert splits
    for train_idx, test_idx in splits:
        assert train_idx.max() < test_idx.min()


def test_model_report_shape():
    _, report = train_and_predict(_df())
    assert "metrics" in report
    for k in ["accuracy", "precision", "recall", "f1", "confusion_matrix", "directional_hit_rate"]:
        assert k in report["metrics"]


def test_prediction_output_shape():
    pred, _ = train_and_predict(_df())
    assert pred.predicted_direction in {"UP", "DOWN", "FLAT"}
    assert 0 <= pred.confidence_score <= 1
    assert pred.model_name
    assert pred.model_version
    assert pred.feature_timestamp


def test_safe_model_uses_logistic_without_multi_class(monkeypatch):
    captured = {}

    class DummyLogistic:
        def __init__(self, **kwargs):
            captured["kwargs"] = kwargs

    monkeypatch.setattr(pred_mod, "LogisticRegression", DummyLogistic)
    model, model_name = pred_mod._safe_model("logistic_regression")
    assert isinstance(model, DummyLogistic)
    assert model_name == "logistic_regression"
    assert "multi_class" not in captured["kwargs"]


def test_safe_model_constructor_fallbacks(monkeypatch):
    class DummyRF:
        def __init__(self, **kwargs):
            if "n_estimators" in kwargs:
                raise TypeError("unsupported")

    class DummyGB:
        def __init__(self, **kwargs):
            if "random_state" in kwargs:
                raise TypeError("unsupported")

    class DummyLogistic:
        def __init__(self, **kwargs):
            if "max_iter" in kwargs:
                raise TypeError("unsupported")

    monkeypatch.setattr(pred_mod, "RandomForestClassifier", DummyRF)
    monkeypatch.setattr(pred_mod, "GradientBoostingClassifier", DummyGB)
    monkeypatch.setattr(pred_mod, "LogisticRegression", DummyLogistic)

    rf_model, rf_name = pred_mod._safe_model("random_forest")
    gb_model, gb_name = pred_mod._safe_model("gradient_boosting")
    lr_model, lr_name = pred_mod._safe_model("logistic_regression")

    assert isinstance(rf_model, DummyRF) and rf_name == "random_forest"
    assert isinstance(gb_model, DummyGB) and gb_name == "gradient_boosting"
    assert isinstance(lr_model, DummyLogistic) and lr_name == "logistic_regression"
