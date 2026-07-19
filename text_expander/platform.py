from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .branding import APP_ID, APP_NAME, ICON_FILE


WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def is_windows() -> bool:
    return sys.platform == "win32"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def detect_session_type() -> str:
    if is_windows():
        return "windows"
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


def windows_launcher_command(start_minimized: bool = False) -> str:
    """Return a safely quoted command suitable for the current-user Run key."""
    if getattr(sys, "frozen", False):
        parts = [sys.executable]
    else:
        parts = [sys.executable, str(app_root() / "run.py")]
    if start_minimized:
        parts.append("--minimized")
    return subprocess.list2cmdline(parts)


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


def install_launcher() -> Path | None:
    """Install a source-tree launcher where the platform uses desktop entries."""
    if not is_linux():
        return None
    target = desktop_entry_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(desktop_entry_content(start_minimized=False), encoding="utf-8")
    return target


def set_autostart(enabled: bool) -> None:
    if is_windows():
        _set_windows_autostart(enabled)
        return
    if not is_linux():
        return
    target = autostart_entry_path()
    if enabled:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(desktop_entry_content(start_minimized=True), encoding="utf-8")
        return
    if target.exists():
        target.unlink()


def _set_windows_autostart(enabled: bool) -> None:
    """Toggle FlitKey in the per-user Windows startup registry key.

    The installer is per-user, so HKCU avoids an elevation prompt and keeps the
    setting scoped to the Windows account that enabled it.
    """
    try:
        import winreg
    except ImportError:
        return

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            WINDOWS_RUN_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                winreg.SetValueEx(
                    key,
                    APP_NAME,
                    0,
                    winreg.REG_SZ,
                    windows_launcher_command(start_minimized=True),
                )
                return
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    except OSError:
        # Keep the app usable when a managed Windows policy blocks the Run key.
        return


def probe_binary(name: str) -> bool:
    return shutil.which(name) is not None
