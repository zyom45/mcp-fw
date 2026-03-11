"""CLI entry point for mcp-fw."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from contextlib import AsyncExitStack
from pathlib import Path

from mcp_fw import __version__
from mcp_fw.menubar.claude_desktop import remove_mcp_fw_from_claude
from mcp_fw.menubar.process_monitor import check_server_status, find_server_pids, stop_server
from mcp_fw.runtime_state import managed_state, read_state

COMMANDS = {"run", "inspect", "status", "stop", "claude-remove", "menubar"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp-fw",
        description="MCP Firewall Proxy — policy-based tool access control",
        epilog=(
            "Commands:\n"
            "  mcp-fw run --config policy.yaml --server filesystem\n"
            "  mcp-fw inspect --config policy.yaml --server filesystem\n"
            "  mcp-fw status --server filesystem\n"
            "  mcp-fw stop --server filesystem\n"
            "  mcp-fw claude-remove [--server filesystem]\n"
            "  mcp-fw menubar --config policy.yaml\n\n"
            "Legacy shorthand:\n"
            "  mcp-fw --config policy.yaml --server filesystem\n"
            "  This is treated as: mcp-fw run ..."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Run the firewall proxy",
    )
    run_parser.add_argument(
        "--config",
        required=True,
        help="Path to the policy YAML file",
    )
    run_parser.add_argument(
        "--server",
        required=True,
        help="Server name (must match a key in the policy file)",
    )
    run_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging",
    )
    run_parser.add_argument(
        "--log-file",
        help="Also write logs to this file",
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect inferred NAIL effects and policy outcome for backend tools",
    )
    inspect_parser.add_argument(
        "--config",
        required=True,
        help="Path to the policy YAML file",
    )
    inspect_parser.add_argument(
        "--server",
        required=True,
        help="Server name (must match a key in the policy file)",
    )

    status_parser = subparsers.add_parser(
        "status",
        help="Show tracked runtime status for a server",
    )
    status_parser.add_argument(
        "--server",
        required=True,
        help="Server name to inspect",
    )

    menubar_parser = subparsers.add_parser(
        "menubar",
        help="Launch the macOS menubar app",
    )
    menubar_parser.add_argument(
        "--config",
        required=True,
        help="Path to the policy YAML file",
    )

    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop running mcp-fw proxy processes for a server",
    )
    stop_parser.add_argument(
        "--server",
        required=True,
        help="Server name to stop",
    )

    claude_remove_parser = subparsers.add_parser(
        "claude-remove",
        help="Remove mcp-fw managed Claude Desktop config entries",
    )
    claude_remove_parser.add_argument(
        "--server",
        help="Remove only one server entry ({server}-fw). Omit to remove all mcp-fw entries.",
    )
    return parser


def _configure_logging(verbose: bool, log_file: str | None) -> None:
    """Configure stderr and optional file logging."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=log_level,
        format=log_format,
        stream=sys.stderr,
    )

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(fh)


def _run_proxy(args: argparse.Namespace) -> None:
    """Run the MCP firewall proxy."""
    from mcp_fw.policy import load_policy
    from mcp_fw.proxy import FirewallProxy

    _configure_logging(args.verbose, args.log_file)
    policy = load_policy(args.config, args.server)
    proxy = FirewallProxy(policy)
    with managed_state(
        args.server,
        config_path=str(Path(args.config).resolve()),
        log_file=str(Path(args.log_file).resolve()) if args.log_file else None,
    ):
        asyncio.run(proxy.run())


async def _inspect_proxy_async(args: argparse.Namespace) -> None:
    """Connect to the backend and print per-tool inspection results."""
    import sys

    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    from mcp_fw.filtering import inspect_tools
    from mcp_fw.policy import compute_effective_allowed, load_policy

    policy = load_policy(args.config, args.server)
    server_params = StdioServerParameters(
        command=policy.command,
        args=policy.args,
        env=policy.env,
    )

    async with AsyncExitStack() as stack:
        read_stream, write_stream = await stack.enter_async_context(
            stdio_client(server_params, errlog=sys.stderr)
        )
        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()
        result = await session.list_tools()

    inspections = inspect_tools(result.tools, policy)
    allowed_effects = ",".join(sorted(compute_effective_allowed(policy)))
    print(f"server={policy.name}")
    print(f"allowed_effects={allowed_effects}")
    print("tool\tinferred\teffective\toverride\tstatus")
    for item in inspections:
        inferred = ",".join(item.inferred_effects) or "-"
        effective = ",".join(item.effective_effects) or "-"
        override = "yes" if item.override_applied else "-"
        status = "allowed" if item.allowed else "blocked"
        print(f"{item.name}\t{inferred}\t{effective}\t{override}\t{status}")


def _inspect_proxy(args: argparse.Namespace) -> None:
    """Inspect backend tool classification."""
    asyncio.run(_inspect_proxy_async(args))


def _stop_proxy(args: argparse.Namespace) -> None:
    """Stop running proxy processes for a server."""
    count = stop_server(args.server)
    if count == 0:
        print(f"No running mcp-fw process found for server '{args.server}'.", file=sys.stderr)
        raise SystemExit(1)
    print(f"Stopped {count} mcp-fw process(es) for server '{args.server}'.")


def _show_status(args: argparse.Namespace) -> None:
    """Print tracked runtime status for a server."""
    state = read_state(args.server)
    status = check_server_status(args.server)
    pids = find_server_pids(args.server)

    print(f"server={args.server}")
    print(f"status={status.value}")
    print(f"pids={','.join(str(pid) for pid in pids) if pids else '-'}")
    if state is None:
        print("state_file=-")
        return

    print(f"state_file=tracked")
    print(f"config_path={state.get('config_path') or '-'}")
    print(f"log_file={state.get('log_file') or '-'}")


def _remove_claude_config(args: argparse.Namespace) -> None:
    """Remove mcp-fw managed Claude Desktop config entries."""
    _, removed = remove_mcp_fw_from_claude(args.server)
    if removed == 0:
        target = f"server '{args.server}'" if args.server else "any mcp-fw server"
        print(f"No Claude Desktop config entry found for {target}.", file=sys.stderr)
        raise SystemExit(1)
    if args.server:
        print(f"Removed Claude Desktop config entry for '{args.server}-fw'.")
    else:
        print(f"Removed {removed} mcp-fw Claude Desktop config entry(s).")


def _launch_menubar(args: argparse.Namespace) -> None:
    """Launch the menubar app."""
    from mcp_fw.menubar.app import main as menubar_main

    menubar_main(["--config", args.config])


def _normalize_argv(argv: list[str]) -> list[str]:
    """Keep legacy 'mcp-fw --config ...' usage working without breaking top-level help."""
    if not argv:
        return argv
    first = argv[0]
    if first in {"-h", "--help", "--version"}:
        return argv
    if first in COMMANDS:
        return argv
    if first.startswith("-"):
        return ["run", *argv]
    return argv


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    argv = _normalize_argv(list(sys.argv[1:] if argv is None else argv))

    args = parser.parse_args(argv)
    if args.command == "run":
        _run_proxy(args)
        return
    if args.command == "inspect":
        _inspect_proxy(args)
        return
    if args.command == "status":
        _show_status(args)
        return
    if args.command == "menubar":
        _launch_menubar(args)
        return
    if args.command == "stop":
        _stop_proxy(args)
        return
    if args.command == "claude-remove":
        _remove_claude_config(args)
        return
    parser.print_help(sys.stderr)
    raise SystemExit(2)
