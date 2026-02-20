"""Find-and-replace edits with exact string matching."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sentry_agent.actions import register
from sentry_agent.actions.base import ActionResult, BaseAction, RiskLevel


@register
class EditFile(BaseAction):
    name = "edit_file"
    description = "Edit a file by replacing an exact string match. Provide 'path', 'old_string', and 'new_string'."
    risk_level = RiskLevel.MODERATE

    def execute(self, args: dict[str, Any]) -> ActionResult:
        file_path = args.get("path", "")
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "")

        if not file_path:
            return ActionResult(output="", success=False, error="Missing 'path' argument")
        if not old_string:
            return ActionResult(output="", success=False, error="Missing 'old_string' argument")

        path = Path(file_path).resolve()
        if not path.exists():
            return ActionResult(output="", success=False, error=f"File not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            return ActionResult(output="", success=False, error=str(exc))

        count = content.count(old_string)
        if count == 0:
            return ActionResult(
                output="", success=False,
                error=f"String not found in {path}. Make sure you read the file first to get the exact text."
            )

        new_content = content.replace(old_string, new_string, 1)

        try:
            path.write_text(new_content, encoding="utf-8")
        except OSError as exc:
            return ActionResult(output="", success=False, error=str(exc))

        return ActionResult(
            output=f"Replaced 1 occurrence in {path} ({count} total matches, replaced first)",
            metadata={"path": str(path), "matches": count},
        )
