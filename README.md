# AURIX TRADE V5.4 — Live-Market Demo Trading

Purpose:
- Use live market data from the Exness MT5 terminal.
- Keep user balances virtual/demo only.
- Simulate customer trading/execution in AURIX.
- Keep real-money execution disabled.

Configuration:
DEMO_MODE=true
REAL_DEPOSITS=false
REAL_WITHDRAWALS=false
LIVE_CUSTOMER_TRADING=true
REAL_MONEY_EXECUTION=false

Risk defaults for a $25 reference demo account:
MAX_RISK_PER_TRADE_PCT=1
MAX_RISK_PER_TRADE_USD=0.25
MAX_DAILY_LOSS_USD=0.75
MAX_OPEN_POSITIONS=1

The MT5 bridge is market-data only for this stage. No broker order is submitted.
The live market feed is used to price simulated AURIX demo fills.
