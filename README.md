# AURIX TRADE V5.0

V5.0 consolidates AURIX TRADE behind explicit market-data, strategy, risk and execution service boundaries while preserving the V4.9 demo/paper-trading workflow.

## Deploy

Upload the contents of this folder to the **root** of the GitHub repository connected to Railway. Keep production secrets in Railway Variables; do not commit `.env` files.

Required existing variable: `BOT_TOKEN`.

Optional: `AURIX_TRADING_MODE=DEMO` (default). `PAPER` is also allowed. Any other value fails closed to `DEMO`.

## V5 safety

Live execution and real-money functionality are disabled. The live execution adapter is a deliberate placeholder that raises if called.

See `V5_ARCHITECTURE.md` for the service boundaries and future integration requirements.
