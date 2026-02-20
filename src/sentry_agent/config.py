"""Manages ~/.sentry/config.json — load, save, first-run wizard."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rich.prompt import Prompt

from sentry_agent.exceptions import ConfigError

CONFIG_DIR = Path.home() / ".sentry"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS: dict[str, Any] = {
    "api_key": "",
    "model": "venice-uncensored",
    "base_url": "https://api.venice.ai/api/v1",
    "temperature": 0.3,
    "max_tokens": 4096,
    "stream": True,
    "safety_confirm_destructive": True,
    "max_react_iterations": 25,
}


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load() -> dict[str, Any]:
    """Load config from disk, applying defaults for missing keys."""
    _ensure_dir()
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ConfigError(f"Failed to read config: {exc}") from exc
    else:
        data = {}

    config = {**DEFAULTS, **data}

    # Env var override
    env_key = os.environ.get("SENTRY_API_KEY")
    if env_key:
        config["api_key"] = env_key

    return config


def save(config: dict[str, Any]) -> None:
    """Write config to disk."""
    _ensure_dir()
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def ensure_exists() -> dict[str, Any]:
    """Load config, running first-run wizard if API key is missing."""
    config = load()
    if not config["api_key"]:
        config = _first_run_wizard(config)
    return config


def _first_run_wizard(config: dict[str, Any]) -> dict[str, Any]:
    """Interactive setup for first run."""
    from rich.console import Console

    console = Console()
    console.print()
    console.print("  [bold yellow]Sentry Agent[/bold yellow] [dim]-- First Run Setup[/dim]")
    console.print()
    console.print("Get your API key from [link=https://venice.ai]venice.ai[/link]\n")

    api_key = Prompt.ask("[bold]Venice API Key[/bold]")
    if not api_key.strip():
        raise ConfigError("API key is required")
    config["api_key"] = api_key.strip()

    model = Prompt.ask(
        "[bold]Model[/bold]",
        default=config["model"],
    )
    config["model"] = model.strip()

    save(config)
    console.print(f"\n[yellow]Config saved to {CONFIG_FILE}[/yellow]")
    return config
