"""Git operations — run git subcommands."""

from __future__ import annotations

import subprocess
from typing import Any

from sentry_agent.actions import register
from sentry_agent.actions.base import ActionResult, BaseAction, RiskLevel


@register
class GitCommand(BaseAction):
    name = "git_command"
    description = "Run a git subcommand (e.g. 'status', 'diff', 'log --oneline -10'). Provide 'subcommand'."
    risk_level = RiskLevel.MODERATE  # Safety module does dynamic risk assessment

    def execute(self, args: dict[str, Any]) -> ActionResult:
        subcommand = args.get("subcommand", "")
        if not subcommand:
            return ActionResult(output="", success=False, error="Missing 'subcommand' argument")

        cmd = f"git {subcommand}"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return ActionResult(output="", success=False, error="Git command timed out")
        except OSError as exc:
            return ActionResult(output="", success=False, error=str(exc))

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(result.stderr)

        output = "\n".join(output_parts) if output_parts else "(no output)"

        if len(output) > 30_000:
            output = output[:30_000] + "\n... (truncated)"

        return ActionResult(
            output=output,
            success=result.returncode == 0,
            error=f"Exit code: {result.returncode}" if result.returncode != 0 else None,
            metadata={"exit_code": result.returncode},
        )
