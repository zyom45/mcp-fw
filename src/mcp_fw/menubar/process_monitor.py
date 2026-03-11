"""Process monitoring for mcp-fw proxy instances."""

from __future__ import annotations

import enum
import os
import signal
import subprocess


class ServerStatus(enum.Enum):
    RUNNING = "running"
    STOPPED = "stopped"


def check_server_status(server_name: str) -> ServerStatus:
    """Check if an mcp-fw proxy for the given server is running."""
    if find_server_pids(server_name):
        return ServerStatus.RUNNING
    return ServerStatus.STOPPED


def find_server_pids(server_name: str) -> list[int]:
    """Return running mcp-fw PIDs for the given server, excluding self."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"mcp_fw.*--server.*{server_name}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            current_pid = os.getpid()
            return [
                int(raw_pid)
                for raw_pid in result.stdout.splitlines()
                if raw_pid.strip() and int(raw_pid) != current_pid
            ]
    except (subprocess.TimeoutExpired, OSError):
        pass
    return []


def stop_server(server_name: str) -> int:
    """Terminate running mcp-fw proxy processes for the given server."""
    pids = find_server_pids(server_name)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    return len(pids)
