"""Multi-stage JSON extraction from LLM responses."""

from __future__ import annotations

import json
import re
from typing import Any

from sentry_agent.exceptions import ParseError


def extract_json(raw: str) -> dict[str, Any]:
    """Extract a JSON object from LLM output using multiple strategies.

    Returns a dict with at least 'thought' and/or 'action' keys.
    Raises ParseError if all strategies fail.
    """
    text = raw.strip()

    # Strategy 1: Direct parse
    result = _try_parse(text)
    if result is not None:
        return result

    # Strategy 2: Strip markdown code fences
    stripped = _strip_code_fences(text)
    if stripped != text:
        result = _try_parse(stripped)
        if result is not None:
            return result

    # Strategy 3: Regex extract first {...} block (with brace matching)
    block = _extract_json_block(text)
    if block:
        result = _try_parse(block)
        if result is not None:
            return result

    # Strategy 4: Try to find JSON starting after common prefixes
    for prefix in ("Here is", "Sure", "```json", "```"):
        idx = text.lower().find(prefix.lower())
        if idx != -1:
            after = text[idx + len(prefix):].strip()
            block = _extract_json_block(after)
            if block:
                result = _try_parse(block)
                if result is not None:
                    return result

    raise ParseError(f"Could not extract valid JSON from response:\n{text[:500]}")


def _try_parse(text: str) -> dict[str, Any] | None:
    """Attempt json.loads, return dict or None."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences like ```json ... ```."""
    pattern = r"```(?:json)?\s*\n?(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def _extract_json_block(text: str) -> str | None:
    """Extract the first balanced {...} block from text."""
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            if in_string:
                escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None
