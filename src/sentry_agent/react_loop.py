"""Core ReAct loop orchestrator."""

from __future__ import annotations

from typing import Any

from sentry_agent import display
from sentry_agent.actions import all_actions, dispatch, get_action, load_all
from sentry_agent.actions.base import ActionResult, RiskLevel
from sentry_agent.api_client import VeniceClient
from sentry_agent.context import ConversationContext
from sentry_agent.exceptions import (
    MaxIterationsError,
    ParseError,
    SafetyAbortError,
    SentryError,
)
from sentry_agent.parser import extract_json
from sentry_agent.safety import check_action
from sentry_agent.system_prompt import build_system_prompt


def run(prompt: str, config: dict[str, Any], stream: bool = True) -> str | None:
    """Execute a single ReAct loop for a user prompt.

    Returns the final message from the 'done' action, or None if max iterations hit.
    """
    load_all()

    client = VeniceClient(config)
    system_prompt = build_system_prompt()
    ctx = ConversationContext(system_prompt)
    ctx.add_user(prompt)

    max_iterations = config.get("max_react_iterations", 25)
    safety_enabled = config.get("safety_confirm_destructive", True)
    parse_errors = 0
    max_parse_errors = 3

    for iteration in range(1, max_iterations + 1):
        display.show_iteration(iteration, max_iterations)

        # Call Venice API
        messages = ctx.get_messages()
        try:
            if stream:
                raw_response = display.show_stream(client.stream(messages))
            else:
                raw_response = client.complete(messages)
        except SentryError as exc:
            display.show_error(str(exc))
            return None

        ctx.add_assistant(raw_response)
        ctx.update_usage(client.last_usage)

        # Parse JSON response
        try:
            parsed = extract_json(raw_response)
            parse_errors = 0
        except ParseError as exc:
            parse_errors += 1
            display.show_error(f"Parse error ({parse_errors}/{max_parse_errors}): {exc}")
            if parse_errors >= max_parse_errors:
                display.show_error("Too many parse errors, aborting.")
                return None
            # Feed correction back to LLM
            ctx.add_user(
                "Your response was not valid JSON. You MUST respond with a JSON object like: "
                '{"thought": "...", "action": {"name": "...", "args": {...}}}'
                "\nPlease try again."
            )
            continue

        # Extract thought and action
        thought = parsed.get("thought", "")
        action_data = parsed.get("action", {})
        action_name = action_data.get("name", "")
        action_args = action_data.get("args", {})

        if thought:
            display.show_thought(thought)

        if not action_name:
            ctx.add_user(
                "Your response is missing an action. Respond with JSON containing "
                '"action": {"name": "action_name", "args": {...}}'
            )
            continue

        # Handle 'done' action
        if action_name == "done":
            message = action_args.get("message", "Task completed.")
            display.show_final(message)
            return message

        # Display and execute action
        display.show_action(action_name, action_args)

        # Safety check
        try:
            action = get_action(action_name)
            check_action(
                action_name,
                action_args,
                action.risk_level,
                display.show_confirm,
                safety_enabled,
            )
        except SafetyAbortError:
            ctx.add_user(f"The user declined the '{action_name}' action. Try a different approach or ask the user what they'd prefer.")
            continue
        except SentryError as exc:
            ctx.add_user(f"Error: {exc}")
            continue

        # Execute action
        try:
            result: ActionResult = dispatch(action_name, action_args)
        except SentryError as exc:
            result = ActionResult(output="", success=False, error=str(exc))

        # Display result
        if result.success:
            display.show_result(result.output)
        else:
            display.show_error(result.error or "Action failed with no error message")

        display.console.print()  # gap between action cycles

        # Feed result back to LLM
        feedback = result.output if result.success else f"ERROR: {result.error}\n{result.output}"
        ctx.add_user(f"Action result:\n{feedback}")

    display.show_error(f"Reached maximum iterations ({max_iterations})")
    return None


def chat_loop(config: dict[str, Any]) -> None:
    """Interactive REPL chat mode."""
    load_all()

    client = VeniceClient(config)
    system_prompt = build_system_prompt()
    ctx = ConversationContext(system_prompt)
    stream = config.get("stream", True)
    max_iterations = config.get("max_react_iterations", 25)
    safety_enabled = config.get("safety_confirm_destructive", True)

    display.show_welcome()

    while True:
        try:
            user_input = display.show_input()
        except (EOFError, KeyboardInterrupt):
            display.console.print("\n[dim]Bye![/dim]")
            break

        if not user_input:
            continue

        # Slash commands
        if user_input.startswith("/"):
            cmd = user_input.lower().split()[0]
            if cmd in ("/exit", "/quit", "/q"):
                display.console.print("[dim]Bye![/dim]")
                break
            elif cmd == "/clear":
                ctx.clear()
                display.show_info("Conversation cleared.")
                continue
            elif cmd == "/help":
                display.console.print()
                display.console.print("  [bold yellow]Commands[/bold yellow]")
                display.console.print()
                display.console.print("  [dim]/help[/dim]     Show this help")
                display.console.print("  [dim]/clear[/dim]    Clear conversation history")
                display.console.print("  [dim]/history[/dim]  Show message count and token estimate")
                display.console.print("  [dim]/model[/dim]    Show current model")
                display.console.print("  [dim]/exit[/dim]     Exit chat")
                display.console.print()
                continue
            elif cmd == "/history":
                tokens = ctx.estimated_tokens()
                display.show_info(
                    f"Messages: {ctx.message_count()}, "
                    f"Est. tokens: {tokens:,}, "
                    f"API prompt tokens: {ctx.total_prompt_tokens:,}, "
                    f"API completion tokens: {ctx.total_completion_tokens:,}"
                )
                continue
            elif cmd == "/model":
                display.show_info(f"Model: {config['model']}")
                continue
            else:
                display.show_error(f"Unknown command: {cmd}")
                continue

        # Run agent loop for this message
        ctx.add_user(user_input)
        parse_errors = 0
        max_parse_errors = 3

        for iteration in range(1, max_iterations + 1):
            display.show_iteration(iteration, max_iterations)

            messages = ctx.get_messages()
            try:
                if stream:
                    raw_response = display.show_stream(client.stream(messages))
                else:
                    raw_response = client.complete(messages)
            except SentryError as exc:
                display.show_error(str(exc))
                break

            ctx.add_assistant(raw_response)
            ctx.update_usage(client.last_usage)

            try:
                parsed = extract_json(raw_response)
                parse_errors = 0
            except ParseError as exc:
                parse_errors += 1
                display.show_error(f"Parse error ({parse_errors}/{max_parse_errors}): {exc}")
                if parse_errors >= max_parse_errors:
                    display.show_error("Too many parse errors.")
                    break
                ctx.add_user(
                    "Your response was not valid JSON. Respond with: "
                    '{"thought": "...", "action": {"name": "...", "args": {...}}}'
                )
                continue

            thought = parsed.get("thought", "")
            action_data = parsed.get("action", {})
            action_name = action_data.get("name", "")
            action_args = action_data.get("args", {})

            if thought:
                display.show_thought(thought)

            if not action_name:
                ctx.add_user(
                    "Missing action in your response. Include "
                    '"action": {"name": "...", "args": {...}}'
                )
                continue

            if action_name == "done":
                message = action_args.get("message", "Done.")
                display.show_final(message)
                break

            display.show_action(action_name, action_args)

            try:
                action = get_action(action_name)
                check_action(action_name, action_args, action.risk_level, display.show_confirm, safety_enabled)
            except SafetyAbortError:
                ctx.add_user(f"User declined '{action_name}'. Try another approach.")
                continue
            except SentryError as exc:
                ctx.add_user(f"Error: {exc}")
                continue

            try:
                result = dispatch(action_name, action_args)
            except SentryError as exc:
                result = ActionResult(output="", success=False, error=str(exc))

            if result.success:
                display.show_result(result.output)
            else:
                display.show_error(result.error or "Action failed")

            display.console.print()  # gap between action cycles

            feedback = result.output if result.success else f"ERROR: {result.error}\n{result.output}"
            ctx.add_user(f"Action result:\n{feedback}")
        else:
            display.show_error(f"Reached max iterations ({max_iterations})")
