import os
from security import constant_time_equal


def test_constant_time_equal():
    assert constant_time_equal("aurix", "aurix")
    assert not constant_time_equal("aurix", "other")


def test_live_flags_default_off(monkeypatch):
    monkeypatch.delenv("LIVE_EXECUTION_ENABLED", raising=False)
    monkeypatch.delenv("REAL_MONEY_ENABLED", raising=False)
    assert os.getenv("LIVE_EXECUTION_ENABLED", "false").lower() not in {"1", "true", "yes"}
    assert os.getenv("REAL_MONEY_ENABLED", "false").lower() not in {"1", "true", "yes"}
