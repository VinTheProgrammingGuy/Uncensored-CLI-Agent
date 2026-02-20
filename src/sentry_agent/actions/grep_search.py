"""Search file contents by regex pattern."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from sentry_agent.actions import register
from sentry_agent.actions.base import ActionResult, BaseAction, RiskLevel

MAX_MATCHES = 100


@register
class GrepSearch(BaseAction):
    name = "grep_search"
    description = "Search file contents for a regex pattern. Provide 'pattern', optional 'path' (directory), optional 'glob' (file filter like '*.py')."
    risk_level = RiskLevel.SAFE

    def execute(self, args: dict[str, Any]) -> ActionResult:
        pattern_str = args.get("pattern", "")
        if not pattern_str:
            return ActionResult(output="", success=False, error="Missing 'pattern' argument")

        base = Path(args.get("path", ".")).resolve()
        file_glob = args.get("glob", "**/*")

        try:
            regex = re.compile(pattern_str, re.IGNORECASE if args.get("case_insensitive") else 0)
        except re.error as exc:
            return ActionResult(output="", success=False, error=f"Invalid regex: {exc}")

        results: list[str] = []
        try:
            for filepath in sorted(base.glob(file_glob)):
                if not filepath.is_file():
                    continue
                if len(results) >= MAX_MATCHES:
                    break
                try:
                    text = filepath.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for line_num, line in enumerate(text.splitlines(), 1):
                    if regex.search(line):
                        results.append(f"{filepath}:{line_num}: {line.rstrip()}")
                        if len(results) >= MAX_MATCHES:
                            break
        except OSError as exc:
            return ActionResult(output="", success=False, error=str(exc))

        if not results:
            return ActionResult(output="No matches found.", metadata={"count": 0})

        output = "\n".join(results)
        if len(results) == MAX_MATCHES:
            output += f"\n... (limited to {MAX_MATCHES} matches)"

        return ActionResult(output=output, metadata={"count": len(results)})
