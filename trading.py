from dataclasses import dataclass
from services.market import MarketDataService
from services.strategy import StrategyService
from services.risk import RiskService
from services.execution import PaperExecutionAdapter

@dataclass
class SignalResult:
    symbol: str
    action: str
    price: float
    confidence: float

class TradingService:
    """Orchestrates market -> strategy -> risk -> paper execution."""
    def __init__(self):
        self.market = MarketDataService()
        self.strategy = StrategyService()
        self.risk = RiskService()
        self.execution = PaperExecutionAdapter()

    def get_signal(self, symbol: str):
        return self.strategy.signal(symbol)

    def open_demo(self, telegram_id, symbol, side, stake):
        snapshot = self.market.snapshot(symbol)
        approved, reason = self.risk.approve_paper_order(telegram_id, symbol, side, stake)
        if not approved:
            return None, reason
        return self.execution.open(telegram_id, symbol, side, stake, snapshot.price)
