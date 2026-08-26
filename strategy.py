from strategy_engine import generate_signal

class StrategyService:
    """Strategy boundary. Strategies produce signals; they never place orders."""
    def signal(self, symbol: str):
        return generate_signal(symbol)
