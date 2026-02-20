"""Directory listing with type and size information."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sentry_agent.actions import register
from sentry_agent.actions.base import ActionResult, BaseAction, RiskLevel


def _format_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


@register
class ListDirectory(BaseAction):
    name = "list_directory"
    description = "List directory contents with type and size. Provide 'path' and optional 'max_depth' (default 1, max 3)."
    risk_level = RiskLevel.SAFE

    def execute(self, args: dict[str, Any]) -> ActionResult:
        dir_path = args.get("path", ".")
        max_depth = min(int(args.get("max_depth", 1)), 3)

        base = Path(dir_path).resolve()
        if not base.is_dir():
            return ActionResult(output="", success=False, error=f"Not a directory: {base}")

        lines: list[str] = []
        self._list_recursive(base, base, 0, max_depth, lines)

        if not lines:
            return ActionResult(output="(empty directory)", metadata={"count": 0})

        return ActionResult(output="\n".join(lines), metadata={"count": len(lines)})

    def _list_recursive(
        self, root: Path, current: Path, depth: int, max_depth: int, lines: list[str]
    ) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            lines.append(f"{'  ' * depth}[permission denied]")
            return

        indent = "  " * depth
        for entry in entries:
            if entry.name.startswith(".") and depth == 0:
                continue  # Skip hidden at top level for cleanliness
            if entry.is_dir():
                lines.append(f"{indent}{entry.name}/")
                if depth < max_depth:
                    self._list_recursive(root, entry, depth + 1, max_depth, lines)
            else:
                try:
                    size = _format_size(entry.stat().st_size)
                except OSError:
                    size = "?"
                lines.append(f"{indent}{entry.name}  ({size})")
