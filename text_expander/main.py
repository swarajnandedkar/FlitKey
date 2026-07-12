from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .app import AppController


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = AppController(app)
    start_minimized = "--minimized" in sys.argv[1:]
    controller.show_initial_window(start_minimized=start_minimized)
    return app.exec()
