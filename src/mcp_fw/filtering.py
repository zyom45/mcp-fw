"""NAIL integration: annotate MCP tools with effects and filter by policy."""

from __future__ import annotations

import logging
from typing import Any

import mcp.types as types
from nail_lang import filter_by_effects, from_mcp, to_mcp

from mcp_fw.policy import ServerPolicy, compute_effective_allowed

logger = logging.getLogger(__name__)


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

    # types.Tool → dict (MCP format)
    mcp_dicts: list[dict[str, Any]] = []
    for tool in backend_tools:
        mcp_dicts.append({
            "name": tool.name,
            "description": tool.description or "",
            "inputSchema": tool.inputSchema,
        })

    # Annotate with NAIL effects
    overrides = policy.tool_overrides if policy.tool_overrides else None
    fc_tools = from_mcp(mcp_dicts, existing_effects=overrides)

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
