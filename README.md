# AURIX TRADE V4 — Demo Telegram Trading Platform

V4 upgrades the V3 demo request workflow with the AURIX TRADE brand system, clearer dashboard/account UX, account tiers, demo transaction ledger, referral identity, improved admin accounting, and stronger risk/demo disclosures.

## Safety / deployment boundary
This build is **DEMO/TEST MODE**. It does not accept, custody, transfer, or withdraw real money and it does not place live broker/exchange orders. Do not publish payment addresses or claim live execution from this build.

Before a real-money launch, establish compliant payment/custody infrastructure, reconciliation, authentication and authorization controls, audit logging, applicable KYC/AML procedures, broker/exchange integrations, security testing, and jurisdiction-specific legal/regulatory advice.

## Commands
- `/start` — user dashboard
- `/admin` — admin request console

## Railway variables
- `BOT_TOKEN` — Telegram bot token
- `ADMIN_TELEGRAM_ID` — administrator Telegram ID
- `SUPPORT_USERNAME` — support username without `@`
- `MIN_DEPOSIT_USD` — default `50`
- `DEPOSIT_FEE_RATE` — demo fee rate, default `0.05`
- `PROFIT_FEE_RATE` — reserved for the future disclosed performance-fee model, default `0.20`
