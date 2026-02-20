"""Run shell commands — powershell on Windows, bash on Unix."""

from __future__ import annotations

import os
import platform
import subprocess
from typing import Any

from sentry_agent.actions import register
from sentry_agent.actions.base import ActionResult, BaseAction, RiskLevel

# Dangerous command patterns that need confirmation
DANGEROUS_PATTERNS = [
    "rm -rf", "rmdir /s", "del /f", "del /q",
    "format ", "mkfs", "dd if=",
    "DROP TABLE", "DROP DATABASE", "TRUNCATE",
    "> /dev/null", "shutdown", "reboot",
    ":(){ :|:& };:",  # fork bomb
]


@register
class RunShell(BaseAction):
    name = "run_shell"
    description = "Execute a shell command and return stdout/stderr. Uses PowerShell on Windows, bash on Unix."
    risk_level = RiskLevel.MODERATE  # Safety module does dynamic risk assessment

    def execute(self, args: dict[str, Any]) -> ActionResult:
        command = args.get("command", "")
        if not command:
            return ActionResult(output="", success=False, error="Missing 'command' argument")

        timeout = min(int(args.get("timeout", 120)), 300)
        cwd = args.get("cwd", os.getcwd())

        is_windows = platform.system() == "Windows"
        if is_windows:
            shell_cmd = ["powershell", "-NoProfile", "-Command", command]
        else:
            shell_cmd = ["bash", "-c", command]

        try:
            result = subprocess.run(
                shell_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            return ActionResult(
                output="", success=False,
                error=f"Command timed out after {timeout}s"
            )
        except OSError as exc:
            return ActionResult(output="", success=False, error=str(exc))

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(f"[stderr]\n{result.stderr}")

        output = "\n".join(output_parts) if output_parts else "(no output)"

        if len(output) > 30_000:
            output = output[:30_000] + "\n... (truncated)"

        return ActionResult(
            output=output,
            success=result.returncode == 0,
            error=f"Exit code: {result.returncode}" if result.returncode != 0 else None,
            metadata={"exit_code": result.returncode},
        )
