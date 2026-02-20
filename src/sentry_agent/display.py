"""Centralized Rich terminal output — flat, minimal, Claude Code style."""

from __future__ import annotations

import os
import sys
from typing import Iterator

# Enable UTF-8 output on Windows so Unicode box-drawing renders correctly
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

from sentry_agent import __version__

console = Console(force_terminal=True, legacy_windows=False)

_ACTION_KEY_PARAM = {
    "read_file": "path",
    "write_file": "path",
    "edit_file": "path",
    "run_shell": "command",
    "glob_search": "pattern",
    "grep_search": "pattern",
    "list_directory": "path",
    "git_command": "subcommand",
}


def _key_param(name: str, params: dict) -> str:
    key = _ACTION_KEY_PARAM.get(name)
    if key and key in params:
        val = str(params[key])
        return val[:77] + "..." if len(val) > 80 else val
    for v in params.values():
        if isinstance(v, str) and v:
            val = str(v)
            return val[:77] + "..." if len(val) > 80 else val
    return ""


def show_welcome() -> None:
    """Display a bordered welcome header in Claude Code style."""
    cwd = os.getcwd()

    body = Text.from_markup(
        "\n"
        f"  [dim]cwd:[/dim] {cwd}\n"
        "\n"
        "  [dim]/help for commands  |  /clear to reset  |  Ctrl+C to exit[/dim]\n"
    )

    title = Text.from_markup(f"[bold yellow]* SENTRY[/bold yellow] [dim]v{__version__}[/dim]")

    console.print()
    console.print(Panel(body, title=title, title_align="left",
                        border_style="yellow", expand=True, padding=(0, 0)))
    console.print()


def show_thought(text: str) -> None:
    """Display LLM reasoning as indented dim italic text."""
    console.print(f"  [dim italic]{text}[/dim italic]")


def show_action(name: str, params: dict) -> None:
    """Display action being executed as a compact one-liner."""
    param_str = _key_param(name, params)
    if param_str:
        console.print(f"  [bold yellow]{name}[/bold yellow] [dim]{param_str}[/dim]")
    else:
        console.print(f"  [bold yellow]{name}[/bold yellow]")


def show_result(text: str, title: str = "Result") -> None:
    """Display action result as indented dim text, truncated to 5 lines."""
    lines = text.splitlines()
    if len(lines) > 5:
        for line in lines[:5]:
            console.print(f"  [dim]{line}[/dim]")
        console.print(f"  [dim]({len(lines) - 5} more lines)[/dim]")
    else:
        for line in lines:
            console.print(f"  [dim]{line}[/dim]")


def show_error(text: str) -> None:
    """Display error as indented red text."""
    console.print(f"  [red]Error: {text}[/red]")


def show_final(text: str) -> None:
    """Display the agent's final answer."""
    console.print()
    console.print(Markdown(text))
    console.print()


def show_stream(iterator: Iterator[str]) -> str:
    """Collect LLM tokens with a static thinking indicator, return full text."""
    console.print("  [dim]Thinking...[/dim]")
    full_text = ""
    for chunk in iterator:
        full_text += chunk
    return full_text


def show_input() -> str:
    """Display input field between gray dividers (both visible while typing)."""
    rule = "\u2500" * console.width
    dim_rule = f"\033[2m{rule}\033[0m"
    # Print top divider
    console.print(f"[dim]{rule}[/dim]")
    # Pre-draw bottom divider one line below, then move cursor back up
    sys.stdout.write(f"\n{dim_rule}\033[1A\r")
    sys.stdout.flush()
    # Cursor is now on the empty line between the two dividers
    text = console.input("[bold yellow]> [/bold yellow]")
    # After Enter, cursor lands on the bottom divider line — skip past it
    sys.stdout.write("\n")
    sys.stdout.flush()
    return text.strip()


def show_confirm(msg: str) -> bool:
    """Show a confirmation prompt, return True if user agrees."""
    return Confirm.ask(f"[bold yellow]{msg}[/bold yellow]")


def show_info(text: str) -> None:
    """Display an informational message."""
    console.print(f"[yellow]{text}[/yellow]")


def show_iteration(current: int, maximum: int) -> None:
    """Suppressed for clean output."""
