"""Read any file with optional offset/limit and line numbers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sentry_agent.actions import register
from sentry_agent.actions.base import ActionResult, BaseAction, RiskLevel


@register
class ReadFile(BaseAction):
    name = "read_file"
    description = "Read a file's contents. Supports optional offset (line number) and limit (line count)."
    risk_level = RiskLevel.SAFE

    def execute(self, args: dict[str, Any]) -> ActionResult:
        file_path = args.get("path", "")
        if not file_path:
            return ActionResult(output="", success=False, error="Missing 'path' argument")

        path = Path(file_path).resolve()
        if not path.exists():
            return ActionResult(output="", success=False, error=f"File not found: {path}")
        if not path.is_file():
            return ActionResult(output="", success=False, error=f"Not a file: {path}")

        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            return ActionResult(output="", success=False, error=str(exc))

        offset = int(args.get("offset", 0))
        limit = int(args.get("limit", 0))

        if offset > 0:
            lines = lines[offset:]
        if limit > 0:
            lines = lines[:limit]

        numbered = [f"{i + offset + 1:>5} | {line}" for i, line in enumerate(lines)]
        content = "\n".join(numbered)

        if len(content) > 50_000:
            content = content[:50_000] + "\n... (truncated)"

        return ActionResult(output=content, metadata={"lines": len(numbered), "path": str(path)})
