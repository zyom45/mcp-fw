"""Integration test: FirewallProxy with a mock FastMCP backend."""

from __future__ import annotations

import asyncio
import textwrap
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# We test by launching mcp-fw as a subprocess talking to a mock backend.
# The mock backend is a simple FastMCP server defined inline.

MOCK_BACKEND = textwrap.dedent('''\
    """Mock MCP backend with FS and NET tools."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("mock-backend")

    @mcp.tool()
    def read_file(path: str) -> str:
        """Read a file from disk."""
        return f"contents of {path}"

    @mcp.tool()
    def http_get(url: str) -> str:
        """Fetch a URL via HTTP."""
        return f"response from {url}"

    @mcp.tool()
    def log_message(message: str) -> str:
        """Log a message to console."""
        return f"logged: {message}"

    mcp.run(transport="stdio")
''')


@pytest.fixture()
def mock_backend_script(tmp_path: Path) -> Path:
    script = tmp_path / "mock_backend.py"
    script.write_text(MOCK_BACKEND)
    return script


@pytest.fixture()
def policy_file(tmp_path: Path, mock_backend_script: Path) -> Path:
    import sys
    p = tmp_path / "policy.yaml"
    p.write_text(textwrap.dedent(f"""\
        servers:
          mock:
            command: {sys.executable}
            args: ["{mock_backend_script}"]
            allow: [FS, IO]
            deny: [NET]
    """))
    return p


@pytest.mark.asyncio
async def test_proxy_filters_tools(policy_file: Path) -> None:
    """list_tools through the proxy should only return FS/IO tools."""
    import sys

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_fw", "--config", str(policy_file), "--server", "mock"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            names = {t.name for t in result.tools}

            assert "read_file" in names
            assert "log_message" in names
            assert "http_get" not in names


@pytest.mark.asyncio
async def test_proxy_forwards_allowed_call(policy_file: Path) -> None:
    """call_tool for an allowed tool should succeed."""
    import sys

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_fw", "--config", str(policy_file), "--server", "mock"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Must list_tools first to populate allowed_names
            await session.list_tools()

            result = await session.call_tool("read_file", {"path": "/tmp/test.txt"})
            assert not result.isError
            assert any("contents of /tmp/test.txt" in c.text for c in result.content if hasattr(c, "text"))


@pytest.mark.asyncio
async def test_proxy_blocks_denied_call(policy_file: Path) -> None:
    """call_tool for a denied tool should return an error."""
    import sys

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_fw", "--config", str(policy_file), "--server", "mock"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Must list_tools first
            await session.list_tools()

            result = await session.call_tool("http_get", {"url": "https://example.com"})
            assert result.isError
            assert any("blocked" in c.text.lower() for c in result.content if hasattr(c, "text"))
