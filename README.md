# AURIX TRADE V4.4 — Production Demo Launch

Production-ready public demo for AURIX TRADE. This release remains strictly DEMO/PAPER TRADING: no real deposits, custody, withdrawals, broker/exchange orders, or live execution.

## V4.4 changes
- Public web landing page at `/`
- Railway health endpoint at `/health`
- Terms, privacy, and risk disclosure pages
- Legal & Risk link from the Telegram bot
- Optional official Telegram channel URL
- Production `PORT` support for Railway
- Clear demo-mode labeling throughout
- Existing V4.3 admin, risk controls, paper trading, and portfolio accounting retained

## Railway Variables
Required: `BOT_TOKEN`, `ADMIN_TELEGRAM_ID`
Optional: `SUPPORT_USERNAME`, `MIN_DEPOSIT_USD`, `DEPOSIT_FEE_RATE`, `PROFIT_FEE_RATE`, `PUBLIC_BASE_URL`, `OFFICIAL_CHANNEL_URL`

Do not commit secrets to GitHub. Set them in Railway Variables.

## Launch checklist
1. Deploy this release from GitHub to Railway.
2. Confirm deployment is successful.
3. Open the Railway public domain and verify `/health`, `/`, `/terms`, `/privacy`, `/risk`.
4. Open Telegram and test `/start`, dashboard, demo trading, and `/admin`.
5. Keep all real-money features disabled until the legal/regulatory and operational requirements are satisfied.
