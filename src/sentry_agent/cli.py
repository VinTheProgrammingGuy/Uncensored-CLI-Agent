"""Typer CLI app — run, chat, config commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax

from sentry_agent import __version__
from sentry_agent.config import ensure_exists, load, save, CONFIG_FILE
from sentry_agent.display import show_error
from sentry_agent.exceptions import SentryError

app = typer.Typer(
    name="sentry",
    help="Sentry Agent — CLI coding agent powered by Venice Uncensored API",
    no_args_is_help=False,
)
console = Console()


@app.command()
def run(
    prompt: str = typer.Argument(..., help="The task prompt for the agent"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming output"),
) -> None:
    """Execute a single-shot agent task."""
    try:
        config = ensure_exists()
    except SentryError as exc:
        show_error(str(exc))
        raise typer.Exit(1)

    from sentry_agent.react_loop import run as react_run

    try:
        react_run(prompt, config, stream=not no_stream)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
    except SentryError as exc:
        show_error(str(exc))
        raise typer.Exit(1)


@app.command()
def chat() -> None:
    """Start interactive REPL chat mode."""
    try:
        config = ensure_exists()
    except SentryError as exc:
        show_error(str(exc))
        raise typer.Exit(1)

    from sentry_agent.react_loop import chat_loop

    try:
        chat_loop(config)
    except KeyboardInterrupt:
        console.print("\n[dim]Bye![/dim]")
    except SentryError as exc:
        show_error(str(exc))
        raise typer.Exit(1)


@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="Config key to view or set"),
    value: Optional[str] = typer.Argument(None, help="New value (omit to view)"),
) -> None:
    """View or edit configuration."""
    try:
        cfg = ensure_exists()
    except SentryError as exc:
        show_error(str(exc))
        raise typer.Exit(1)

    if key is None:
        # Show full config (mask API key)
        display_cfg = dict(cfg)
        if display_cfg.get("api_key"):
            k = display_cfg["api_key"]
            display_cfg["api_key"] = k[:10] + "..." + k[-4:] if len(k) > 14 else "***"
        console.print(f"[dim]Config file: {CONFIG_FILE}[/dim]\n")
        console.print(Syntax(json.dumps(display_cfg, indent=2), "json", theme="monokai"))
        return

    if key not in cfg:
        show_error(f"Unknown config key: {key}")
        raise typer.Exit(1)

    if value is None:
        # Show single key
        v = cfg[key]
        if key == "api_key" and v:
            v = v[:10] + "..." + v[-4:] if len(v) > 14 else "***"
        console.print(f"[bold]{key}[/bold] = {v}")
        return

    # Set value with type coercion
    old = cfg[key]
    if isinstance(old, bool):
        cfg[key] = value.lower() in ("true", "1", "yes")
    elif isinstance(old, int):
        cfg[key] = int(value)
    elif isinstance(old, float):
        cfg[key] = float(value)
    else:
        cfg[key] = value

    save(cfg)
    console.print(f"[green]Set {key} = {cfg[key]}[/green]")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    """Sentry Agent CLI."""
    if version:
        console.print(f"sentry-agent {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        chat()
