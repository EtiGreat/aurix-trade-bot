# AURIX TRADE V5.0 — Production Architecture

V5.0 consolidates the trading system behind explicit service boundaries while keeping the working V4.9 Telegram bot and database intact.

## Flow

`MarketDataService -> StrategyService -> RiskService -> PaperExecutionAdapter`

The strategy layer creates signals only. The risk layer is the single approval gate. The execution layer is an adapter and the V5 default is paper execution.

## Safety boundary

- `LIVE_EXECUTION_ENABLED = False`
- `REAL_MONEY_ENABLED = False`
- `LiveExecutionAdapter` is intentionally disabled and raises if called.
- `AURIX_TRADING_MODE` accepts only `DEMO` or `PAPER`; any other value fails closed to `DEMO`.

## Integration boundary for a future regulated deployment

A future broker/exchange connector must implement `ExecutionAdapter` and be enabled only after the appropriate legal, regulatory, custody, AML/KYC, payment, security and operational controls have been independently established.

No credential, API secret, payment method, or exchange endpoint is added by this build.
