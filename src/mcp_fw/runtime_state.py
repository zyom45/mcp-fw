"""Process state tracking for running mcp-fw proxy instances."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Iterator

STATE_DIR = Path.home() / "Library/Application Support/mcp-fw/state"


def get_state_dir() -> Path:
    """Return the preferred writable directory for runtime state."""
    override = os.environ.get("MCP_FW_STATE_DIR")
    if override:
        return Path(override)

    current = STATE_DIR
    while not current.exists() and current != current.parent:
        current = current.parent
    if os.access(current, os.W_OK):
        return STATE_DIR
    return Path(tempfile.gettempdir()) / "mcp-fw" / "state"


def get_state_path(server_name: str) -> Path:
    """Return the state file path for a server."""
    safe_name = server_name.replace("/", "_")
    return get_state_dir() / f"{safe_name}.json"


def _pid_is_running(pid: int) -> bool:
    """Return whether a process is still alive."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_state(server_name: str) -> dict[str, Any] | None:
    """Load state for a server, removing stale entries automatically."""
    path = get_state_path(server_name)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text())
    except JSONDecodeError:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return None
    pid = data.get("pid")
    if not isinstance(pid, int) or not _pid_is_running(pid):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return None
    return data


def write_state(server_name: str, *, config_path: str, log_file: str | None) -> dict[str, Any]:
    """Persist state for the current process."""
    state_dir = get_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "server": server_name,
        "pid": os.getpid(),
        "config_path": config_path,
        "log_file": log_file,
    }
    get_state_path(server_name).write_text(json.dumps(state, indent=2) + "\n")
    return state


def clear_state(server_name: str, pid: int | None = None) -> None:
    """Remove a server state file, optionally only if it belongs to *pid*."""
    path = get_state_path(server_name)
    if not path.exists():
        return
    if pid is not None:
        try:
            current = json.loads(path.read_text())
        except JSONDecodeError:
            path.unlink()
            return
        if current.get("pid") != pid:
            return
    path.unlink()


@contextmanager
def managed_state(server_name: str, *, config_path: str, log_file: str | None) -> Iterator[dict[str, Any]]:
    """Write and later clean up process state for a running proxy."""
    state = write_state(server_name, config_path=config_path, log_file=log_file)
    try:
        yield state
    finally:
        clear_state(server_name, pid=state["pid"])
