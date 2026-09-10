from __future__ import annotations

import subprocess

from ..models import CapabilityReport, Snippet
from ..placeholders import render_placeholders
from ..platform import probe_binary
from .base import RuntimeBackend

_KEY_LEFT_EVDEV = "105"


class WaylandBackend(RuntimeBackend):
    """Wayland: no global key capture, so expansion is picker-driven.

    Text is inserted with wtype (wlroots compositors, KDE) or ydotool
    (anywhere, needs ydotoold running); without either the controller falls
    back to copying to the clipboard.
    """

    def __init__(self) -> None:
        self.typer = next((tool for tool in ("wtype", "ydotool") if probe_binary(tool)), None)
        if self.typer:
            status = (
                f"Wayland: Quick Insert types directly via {self.typer}. Typed keyword expansion "
                "needs an X11 session. Bind a desktop keyboard shortcut to `flitkey --picker` "
                "to open Quick Insert from anywhere."
            )
        else:
            status = (
                "Wayland: Quick Insert copies to the clipboard. Install wtype (Sway, Hyprland, KDE) "
                "or ydotool (GNOME; start ydotoold) for direct insertion, and bind a desktop "
                "keyboard shortcut to `flitkey --picker`."
            )
        report = CapabilityReport(
            session_type="wayland",
            backend_name=f"wayland-{self.typer or 'clipboard'}",
            typed_expansion_supported=False,
            global_hotkeys_supported=False,
            tray_supported=True,
            autostart_supported=True,
            status_message=status,
        )
        super().__init__(report)
        self._snippets: list[Snippet] = []

    def start(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        self._snippets = snippets
        self.status_changed.emit(self.capability_report.status_message)

    def stop(self) -> None:
        return

    def can_inject_text(self) -> bool:
        return self.typer is not None

    def inject_text(
        self, text: str, preserve_trailing_newline: bool = True, values: dict[str, str] | None = None
    ) -> bool:
        if not self.typer:
            return False
        rendered = render_placeholders(text, values)
        if not preserve_trailing_newline and rendered.endswith(("\n", "\r")):
            rendered = rendered[:-2] if rendered.endswith("\r\n") else rendered[:-1]

        cursor_index = rendered.find("{{cursor}}")
        if cursor_index != -1:
            typed = rendered[:cursor_index] + rendered[cursor_index + len("{{cursor}}") :]
            move_left = len(rendered) - cursor_index - len("{{cursor}}")
        else:
            typed, move_left = rendered, 0

        # ponytail: types character-by-character; newlines press Return, so multi-line
        # snippets can submit chat inputs. Switch to wl-copy + paste if that bites.
        if self.typer == "wtype":
            type_cmd, type_input = ["wtype", "-"], typed
            left_cmd = ["wtype", *(["-k", "Left"] * move_left)]
        else:
            type_cmd, type_input = ["ydotool", "type", "--", typed], None
            left_cmd = ["ydotool", "key", *([f"{_KEY_LEFT_EVDEV}:1", f"{_KEY_LEFT_EVDEV}:0"] * move_left)]

        try:
            if typed:
                subprocess.run(type_cmd, input=type_input, text=True, check=True, timeout=10.0)
            if move_left:
                subprocess.run(left_cmd, check=True, timeout=5.0)
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
        return True
