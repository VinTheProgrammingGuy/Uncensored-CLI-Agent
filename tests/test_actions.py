"""Tests for action executors."""

import os
from pathlib import Path

import pytest

from sentry_agent.actions import load_all, dispatch
from sentry_agent.actions.base import ActionResult

# Ensure all actions are registered
load_all()


class TestReadFile:
    def test_read_existing(self, tmp_dir):
        f = tmp_dir / "hello.txt"
        f.write_text("line1\nline2\nline3")
        result = dispatch("read_file", {"path": str(f)})
        assert result.success
        assert "line1" in result.output
        assert "line2" in result.output

    def test_read_with_offset(self, tmp_dir):
        f = tmp_dir / "nums.txt"
        f.write_text("a\nb\nc\nd\ne")
        result = dispatch("read_file", {"path": str(f), "offset": 2, "limit": 2})
        assert result.success
        assert "c" in result.output
        assert "d" in result.output

    def test_read_missing_file(self, tmp_dir):
        result = dispatch("read_file", {"path": str(tmp_dir / "nope.txt")})
        assert not result.success

    def test_read_missing_path_arg(self):
        result = dispatch("read_file", {})
        assert not result.success


class TestWriteFile:
    def test_write_new_file(self, tmp_dir):
        target = tmp_dir / "new.txt"
        result = dispatch("write_file", {"path": str(target), "content": "hello"})
        assert result.success
        assert target.read_text() == "hello"

    def test_write_creates_parents(self, tmp_dir):
        target = tmp_dir / "sub" / "deep" / "file.txt"
        result = dispatch("write_file", {"path": str(target), "content": "nested"})
        assert result.success
        assert target.read_text() == "nested"

    def test_write_overwrite(self, tmp_dir):
        target = tmp_dir / "over.txt"
        target.write_text("old")
        dispatch("write_file", {"path": str(target), "content": "new"})
        assert target.read_text() == "new"


class TestEditFile:
    def test_edit_replace(self, tmp_dir):
        f = tmp_dir / "edit.txt"
        f.write_text("hello world")
        result = dispatch("edit_file", {
            "path": str(f),
            "old_string": "world",
            "new_string": "earth",
        })
        assert result.success
        assert f.read_text() == "hello earth"

    def test_edit_string_not_found(self, tmp_dir):
        f = tmp_dir / "edit2.txt"
        f.write_text("hello world")
        result = dispatch("edit_file", {
            "path": str(f),
            "old_string": "missing",
            "new_string": "replaced",
        })
        assert not result.success


class TestGlobSearch:
    def test_glob_find_py(self, tmp_dir):
        (tmp_dir / "a.py").write_text("x")
        (tmp_dir / "b.txt").write_text("y")
        result = dispatch("glob_search", {"pattern": "*.py", "path": str(tmp_dir)})
        assert result.success
        assert "a.py" in result.output
        assert "b.txt" not in result.output

    def test_glob_no_match(self, tmp_dir):
        result = dispatch("glob_search", {"pattern": "*.xyz", "path": str(tmp_dir)})
        assert "No files" in result.output


class TestGrepSearch:
    def test_grep_finds_pattern(self, tmp_dir):
        (tmp_dir / "test.py").write_text("def hello():\n    pass\ndef world():\n    pass")
        result = dispatch("grep_search", {"pattern": "def \\w+", "path": str(tmp_dir), "glob": "*.py"})
        assert result.success
        assert "hello" in result.output

    def test_grep_no_match(self, tmp_dir):
        (tmp_dir / "test.py").write_text("nothing here")
        result = dispatch("grep_search", {"pattern": "zzzzz", "path": str(tmp_dir)})
        assert "No matches" in result.output


class TestListDir:
    def test_list_dir(self, tmp_dir):
        (tmp_dir / "file.txt").write_text("x")
        (tmp_dir / "subdir").mkdir()
        result = dispatch("list_directory", {"path": str(tmp_dir)})
        assert result.success
        assert "file.txt" in result.output
        assert "subdir" in result.output


class TestRunShell:
    def test_echo(self, tmp_dir):
        result = dispatch("run_shell", {"command": "echo hello"})
        assert result.success
        assert "hello" in result.output

    def test_missing_command(self):
        result = dispatch("run_shell", {})
        assert not result.success
