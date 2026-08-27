# V5.4 Runbook

1. Keep the existing Exness MT5 bridge running on Windows/VPS.
2. Verify MT5 is connected to the intended account and symbol.
3. Configure Railway:
   DEMO_MODE=true
   REAL_DEPOSITS=false
   REAL_WITHDRAWALS=false
   LIVE_CUSTOMER_TRADING=true
   REAL_MONEY_EXECUTION=false
4. AURIX reads the current MT5 quote.
5. Strategy creates a signal.
6. Risk engine calculates estimated loss.
7. If risk passes, AURIX records a simulated fill at the live quote.
8. P/L is calculated against subsequent live quotes.
9. No MT5 OrderSend/order request is made in this stage.

Never set REAL_MONEY_EXECUTION=true for this build.
