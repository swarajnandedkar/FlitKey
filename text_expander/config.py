from __future__ import annotations

import json
import os
import shutil
import sys
from json import JSONDecodeError
from pathlib import Path

from .branding import APP_ID, LEGACY_APP_IDS
from .models import Settings, Snippet


APP_DIR_NAME = APP_ID
CONFIG_FILE_NAME = "config.json"


def _xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


def _config_home() -> Path:
    """Return the appropriate per-user configuration root for this platform."""
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if app_data:
            return Path(app_data)
        return Path.home() / "AppData" / "Roaming"
    return _xdg_config_home()


def _legacy_config_dirs() -> list[Path]:
    base = _config_home()
    return [base / legacy_id for legacy_id in LEGACY_APP_IDS]


def _migrate_legacy_state(target: Path) -> None:
    if target.exists():
        return
    for legacy_dir in _legacy_config_dirs():
        if not legacy_dir.exists() or legacy_dir == target:
            continue
        try:
            shutil.copytree(legacy_dir, target)
        except OSError:
            return
        return


def app_config_dir() -> Path:
    path = _config_home() / APP_DIR_NAME
    _migrate_legacy_state(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return app_config_dir() / CONFIG_FILE_NAME


def load_state() -> tuple[list[Snippet], Settings]:
    path = config_path()
    if not path.exists():
        return [], Settings()

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, JSONDecodeError, TypeError, ValueError):
        return [], Settings()

    if not isinstance(payload, dict):
        return [], Settings()

    raw_snippets = payload.get("snippets", [])
    if not isinstance(raw_snippets, list):
        raw_snippets = []
    snippets = [Snippet.from_dict(item) for item in raw_snippets if isinstance(item, dict)]
    settings_payload = payload.get("settings", {})
    if not isinstance(settings_payload, dict):
        settings_payload = {}
    settings = Settings.from_dict(settings_payload)
    return snippets, settings


def save_state(snippets: list[Snippet], settings: Settings) -> None:
    payload = {
        "snippets": [snippet.to_dict() for snippet in snippets],
        "settings": settings.to_dict(),
    }
    with config_path().open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
