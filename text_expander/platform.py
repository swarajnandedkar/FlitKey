from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from .branding import APP_ID, APP_NAME, ICON_FILE


def detect_session_type() -> str:
    session_type = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
    if session_type:
        return session_type
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def app_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _desktop_exec_arg(value: str | Path) -> str:
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def launcher_command(start_minimized: bool = False) -> str:
    parts = [_desktop_exec_arg(sys.executable), _desktop_exec_arg(app_root() / "run.py")]
    if start_minimized:
        parts.append("--minimized")
    return " ".join(parts)


def desktop_entry_content(start_minimized: bool = False) -> str:
    icon_path = app_root() / "assets" / ICON_FILE
    return "\n".join(
        [
            "[Desktop Entry]",
            "Type=Application",
            f"Name={APP_NAME}",
            "Comment=Fast snippets and text expansion for Linux desktops",
            f"Exec={launcher_command(start_minimized=start_minimized)}",
            f"Icon={icon_path}",
            "Terminal=false",
            "Categories=Utility;",
            "StartupNotify=true",
            "X-GNOME-Autostart-enabled=true",
            "",
        ]
    )


def desktop_entry_path() -> Path:
    return Path.home() / ".local" / "share" / "applications" / f"{APP_ID}.desktop"


def autostart_entry_path() -> Path:
    return Path.home() / ".config" / "autostart" / f"{APP_ID}.desktop"


def install_launcher() -> Path:
    target = desktop_entry_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(desktop_entry_content(start_minimized=False), encoding="utf-8")
    return target


def set_autostart(enabled: bool) -> None:
    target = autostart_entry_path()
    if enabled:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(desktop_entry_content(start_minimized=True), encoding="utf-8")
        return
    if target.exists():
        target.unlink()


def probe_binary(name: str) -> bool:
    return shutil.which(name) is not None
