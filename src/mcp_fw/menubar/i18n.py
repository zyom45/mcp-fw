"""Internationalisation helpers for mcp-fw menubar."""

from __future__ import annotations

import locale

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "status_running": "Running",
        "status_stopped": "Stopped",
        "status_label": "Status: {status}",
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
        "quit": "Quit",
        "log_window_title": "mcp-fw Logs",
    },
    "ja": {
        "status_running": "実行中",
        "status_stopped": "停止中",
        "status_label": "状態: {status}",
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
        "quit": "終了",
        "log_window_title": "mcp-fw ログ",
    },
}


def _detect_lang() -> str:
    """Detect language from macOS / system locale, fallback to 'en'."""
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
