from dataclasses import dataclass

@dataclass
class RiskConfig:
    equity: float = 25.0
    risk_pct: float = 0.01
    max_daily_loss: float = 0.75
    max_open_positions: int = 1
    max_xau_lot: float = 0.01

def allowed_trade(cfg: RiskConfig, estimated_loss: float, lot: float, open_positions: int = 0, daily_loss: float = 0.0):
    if lot <= 0: return False, 'invalid lot size'
    if lot > cfg.max_xau_lot: return False, 'lot exceeds configured maximum'
    if estimated_loss > cfg.equity * cfg.risk_pct: return False, 'estimated loss exceeds per-trade risk limit'
    if daily_loss + estimated_loss > cfg.max_daily_loss: return False, 'daily loss limit would be exceeded'
    if open_positions >= cfg.max_open_positions: return False, 'maximum open positions reached'
    return True, 'trade passes configured risk checks'

if __name__ == '__main__':
    ok, reason = allowed_trade(RiskConfig(), estimated_loss=0.25, lot=0.01)
    print('PASS' if ok else 'REJECT', '-', reason)
