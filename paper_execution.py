from database import lock_balance, create_demo_trade
from risk_engine import check_paper_order

def open_paper_position(tid: int, symbol: str, side: str, stake: float, price: float):
    ok, reason = check_paper_order(tid, stake)
    if not ok: return None, reason
    if not lock_balance(tid, stake): return None, "Unable to reserve demo capital."
    trade_id = create_demo_trade(tid, symbol, side, stake, price)
    return trade_id, "Paper position opened. No broker/exchange order was sent."
