"""Internationalisation helpers for mcp-fw menubar."""

from __future__ import annotations

import locale
import subprocess

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "status_running": "Running",
        "status_stopped": "Stopped",
        "status_label": "Status: {status}",
        "stop_server": "Stop Proxy",
        "stop_server_title": "Stop Proxy",
        "stop_server_message": "Stop running mcp-fw process for {server}?",
        "stop_server_ok": "Stop",
        "stop_server_cancel": "Cancel",
        "stop_server_complete_subtitle": "Proxy stopped",
        "stop_server_complete_message": "Stopped {count} process(es) for {server}.",
        "stop_server_missing": "No running mcp-fw process was found for {server}.",
        "tool_overrides": "Tool Overrides...",
        "tool_overrides_title": "Tool Overrides — {server}",
        "tool_overrides_none": "No tool overrides configured for this server.",
        "tool_overrides_body": "Current overrides:\n{text}\n\nEdit the policy YAML to modify.",
        "edit_policy": "Edit Policy YAML",
        "view_logs": "View Logs...",
        "sync_claude": "Sync to Claude Desktop",
        "sync_title": "Sync to Claude Desktop",
        "sync_message": (
            "This will update claude_desktop_config.json with mcp-fw proxy entries.\n\n"
            "Existing non-mcp-fw server entries will be preserved.\n\n"
            "Continue?"
        ),
        "sync_ok": "Sync",
        "sync_cancel": "Cancel",
        "sync_complete_subtitle": "Sync complete",
        "sync_complete_message": "Updated {name}. Please restart Claude Desktop.",
        "sync_error": "Sync Error",
        "open_claude_config": "Open Claude Desktop Config",
        "remove_claude": "Remove from Claude Desktop",
        "remove_claude_title": "Remove from Claude Desktop",
        "remove_claude_message": "Remove all mcp-fw managed Claude Desktop entries?",
        "remove_claude_ok": "Remove",
        "remove_claude_cancel": "Cancel",
        "remove_claude_complete_subtitle": "Claude config updated",
        "remove_claude_complete_message": "Removed {count} mcp-fw entry(ies). Please restart Claude Desktop.",
        "remove_claude_missing": "No mcp-fw Claude Desktop entries were found.",
        "quit": "Quit",
        "log_window_title": "mcp-fw Logs",
    },
    "ja": {
        "status_running": "実行中",
        "status_stopped": "停止中",
        "status_label": "状態: {status}",
        "stop_server": "プロキシを停止",
        "stop_server_title": "プロキシを停止",
        "stop_server_message": "{server} の実行中 mcp-fw プロセスを停止しますか？",
        "stop_server_ok": "停止",
        "stop_server_cancel": "キャンセル",
        "stop_server_complete_subtitle": "プロキシを停止しました",
        "stop_server_complete_message": "{server} のプロセスを {count} 件停止しました。",
        "stop_server_missing": "{server} の実行中 mcp-fw プロセスは見つかりませんでした。",
        "tool_overrides": "ツールオーバーライド...",
        "tool_overrides_title": "ツールオーバーライド — {server}",
        "tool_overrides_none": "このサーバーにはオーバーライドが設定されていません。",
        "tool_overrides_body": "現在のオーバーライド:\n{text}\n\n変更するにはポリシーYAMLを編集してください。",
        "edit_policy": "ポリシーYAMLを編集",
        "view_logs": "ログを表示...",
        "sync_claude": "Claude Desktopに同期",
        "sync_title": "Claude Desktopに同期",
        "sync_message": (
            "claude_desktop_config.json をmcp-fwプロキシエントリで更新します。\n\n"
            "既存のmcp-fw以外のサーバーエントリは保持されます。\n\n"
            "続行しますか？"
        ),
        "sync_ok": "同期",
        "sync_cancel": "キャンセル",
        "sync_complete_subtitle": "同期完了",
        "sync_complete_message": "{name} を更新しました。Claude Desktopを再起動してください。",
        "sync_error": "同期エラー",
        "open_claude_config": "Claude Desktop設定を開く",
        "remove_claude": "Claude Desktop設定から削除",
        "remove_claude_title": "Claude Desktop設定から削除",
        "remove_claude_message": "mcp-fw が管理している Claude Desktop エントリをすべて削除しますか？",
        "remove_claude_ok": "削除",
        "remove_claude_cancel": "キャンセル",
        "remove_claude_complete_subtitle": "Claude設定を更新しました",
        "remove_claude_complete_message": "mcp-fw エントリを {count} 件削除しました。Claude Desktopを再起動してください。",
        "remove_claude_missing": "mcp-fw の Claude Desktop エントリは見つかりませんでした。",
        "quit": "終了",
        "log_window_title": "mcp-fw ログ",
    },
}


def _detect_lang() -> str:
    """Detect language from macOS UI preferences, fallback to 'en'."""
    # First, try macOS AppleLanguages (reflects System Settings → Language & Region)
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleLanguages"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            for token in result.stdout.replace("(", "").replace(")", "").replace('"', "").replace(",", "").split():
                token = token.strip()
                if not token:
                    continue
                lang = token.split("-")[0]
                if lang in _STRINGS:
                    return lang
    except Exception:
        pass

    # Fallback: environment-variable locale
    try:
        loc, _ = locale.getdefaultlocale()
    except ValueError:
        loc = None
    if loc:
        lang = loc.split("_")[0]
        if lang in _STRINGS:
            return lang
    return "en"


_LANG = _detect_lang()


def t(key: str, **kwargs: object) -> str:
    """Return translated string for *key*, formatted with *kwargs*."""
    table = _STRINGS.get(_LANG, _STRINGS["en"])
    raw = table.get(key, _STRINGS["en"].get(key, key))
    if kwargs:
        return raw.format(**kwargs)
    return raw
