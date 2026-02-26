"""YAML policy read/write with comment preservation via ruamel.yaml."""

from __future__ import annotations

import fcntl
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

# Effects that can be toggled in the menu (PURE is implicit, not user-facing)
TOGGLEABLE_EFFECTS = ("FS", "IO", "NET", "PROC", "TIME", "RAND")


class PolicyManager:
    """Manages reading and writing the mcp-fw policy YAML file."""

    def __init__(self, policy_path: str | Path) -> None:
        self.path = Path(policy_path)
        self._yaml = YAML()
        self._yaml.preserve_quotes = True

    def _load(self) -> dict[str, Any]:
        with open(self.path) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return self._yaml.load(f) or {}
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def _save(self, data: dict[str, Any]) -> None:
        with open(self.path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                self._yaml.dump(data, f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def server_names(self) -> list[str]:
        data = self._load()
        return list(data.get("servers", {}).keys())

    def load_all_servers(self) -> dict[str, dict[str, Any]]:
        """Return dict of {server_name: server_config} for all servers."""
        data = self._load()
        return dict(data.get("servers", {}))

    def get_server_config(self, server: str) -> dict[str, Any]:
        data = self._load()
        return dict(data["servers"][server])

    def get_server_effects(self, server: str) -> tuple[list[str], list[str]]:
        """Return (allow, deny) lists for a server."""
        cfg = self.get_server_config(server)
        allow = list(cfg.get("allow", []))
        deny = list(cfg.get("deny", []))
        return allow, deny

    def is_effect_enabled(self, server: str, effect: str) -> bool:
        """Check if an effect is effectively allowed for a server.

        - If allow is empty (all permitted), effect is enabled unless in deny.
        - If allow is explicit, effect must be in allow and not in deny.
        """
        allow, deny = self.get_server_effects(server)
        if effect in deny:
            return False
        if not allow:  # empty = all allowed
            return True
        return effect in allow

    def update_server_effects(self, server: str, effect: str, enabled: bool) -> None:
        """Toggle an effect for a server in the policy file.

        Logic:
        - allow empty (all permitted): toggle deny list only
        - allow explicit: toggle both allow and deny lists
        """
        data = self._load()
        cfg = data["servers"][server]

        allow = list(cfg.get("allow") or [])
        deny = list(cfg.get("deny") or [])

        if not allow:
            # All effects allowed by default — use deny to restrict
            if enabled:
                if effect in deny:
                    deny.remove(effect)
            else:
                if effect not in deny:
                    deny.append(effect)
        else:
            # Explicit allow list
            if enabled:
                if effect not in allow:
                    allow.append(effect)
                if effect in deny:
                    deny.remove(effect)
            else:
                if effect in allow:
                    allow.remove(effect)
                if effect not in deny:
                    deny.append(effect)

        cfg["allow"] = allow
        cfg["deny"] = deny
        self._save(data)

    def get_tool_overrides(self, server: str) -> dict[str, list[str]]:
        cfg = self.get_server_config(server)
        return dict(cfg.get("tool_overrides", {}))
