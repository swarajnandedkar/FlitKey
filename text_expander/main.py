from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from . import ipc
from .branding import APP_ID, APP_NAME
from .single_instance import SingleInstanceLock
from .app import AppController
from .theme import apply_theme


def main() -> int:
    args = sys.argv[1:]
    command = "picker" if "--picker" in args else "show"

    lock = SingleInstanceLock(APP_ID)
    if not lock.acquire():
        # A second instance would double-expand every keystroke: hand the
        # request to the running one instead (this is how `flitkey --picker`
        # bound to a desktop shortcut reaches the app).
        app = QApplication.instance() or QApplication(sys.argv)
        if ipc.send(ipc.socket_name(), command):
            return 0
        QMessageBox.warning(
            None,
            APP_NAME,
            f"{APP_NAME} is already running. Check your system tray.",
        )
        return 1

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    apply_theme(app)
    server = None
    try:
        controller = AppController(app)
        server = ipc.serve(ipc.socket_name(), controller.handle_remote_command)
        controller.show_initial_window(start_minimized="--minimized" in args)
        if command == "picker":
            controller.open_picker()
        return app.exec()
    finally:
        if server is not None:
            server.close()
        lock.release()
