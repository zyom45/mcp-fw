"""Tests for menubar i18n strings."""

from mcp_fw.menubar import i18n


def test_effects_hint_english(monkeypatch) -> None:
    monkeypatch.setattr(i18n, "_LANG", "en")
    assert i18n.t("effects_hint") == "Checked = allowed, unchecked = blocked"


def test_effects_hint_japanese(monkeypatch) -> None:
    monkeypatch.setattr(i18n, "_LANG", "ja")
    assert i18n.t("effects_hint") == "チェック済み = 許可、未チェック = ブロック"
