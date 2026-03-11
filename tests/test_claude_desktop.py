"""Tests for Claude Desktop config helpers."""

from __future__ import annotations

import json
from pathlib import Path

import mcp_fw.menubar.claude_desktop as claude_desktop
from mcp_fw.menubar.claude_desktop import remove_mcp_fw_from_claude, sync_policy_to_claude


def test_sync_policy_to_claude_replaces_only_fw_entries(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "claude_desktop_config.json"
    log_dir = tmp_path / "logs"
    monkeypatch.setattr(claude_desktop, "CLAUDE_CONFIG", config_path)
    monkeypatch.setattr(claude_desktop, "LOG_DIR", log_dir)

    config_path.write_text(json.dumps({
        "theme": "dark",
        "mcpServers": {
            "existing": {"command": "node", "args": ["server.js"]},
            "old-fw": {"command": "python", "args": ["-m", "mcp_fw"]},
        },
    }))

    written_path = sync_policy_to_claude(
        tmp_path / "policy.yaml",
        {"filesystem": {"command": "npx", "args": ["@scope/server"]}},
        "/usr/bin/python3",
    )

    assert written_path == config_path
    saved = json.loads(config_path.read_text())
    assert saved["theme"] == "dark"
    assert "existing" in saved["mcpServers"]
    assert "old-fw" not in saved["mcpServers"]
    assert saved["mcpServers"]["filesystem-fw"]["command"] == "/usr/bin/python3"


def test_remove_mcp_fw_from_claude_removes_all_fw_entries(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "claude_desktop_config.json"
    monkeypatch.setattr(claude_desktop, "CLAUDE_CONFIG", config_path)

    config_path.write_text(json.dumps({
        "mcpServers": {
            "filesystem-fw": {"command": "python"},
            "github-fw": {"command": "python"},
            "preserve": {"command": "node"},
        },
    }))

    written_path, removed = remove_mcp_fw_from_claude()

    assert written_path == config_path
    assert removed == 2
    saved = json.loads(config_path.read_text())
    assert saved["mcpServers"] == {"preserve": {"command": "node"}}


def test_remove_mcp_fw_from_claude_removes_single_server(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "claude_desktop_config.json"
    monkeypatch.setattr(claude_desktop, "CLAUDE_CONFIG", config_path)

    config_path.write_text(json.dumps({
        "mcpServers": {
            "filesystem-fw": {"command": "python"},
            "github-fw": {"command": "python"},
        },
    }))

    _, removed = remove_mcp_fw_from_claude("filesystem")

    assert removed == 1
    saved = json.loads(config_path.read_text())
    assert "filesystem-fw" not in saved["mcpServers"]
    assert "github-fw" in saved["mcpServers"]
