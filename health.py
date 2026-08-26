from services.mode import MODE, LIVE_EXECUTION_ENABLED, REAL_MONEY_ENABLED

def system_status():
    return {
        "mode": MODE,
        "live_execution_enabled": LIVE_EXECUTION_ENABLED,
        "real_money_enabled": REAL_MONEY_ENABLED,
        "market_data": "synthetic",
        "execution": "paper",
    }
