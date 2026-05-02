# Architecture Overview

## Unified signal path
- `signal_engine.stage3_analysis()` is the single source for Stage 3 scoring.
- Analyzer, paper signal evaluation, and Stage3 composite strategy all consume this path.

## Strategy layer
- `BaseStrategy` defines `generate_signal(df)`.
- Implementations: Stage3 composite, EMA crossover, RSI mean reversion, breakout+volume.

## Backtesting/research
- `run_backtest()` executes a strategy with shared risk model.
- `batch_backtest()`, `optimize_parameters()`, and `walk_forward_validation()` support research workflows.

## Paper event schema
- `append_event_jsonl()` writes unified keys.
- `normalize_event_payload()` adapts legacy event records.

## Safety
- Paper-only guards are enforced; no live execution code exists.
