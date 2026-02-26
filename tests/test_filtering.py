"""Tests for filtering.py — NAIL pipeline: annotate + filter + gate."""

import mcp.types as types

from mcp_fw.filtering import build_allowed_tools, is_tool_allowed
from mcp_fw.policy import ServerPolicy


def _make_tool(name: str, description: str = "") -> types.Tool:
    return types.Tool(
        name=name,
        description=description,
        inputSchema={"type": "object", "properties": {}},
    )


def test_build_allowed_tools_filters_by_effect() -> None:
    """Tools with NET effect should be excluded when only FS/IO allowed."""
    tools = [
        _make_tool("read_file", "Read a file from disk"),
        _make_tool("http_get", "Fetch a URL via HTTP"),
        _make_tool("log_message", "Log a message to console"),
    ]
    policy = ServerPolicy(
        name="test",
        command="echo",
        allow={"FS", "IO"},
        deny=set(),
    )
    filtered, names = build_allowed_tools(tools, policy)

    assert "read_file" in names
    assert "log_message" in names
    assert "http_get" not in names
    assert len(filtered) == 2


def test_build_allowed_tools_deny_removes() -> None:
    """deny=NET should block NET tools even if allow is empty (all)."""
    tools = [
        _make_tool("read_file", "Read a file from disk"),
        _make_tool("http_get", "Fetch a URL via HTTP"),
    ]
    policy = ServerPolicy(
        name="test",
        command="echo",
        deny={"NET"},
    )
    filtered, names = build_allowed_tools(tools, policy)

    assert "read_file" in names
    assert "http_get" not in names


def test_build_allowed_tools_with_overrides() -> None:
    """tool_overrides should override inferred effects."""
    tools = [
        _make_tool("ambiguous_tool", "Does something"),
    ]
    policy = ServerPolicy(
        name="test",
        command="echo",
        allow={"FS"},
        tool_overrides={"ambiguous_tool": ["FS"]},
    )
    filtered, names = build_allowed_tools(tools, policy)

    assert "ambiguous_tool" in names


def test_build_allowed_tools_override_blocked() -> None:
    """tool_overrides effect outside allow set should be blocked."""
    tools = [
        _make_tool("ambiguous_tool", "Does something"),
    ]
    policy = ServerPolicy(
        name="test",
        command="echo",
        allow={"FS"},
        tool_overrides={"ambiguous_tool": ["NET"]},
    )
    filtered, names = build_allowed_tools(tools, policy)

    assert "ambiguous_tool" not in names


def test_is_tool_allowed() -> None:
    allowed = {"read_file", "log"}
    assert is_tool_allowed("read_file", allowed) is True
    assert is_tool_allowed("http_get", allowed) is False
