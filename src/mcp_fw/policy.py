"""YAML policy parsing for mcp-fw.

Policy file format:
```yaml
servers:
  filesystem:
    command: npx
    args: ["@modelcontextprotocol/server-filesystem", "/tmp"]
    allow: [FS, IO]
    deny: [NET]
    tool_overrides:
      special_tool: [FS, NET]
```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from nail_lang import VALID_EFFECTS


@dataclass
class ServerPolicy:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None
    allow: set[str] = field(default_factory=set)
    deny: set[str] = field(default_factory=set)
    tool_overrides: dict[str, list[str]] = field(default_factory=dict)


def _validate_effects(effects: set[str] | list[str], context: str) -> None:
    """Raise ValueError if any effect label is not in VALID_EFFECTS."""
    invalid = set(effects) - VALID_EFFECTS
    if invalid:
        raise ValueError(
            f"Invalid effect(s) in {context}: {sorted(invalid)}. "
            f"Valid effects: {sorted(VALID_EFFECTS)}"
        )


def load_policy(path: str | Path, server_name: str) -> ServerPolicy:
    """Parse a YAML policy file and return the policy for the named server.

    Raises:
        FileNotFoundError: If the policy file doesn't exist.
        KeyError: If the server name is not found in the policy.
        ValueError: If effect labels are invalid.
    """
    path = Path(path)
    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(
            f"Policy file must contain a YAML mapping, got {type(data).__name__}"
        )
    if "servers" not in data or not isinstance(data["servers"], dict):
        raise ValueError("Policy file must contain a 'servers' mapping")

    servers = data.get("servers", {})
    if server_name not in servers:
        raise KeyError(
            f"Server '{server_name}' not found in policy. "
            f"Available: {sorted(servers.keys())}"
        )

    cfg = servers[server_name]

    if "command" not in cfg:
        raise ValueError(f"Server '{server_name}' is missing required 'command' field")

    allow = set(cfg.get("allow", []))
    deny = set(cfg.get("deny", []))
    tool_overrides: dict[str, list[str]] = {}

    _validate_effects(allow, f"servers.{server_name}.allow")
    _validate_effects(deny, f"servers.{server_name}.deny")

    for tool_name, effects in cfg.get("tool_overrides", {}).items():
        _validate_effects(effects, f"servers.{server_name}.tool_overrides.{tool_name}")
        tool_overrides[tool_name] = list(effects)

    return ServerPolicy(
        name=server_name,
        command=cfg["command"],
        args=cfg.get("args", []),
        env=cfg.get("env"),
        allow=allow,
        deny=deny,
        tool_overrides=tool_overrides,
    )


def compute_effective_allowed(policy: ServerPolicy) -> set[str]:
    """Compute the effective set of allowed effects.

    - If ``allow`` is empty, all valid effects are permitted.
    - ``deny`` is always subtracted (deny > allow).
    """
    base = policy.allow if policy.allow else set(VALID_EFFECTS)
    return base - policy.deny
