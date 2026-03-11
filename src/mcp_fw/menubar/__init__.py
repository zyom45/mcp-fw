"""mcp-fw menubar application."""


def main() -> None:
    from mcp_fw.menubar.app import main as app_main

    app_main()


__all__ = ["main"]
