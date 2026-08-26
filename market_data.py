import math, time
from dataclasses import dataclass
from typing import List

@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float

BASE = {"XAU/USD": 2400.0, "BTC/USDT": 105000.0}

def _seed(symbol: str) -> float:
    return 17.0 if symbol == "XAU/USD" else 29.0

def current_price(symbol: str) -> float:
    base = BASE.get(symbol, 2400.0)
    t = time.time() / 60.0
    wave = math.sin(t / 9.0 + _seed(symbol)) * 0.006 + math.sin(t / 31.0 + _seed(symbol)) * 0.004
    return round(base * (1 + wave), 2)

def candles(symbol: str, count: int = 60) -> List[Candle]:
    base = BASE.get(symbol, 2400.0)
    now = int(time.time() // 60) * 60
    result=[]
    for i in range(count):
        ts = now - (count-i)*60
        x = ts/60.0
        close = base * (1 + math.sin(x/9 + _seed(symbol))*0.006 + math.sin(x/31 + _seed(symbol))*0.004)
        prev_x = (ts-60)/60.0
        op = base * (1 + math.sin(prev_x/9 + _seed(symbol))*0.006 + math.sin(prev_x/31 + _seed(symbol))*0.004)
        wiggle = base * 0.0008 * (1 + (i % 4)/4)
        result.append(Candle(ts, round(op,2), round(max(op,close)+wiggle,2), round(min(op,close)-wiggle,2), round(close,2)))
    return result
