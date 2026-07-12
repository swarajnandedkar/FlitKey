from __future__ import annotations

from ..models import CapabilityReport, Snippet
from .base import RuntimeBackend


class WaylandBackend(RuntimeBackend):
    def __init__(self) -> None:
        report = CapabilityReport(
            session_type="wayland",
            backend_name="wayland-fallback",
            typed_expansion_supported=False,
            global_hotkeys_supported=False,
            tray_supported=True,
            autostart_supported=True,
            status_message="Wayland session detected. Universal typed expansion is not available in this backend.",
        )
        super().__init__(report)
        self._snippets: list[Snippet] = []

    def start(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        self._snippets = snippets
        self.status_changed.emit(self.capability_report.status_message)

    def stop(self) -> None:
        return
