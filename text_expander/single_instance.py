from __future__ import annotations

import os
import sys
from pathlib import Path


class SingleInstanceLock:
    """Prevent a second app instance from running.

    Uses a PID lock file in a platform-appropriate runtime directory.
    A stale lock (left by a crashed process whose PID no longer exists)
    is detected and replaced automatically.
    """

    def __init__(self, name: str) -> None:
        self._path = self._lock_path(name)
        self._acquired = False

    @staticmethod
    def _lock_path(name: str) -> Path:
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
            directory = Path(base) / name
        else:
            runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
            if runtime_dir:
                directory = Path(runtime_dir) / name
            else:
                # Fall back to a private temp dir when XDG_RUNTIME_DIR is absent.
                import getpass
                import tempfile

                uid = os.getuid()
                user = getpass.getuser()
                directory = Path(tempfile.gettempdir()) / f"{name}-{uid}-{user}"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / "instance.lock"

    def acquire(self) -> bool:
        """Return True if this process now holds the single-instance lock."""
        if self._acquired:
            return True

        if self._path.exists():
            if not self._lock_is_stale():
                return False
            try:
                self._path.unlink()
            except OSError:
                return False

        try:
            # O_CREAT|O_EXCL guarantees only one process can create it.
            fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(str(os.getpid()))
        except FileExistsError:
            # Lost a race with another instance between the check and create.
            return False
        except OSError:
            return False

        self._acquired = True
        return True

    def _lock_is_stale(self) -> bool:
        try:
            recorded = int(self._path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            # Unreadable or corrupt lock: treat as stale so a crash cannot
            # permanently block startup.
            return True
        if sys.platform == "win32":
            return not self._pid_alive_windows(recorded)
        return not self._pid_alive_posix(recorded)

    @staticmethod
    def _pid_alive_windows(pid: int) -> bool:
        try:
            import ctypes

            SYNCHRONIZE = 0x00100000
            ERROR_INVALID_PARAMETER = 87
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return kernel32.GetLastError() != ERROR_INVALID_PARAMETER
        except Exception:
            return True  # Cannot tell; assume alive to stay safe.

    @staticmethod
    def _pid_alive_posix(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # Exists but owned by someone else.
        except OSError:
            return True
        return True

    def release(self) -> None:
        if not self._acquired:
            return
        try:
            self._path.unlink()
        except OSError:
            pass
        self._acquired = False
