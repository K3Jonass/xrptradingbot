from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import ANALYSIS, DATA_DIR, INDICATORS, SETTINGS

try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
except Exception:  # pragma: no cover
    GradientBoostingClassifier = None
    RandomForestClassifier = None
    LogisticRegression = None


@dataclass
class PredictionResult:
    predicted_direction: str
    confidence_score: float
    model_name: str
    model_version: str
    feature_timestamp: str


class _FallbackMajorityModel:
    def fit(self, X, y):
        counts = pd.Series(y).value_counts()
        self.majority = int(counts.index[0]) if not counts.empty else 1
        self.n_classes = max(3, int(pd.Series(y).nunique() or 3))
        return self

    def predict(self, X):
        return np.full(len(X), self.majority, dtype=int)

    def predict_proba(self, X):
        out = np.zeros((len(X), self.n_classes), dtype=float)
        out[:, self.majority] = 1.0
        return out


def _safe_model(model_type: str):
    if model_type == "random_forest" and RandomForestClassifier is not None:
        try:
            return RandomForestClassifier(n_estimators=150, random_state=42), "random_forest"
        except TypeError:
            return RandomForestClassifier(), "random_forest"

    if model_type == "gradient_boosting" and GradientBoostingClassifier is not None:
        try:
            return GradientBoostingClassifier(random_state=42), "gradient_boosting"
        except TypeError:
            return GradientBoostingClassifier(), "gradient_boosting"

    if LogisticRegression is not None:
        # Avoid version-sensitive kwargs (e.g., multi_class) and gracefully
        # degrade to a bare constructor on older/newer sklearn variants.
        try:
            return LogisticRegression(max_iter=1000), "logistic_regression"
        except TypeError:
            return LogisticRegression(), "logistic_regression"

    return _FallbackMajorityModel(), "fallback_majority"


def _market_regime(adx: float, ema_fast: float, ema_slow: float) -> int:
    if pd.isna(adx) or pd.isna(ema_fast) or pd.isna(ema_slow):
        return 0
    if adx < ANALYSIS["adx_trend_threshold"]:
        return 0
    return 1 if ema_fast >= ema_slow else -1


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["returns"] = out["close"].pct_change()
    out["volatility"] = out["returns"].rolling(INDICATORS["rsi_period"]).std()
    out["ema_distance"] = (out["ema_20"] - out["ema_50"]) / out["close"]
    out["volume_ratio"] = out["volume"] / out["volume_ma_20"].replace(0, np.nan)
    lookback = ANALYSIS["support_resistance_lookback"]
    out["support"] = out["low"].rolling(lookback).min()
    out["resistance"] = out["high"].rolling(lookback).max()
    out["dist_to_support"] = (out["close"] - out["support"]) / out["close"]
    out["dist_to_resistance"] = (out["resistance"] - out["close"]) / out["close"]
    out["market_regime"] = [
        _market_regime(a, e1, e2) for a, e1, e2 in zip(out["adx_14"], out["ema_20"], out["ema_50"])
    ]
    return out


def add_labels(df: pd.DataFrame, horizon: int, flat_threshold: float) -> pd.DataFrame:
    out = df.copy()
    out["future_return"] = out["close"].shift(-horizon) / out["close"] - 1.0
    out["direction_label"] = np.select(
        [out["future_return"] > flat_threshold, out["future_return"] < -flat_threshold],
        ["UP", "DOWN"],
        default="FLAT",
    )
    return out


def time_series_splits(n_rows: int, n_splits: int = 3) -> list[tuple[np.ndarray, np.ndarray]]:
    fold = max(1, n_rows // (n_splits + 1))
    splits: list[tuple[np.ndarray, np.ndarray]] = []
    for i in range(1, n_splits + 1):
        train_end = fold * i
        test_end = min(fold * (i + 1), n_rows)
        if train_end < 10 or test_end <= train_end:
            continue
        splits.append((np.arange(0, train_end), np.arange(train_end, test_end)))
    return splits


def _metrics(y_true: pd.Series, y_pred: pd.Series, future_return: pd.Series) -> dict[str, Any]:
    classes = ["DOWN", "FLAT", "UP"]
    cm = {a: {b: 0 for b in classes} for a in classes}
    for t, p in zip(y_true, y_pred):
        cm[t][p] += 1
    total = len(y_true)
    accuracy = float((y_true == y_pred).mean()) if total else 0.0

    def prf(label: str) -> tuple[float, float, float]:
        tp = cm[label][label]
        fp = sum(cm[x][label] for x in classes if x != label)
        fn = sum(cm[label][x] for x in classes if x != label)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        return prec, rec, f1

    p_list, r_list, f1_list = zip(*(prf(c) for c in classes))
    hit = float(((y_pred == "UP") & (future_return > 0) | ((y_pred == "DOWN") & (future_return < 0))).mean())
    afr = {c: float(future_return[y_pred == c].mean()) if (y_pred == c).any() else 0.0 for c in classes}
    return {
        "accuracy": accuracy,
        "precision": float(np.mean(p_list)),
        "recall": float(np.mean(r_list)),
        "f1": float(np.mean(f1_list)),
        "confusion_matrix": cm,
        "directional_hit_rate": hit,
        "avg_forward_return_by_predicted_class": afr,
    }


def train_and_predict(df: pd.DataFrame) -> tuple[PredictionResult, dict[str, Any]]:
    cfg = SETTINGS.get("prediction", {})
    horizon = int(cfg.get("label_horizon", 4))
    flat_threshold = float(cfg.get("flat_threshold", 0.001))
    model_type = str(cfg.get("model_type", "logistic_regression"))
    min_conf = float(cfg.get("min_confidence_threshold", 0.55))

    feat = build_features(df)
    labeled = add_labels(feat, horizon=horizon, flat_threshold=flat_threshold)
    cols = ["returns", "volatility", "rsi_14", "macd_line", "ema_distance", "volume_ratio", "atr_14", "adx_14", "dist_to_support", "dist_to_resistance", "market_regime"]
    work = labeled.dropna(subset=cols + ["direction_label", "future_return"]).copy()

    label_map = {"DOWN": 0, "FLAT": 1, "UP": 2}
    inv_map = {v: k for k, v in label_map.items()}
    X = work[cols]
    y = work["direction_label"].map(label_map)

    model, model_type = _safe_model(model_type)

    splits = time_series_splits(len(work), n_splits=3)
    preds: list[int] = []
    truth: list[int] = []
    returns: list[float] = []
    for train_idx, test_idx in splits:
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        p = model.predict(X.iloc[test_idx])
        preds.extend(p.tolist())
        truth.extend(y.iloc[test_idx].tolist())
        returns.extend(work["future_return"].iloc[test_idx].tolist())

    y_true = pd.Series([inv_map[v] for v in truth])
    y_pred = pd.Series([inv_map[v] for v in preds])
    metrics = _metrics(y_true, y_pred, pd.Series(returns)) if len(truth) else {}

    model.fit(X, y)
    latest_x = X.iloc[[-1]]
    proba = model.predict_proba(latest_x)[0]
    idx = int(np.argmax(proba))
    predicted = inv_map[idx]
    conf = float(proba[idx])
    if conf < min_conf:
        predicted = "FLAT"

    result = PredictionResult(
        predicted_direction=predicted,
        confidence_score=conf,
        model_name=model_type,
        model_version="v1",
        feature_timestamp=str(work["open_time"].iloc[-1]),
    )
    report = {
        "model": model_type,
        "version": "v1",
        "label_horizon": horizon,
        "flat_threshold": flat_threshold,
        "features": cols,
        "metrics": metrics,
        "paper_trading_only": True,
    }
    (DATA_DIR / "models").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "models" / "model_report.json").write_text(pd.Series(report).to_json(indent=2), encoding="utf-8")
    return result, report
