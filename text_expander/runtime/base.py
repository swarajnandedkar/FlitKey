from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from ..models import CapabilityReport, Snippet


class RuntimeBackend(QObject):
    status_changed = pyqtSignal(str)
    snippet_triggered = pyqtSignal(str)

    def __init__(self, capability_report: CapabilityReport):
        super().__init__()
        self.capability_report = capability_report
        self._paused = False

    def start(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def reload(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        self.stop()
        self.start(snippets, case_sensitive)

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        state = "Paused" if paused else "Running"
        self.status_changed.emit(state)

    def can_inject_text(self) -> bool:
        return False

    def inject_text(self, text: str) -> bool:
        return False
