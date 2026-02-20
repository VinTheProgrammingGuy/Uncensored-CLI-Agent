"""Custom exception hierarchy for Sentry Agent."""


class SentryError(Exception):
    """Base exception for all Sentry Agent errors."""


class ConfigError(SentryError):
    """Configuration loading or validation error."""


class APIError(SentryError):
    """Venice API communication error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(APIError):
    """API rate limit exceeded (429)."""

    def __init__(self, message: str = "Rate limit exceeded, retrying..."):
        super().__init__(message, status_code=429)


class AuthError(APIError):
    """API authentication failure (401/403)."""

    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, status_code=401)


class ParseError(SentryError):
    """Failed to parse LLM JSON response."""


class ActionError(SentryError):
    """Action execution failure."""


class SafetyAbortError(SentryError):
    """User declined a dangerous action."""


class MaxIterationsError(SentryError):
    """ReAct loop exceeded maximum iterations."""
