# Data Schemas

## Prediction Output (`xrp-predict` stdout)
```json
{
  "predicted_direction": "UP|DOWN|FLAT",
  "confidence_score": 0.0,
  "model_name": "logistic_regression|random_forest|gradient_boosting",
  "model_version": "v1",
  "feature_timestamp": "<candle-open-time>",
  "paper_trading_only": true,
  "advisory_only": true,
  "no_execution_authority": true,
  "report_summary": {}
}
```

## Model Report (`data/models/model_report.json`)
```json
{
  "model": "...",
  "version": "v1",
  "label_horizon": 4,
  "flat_threshold": 0.001,
  "features": ["..."],
  "metrics": {
    "accuracy": 0.0,
    "precision": 0.0,
    "recall": 0.0,
    "f1": 0.0,
    "confusion_matrix": {},
    "directional_hit_rate": 0.0,
    "avg_forward_return_by_predicted_class": {}
  },
  "paper_trading_only": true
}
```

## Optional Prediction Context in Reports
`prediction_context` may appear in analyzer/paper JSON outputs and is advisory-only.
