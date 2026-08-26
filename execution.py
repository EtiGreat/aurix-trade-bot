from abc import ABC, abstractmethod
from paper_execution import open_paper_position

class ExecutionAdapter(ABC):
    @abstractmethod
    def open(self, telegram_id, symbol, side, stake, entry_price):
        raise NotImplementedError

class PaperExecutionAdapter(ExecutionAdapter):
    """Safe V5 default. This adapter cannot submit broker/exchange orders."""
    mode = "PAPER"
    def open(self, telegram_id, symbol, side, stake, entry_price):
        return open_paper_position(telegram_id, symbol, side, stake, entry_price)

class LiveExecutionAdapter(ExecutionAdapter):
    """Placeholder only. Live execution is deliberately unavailable in V5."""
    mode = "DISABLED"
    def open(self, *args, **kwargs):
        raise RuntimeError("Live execution is disabled in AURIX TRADE V5.0")
