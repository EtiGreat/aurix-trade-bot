# AURIX TRADE V4.2 — Portfolio & Risk Demo

Paper-trading demo for Telegram. No real deposits, custody, withdrawals, broker/exchange orders, or live execution.

## V4.2 changes
- Properly reserves/locks demo stake when a paper position opens.
- Releases the stake plus simulated P/L when a paper position closes.
- Dashboard shows available balance, locked capital, and demo equity.
- Performance shows wins, losses, win rate, demo volume, and realized simulated P/L.
- Existing SQLite database migrates `locked_balance` automatically.

## Railway
Set `BOT_TOKEN`, `ADMIN_TELEGRAM_ID`, and any existing support/config variables in Railway Variables. Do not commit secrets.
