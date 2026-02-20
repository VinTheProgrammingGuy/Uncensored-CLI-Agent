"""Create or overwrite files, auto-creating parent directories."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sentry_agent.actions import register
from sentry_agent.actions.base import ActionResult, BaseAction, RiskLevel


@register
class WriteFile(BaseAction):
    name = "write_file"
    description = "Create or overwrite a file with the given content. Parent directories are created automatically."
    risk_level = RiskLevel.MODERATE

    def execute(self, args: dict[str, Any]) -> ActionResult:
        file_path = args.get("path", "")
        content = args.get("content", "")

        if not file_path:
            return ActionResult(output="", success=False, error="Missing 'path' argument")

        path = Path(file_path).resolve()

        # Default to .md when no file extension is specified
        if not path.suffix:
            path = path.with_suffix(".md")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            return ActionResult(output="", success=False, error=str(exc))

        return ActionResult(
            output=f"Wrote {len(content)} bytes to {path}",
            metadata={"path": str(path), "bytes": len(content)},
        )
