import os

MODE = os.getenv("AURIX_TRADING_MODE", "DEMO").upper()

if MODE not in {"DEMO", "PAPER"}:
    # Fail closed: V5 cannot be switched to live execution by an environment typo.
    MODE = "DEMO"

LIVE_EXECUTION_ENABLED = False
REAL_MONEY_ENABLED = False
