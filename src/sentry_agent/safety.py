"""Destructive action detection and confirmation."""

from __future__ import annotations

import re
from typing import Any

from sentry_agent.actions.base import RiskLevel
from sentry_agent.exceptions import SafetyAbortError

# Patterns that always require confirmation regardless of action risk level
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"rm\s+-r\s",
    r"rmdir\s+/s",
    r"del\s+/[fqs]",
    r"Remove-Item.*-Recurse",
    r"git\s+push\s+.*--force",
    r"git\s+push\s+-f\b",
    r"git\s+reset\s+--hard",
    r"git\s+clean\s+-fd",
    r"DROP\s+TABLE",
    r"DROP\s+DATABASE",
    r"TRUNCATE\s+TABLE",
    r"FORMAT\s+",
    r"mkfs\.",
    r"dd\s+if=",
    r">\s*/dev/s",
    r"shutdown",
    r"reboot",
    r":\(\)\s*\{",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]


def check_action(
    action_name: str,
    args: dict[str, Any],
    risk_level: RiskLevel,
    confirm_fn: Any,
    safety_enabled: bool = True,
) -> None:
    """Check if an action requires confirmation. Raises SafetyAbortError if declined.

    Args:
        action_name: Name of the action being executed
        args: Action arguments
        risk_level: The action's declared risk level
        confirm_fn: Callable(msg) -> bool for user confirmation
        safety_enabled: Whether safety checks are active
    """
    if not safety_enabled:
        return

    # Check for dangerous patterns in args
    args_text = _flatten_args(args)
    is_dangerous = _matches_dangerous(args_text)

    if is_dangerous:
        msg = f"Dangerous operation detected:\n  Action: {action_name}\n  Args: {args_text[:200]}\n\nProceed?"
        if not confirm_fn(msg):
            raise SafetyAbortError(f"User declined: {action_name}")
        return

    # SAFE actions always pass
    if risk_level == RiskLevel.SAFE:
        return

    # DANGEROUS actions (from risk_level) always prompt
    if risk_level == RiskLevel.DANGEROUS:
        msg = f"This action is marked as dangerous:\n  Action: {action_name}\n  Args: {args_text[:200]}\n\nProceed?"
        if not confirm_fn(msg):
            raise SafetyAbortError(f"User declined: {action_name}")


def _flatten_args(args: dict[str, Any]) -> str:
    """Flatten args dict to a searchable string."""
    parts = []
    for v in args.values():
        parts.append(str(v))
    return " ".join(parts)


def _matches_dangerous(text: str) -> bool:
    """Check if text matches any dangerous pattern."""
    return any(p.search(text) for p in _compiled)
