"""Tests for menubar config discovery and persistence."""

from __future__ import annotations

from pathlib import Path

from mcp_fw.menubar import config_locator


def test_resolve_config_path_prefers_explicit_argument(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(config_locator, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(config_locator, "LAST_CONFIG_PATH", tmp_path / "app" / "last-menubar-config.txt")
    explicit = tmp_path / "custom.yaml"
    explicit.write_text("servers: {}\n")

    assert config_locator.resolve_config_path(str(explicit), cwd=tmp_path) == explicit.resolve()


def test_resolve_config_path_uses_last_config(tmp_path: Path, monkeypatch) -> None:
    app_dir = tmp_path / "app"
    monkeypatch.setattr(config_locator, "APP_DIR", app_dir)
    monkeypatch.setattr(config_locator, "LAST_CONFIG_PATH", app_dir / "last-menubar-config.txt")

    saved = tmp_path / "saved-policy.yaml"
    saved.write_text("servers: {}\n")
    config_locator.save_last_config_path(saved)

    assert config_locator.resolve_config_path(None, cwd=tmp_path) == saved.resolve()


def test_resolve_config_path_finds_default_policy_in_cwd(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(config_locator, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(config_locator, "LAST_CONFIG_PATH", tmp_path / "app" / "last-menubar-config.txt")

    policy = tmp_path / "policy.yaml"
    policy.write_text("servers: {}\n")

    assert config_locator.resolve_config_path(None, cwd=tmp_path) == policy.resolve()


def test_missing_config_message_mentions_examples(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(config_locator, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(config_locator, "LAST_CONFIG_PATH", tmp_path / "app" / "last-menubar-config.txt")

    message = config_locator.missing_config_message(tmp_path)
    assert "mcp-fw menubar --config ./policy.yaml" in message
    assert "policy.yaml" in message
