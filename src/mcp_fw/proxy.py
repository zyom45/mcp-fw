"""Core stdio proxy: MCP server (frontend) + MCP client (backend)."""

from __future__ import annotations

import logging
import sys
from contextlib import AsyncExitStack

import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.stdio import stdio_server

from mcp.shared.exceptions import McpError

from mcp_fw.filtering import build_allowed_tools, is_tool_allowed
from mcp_fw.policy import ServerPolicy

logger = logging.getLogger(__name__)


class FirewallProxy:
    """MCP proxy that filters tools based on NAIL effect policy."""

    def __init__(self, policy: ServerPolicy) -> None:
        self.policy = policy
        self._backend: ClientSession | None = None
        self._allowed_names: set[str] = set()

    async def _ensure_allowed_names(self) -> set[str]:
        """Lazily initialize allowed tool names if not yet populated."""
        if not self._allowed_names:
            assert self._backend is not None
            result = await self._backend.list_tools()
            _, self._allowed_names = build_allowed_tools(result.tools, self.policy)
        return self._allowed_names

    async def run(self) -> None:
        """Start the proxy: connect to backend, then serve the frontend."""
        async with AsyncExitStack() as stack:
            # ── Connect to backend MCP server ──
            server_params = StdioServerParameters(
                command=self.policy.command,
                args=self.policy.args,
                env=self.policy.env,
            )
            logger.info(
                "Connecting to backend: %s %s",
                self.policy.command,
                " ".join(self.policy.args),
            )
            read_stream, write_stream = await stack.enter_async_context(
                stdio_client(server_params, errlog=sys.stderr)
            )
            self._backend = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self._backend.initialize()
            logger.info("Backend initialized")

            # ── Build frontend MCP server ──
            server = Server("mcp-fw")
            self._register_handlers(server)

            init_options = server.create_initialization_options(
                notification_options=NotificationOptions(),
            )

            # ── Run frontend on stdio ──
            async with stdio_server() as (srv_read, srv_write):
                logger.info("Firewall proxy running")
                await server.run(srv_read, srv_write, init_options)

    def _register_handlers(self, server: Server) -> None:
        """Register all MCP request handlers on the frontend server."""
        backend = self._backend
        assert backend is not None

        @server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            result = await backend.list_tools()
            filtered, self._allowed_names = build_allowed_tools(
                result.tools, self.policy
            )
            return filtered

        @server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            allowed = await self._ensure_allowed_names()
            if not is_tool_allowed(name, allowed):
                logger.warning("Blocked tool call: %s", name)
                raise McpError(
                    types.ErrorData(
                        code=types.INVALID_PARAMS,
                        message=f"Tool '{name}' is blocked by firewall policy",
                    )
                )
            logger.debug("Forwarding tool call: %s", name)
            result = await backend.call_tool(name, arguments)
            return list(result.content)

        @server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            result = await backend.list_resources()
            logger.info("Forwarding %d resources (not filtered)", len(result.resources))
            return list(result.resources)

        @server.read_resource()
        async def handle_read_resource(uri) -> str:
            logger.info("Forwarding read_resource: %s (not filtered)", uri)
            result = await backend.read_resource(uri)
            # Return the text of the first content item
            for content in result.contents:
                if hasattr(content, "text"):
                    return content.text
                if hasattr(content, "blob"):
                    return content.blob
            return ""

        @server.list_prompts()
        async def handle_list_prompts() -> list[types.Prompt]:
            result = await backend.list_prompts()
            logger.info("Forwarding %d prompts (not filtered)", len(result.prompts))
            return list(result.prompts)

        @server.get_prompt()
        async def handle_get_prompt(
            name: str, arguments: dict[str, str] | None
        ) -> types.GetPromptResult:
            logger.info("Forwarding get_prompt: %s (not filtered)", name)
            return await backend.get_prompt(name, arguments)
