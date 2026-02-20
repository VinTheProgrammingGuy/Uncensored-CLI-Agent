"""Conversation history manager with token tracking and truncation."""

from __future__ import annotations

from typing import Any


# Rough estimate: 1 token ≈ 4 chars for English text
TOKEN_ESTIMATE_RATIO = 4
MAX_CONTEXT_TOKENS = 28_000  # Leave headroom under 32K limit
KEEP_RECENT_TURNS = 4  # Keep last N user/assistant pairs when truncating


class ConversationContext:
    """Manages the message history for the ReAct loop."""

    def __init__(self, system_prompt: str) -> None:
        self.system_message: dict[str, str] = {"role": "system", "content": system_prompt}
        self.messages: list[dict[str, str]] = []
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self._maybe_truncate()

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def update_usage(self, usage: dict[str, int] | None) -> None:
        if usage:
            self.total_prompt_tokens += usage.get("prompt_tokens", 0)
            self.total_completion_tokens += usage.get("completion_tokens", 0)

    def get_messages(self) -> list[dict[str, str]]:
        return [self.system_message] + self.messages

    def clear(self) -> None:
        self.messages.clear()

    def estimated_tokens(self) -> int:
        total_chars = len(self.system_message["content"])
        for msg in self.messages:
            total_chars += len(msg["content"])
        return total_chars // TOKEN_ESTIMATE_RATIO

    def _maybe_truncate(self) -> None:
        """If approaching context limit, summarize middle messages."""
        if self.estimated_tokens() < MAX_CONTEXT_TOKENS:
            return

        # Keep system prompt + first user message + last KEEP_RECENT_TURNS pairs
        keep_end = KEEP_RECENT_TURNS * 2  # pairs of user+assistant
        if len(self.messages) <= keep_end + 2:
            return

        first_msg = self.messages[0]
        recent = self.messages[-keep_end:]
        middle = self.messages[1:-keep_end]

        # Create a summary of truncated messages
        summary_parts = []
        for msg in middle:
            role = msg["role"]
            content = msg["content"][:200]
            summary_parts.append(f"[{role}]: {content}...")

        summary = "[Earlier conversation truncated]\n" + "\n".join(summary_parts[-5:])

        self.messages = [
            first_msg,
            {"role": "user", "content": summary},
        ] + recent

    def message_count(self) -> int:
        return len(self.messages)
