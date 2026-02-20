"""Shared test fixtures."""

import pytest
from pathlib import Path
import tempfile
import os


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as d:
        old_cwd = os.getcwd()
        os.chdir(d)
        yield Path(d)
        os.chdir(old_cwd)


@pytest.fixture
def sample_config():
    """Return a sample config dict."""
    return {
        "api_key": "test-key-123",
        "model": "venice-uncensored",
        "base_url": "https://api.venice.ai/api/v1",
        "temperature": 0.3,
        "max_tokens": 4096,
        "stream": True,
        "safety_confirm_destructive": True,
        "max_react_iterations": 25,
    }
