from __future__ import annotations

import threading

from PyQt6.QtCore import QObject, pyqtSignal

from ..models import CapabilityReport, Snippet


class RuntimeBackend(QObject):
    status_changed = pyqtSignal(str)
    snippet_triggered = pyqtSignal(str)

    def __init__(self, capability_report: CapabilityReport):
        super().__init__()
        self.capability_report = capability_report
        # Guards all mutable state shared between the Qt main thread
        # (start/stop/reload/set_paused/inject from the picker) and the
        # backend's keyboard-listener thread. Reentrant because trigger
        # handling nests calls (e.g. _expand_keyword -> inject_text).
        self._state_lock = threading.RLock()
        self._paused = False

    def start(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def reload(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        self.stop()
        self.start(snippets, case_sensitive)

    def set_paused(self, paused: bool) -> None:
        with self._state_lock:
            self._paused = paused
        state = "Paused" if paused else "Running"
        self.status_changed.emit(state)

    def can_inject_text(self) -> bool:
        return False

    def inject_text(self, text: str, preserve_trailing_newline: bool = True) -> bool:
        return False
