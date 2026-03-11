"""Tests for CLI argument routing and help output."""

from __future__ import annotations

import pytest

from mcp_fw import cli


def test_normalize_argv_preserves_top_level_help() -> None:
    assert cli._normalize_argv(["-h"]) == ["-h"]
    assert cli._normalize_argv(["--help"]) == ["--help"]


def test_normalize_argv_keeps_legacy_run_flags() -> None:
    assert cli._normalize_argv(["--config", "policy.yaml", "--server", "fs"]) == [
        "run",
        "--config",
        "policy.yaml",
        "--server",
        "fs",
    ]


def test_main_help_lists_subcommands(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["-h"])

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "run" in captured.out
    assert "stop" in captured.out
    assert "claude-remove" in captured.out
    assert "menubar" in captured.out
    assert "Legacy shorthand" in captured.out
