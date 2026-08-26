from risk_engine import check_paper_order

class RiskService:
    """Single risk gate for paper execution."""
    def approve_paper_order(self, telegram_id, symbol, side, stake):
        return check_paper_order(telegram_id, symbol, side, stake)
