"""Tests for policy.py — YAML parsing, validation, allow/deny resolution."""

import textwrap
from pathlib import Path

import pytest

from mcp_fw.policy import ServerPolicy, compute_effective_allowed, load_policy


@pytest.fixture()
def policy_file(tmp_path: Path) -> Path:
    p = tmp_path / "policy.yaml"
    p.write_text(textwrap.dedent("""\
        servers:
          fs_server:
            command: npx
            args: ["@modelcontextprotocol/server-filesystem", "/tmp"]
            allow: [FS, IO]
            deny: [NET]
          open_server:
            command: python
            args: ["-m", "some_server"]
          override_server:
            command: node
            args: ["server.js"]
            allow: [FS]
            tool_overrides:
              special_tool: [NET, IO]
    """))
    return p


def test_load_policy_basic(policy_file: Path) -> None:
    policy = load_policy(policy_file, "fs_server")
    assert policy.name == "fs_server"
    assert policy.command == "npx"
    assert policy.args == ["@modelcontextprotocol/server-filesystem", "/tmp"]
    assert policy.allow == {"FS", "IO"}
    assert policy.deny == {"NET"}


def test_load_policy_open_server(policy_file: Path) -> None:
    policy = load_policy(policy_file, "open_server")
    assert policy.allow == set()
    assert policy.deny == set()


def test_load_policy_with_overrides(policy_file: Path) -> None:
    policy = load_policy(policy_file, "override_server")
    assert policy.tool_overrides == {"special_tool": ["NET", "IO"]}


def test_load_policy_missing_server(policy_file: Path) -> None:
    with pytest.raises(KeyError, match="nonexistent"):
        load_policy(policy_file, "nonexistent")


def test_load_policy_invalid_effect(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(textwrap.dedent("""\
        servers:
          bad:
            command: echo
            allow: [FS, INVALID_EFFECT]
    """))
    with pytest.raises(ValueError, match="Invalid effect"):
        load_policy(p, "bad")


def test_load_policy_invalid_deny_effect(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(textwrap.dedent("""\
        servers:
          bad:
            command: echo
            deny: [BOGUS]
    """))
    with pytest.raises(ValueError, match="Invalid effect"):
        load_policy(p, "bad")


def test_load_policy_invalid_override_effect(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(textwrap.dedent("""\
        servers:
          bad:
            command: echo
            tool_overrides:
              my_tool: [FAKE]
    """))
    with pytest.raises(ValueError, match="Invalid effect"):
        load_policy(p, "bad")


def test_load_policy_empty_yaml(tmp_path: Path) -> None:
    p = tmp_path / "empty.yaml"
    p.write_text("")
    with pytest.raises(ValueError, match="YAML mapping"):
        load_policy(p, "any")


def test_load_policy_non_dict_yaml(tmp_path: Path) -> None:
    p = tmp_path / "list.yaml"
    p.write_text("- item1\n- item2\n")
    with pytest.raises(ValueError, match="YAML mapping"):
        load_policy(p, "any")


def test_load_policy_missing_servers_key(tmp_path: Path) -> None:
    p = tmp_path / "noservers.yaml"
    p.write_text("something_else: true\n")
    with pytest.raises(ValueError, match="'servers' mapping"):
        load_policy(p, "any")


def test_load_policy_missing_command(tmp_path: Path) -> None:
    p = tmp_path / "nocmd.yaml"
    p.write_text(textwrap.dedent("""\
        servers:
          bad:
            allow: [FS]
    """))
    with pytest.raises(ValueError, match="missing required 'command'"):
        load_policy(p, "bad")


def test_compute_effective_allowed_with_allow_and_deny() -> None:
    policy = ServerPolicy(name="t", command="echo", allow={"FS", "IO", "NET"}, deny={"NET"})
    assert compute_effective_allowed(policy) == {"FS", "IO"}


def test_compute_effective_allowed_empty_allow() -> None:
    """Empty allow = all effects permitted, minus deny."""
    policy = ServerPolicy(name="t", command="echo", deny={"PROC"})
    result = compute_effective_allowed(policy)
    assert "PROC" not in result
    assert "FS" in result
    assert "IO" in result


def test_compute_effective_allowed_deny_overrides_allow() -> None:
    """deny > allow: if something is in both, it's denied."""
    policy = ServerPolicy(name="t", command="echo", allow={"FS"}, deny={"FS"})
    assert compute_effective_allowed(policy) == set()
