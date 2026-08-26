from decimal import Decimal
from database import get_balance, get_demo_trades, get_user_controls

def check_paper_order(tid: int, stake: float) -> tuple[bool, str]:
    controls = get_user_controls(tid)
    if controls["status"] != "active": return False, "Account is restricted."
    stake_d = Decimal(str(stake))
    if stake_d <= 0: return False, "Stake must be greater than zero."
    if stake_d > Decimal(str(controls["max_trade_stake"])): return False, "Stake exceeds the configured demo risk limit."
    if len(get_demo_trades(tid, "open")) >= int(controls["max_open_positions"]): return False, "Maximum open demo positions reached."
    open_stake = sum(Decimal(str(t["stake"])) for t in get_demo_trades(tid, "open"))
    available = Decimal(str(get_balance(tid))) - open_stake
    if stake_d > available: return False, "Stake exceeds available demo capital."
    return True, "Risk checks passed (demo only)."
