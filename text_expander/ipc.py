from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from .branding import APP_ID

COMMANDS = frozenset({"picker", "show"})


def socket_name() -> str:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        # Same private directory as the single-instance lock, rather than Qt's /tmp default.
        return str(Path(runtime_dir) / APP_ID / "ipc.sock")
    return f"{APP_ID}-{os.getuid() if hasattr(os, 'getuid') else os.getlogin()}"


def serve(name: str, on_command: Callable[[str], None]) -> QLocalServer | None:
    """Listen for one-word commands from later `flitkey` invocations."""
    QLocalServer.removeServer(name)
    server = QLocalServer()
    if not server.listen(name):
        return None

    def read(socket: QLocalSocket) -> None:
        command = bytes(socket.readAll()).decode("utf-8", "replace").strip()
        socket.disconnectFromServer()
        if command in COMMANDS:
            on_command(command)

    def accept() -> None:
        while (socket := server.nextPendingConnection()) is not None:
            if socket.bytesAvailable():
                read(socket)
            else:
                socket.readyRead.connect(lambda s=socket: read(s))

    server.newConnection.connect(accept)
    return server


def send(name: str, command: str, timeout_ms: int = 500) -> bool:
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(timeout_ms):
        return False
    socket.write(command.encode("utf-8"))
    socket.waitForBytesWritten(timeout_ms)
    socket.disconnectFromServer()
    return True
