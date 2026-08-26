# AURIX TRADE V4.7 — Professional Web Dashboard

Adds a secure Telegram Web App dashboard to the V4.6 demo/paper-trading system.

## New
- Telegram Web App button in the bot menu
- Secure Telegram `initData` HMAC validation
- User-specific dashboard for balance, locked capital, equity and tier
- Open positions and recent demo trades
- Win rate and realized simulated P/L
- Onboarding/security status
- Responsive AURIX black/gold UI
- `/app` dashboard and `/api/me` authenticated data endpoint
- `/health` reports dashboard enabled

## Deploy
1. Replace the V4.6 project files in the GitHub repository with these files at the repository root.
2. Keep secrets out of GitHub.
3. In Railway, set `PUBLIC_BASE_URL` to the Railway HTTPS public URL.
4. Redeploy and wait for Successful.
5. Open the AURIX Telegram bot and tap **🌐 Web Dashboard**.

## Important
This remains a DEMO/PAPER-TRADING environment. No real deposits, custody, withdrawals, or broker/exchange orders are enabled.
