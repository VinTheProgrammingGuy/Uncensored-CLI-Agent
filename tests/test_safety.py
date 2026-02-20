"""Tests for the safety module."""

import pytest

from sentry_agent.actions.base import RiskLevel
from sentry_agent.exceptions import SafetyAbortError
from sentry_agent.safety import check_action, _matches_dangerous


class TestDangerousPatterns:
    def test_rm_rf(self):
        assert _matches_dangerous("rm -rf /")

    def test_git_force_push(self):
        assert _matches_dangerous("git push origin main --force")

    def test_git_reset_hard(self):
        assert _matches_dangerous("git reset --hard HEAD~3")

    def test_drop_table(self):
        assert _matches_dangerous("DROP TABLE users;")

    def test_safe_command(self):
        assert not _matches_dangerous("ls -la")

    def test_safe_git(self):
        assert not _matches_dangerous("git status")

    def test_echo(self):
        assert not _matches_dangerous("echo hello world")


class TestCheckAction:
    def test_safe_action_passes(self):
        check_action("read_file", {"path": "test.txt"}, RiskLevel.SAFE, lambda m: False)

    def test_dangerous_pattern_confirmed(self):
        check_action(
            "run_shell",
            {"command": "rm -rf /tmp/test"},
            RiskLevel.MODERATE,
            lambda m: True,  # user confirms
        )

    def test_dangerous_pattern_declined(self):
        with pytest.raises(SafetyAbortError):
            check_action(
                "run_shell",
                {"command": "rm -rf /tmp/test"},
                RiskLevel.MODERATE,
                lambda m: False,  # user declines
            )

    def test_safety_disabled(self):
        # Should not raise even with dangerous command when safety is off
        check_action(
            "run_shell",
            {"command": "rm -rf /"},
            RiskLevel.DANGEROUS,
            lambda m: False,
            safety_enabled=False,
        )
