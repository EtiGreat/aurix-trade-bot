# AURIX TRADE V4.6 — Onboarding & Account Security

V4.6 extends V4.5.1 with a demo-safe onboarding and account-security layer.

## Added
- Account & Security screen
- Demo Terms / Privacy / Risk acknowledgements
- Basic profile completion using Telegram profile data only
- Verification status placeholder (no document collection)
- Security reminder around Telegram login codes
- Automatic SQLite migration for onboarding data

## Safety boundary
This build remains DEMO / PAPER TRADING ONLY. It does not collect identity documents, process real deposits, custody funds, execute broker/exchange orders, or perform real withdrawals. A future live-money release should implement appropriate KYC/AML, sanctions, privacy, security, regulatory and operational controls before activation.

## Deploy
Replace the repository root files, commit, and let Railway redeploy. Do not upload `.env` or secrets.
