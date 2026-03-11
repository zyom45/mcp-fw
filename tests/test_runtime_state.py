"""Tests for runtime state tracking."""

from __future__ import annotations

import json
from pathlib import Path

import mcp_fw.runtime_state as runtime_state


def test_write_and_read_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime_state, "STATE_DIR", tmp_path)
    monkeypatch.setattr(runtime_state.os, "getpid", lambda: 4321)
    monkeypatch.setattr(runtime_state, "_pid_is_running", lambda pid: pid == 4321)

    runtime_state.write_state("filesystem", config_path="/tmp/policy.yaml", log_file="/tmp/fs.log")
    state = runtime_state.read_state("filesystem")

    assert state is not None
    assert state["pid"] == 4321
    assert state["config_path"] == "/tmp/policy.yaml"
    assert state["log_file"] == "/tmp/fs.log"


def test_read_state_removes_stale_entry(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime_state, "STATE_DIR", tmp_path)
    path = runtime_state.get_state_path("filesystem")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pid": 999}))
    monkeypatch.setattr(runtime_state, "_pid_is_running", lambda _pid: False)

    assert runtime_state.read_state("filesystem") is None
    assert not path.exists()


def test_read_state_removes_corrupt_entry(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime_state, "STATE_DIR", tmp_path)
    path = runtime_state.get_state_path("filesystem")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{invalid json")

    assert runtime_state.read_state("filesystem") is None
    assert not path.exists()


def test_clear_state_removes_corrupt_entry(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime_state, "STATE_DIR", tmp_path)
    path = runtime_state.get_state_path("filesystem")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{invalid json")

    runtime_state.clear_state("filesystem", pid=999)

    assert not path.exists()
