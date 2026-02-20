"""Action registry and dispatcher."""

from __future__ import annotations

from typing import Any

from sentry_agent.actions.base import ActionResult, BaseAction, RiskLevel
from sentry_agent.exceptions import ActionError

_REGISTRY: dict[str, BaseAction] = {}


def register(action_class: type[BaseAction]) -> type[BaseAction]:
    """Decorator to register an action class."""
    instance = action_class()
    _REGISTRY[instance.name] = instance
    return action_class


def get_action(name: str) -> BaseAction:
    """Look up an action by name."""
    if name not in _REGISTRY:
        raise ActionError(f"Unknown action: {name}")
    return _REGISTRY[name]


def dispatch(name: str, args: dict[str, Any]) -> ActionResult:
    """Look up and execute an action."""
    action = get_action(name)
    return action.execute(args)


def all_actions() -> dict[str, BaseAction]:
    """Return all registered actions."""
    return dict(_REGISTRY)


def load_all() -> None:
    """Import all action modules to trigger registration."""
    from sentry_agent.actions import (  # noqa: F401
        read_file,
        write_file,
        edit_file,
        shell,
        glob_search,
        grep_search,
        list_dir,
        git,
    )


__all__ = [
    "register",
    "get_action",
    "dispatch",
    "all_actions",
    "load_all",
    "BaseAction",
    "ActionResult",
    "RiskLevel",
]
