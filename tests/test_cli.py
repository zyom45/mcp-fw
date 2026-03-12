"""Tests for CLI argument routing and help output."""

from __future__ import annotations

import argparse

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


def test_launch_menubar_without_config_passes_empty_args(monkeypatch) -> None:
    called: list[list[str]] = []

    def fake_main(argv: list[str] | None = None) -> None:
        called.append(argv or [])

    monkeypatch.setattr("mcp_fw.menubar.app.main", fake_main)
    cli._launch_menubar(argparse.Namespace(config=None))

    assert called == [[]]


def test_is_managed_by_pipx_false_without_binary(monkeypatch) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda _name: None)
    assert cli._is_managed_by_pipx("mcp-fw") is False


def test_is_managed_by_pipx_checks_pipx_list(monkeypatch) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda _name: "/usr/bin/pipx")

    class _Result:
        returncode = 0
        stdout = '{"venvs":{"mcp-fw":{}}}'

    monkeypatch.setattr(cli.subprocess, "run", lambda *_args, **_kwargs: _Result())
    assert cli._is_managed_by_pipx("mcp-fw") is True


def test_upgrade_uses_pip_when_not_managed_by_pipx(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_is_managed_by_pipx", lambda _name: False)
    monkeypatch.setattr(cli, "_run_upgrade_command", lambda cmd: 0 if cmd[0] == cli.sys.executable else 1)

    with pytest.raises(SystemExit) as excinfo:
        cli._upgrade(argparse.Namespace())

    assert excinfo.value.code == 0


def test_upgrade_falls_back_to_pip_after_pipx_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_is_managed_by_pipx", lambda _name: True)

    calls: list[list[str]] = []

    def fake_run(cmd: list[str]) -> int:
        calls.append(cmd)
        if cmd[0] == "pipx":
            return 1
        return 0

    monkeypatch.setattr(cli, "_run_upgrade_command", fake_run)

    with pytest.raises(SystemExit) as excinfo:
        cli._upgrade(argparse.Namespace())

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "pipx upgrade failed" in captured.err
    assert calls[0] == ["pipx", "upgrade", "mcp-fw"]
    assert calls[1][0] == cli.sys.executable
