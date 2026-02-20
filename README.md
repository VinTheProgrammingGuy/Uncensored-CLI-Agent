# Sentry Agent

CLI coding agent powered by the Venice Uncensored API. Works like Claude Code — natural language commands, file operations, shell execution — with a pure ReAct loop.

## Install

```bash
cd Uncensored-Agent-CLI
pip install -e .
```

## Usage

```bash
# First run — configure API key
sentry config

# Single-shot mode
sentry run "create a Python script that prints hello world"

# Interactive chat
sentry chat

# View/edit config
sentry config
sentry config model venice-uncensored
```

## Commands

| Command | Description |
|---------|-------------|
| `sentry run "<prompt>"` | Execute a single task |
| `sentry chat` | Interactive REPL mode |
| `sentry config` | View/edit configuration |
| `sentry --version` | Show version |

## Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/history` | Show token usage stats |
| `/model` | Show current model |
| `/exit` | Exit chat |

## Configuration

Config is stored at `~/.sentry/config.json`. Environment variable `SENTRY_API_KEY` overrides the config file.
