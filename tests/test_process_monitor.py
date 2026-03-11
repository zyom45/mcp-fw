"""Tests for process monitoring helpers."""

from __future__ import annotations

import signal

import mcp_fw.menubar.process_monitor as process_monitor


class _CompletedProcess:
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


def test_find_server_pids_filters_out_current_process(monkeypatch) -> None:
    monkeypatch.setattr(process_monitor.os, "getpid", lambda: 200)

    def fake_run(*_args, **_kwargs):
        return _CompletedProcess(0, "100\n200\n300\n")

    monkeypatch.setattr(process_monitor.subprocess, "run", fake_run)

    assert process_monitor.find_server_pids("filesystem") == [100, 300]


def test_check_server_status_uses_find_server_pids(monkeypatch) -> None:
    monkeypatch.setattr(process_monitor, "find_server_pids", lambda _server: [1234])
    assert process_monitor.check_server_status("filesystem") == process_monitor.ServerStatus.RUNNING

    monkeypatch.setattr(process_monitor, "find_server_pids", lambda _server: [])
    assert process_monitor.check_server_status("filesystem") == process_monitor.ServerStatus.STOPPED


def test_stop_server_sends_sigterm(monkeypatch) -> None:
    monkeypatch.setattr(process_monitor, "find_server_pids", lambda _server: [111, 222])
    killed: list[tuple[int, int]] = []

    def fake_kill(pid: int, sig: int) -> None:
        killed.append((pid, sig))

    monkeypatch.setattr(process_monitor.os, "kill", fake_kill)

    assert process_monitor.stop_server("filesystem") == 2
    assert killed == [(111, signal.SIGTERM), (222, signal.SIGTERM)]
