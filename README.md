# AURIX TRADE — Telegram Bot Foundation

A clean-from-scratch foundation for the AURIX TRADE Telegram platform.

## Current build

- Telegram bot with AURIX branding
- Dashboard menu
- $50 minimum trading capital
- 5% deposit fee calculation
- 20% fee on positive realized trading profit
- SQLite user/transaction database
- Risk disclosure
- Demo/not-live trading status
- Railway deployment files

## Fee model

A user who wants $50 credited as trading capital pays:

- Trading capital: $50.00
- 5% deposit fee: $2.50
- Total payment: $52.50

For a genuine realized trading profit of $10:

- Gross profit: $10.00
- AURIX performance fee (20%): $2.00
- Net profit: $8.00

The live payment, custody, broker and exchange integrations are intentionally not enabled in this foundation.

## Local setup

1. Install Python 3.11+.
2. Create a virtual environment.
3. Install dependencies:

   pip install -r requirements.txt

4. Copy `.env.example` to `.env`.
5. Add your BotFather token.
6. Run:

   python bot.py

## Railway

Push the project to GitHub, create a Railway project from the repository, and add the variables from `.env.example` in Railway Variables.

Do NOT commit `.env` or a real bot token to GitHub.

## Before accepting real money

The project still needs:

- Verified payment/deposit provider
- Real wallet/exchange or broker integration
- User identity/verification flow where legally required
- Withdrawal processor
- Strong admin authentication
- Audit logs
- Reconciliation between user balances and actual custodial/trading balances
- Trading strategy/backtesting
- Risk limits
- Legal/regulatory review for the jurisdictions served

Never represent demo balances or simulated profits as real trading performance.
