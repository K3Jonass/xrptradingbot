import pandas as pd

from xrp_bot.validation import build_soak_test_report, calculate_readiness, PromotionGateConfig


def _events(n=40, exec_q=0.9):
    rows = []
    for i in range(n):
        rows.append({
            "event_type": "CLOSE",
            "pnl": 1.0 if i % 3 else -0.2,
            "risk_amount": 1.0,
            "execution_quality": exec_q,
            "slippage_bps": 2.0,
            "false_breakout": False,
            "market_regime": "ranging",
            "strategy_module": "core",
        })
    return pd.DataFrame(rows)


def test_readiness_score_calculation():
    report = build_soak_test_report(_events(), pd.DataFrame([{}] * 40))
    out = calculate_readiness(report, {})
    assert 0 <= out["readiness_score"] <= 100
    assert out["testnet_allowed"] is True


def test_failed_gates_block_promotion():
    report = build_soak_test_report(_events(n=10), pd.DataFrame([{}] * 10))
    out = calculate_readiness(report, {})
    assert out["testnet_allowed"] is False
    assert "minimum sample size" in out["failed_gates"]


def test_insufficient_sample_blocks_promotion():
    report = build_soak_test_report(_events(n=5), pd.DataFrame([{}] * 5))
    out = calculate_readiness(report, {})
    assert out["testnet_blocked"] is True


def test_reconciliation_warnings_block_promotion():
    report = build_soak_test_report(_events(), pd.DataFrame([{}] * 40))
    out = calculate_readiness(report, {"reconciliation_unresolved": 2})
    assert out["testnet_allowed"] is False
    assert "no unresolved reconciliation warnings" in out["failed_gates"]


def test_poor_execution_quality_blocks_promotion():
    report = build_soak_test_report(_events(exec_q=0.2), pd.DataFrame([{}] * 40))
    out = calculate_readiness(report, {})
    assert out["testnet_allowed"] is False
    assert "minimum execution quality" in out["failed_gates"]
