"""Tests for the multi-stage JSON parser."""

import pytest
from sentry_agent.parser import extract_json
from sentry_agent.exceptions import ParseError


class TestExtractJson:
    def test_direct_json(self):
        raw = '{"thought": "thinking", "action": {"name": "done", "args": {}}}'
        result = extract_json(raw)
        assert result["thought"] == "thinking"
        assert result["action"]["name"] == "done"

    def test_json_with_whitespace(self):
        raw = '  \n  {"thought": "hi", "action": {"name": "done", "args": {}}}  \n  '
        result = extract_json(raw)
        assert result["thought"] == "hi"

    def test_markdown_code_fence(self):
        raw = '```json\n{"thought": "x", "action": {"name": "done", "args": {}}}\n```'
        result = extract_json(raw)
        assert result["thought"] == "x"

    def test_markdown_fence_no_lang(self):
        raw = '```\n{"thought": "y", "action": {"name": "done", "args": {}}}\n```'
        result = extract_json(raw)
        assert result["thought"] == "y"

    def test_json_with_surrounding_text(self):
        raw = 'Here is my response:\n{"thought": "test", "action": {"name": "read_file", "args": {"path": "foo.txt"}}}\nDone!'
        result = extract_json(raw)
        assert result["action"]["name"] == "read_file"

    def test_nested_json(self):
        raw = '{"thought": "need to write", "action": {"name": "write_file", "args": {"path": "a.py", "content": "x = {1: 2}"}}}'
        result = extract_json(raw)
        assert result["action"]["args"]["content"] == "x = {1: 2}"

    def test_invalid_json_raises(self):
        with pytest.raises(ParseError):
            extract_json("This is not JSON at all, just plain text without any braces")

    def test_empty_string_raises(self):
        with pytest.raises(ParseError):
            extract_json("")

    def test_partial_json_raises(self):
        with pytest.raises(ParseError):
            extract_json('{"thought": "incomplete')

    def test_array_not_dict_raises(self):
        with pytest.raises(ParseError):
            extract_json("[1, 2, 3]")

    def test_json_with_escaped_quotes(self):
        raw = r'{"thought": "he said \"hello\"", "action": {"name": "done", "args": {}}}'
        result = extract_json(raw)
        assert "hello" in result["thought"]
