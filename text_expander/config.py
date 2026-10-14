from __future__ import annotations

import json
import os
import shutil
import sys
from json import JSONDecodeError
from pathlib import Path

from .branding import APP_ID, LEGACY_APP_IDS
from .models import Settings, Snippet
from .security import atomic_write_json, ensure_private_directory


APP_DIR_NAME = APP_ID
CONFIG_FILE_NAME = "config.json"
SCHEMA_VERSION = 1


def _migrate(payload: dict) -> dict:
    """Upgrade an older config payload in place to SCHEMA_VERSION."""
    version = payload.get("schema_version")
    if not isinstance(version, int) or version < 1:
        version = 0  # pre-versioned configs
    # Add `if version < N:` blocks here as the schema evolves; each bumps `version`.
    payload["schema_version"] = SCHEMA_VERSION
    return payload


def _payload(snippets: list[Snippet], settings: Settings) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "snippets": [snippet.to_dict() for snippet in snippets],
        "settings": settings.to_dict(),
    }


def _parse_payload(payload: dict) -> tuple[list[Snippet], Settings]:
    payload = _migrate(payload)
    raw_snippets = payload.get("snippets", [])
    if not isinstance(raw_snippets, list):
        raw_snippets = []
    snippets = [Snippet.from_dict(item) for item in raw_snippets if isinstance(item, dict)]
    settings_payload = payload.get("settings", {})
    if not isinstance(settings_payload, dict):
        settings_payload = {}
    return snippets, Settings.from_dict(settings_payload)


def _validate_snippet_dict(item: dict, index: int) -> None:
    """Strictly validate one snippet entry from a user-provided backup.

    Missing keys are allowed (older exports); present keys must have the
    correct JSON type. Raises ValueError describing the first violation.
    """
    for key in ("label", "keyword", "hotkey", "expansion_text", "pack_id", "id"):
        if key in item and not isinstance(item[key], str):
            raise ValueError(f"Import payload snippet #{index} field '{key}' must be a string.")
    if "trigger_type" in item and item["trigger_type"] not in ("keyword", "hotkey"):
        raise ValueError(f"Import payload snippet #{index} field 'trigger_type' must be 'keyword' or 'hotkey'.")
    if "use_count" in item:
        value = item["use_count"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"Import payload snippet #{index} field 'use_count' must be an integer.")
        if value < 0:
            raise ValueError(f"Import payload snippet #{index} field 'use_count' must be >= 0.")
    for key in ("enabled", "word_boundary"):
        if key in item and not isinstance(item[key], bool):
            raise ValueError(f"Import payload snippet #{index} field '{key}' must be a boolean.")


def _validate_settings_dict(settings_payload: dict) -> None:
    """Strictly validate the settings object of a user-provided backup."""
    for key in ("autostart", "start_minimized", "paused", "case_sensitive", "notify_on_expansion"):
        if key in settings_payload and not isinstance(settings_payload[key], bool):
            raise ValueError(f"Import payload settings field '{key}' must be a boolean.")
    for key in ("wayland_fallback_mode", "pause_hotkey"):
        if key in settings_payload and not isinstance(settings_payload[key], str):
            raise ValueError(f"Import payload settings field '{key}' must be a string.")
    if "excluded_apps" in settings_payload:
        raw = settings_payload["excluded_apps"]
        if not isinstance(raw, list) or any(not isinstance(x, str) for x in raw):
            raise ValueError("Import payload settings field 'excluded_apps' must be a list of strings.")


def _validate_import_payload(payload: dict) -> None:
    """Validate a user-provided backup before it may replace current state.

    Unlike load_state() (which coerces leniently so startup never crashes),
    imports are rejected with ValueError on any schema or field-type
    violation so malformed backups are reported, never silently repaired.
    """
    raw_snippets = payload.get("snippets", [])
    if "snippets" in payload and not isinstance(raw_snippets, list):
        raise ValueError("Import payload 'snippets' must be a list.")
    if isinstance(raw_snippets, list):
        for index, item in enumerate(raw_snippets):
            if not isinstance(item, dict):
                raise ValueError(f"Import payload snippet #{index} must be an object.")
            _validate_snippet_dict(item, index)
    settings_payload = payload.get("settings", {})
    if "settings" in payload and not isinstance(settings_payload, dict):
        raise ValueError("Import payload 'settings' must be an object.")
    if isinstance(settings_payload, dict):
        _validate_settings_dict(settings_payload)


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
    return ensure_private_directory(path)


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
    try:
        return _parse_payload(payload)
    except (ValueError, TypeError, AttributeError):
        return [], Settings()


def save_state(snippets: list[Snippet], settings: Settings) -> None:
    atomic_write_json(config_path(), _payload(snippets, settings))


def export_state(destination: Path) -> None:
    """Export the local user data for access/portability requests."""
    snippets, settings = load_state()
    atomic_write_json(destination, _payload(snippets, settings))


def import_state(source: Path) -> None:
    """Import user data from a previously exported JSON file, replacing current state."""
    if not source.exists():
        raise FileNotFoundError(f"Import file does not exist: {source}")
    try:
        with source.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, JSONDecodeError) as e:
        raise ValueError(f"Failed to read import file: {e}")
    # Validate structure
    if not isinstance(payload, dict):
        raise ValueError("Import payload must be a JSON object.")
    _validate_import_payload(payload)
    try:
        snippets, settings = _parse_payload(payload)
    except (ValueError, TypeError, AttributeError) as e:
        raise ValueError(f"Invalid import payload: {e}")
    # Back up current data so an accidental import can be undone.
    _backup_before_replace()
    atomic_write_json(config_path(), _payload(snippets, settings))


def _backup_before_replace() -> None:
    """Snapshot the current config next to itself before a destructive import."""
    path = config_path()
    if not path.exists():
        return
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = app_config_dir() / f"config.backup-{stamp}.json"
    try:
        shutil.copy2(path, backup_path)
    except OSError:
        pass  # Best effort; never block the import over a backup failure.


def delete_state() -> bool:
    """Delete the local FlitKey data file, returning whether it existed."""
    path = config_path()
    if not path.exists():
        return False
    path.unlink()
    return True
