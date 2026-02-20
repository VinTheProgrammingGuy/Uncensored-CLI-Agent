"""BaseAction abstract class and ActionResult dataclass."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    DANGEROUS = "dangerous"


@dataclass
class ActionResult:
    """Result returned by every action executor."""
    output: str
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAction(ABC):
    """Abstract base class for all agent actions."""

    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.SAFE

    @abstractmethod
    def execute(self, args: dict[str, Any]) -> ActionResult:
        """Execute the action with given arguments. Must be implemented."""
        ...
