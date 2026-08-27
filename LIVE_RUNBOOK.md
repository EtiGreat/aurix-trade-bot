# AURIX V5.3 Personal Live Runbook

## Railway variables
EXNESS_MT5_LOGIN=<personal live account number>
EXNESS_MT5_SERVER=<exact Exness server name>
EXNESS_MODE=live
LIVE_TRADING=true
LIVE_CONFIRMATION=I_UNDERSTAND_LIVE_RISK
LIVE_MAX_LOTS=0.01
LIVE_MAX_DAILY_LOSS=10
LIVE_ALLOWED_SYMBOLS=XAUUSD,BTCUSD

Do NOT commit the MT5 password to GitHub. Keep it in the MT5 terminal/VPS secret store.

## Critical deployment rule
Do not set LIVE_TRADING=true until the bridge has been tested with demo funds and the
AURIX ledger reconciles with MT5. The adapter contains a fail-closed gate, but operational
controls must be independently verified.

## Recommended infrastructure
Run MT5 on a Windows VPS close to the broker. Keep AURIX/Railway as the orchestration layer.
Do not expose MT5 credentials through a web endpoint.

## First live test
Use the smallest permitted volume, one approved symbol, and a pre-agreed loss limit.
Verify: order ID, fill price, volume, stop-loss/take-profit, broker position, AURIX ledger,
and close/reconciliation. Stop immediately if any mismatch occurs.
