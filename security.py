"""AURIX TRADE V5.1 security guardrails.

This module provides startup validation and conservative helpers. It does not
implement live-money execution and deliberately fails closed.
"""
import os
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityReport:
    ok: bool
    issues: tuple[str, ...]


def validate_runtime() -> SecurityReport:
    issues = []
    mode = os.getenv("AURIX_TRADING_MODE", "DEMO").upper()
    if mode not in {"DEMO", "PAPER"}:
        issues.append("AURIX_TRADING_MODE must be DEMO or PAPER")
    if os.getenv("LIVE_EXECUTION_ENABLED", "false").lower() in {"1", "true", "yes"}:
        issues.append("LIVE_EXECUTION_ENABLED must remain disabled in V5.1")
    if os.getenv("REAL_MONEY_ENABLED", "false").lower() in {"1", "true", "yes"}:
        issues.append("REAL_MONEY_ENABLED must remain disabled in V5.1")
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        issues.append("BOT_TOKEN is missing")
    return SecurityReport(not issues, tuple(issues))


def constant_time_equal(a: str, b: str) -> bool:
    return secrets.compare_digest(str(a), str(b))
