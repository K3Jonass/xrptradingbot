from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class PromotionGateConfig:
    min_sample_size: int = 30
    min_expectancy: float = 0.05
    max_drawdown: float = 150.0
    max_false_breakout_rate: float = 0.45
    min_execution_quality: float = 0.70


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(out):
        return default
    return out


def build_soak_test_report(events_df: pd.DataFrame, journal_df: pd.DataFrame) -> dict:
    if events_df.empty:
        return {
            "total_signals": 0,
            "total_trades": 0,
            "skipped_trades": 0,
            "win_rate": 0.0,
            "average_r_multiple": 0.0,
            "expectancy": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": 0.0,
            "average_execution_quality": 0.0,
            "slippage_impact": 0.0,
            "false_breakout_rate": 0.0,
            "performance_by_market_regime": {},
            "performance_by_strategy_module": {},
        }

    pnl = events_df.get("pnl", pd.Series(dtype=float)).astype(float, errors="ignore").fillna(0.0)
    event_types = events_df.get("event_type", pd.Series(dtype=str)).astype(str)
    closed = events_df[event_types == "CLOSE"].copy()
    if "pnl" in closed.columns:
        closed_pnl = closed["pnl"].astype(float, errors="ignore").fillna(0.0)
    else:
        closed_pnl = pd.Series(dtype=float)

    wins = closed_pnl[closed_pnl > 0]
    losses = closed_pnl[closed_pnl < 0]
    total_trades = int(len(closed_pnl))
    win_rate = (len(wins) / total_trades) if total_trades else 0.0
    profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) else (1.0 if len(wins) else 0.0)

    risk = events_df.get("risk_amount", pd.Series([1.0] * len(events_df))).astype(float, errors="ignore").replace(0.0, 1.0)
    r_multiple = pnl / risk

    equity = closed_pnl.cumsum()
    dd = equity - equity.cummax()
    max_drawdown = float(abs(dd.min())) if not dd.empty else 0.0

    exec_quality = events_df.get("execution_quality", pd.Series([0.0] * len(events_df))).astype(float, errors="ignore")
    slippage = events_df.get("slippage_bps", pd.Series([0.0] * len(events_df))).astype(float, errors="ignore")

    fb = events_df.get("false_breakout", pd.Series([False] * len(events_df))).astype(bool)

    regime_perf = {}
    if "market_regime" in events_df.columns:
        for regime, grp in events_df.groupby("market_regime"):
            regime_perf[str(regime)] = _safe_float(grp.get("pnl", pd.Series(dtype=float)).sum())

    module_perf = {}
    if "strategy_module" in events_df.columns:
        for module, grp in events_df.groupby("strategy_module"):
            module_perf[str(module)] = _safe_float(grp.get("pnl", pd.Series(dtype=float)).sum())

    return {
        "total_signals": int(len(events_df)),
        "total_trades": total_trades,
        "skipped_trades": int((event_types == "SKIP").sum()),
        "win_rate": float(win_rate),
        "average_r_multiple": float(r_multiple.mean()) if len(r_multiple) else 0.0,
        "expectancy": float(closed_pnl.mean()) if total_trades else 0.0,
        "max_drawdown": max_drawdown,
        "profit_factor": profit_factor,
        "average_execution_quality": float(exec_quality.mean()) if len(exec_quality) else 0.0,
        "slippage_impact": float(slippage.mean()) if len(slippage) else 0.0,
        "false_breakout_rate": float(fb.mean()) if len(fb) else 0.0,
        "performance_by_market_regime": regime_perf,
        "performance_by_strategy_module": module_perf,
        "journal_completeness": 1.0 if len(journal_df) >= total_trades else (len(journal_df) / total_trades if total_trades else 1.0),
    }


def calculate_readiness(report: dict, health: dict, gate_config: PromotionGateConfig | None = None) -> dict:
    cfg = gate_config or PromotionGateConfig()
    perf = max(0.0, min(1.0, _safe_float(report.get("expectancy"), 0.0) / max(cfg.min_expectancy, 1e-9)))
    dd = max(0.0, 1.0 - (_safe_float(report.get("max_drawdown"), 0.0) / max(cfg.max_drawdown, 1e-9)))
    exec_q = max(0.0, min(1.0, _safe_float(report.get("average_execution_quality"), 0.0)))
    safety = 1.0 if int(health.get("safety_bypass_incidents", 0)) == 0 else 0.0
    recon = 1.0 if int(health.get("reconciliation_unresolved", 0)) == 0 else 0.0
    idem = 1.0 if int(health.get("duplicate_order_incidents", 0)) == 0 else 0.0
    emergency = 1.0 if int(health.get("emergency_stop_incidents", 0)) == 0 else 0.5
    journal = max(0.0, min(1.0, _safe_float(report.get("journal_completeness"), 1.0)))

    score = round(100 * (0.25 * perf + 0.15 * dd + 0.15 * exec_q + 0.1 * safety + 0.1 * recon + 0.1 * idem + 0.05 * emergency + 0.1 * journal), 2)

    failed_gates = []
    if int(report.get("total_trades", 0)) < cfg.min_sample_size:
        failed_gates.append("minimum sample size")
    if _safe_float(report.get("expectancy"), 0.0) < cfg.min_expectancy:
        failed_gates.append("minimum expectancy")
    if _safe_float(report.get("max_drawdown"), 0.0) > cfg.max_drawdown:
        failed_gates.append("max allowed drawdown")
    if _safe_float(report.get("false_breakout_rate"), 0.0) > cfg.max_false_breakout_rate:
        failed_gates.append("max false breakout rate")
    if _safe_float(report.get("average_execution_quality"), 0.0) < cfg.min_execution_quality:
        failed_gates.append("minimum execution quality")
    if int(health.get("reconciliation_unresolved", 0)) > 0:
        failed_gates.append("no unresolved reconciliation warnings")
    if int(health.get("duplicate_order_incidents", 0)) > 0:
        failed_gates.append("no duplicate order incidents")
    if int(health.get("safety_bypass_incidents", 0)) > 0:
        failed_gates.append("no safety bypass incidents")

    allowed = not failed_gates
    return {
        "readiness_score": score,
        "soak_test_status": "PASS" if allowed else "FAIL",
        "failed_gates": failed_gates,
        "recommended_action": "Allow Spot Testnet dry run" if allowed else "Keep paper soak running; fix failed gates",
        "testnet_allowed": allowed,
        "testnet_blocked": not allowed,
    }
