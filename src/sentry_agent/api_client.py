"""Venice API client — requests + SSE streaming."""

from __future__ import annotations

import json
import time
from typing import Any, Iterator

import requests

from sentry_agent.exceptions import APIError, AuthError, RateLimitError

RETRYABLE_CODES = {429, 503, 504}
MAX_RETRIES = 3
BASE_BACKOFF = 1.0


class VeniceClient:
    """HTTP client for the Venice uncensored chat completions API."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.base_url = config["base_url"].rstrip("/")
        self.api_key = config["api_key"]
        self.model = config["model"]
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 4096)
        self.endpoint = f"{self.base_url}/chat/completions"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        self.last_usage: dict[str, int] | None = None

    def _build_body(self, messages: list[dict], stream: bool = False) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
            "venice_parameters": {
                "include_venice_system_prompt": False,
            },
        }

    def complete(self, messages: list[dict]) -> str:
        """Non-streaming completion. Returns assistant content."""
        body = self._build_body(messages, stream=False)

        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.post(
                    self.endpoint, json=body, timeout=(10, 120)
                )
            except requests.ConnectionError as exc:
                raise APIError(f"Connection failed: {exc}") from exc
            except requests.Timeout as exc:
                raise APIError(f"Request timed out: {exc}") from exc

            if resp.status_code == 200:
                data = resp.json()
                self.last_usage = data.get("usage")
                return data["choices"][0]["message"]["content"]

            if resp.status_code in (401, 403):
                raise AuthError(f"Authentication failed ({resp.status_code})")

            if resp.status_code in RETRYABLE_CODES:
                if attempt < MAX_RETRIES - 1:
                    wait = BASE_BACKOFF * (2 ** attempt)
                    time.sleep(wait)
                    continue
                raise RateLimitError(f"Still failing after {MAX_RETRIES} retries")

            raise APIError(f"API error {resp.status_code}: {resp.text[:500]}", resp.status_code)

        raise APIError("Exhausted retries")

    def stream(self, messages: list[dict]) -> Iterator[str]:
        """SSE streaming completion. Yields content deltas."""
        body = self._build_body(messages, stream=True)

        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.post(
                    self.endpoint, json=body, stream=True, timeout=(10, 120)
                )
            except requests.ConnectionError as exc:
                raise APIError(f"Connection failed: {exc}") from exc
            except requests.Timeout as exc:
                raise APIError(f"Request timed out: {exc}") from exc

            if resp.status_code == 200:
                yield from self._parse_sse(resp)
                return

            if resp.status_code in (401, 403):
                raise AuthError(f"Authentication failed ({resp.status_code})")

            if resp.status_code in RETRYABLE_CODES:
                if attempt < MAX_RETRIES - 1:
                    wait = BASE_BACKOFF * (2 ** attempt)
                    time.sleep(wait)
                    continue
                raise RateLimitError(f"Still failing after {MAX_RETRIES} retries")

            raise APIError(f"API error {resp.status_code}: {resp.text[:500]}", resp.status_code)

    def _parse_sse(self, resp: requests.Response) -> Iterator[str]:
        """Parse Server-Sent Events from streaming response."""
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data.strip() == "[DONE]":
                return
            try:
                chunk = json.loads(data)
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content")
                if content:
                    yield content
                # Capture usage from the final chunk if present
                usage = chunk.get("usage")
                if usage:
                    self.last_usage = usage
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
