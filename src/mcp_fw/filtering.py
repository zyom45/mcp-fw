"""NAIL integration: annotate MCP tools with effects and filter by policy."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import mcp.types as types
from nail_lang import filter_by_effects, from_mcp, get_tool_effects, to_mcp

from mcp_fw.policy import ServerPolicy, compute_effective_allowed

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolInspection:
    name: str
    inferred_effects: tuple[str, ...]
    effective_effects: tuple[str, ...]
    override_applied: bool
    allowed: bool


def _tools_to_mcp_dicts(backend_tools: list[types.Tool]) -> list[dict[str, Any]]:
    """Convert MCP Tool objects into plain MCP dictionaries."""
    mcp_dicts: list[dict[str, Any]] = []
    for tool in backend_tools:
        mcp_dicts.append({
            "name": tool.name,
            "description": tool.description or "",
            "inputSchema": tool.inputSchema,
        })
    return mcp_dicts


def _annotate_tools(
    backend_tools: list[types.Tool],
    overrides: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Return FC-standard tool dictionaries annotated by NAIL."""
    return from_mcp(_tools_to_mcp_dicts(backend_tools), existing_effects=overrides)


def _extract_effects_by_name(fc_tools: list[dict[str, Any]]) -> dict[str, tuple[str, ...]]:
    """Return a mapping of tool name to sorted effect tuple."""
    effects_by_name: dict[str, tuple[str, ...]] = {}
    for fc in fc_tools:
        fn = fc.get("function", {})
        name = fn.get("name")
        if not name:
            continue
        effects = tuple(sorted(get_tool_effects(fc) or ()))
        effects_by_name[name] = effects
    return effects_by_name


def inspect_tools(
    backend_tools: list[types.Tool],
    policy: ServerPolicy,
) -> list[ToolInspection]:
    """Return per-tool inspection details for operator-facing diagnostics."""
    inferred_fc = _annotate_tools(backend_tools)
    overrides = policy.tool_overrides if policy.tool_overrides else None
    effective_fc = _annotate_tools(backend_tools, overrides=overrides) if overrides else inferred_fc
    allowed_effects = compute_effective_allowed(policy)
    filtered_fc = filter_by_effects(effective_fc, allowed=allowed_effects)

    inferred_by_name = _extract_effects_by_name(inferred_fc)
    effective_by_name = _extract_effects_by_name(effective_fc)
    allowed_names = set(_extract_effects_by_name(filtered_fc))

    return [
        ToolInspection(
            name=tool.name,
            inferred_effects=inferred_by_name.get(tool.name, ()),
            effective_effects=effective_by_name.get(tool.name, ()),
            override_applied=inferred_by_name.get(tool.name, ()) != effective_by_name.get(tool.name, ()),
            allowed=tool.name in allowed_names,
        )
        for tool in backend_tools
    ]


def build_allowed_tools(
    backend_tools: list[types.Tool],
    policy: ServerPolicy,
) -> tuple[list[types.Tool], set[str]]:
    """Run the NAIL effect pipeline on backend tools and filter by policy.

    1. Convert ``types.Tool`` → MCP dicts
    2. ``from_mcp()`` to annotate with effects (using tool_overrides)
    3. ``filter_by_effects()`` to keep only allowed effects
    4. Convert back to ``types.Tool``

    Returns:
        (filtered_tools, allowed_names_set)
    """
    allowed_effects = compute_effective_allowed(policy)
    logger.debug("Effective allowed effects: %s", sorted(allowed_effects))

    # Annotate with NAIL effects
    overrides = policy.tool_overrides if policy.tool_overrides else None
    fc_tools = _annotate_tools(backend_tools, overrides=overrides)

    for fc in fc_tools:
        fn = fc.get("function", {})
        logger.debug(
            "Tool %r → effects %s", fn.get("name"), fn.get("effects", [])
        )

    # Filter by allowed effects
    filtered_fc = filter_by_effects(fc_tools, allowed=allowed_effects)

    # Convert back to MCP dicts, then to types.Tool
    filtered_mcp = to_mcp(filtered_fc)
    filtered_tools: list[types.Tool] = []
    allowed_names: set[str] = set()

    for d in filtered_mcp:
        tool = types.Tool(
            name=d["name"],
            description=d.get("description"),
            inputSchema=d.get("inputSchema", {}),
        )
        filtered_tools.append(tool)
        allowed_names.add(d["name"])

    logger.info(
        "Filtered %d → %d tools (allowed effects: %s)",
        len(backend_tools),
        len(filtered_tools),
        sorted(allowed_effects),
    )

    return filtered_tools, allowed_names


def is_tool_allowed(name: str, allowed_names: set[str]) -> bool:
    """Check whether a tool call is permitted."""
    return name in allowed_names
