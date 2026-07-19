from __future__ import annotations

from ..platform import detect_session_type
from .base import RuntimeBackend
from .wayland_backend import WaylandBackend
from .x11_backend import X11Backend


def create_backend() -> RuntimeBackend:
    session_type = detect_session_type()
    if session_type == "windows":
        # Keep the Win32-only imports out of Linux and Wayland startup paths.
        from .windows_backend import WindowsBackend

        return WindowsBackend()
    if session_type == "x11":
        return X11Backend()
    return WaylandBackend()
