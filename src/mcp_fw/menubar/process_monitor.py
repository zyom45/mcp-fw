"""Process monitoring for mcp-fw proxy instances."""

from __future__ import annotations

import enum
import subprocess


class ServerStatus(enum.Enum):
    RUNNING = "running"
    STOPPED = "stopped"


def check_server_status(server_name: str) -> ServerStatus:
    """Check if an mcp-fw proxy for the given server is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"mcp_fw.*--server.*{server_name}"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return ServerStatus.RUNNING
    except (subprocess.TimeoutExpired, OSError):
        pass
    return ServerStatus.STOPPED
