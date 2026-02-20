# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Sentry Agent — a CLI coding agent powered by the Venice Uncensored API. Implements a ReAct (Reason + Act) loop where the LLM responds with JSON containing a thought and an action, which is executed and fed back until the task is done.

## Commands

```bash
# Install in editable mode
pip install -e .

# Run interactive chat
sentry

# Single-shot execution
sentry run "your prompt here"

# View/set config
sentry config
sentry config model venice-uncensored

# Run all tests
pytest tests/

# Run a single test file or test
pytest tests/test_parser.py
pytest tests/test_actions.py::TestReadFile::test_read_existing_file

# Version check
sentry --version
```

No linter or formatter is configured in pyproject.toml. Tests use pytest with fixtures in `tests/conftest.py`.

## Architecture

**ReAct loop** (`react_loop.py`): The core loop calls the Venice API, parses the JSON response, extracts thought + action, executes the action via the registry, feeds the result back as a user message, and repeats. `run()` handles single-shot mode; `chat_loop()` handles the interactive REPL with slash commands.

**Action registry** (`actions/__init__.py`): Actions are registered with the `@register` decorator on classes that extend `BaseAction`. Each action has a `name`, `description`, `risk_level` (SAFE/MODERATE/DANGEROUS), and `execute(args)` method returning an `ActionResult`. Call `load_all()` to import all action modules, then `dispatch(name, args)` to execute.

**JSON parser** (`parser.py`): Multi-strategy extraction — tries direct parse, strips markdown fences, regex-extracts first `{...}` block with brace matching, then searches after common LLM prefixes. This handles the Venice model's inconsistent JSON formatting.

**Context management** (`context.py`): `ConversationContext` tracks message history and token usage. Auto-truncates to the last 4 message pairs when approaching 28K tokens, preserving the first user message.

**Safety** (`safety.py`): Regex-based detection of dangerous shell patterns (rm -rf, DROP TABLE, git push --force, etc.). DANGEROUS-level actions require user confirmation via `show_confirm()`.

**Display** (`display.py`): All terminal output goes through this module. Uses Rich with `legacy_windows=False` and UTF-8 stdout reconfiguration for Windows. The input field pre-draws both dividers using ANSI cursor movement. The `show_stream()` function collects tokens behind a static "Thinking..." line (no cursor-manipulating spinner).

**API client** (`api_client.py`): `VeniceClient` handles HTTP to the Venice chat completions endpoint. Supports streaming (SSE) and non-streaming. Retries on 429/503/504 with exponential backoff. Sends `venice_parameters.disable_venice_system_prompt: true`.

**Config** (`config.py`): Stored at `~/.sentry/config.json`. Env var `SENTRY_API_KEY` overrides the stored key. First-run wizard prompts for API key and model.

## Key Patterns

- **All LLM responses must be JSON**: `{"thought": "...", "action": {"name": "...", "args": {...}}}`. The `done` action signals task completion.
- **Actions are self-registering**: Add a new action by creating a file in `actions/`, subclassing `BaseAction`, and decorating with `@register`. It auto-loads via `load_all()`.
- **Version lives in two places**: `src/sentry_agent/__init__.py` and `pyproject.toml` — keep them in sync.
- **Windows compatibility matters**: Shell commands use PowerShell on Windows, bash on Unix. Display uses UTF-8 reconfiguration and ANSI escape codes (no legacy Win32 renderer). Avoid Unicode in user-facing strings outside of Rich markup.
- **write_file defaults to .md** when no file extension is specified.

## Exception Hierarchy

`SentryError` is the base. Subtypes: `ConfigError`, `APIError`, `RateLimitError`, `AuthError`, `ParseError`, `ActionError`, `SafetyAbortError`, `MaxIterationsError`. Catch `SentryError` for broad error handling in the loop.
