# AURIX TRADE V4.1 — Demo / Paper Trading Stage

V4.1 adds a simulated paper-trading layer for XAU/USD and BTC/USDT, open/close demo positions, simulated P/L, open-position tracking and performance summaries. It remains DEMO/TEST MODE.

## Safety / deployment boundary
This build does **not** accept, custody, transfer, or withdraw real money and does not place live broker/exchange orders. Market prices and P/L are simulated for product testing only.

Before any real-money launch, establish compliant payment/custody infrastructure, reconciliation, authentication and authorization controls, audit logging, applicable KYC/AML procedures, broker/exchange integrations, security testing, and jurisdiction-specific legal/regulatory advice.

## Commands
- `/start` — user dashboard
- `/admin` — admin request console

## Railway variables
- `BOT_TOKEN` — Telegram bot token
- `ADMIN_TELEGRAM_ID` — administrator Telegram ID
- `SUPPORT_USERNAME` — support username without `@`
- `MIN_DEPOSIT_USD` — default `50`
- `DEPOSIT_FEE_RATE` — demo fee rate, default `0.05`
- `PROFIT_FEE_RATE` — reserved for future disclosed performance-fee model
