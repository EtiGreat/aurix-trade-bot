from services.mode import MODE, LIVE_EXECUTION_ENABLED, REAL_MONEY_ENABLED
from services.execution import LiveExecutionAdapter
from services.health import system_status

assert MODE in {"DEMO", "PAPER"}
assert LIVE_EXECUTION_ENABLED is False
assert REAL_MONEY_ENABLED is False
assert system_status()["execution"] == "paper"
try:
    LiveExecutionAdapter().open(1, "XAU/USD", "LONG", 10, 2000)
except RuntimeError:
    pass
else:
    raise AssertionError("Live execution must remain disabled")
print("V5 architecture safety checks passed")
