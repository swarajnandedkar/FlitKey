from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from .branding import APP_ID, APP_NAME
from .single_instance import SingleInstanceLock
from .app import AppController
from .theme import apply_theme


def main() -> int:
    lock = SingleInstanceLock(APP_ID)
    if not lock.acquire():
        # A second instance would double-expand every keystroke; surface it
        # without a display dependency when running headless.
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.warning(
            None,
            APP_NAME,
            f"{APP_NAME} is already running. Check your system tray.",
        )
        return 1

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    apply_theme(app)
    try:
        controller = AppController(app)
        start_minimized = "--minimized" in sys.argv[1:]
        controller.show_initial_window(start_minimized=start_minimized)
        return app.exec()
    finally:
        lock.release()
