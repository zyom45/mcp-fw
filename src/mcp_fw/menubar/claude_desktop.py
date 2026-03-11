"""Claude Desktop configuration sync for mcp-fw."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CLAUDE_CONFIG = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
LOG_DIR = Path.home() / "Library/Logs/mcp-fw"


def _get_python_path() -> str:
    """Return the path to the current Python interpreter."""
    return sys.executable


def _load_claude_config() -> dict[str, Any]:
    """Load Claude Desktop config, returning an empty mapping when absent."""
    if not CLAUDE_CONFIG.exists():
        return {}
    return json.loads(CLAUDE_CONFIG.read_text())


def _write_claude_config(config: dict[str, Any]) -> Path:
    """Persist Claude Desktop config."""
    CLAUDE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_CONFIG.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    return CLAUDE_CONFIG


def _build_mcp_server_entry(
    server_name: str,
    server_cfg: dict[str, Any],
    policy_path: Path,
    python_path: str | None = None,
) -> dict[str, Any]:
    """Build a single mcpServers entry for Claude Desktop config."""
    python = python_path or _get_python_path()
    log_file = LOG_DIR / f"{server_name}.log"

    return {
        "command": python,
        "args": [
            "-m", "mcp_fw",
            "--config", str(policy_path),
            "--server", server_name,
            "--log-file", str(log_file),
        ],
    }


def sync_policy_to_claude(
    policy_path: Path,
    servers: dict[str, dict[str, Any]],
    python_path: str | None = None,
) -> Path:
    """Sync mcp-fw policy to Claude Desktop config.

    - Generates mcpServers entries with key "{server_name}-fw"
    - Preserves existing non-mcp-fw entries and preferences
    - Returns the config file path
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    config = _load_claude_config()
    existing_servers = config.get("mcpServers", {})

    # Remove old mcp-fw entries (keys ending with "-fw")
    preserved = {k: v for k, v in existing_servers.items() if not k.endswith("-fw")}

    # Generate new mcp-fw entries
    for name, cfg in servers.items():
        key = f"{name}-fw"
        preserved[key] = _build_mcp_server_entry(
            name, cfg, policy_path, python_path
        )

    config["mcpServers"] = preserved

    return _write_claude_config(config)


def remove_mcp_fw_from_claude(server_name: str | None = None) -> tuple[Path, int]:
    """Remove mcp-fw managed Claude Desktop entries.

    When ``server_name`` is provided, only ``{server_name}-fw`` is removed.
    Otherwise all ``*-fw`` entries are removed.
    """
    config = _load_claude_config()
    existing_servers = config.get("mcpServers", {})
    if not existing_servers:
        return CLAUDE_CONFIG, 0

    if server_name is None:
        keys_to_remove = {key for key in existing_servers if key.endswith("-fw")}
    else:
        keys_to_remove = {f"{server_name}-fw"} if f"{server_name}-fw" in existing_servers else set()

    if not keys_to_remove:
        return CLAUDE_CONFIG, 0

    config["mcpServers"] = {
        key: value
        for key, value in existing_servers.items()
        if key not in keys_to_remove
    }
    _write_claude_config(config)
    return CLAUDE_CONFIG, len(keys_to_remove)
