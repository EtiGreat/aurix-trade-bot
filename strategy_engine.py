from dataclasses import dataclass
from typing import Optional
from market_data import candles

@dataclass
class Signal:
    symbol: str
    action: str
    confidence: float
    price: float
    fast_ma: float
    slow_ma: float
    momentum: float
    label: str = "SIMULATED / DEMO"

def _sma(values, n):
    return sum(values[-n:]) / n if len(values) >= n else sum(values)/len(values)

def generate_signal(symbol: str) -> Signal:
    cs = candles(symbol, 60)
    closes = [c.close for c in cs]
    fast = _sma(closes, 8)
    slow = _sma(closes, 21)
    momentum = ((closes[-1] - closes[-6]) / closes[-6]) * 100 if len(closes) >= 6 else 0
    gap = abs(fast-slow)/slow*100
    if fast > slow and momentum >= 0:
        action = "LONG"
    elif fast < slow and momentum <= 0:
        action = "SHORT"
    else:
        action = "WAIT"
    confidence = min(95.0, 50.0 + gap*80.0 + min(abs(momentum)*8.0, 25.0))
    if action == "WAIT": confidence = min(confidence, 55.0)
    return Signal(symbol, action, round(confidence,1), closes[-1], round(fast,2), round(slow,2), round(momentum,3))
