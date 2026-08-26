from dataclasses import dataclass
from market_data import current_price

@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    price: float
    mode: str = "DEMO"

class MarketDataService:
    """Market-data boundary. V5 currently exposes synthetic paper data only."""
    def snapshot(self, symbol: str) -> MarketSnapshot:
        return MarketSnapshot(symbol=symbol, price=float(current_price(symbol)))
