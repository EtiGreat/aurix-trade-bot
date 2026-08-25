from decimal import Decimal, ROUND_HALF_UP
from config import DEPOSIT_FEE_RATE, PROFIT_FEE_RATE, MIN_DEPOSIT_USD

CENT = Decimal("0.01")

def q(v):
    return Decimal(str(v)).quantize(CENT, rounding=ROUND_HALF_UP)

def calculate_deposit(trading_capital):
    """
    User chooses the amount they want credited as trading capital.
    AURIX charges an additional 5% fee.
    Example: $50 capital -> $52.50 total payment.
    """
    capital = q(trading_capital)
    if capital < MIN_DEPOSIT_USD:
        raise ValueError(f"Minimum deposit is ${MIN_DEPOSIT_USD}")
    fee = q(capital * DEPOSIT_FEE_RATE)
    total = q(capital + fee)
    return {"capital": capital, "fee": fee, "total_due": total}

def calculate_profit_fee(gross_profit):
    profit = q(gross_profit)
    if profit <= 0:
        return {"gross_profit": q(0), "fee": q(0), "net_profit": q(profit)}
    fee = q(profit * PROFIT_FEE_RATE)
    return {
        "gross_profit": profit,
        "fee": fee,
        "net_profit": q(profit - fee),
    }
