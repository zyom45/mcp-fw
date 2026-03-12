"""Helpers for locating and remembering menubar policy files."""

from __future__ import annotations

from pathlib import Path

APP_DIR = Path.home() / "Library/Application Support/mcp-fw"
LAST_CONFIG_PATH = APP_DIR / "last-menubar-config.txt"


def _default_candidates(cwd: Path | None = None) -> list[Path]:
    base = (cwd or Path.cwd()).resolve()
    return [
        base / "policy.yaml",
        base / "policy.yml",
        base / "examples" / "policy.yaml",
        APP_DIR / "policy.yaml",
        APP_DIR / "policy.yml",
    ]


def load_last_config_path() -> Path | None:
    """Return the last remembered config path if it still exists."""
    if not LAST_CONFIG_PATH.exists():
        return None

    candidate = Path(LAST_CONFIG_PATH.read_text().strip()).expanduser()
    if candidate.exists():
        return candidate.resolve()
    return None


def save_last_config_path(path: Path) -> None:
    """Remember a successfully used config path for future launches."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    LAST_CONFIG_PATH.write_text(str(path.resolve()) + "\n")


def resolve_config_path(config_arg: str | None, cwd: Path | None = None) -> Path | None:
    """Resolve a menubar policy path from CLI input, history, or common defaults."""
    if config_arg:
        candidate = Path(config_arg).expanduser().resolve()
        return candidate if candidate.exists() else None

    last_path = load_last_config_path()
    if last_path is not None:
        return last_path

    for candidate in _default_candidates(cwd):
        if candidate.exists():
            return candidate.resolve()
    return None


def missing_config_message(cwd: Path | None = None) -> str:
    """Return a helpful error message for missing menubar config."""
    candidates = "\n".join(f"  - {path}" for path in _default_candidates(cwd))
    return (
        "Error: no policy file found for menubar.\n\n"
        "Pass --config explicitly, for example:\n"
        "  mcp-fw menubar --config ./policy.yaml\n"
        "  mcp-fw-menubar --config ./policy.yaml\n\n"
        "Searched:\n"
        f"{candidates}\n"
    )
