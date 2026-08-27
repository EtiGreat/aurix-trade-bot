from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class DemoAccount:
    balance: float = 25.0
    equity: float = 25.0
    realized_pnl: float = 0.0
    open_positions: int = 0

@dataclass
class DemoOrder:
    symbol: str
    side: str
    volume: float
    price: float
    stop_loss: float | None
    take_profit: float | None
    status: str = "SIMULATED"

def risk_check(account: DemoAccount, estimated_loss: float,
               volume: float, max_risk_usd: float = 0.25,
               max_open_positions: int = 1):
    if estimated_loss > max_risk_usd:
        return False, "RISK_LIMIT_EXCEEDED"
    if account.open_positions >= max_open_positions:
        return False, "MAX_OPEN_POSITIONS"
    if volume <= 0:
        return False, "INVALID_VOLUME"
    return True, "PASS"

def simulate_fill(account: DemoAccount, order: DemoOrder,
                  estimated_loss: float):
    ok, reason = risk_check(account, estimated_loss, order.volume)
    if not ok:
        order.status = f"REJECTED:{reason}"
        return order
    order.status = "SIMULATED_FILLED"
    account.open_positions += 1
    return order

if __name__ == "__main__":
    account = DemoAccount()
    order = DemoOrder("XAUUSD", "BUY", 0.01, 0.0, None, None)
    print(simulate_fill(account, order, 0.20))
