"""Find files by glob pattern."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sentry_agent.actions import register
from sentry_agent.actions.base import ActionResult, BaseAction, RiskLevel

MAX_RESULTS = 200


@register
class GlobSearch(BaseAction):
    name = "glob_search"
    description = "Find files matching a glob pattern (e.g. '**/*.py'). Provide 'pattern' and optional 'path' (base directory)."
    risk_level = RiskLevel.SAFE

    def execute(self, args: dict[str, Any]) -> ActionResult:
        pattern = args.get("pattern", "")
        if not pattern:
            return ActionResult(output="", success=False, error="Missing 'pattern' argument")

        base = Path(args.get("path", ".")).resolve()
        if not base.is_dir():
            return ActionResult(output="", success=False, error=f"Not a directory: {base}")

        try:
            matches = sorted(base.glob(pattern))[:MAX_RESULTS]
        except OSError as exc:
            return ActionResult(output="", success=False, error=str(exc))

        if not matches:
            return ActionResult(output="No files matched the pattern.", metadata={"count": 0})

        lines = [str(m) for m in matches]
        total = len(lines)
        output = "\n".join(lines)
        if total == MAX_RESULTS:
            output += f"\n... (limited to {MAX_RESULTS} results)"

        return ActionResult(output=output, metadata={"count": total})
