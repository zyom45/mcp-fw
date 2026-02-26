"""mcp-fw menubar application using rumps."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import rumps

from mcp_fw import __version__
from mcp_fw.menubar.claude_desktop import LOG_DIR, sync_policy_to_claude
from mcp_fw.menubar.i18n import t
from mcp_fw.menubar.log_viewer import LogViewerWindow
from mcp_fw.menubar.policy_manager import TOGGLEABLE_EFFECTS, PolicyManager
from mcp_fw.menubar.process_monitor import ServerStatus, check_server_status


class McpFwMenuBarApp(rumps.App):
    """macOS menubar app for managing mcp-fw policies."""

    def __init__(self, policy_path: Path) -> None:
        icon_path = Path(__file__).parent / "resources" / "icon.pdf"
        if icon_path.exists():
            super().__init__("FW", icon=str(icon_path), quit_button=None, template=True)
        else:
            super().__init__("FW", quit_button=None)
        self._policy_path = policy_path
        self._pm = PolicyManager(policy_path)
        self._log_viewer = LogViewerWindow(LOG_DIR)
        # Map (server, effect) -> menu item for state updates
        self._effect_items: dict[tuple[str, str], rumps.MenuItem] = {}
        # Map server_name -> status menu item
        self._status_items: dict[str, rumps.MenuItem] = {}
        # Map server_name -> submenu item (for ●/○ prefix)
        self._server_items: dict[str, rumps.MenuItem] = {}
        self._build_menu()

    def _build_menu(self) -> None:
        """Build the full menu hierarchy from policy."""
        menu_items: list[rumps.MenuItem | None] = []

        # Version info
        info = rumps.MenuItem(f"mcp-fw v{__version__}")
        info.set_callback(None)
        menu_items.append(info)
        menu_items.append(None)  # separator

        # Server submenus
        servers = self._pm.load_all_servers()
        for name, cfg in servers.items():
            status = check_server_status(name)
            prefix = "●" if status == ServerStatus.RUNNING else "○"
            server_item = rumps.MenuItem(f"{prefix} {name}")
            self._server_items[name] = server_item

            # Status display (disabled)
            status_text = t("status_running") if status == ServerStatus.RUNNING else t("status_stopped")
            status_item = rumps.MenuItem(t("status_label", status=status_text))
            status_item.set_callback(None)
            self._status_items[name] = status_item
            server_item.add(status_item)
            server_item.add(None)  # separator

            # Effect checkboxes
            allow, deny = self._pm.get_server_effects(name)
            for effect in TOGGLEABLE_EFFECTS:
                enabled = self._pm.is_effect_enabled(name, effect)
                item = rumps.MenuItem(effect, callback=self._on_effect_toggle)
                item.state = 1 if enabled else 0
                # Store server/effect identity on the item
                item._fw_server = name
                item._fw_effect = effect
                self._effect_items[(name, effect)] = item
                server_item.add(item)

            server_item.add(None)  # separator

            # Tool overrides action
            overrides_item = rumps.MenuItem(
                t("tool_overrides"), callback=self._on_tool_overrides
            )
            overrides_item._fw_server = name
            server_item.add(overrides_item)

            menu_items.append(server_item)

        menu_items.append(None)  # separator

        # Global actions
        menu_items.append(
            rumps.MenuItem(t("edit_policy"), callback=self._edit_policy)
        )
        menu_items.append(rumps.MenuItem(t("view_logs"), callback=self._show_logs))
        menu_items.append(None)  # separator
        menu_items.append(
            rumps.MenuItem(t("sync_claude"), callback=self._sync_claude)
        )
        menu_items.append(
            rumps.MenuItem(t("open_claude_config"), callback=self._open_claude_config)
        )
        menu_items.append(None)  # separator
        menu_items.append(rumps.MenuItem(t("quit"), callback=self._quit))

        self.menu.clear()
        for item in menu_items:
            if item is None:
                self.menu.add(rumps.separator)
            else:
                self.menu.add(item)

    def _on_effect_toggle(self, sender: rumps.MenuItem) -> None:
        """Handle effect checkbox toggle."""
        server = sender._fw_server
        effect = sender._fw_effect
        new_state = 0 if sender.state else 1
        enabled = new_state == 1

        self._pm.update_server_effects(server, effect, enabled)
        sender.state = new_state

    def _on_tool_overrides(self, sender: rumps.MenuItem) -> None:
        """Show tool overrides dialog."""
        server = sender._fw_server
        overrides = self._pm.get_tool_overrides(server)

        if not overrides:
            rumps.alert(
                title=t("tool_overrides_title", server=server),
                message=t("tool_overrides_none"),
            )
            return

        lines = []
        for tool, effects in overrides.items():
            lines.append(f"  {tool}: [{', '.join(effects)}]")
        text = "\n".join(lines)

        rumps.alert(
            title=t("tool_overrides_title", server=server),
            message=t("tool_overrides_body", text=text),
        )

    def _edit_policy(self, _sender: rumps.MenuItem) -> None:
        """Open the policy YAML in the default editor."""
        subprocess.run(["open", str(self._policy_path)])

    def _show_logs(self, _sender: rumps.MenuItem) -> None:
        """Show the log viewer window."""
        self._log_viewer.show()

    def _sync_claude(self, _sender: rumps.MenuItem) -> None:
        """Sync policy to Claude Desktop config."""
        response = rumps.alert(
            title=t("sync_title"),
            message=t("sync_message"),
            ok=t("sync_ok"),
            cancel=t("sync_cancel"),
        )
        if response != 1:  # Cancel
            return

        try:
            servers = self._pm.load_all_servers()
            config_path = sync_policy_to_claude(
                self._policy_path, servers, sys.executable
            )
            rumps.notification(
                title="mcp-fw",
                subtitle=t("sync_complete_subtitle"),
                message=t("sync_complete_message", name=config_path.name),
            )
        except Exception as e:
            rumps.alert(
                title=t("sync_error"),
                message=str(e),
            )

    def _open_claude_config(self, _sender: rumps.MenuItem) -> None:
        """Open Claude Desktop config in the default editor."""
        from mcp_fw.menubar.claude_desktop import CLAUDE_CONFIG

        subprocess.run(["open", str(CLAUDE_CONFIG)])

    def _quit(self, _sender: rumps.MenuItem) -> None:
        self._log_viewer.close()
        rumps.quit_application()

    @rumps.timer(5)
    def _refresh_status(self, _timer: rumps.Timer) -> None:
        """Periodically refresh server running status."""
        for name, server_item in self._server_items.items():
            status = check_server_status(name)
            prefix = "●" if status == ServerStatus.RUNNING else "○"
            new_title = f"{prefix} {name}"
            if server_item.title != new_title:
                server_item.title = new_title

            # Update status sub-item
            if name in self._status_items:
                status_text = t("status_running") if status == ServerStatus.RUNNING else t("status_stopped")
                self._status_items[name].title = t("status_label", status=status_text)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mcp-fw-menubar",
        description="mcp-fw menubar application",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the policy YAML file",
    )
    args = parser.parse_args()

    policy_path = Path(args.config).resolve()
    if not policy_path.exists():
        print(f"Error: Policy file not found: {policy_path}", file=sys.stderr)
        sys.exit(1)

    app = McpFwMenuBarApp(policy_path)
    app.run()
