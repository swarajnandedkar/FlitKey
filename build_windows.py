from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from text_expander.branding import APP_NAME, APP_VERSION


ROOT = Path(__file__).resolve().parent
ASSETS_DIR = ROOT / "assets"
WINDOWS_BUILD_DIR = ROOT / "build" / "windows"
PYINSTALLER_DIST_DIR = WINDOWS_BUILD_DIR / "dist"
PYINSTALLER_WORK_DIR = WINDOWS_BUILD_DIR / "work"
ICON_PATH = WINDOWS_BUILD_DIR / "flitkey.ico"
INSTALLER_SCRIPT = ROOT / "installer" / "flitkey.iss"


def _run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def _create_windows_icon() -> None:
    """Rasterize the existing SVG into an ICO used by PyInstaller and Inno."""
    from PyQt6.QtCore import QSize
    from PyQt6.QtGui import QGuiApplication, QIcon

    application = QGuiApplication.instance()
    owns_application = application is None
    if owns_application:
        application = QGuiApplication(["flitkey-icon-builder"])
    try:
        icon = QIcon(str(ASSETS_DIR / "flitkey.svg"))
        pixmap = icon.pixmap(QSize(256, 256))
        if pixmap.isNull() or not pixmap.save(str(ICON_PATH), "ICO"):
            raise RuntimeError("Qt could not write the Windows ICO icon")
    finally:
        if owns_application and application is not None:
            application.quit()


def _find_iscc() -> Path:
    candidates = []
    on_path = shutil.which("iscc") or shutil.which("ISCC.exe")
    if on_path:
        candidates.append(Path(on_path))
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(variable)
        if base:
            candidates.append(Path(base) / "Inno Setup 6" / "ISCC.exe")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(
        "Inno Setup 6 (ISCC.exe) was not found. Install it from https://jrsoftware.org/isinfo.php."
    )


def _sign_file(file_path: Path) -> None:
    """Sign an executable binary if CODESIGN_CERT_PATH environment variable is set."""
    cert_path = os.environ.get("CODESIGN_CERT_PATH")
    cert_pass = os.environ.get("CODESIGN_CERT_PASSWORD", "")
    signtool = shutil.which("signtool") or os.environ.get("SIGNTOOL_PATH")

    if cert_path and Path(cert_path).exists():
        if not signtool:
            print("Warning: CODESIGN_CERT_PATH is set but signtool.exe was not found on PATH.")
            return
        print(f"Signing {file_path.name}...")
        cmd = [
            signtool,
            "sign",
            "/f",
            cert_path,
            "/tr",
            "http://timestamp.digicert.com",
            "/td",
            "sha256",
            "/fd",
            "sha256",
        ]
        if cert_pass:
            cmd.extend(["/p", cert_pass])
        cmd.append(str(file_path))
        _run(cmd)
    else:
        print(f"Notice: Code signing skipped for {file_path.name} (CODESIGN_CERT_PATH not set). Unsigned binaries may trigger Windows SmartScreen warnings.")


def build() -> Path:
    if sys.platform != "win32":
        raise SystemExit(
            "A native Windows build is required for a Windows .exe. "
            "Run this script on Windows or use the GitHub Actions workflow."
        )

    WINDOWS_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    PYINSTALLER_DIST_DIR.mkdir(parents=True, exist_ok=True)
    PYINSTALLER_WORK_DIR.mkdir(parents=True, exist_ok=True)
    _create_windows_icon()

    _run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--windowed",
            "--name",
            APP_NAME,
            "--icon",
            str(ICON_PATH),
            "--add-data",
            f"{ASSETS_DIR};assets",
            "--distpath",
            str(PYINSTALLER_DIST_DIR),
            "--workpath",
            str(PYINSTALLER_WORK_DIR),
            "run.py",
        ]
    )

    exe_file = PYINSTALLER_DIST_DIR / APP_NAME / f"{APP_NAME}.exe"
    if exe_file.exists():
        _sign_file(exe_file)

    iscc = _find_iscc()
    _run([str(iscc), str(INSTALLER_SCRIPT), f"/DMyAppVersion={APP_VERSION}"])
    installer = ROOT / "dist" / "windows" / f"FlitKey-Setup-{APP_VERSION}-x64.exe"

    if installer.exists():
        _sign_file(installer)

    print(f"Built {installer}")
    return installer


if __name__ == "__main__":
    build()

