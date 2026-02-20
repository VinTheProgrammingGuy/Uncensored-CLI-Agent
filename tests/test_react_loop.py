"""Tests for the ReAct loop (mocked API calls)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from sentry_agent.react_loop import run
from sentry_agent.actions import load_all

load_all()


@pytest.fixture
def mock_config():
    return {
        "api_key": "test-key",
        "model": "venice-uncensored",
        "base_url": "https://api.venice.ai/api/v1",
        "temperature": 0.3,
        "max_tokens": 4096,
        "stream": False,
        "safety_confirm_destructive": True,
        "max_react_iterations": 5,
    }


class TestReactLoop:
    @patch("sentry_agent.react_loop.VeniceClient")
    def test_immediate_done(self, MockClient, mock_config):
        """Agent immediately returns done."""
        instance = MockClient.return_value
        instance.complete.return_value = json.dumps({
            "thought": "The user asked me to say hello",
            "action": {"name": "done", "args": {"message": "Hello!"}}
        })
        instance.last_usage = {"prompt_tokens": 100, "completion_tokens": 50}

        result = run("say hello", mock_config, stream=False)
        assert result == "Hello!"

    @patch("sentry_agent.react_loop.VeniceClient")
    def test_read_then_done(self, MockClient, mock_config, tmp_dir):
        """Agent reads a file then reports done."""
        test_file = tmp_dir / "test.txt"
        test_file.write_text("hello world")

        responses = [
            json.dumps({
                "thought": "I need to read the file",
                "action": {"name": "read_file", "args": {"path": str(test_file)}}
            }),
            json.dumps({
                "thought": "The file contains hello world",
                "action": {"name": "done", "args": {"message": "The file says: hello world"}}
            }),
        ]
        instance = MockClient.return_value
        instance.complete.side_effect = responses
        instance.last_usage = {"prompt_tokens": 100, "completion_tokens": 50}

        result = run("what is in test.txt?", mock_config, stream=False)
        assert "hello world" in result

    @patch("sentry_agent.react_loop.VeniceClient")
    def test_max_iterations(self, MockClient, mock_config):
        """Agent loops forever without done → hits max iterations."""
        instance = MockClient.return_value
        instance.complete.return_value = json.dumps({
            "thought": "Still thinking",
            "action": {"name": "list_directory", "args": {"path": "."}}
        })
        instance.last_usage = {"prompt_tokens": 100, "completion_tokens": 50}

        mock_config["max_react_iterations"] = 3
        result = run("infinite loop test", mock_config, stream=False)
        assert result is None
