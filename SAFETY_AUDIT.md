


## Stage 9 Telegram Institutional Signal Engine
- PAPER_TRADING_ONLY remains enforced. Telegram is advisory/monitoring and paper-control only.
- Secrets are loaded from `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) with placeholders in `.env.example`.
- Alerts include strong signals, paper OPEN/CLOSE, risk/system events, and daily summary. HOLD/SKIP are summarized every configurable N cycles (`telegram.hold_skip_summary_every`).
- Commands supported: `/status`, `/summary`, `/risk`, `/pause`, `/resume`, `/lastsignal` (paper mode only).
- Runtime state includes active/paused, cycle count, last alert timestamp, and last signal sent.
- CLI test command: `xrp-telegram-test` validates env config and sends a test message only.
