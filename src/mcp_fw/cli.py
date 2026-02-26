"""CLI entry point for mcp-fw."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from mcp_fw.policy import load_policy
from mcp_fw.proxy import FirewallProxy


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mcp-fw",
        description="MCP Firewall Proxy — policy-based tool access control",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the policy YAML file",
    )
    parser.add_argument(
        "--server",
        required=True,
        help="Server name (must match a key in the policy file)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging",
    )
    parser.add_argument(
        "--log-file",
        help="Also write logs to this file",
    )
    args = parser.parse_args()

    # All logging goes to stderr (stdout is the MCP protocol channel)
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=log_level,
        format=log_format,
        stream=sys.stderr,
    )

    if args.log_file:
        from pathlib import Path

        Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(args.log_file)
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(fh)

    policy = load_policy(args.config, args.server)
    proxy = FirewallProxy(policy)
    asyncio.run(proxy.run())
