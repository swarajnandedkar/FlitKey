from __future__ import annotations

import shutil
import stat
import subprocess
from pathlib import Path

from text_expander.branding import APP_VERSION

PACKAGE_NAME = "flitkey"
VERSION = APP_VERSION
ARCH = "all"
ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = DIST_DIR / "pkgroot"
APP_INSTALL_DIR = BUILD_DIR / "opt" / PACKAGE_NAME
DEBIAN_DIR = BUILD_DIR / "DEBIAN"
BIN_DIR = BUILD_DIR / "usr" / "bin"
APPLICATIONS_DIR = BUILD_DIR / "usr" / "share" / "applications"
PIXMAPS_DIR = BUILD_DIR / "usr" / "share" / "pixmaps"
OUTPUT_DEB = DIST_DIR / f"{PACKAGE_NAME}_{VERSION}_{ARCH}.deb"

EXCLUDE_NAMES = {"__pycache__", ".git", ".agents", ".codex", "dist", "tests", "build_deb.py", "build_windows.py", "requirements-windows.txt", "flitkey-website", ".claude", ".github", ".gitignore", "installer"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def should_copy(path: Path) -> bool:
    if path.name in EXCLUDE_NAMES:
        return False
    if "GTM" in path.name:
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


def copy_project_tree() -> None:
    for source in ROOT.iterdir():
        if not should_copy(source):
            continue
        destination = APP_INSTALL_DIR / source.name
        if source.is_dir():
            shutil.copytree(
                source,
                destination,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def write_control() -> None:
    control = f"""Package: {PACKAGE_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: {ARCH}
Maintainer: Local Build <local@example.com>
Depends: python3, python3-pyqt6, xdotool, xinput, x11-xserver-utils
Description: FlitKey desktop text expander
 FlitKey is a polished Linux desktop text expander with a modern GUI,
 tray integration, autostart support, X11 keyword expansion,
 and graceful Wayland fallback behavior.
"""
    (DEBIAN_DIR / "control").write_text(control, encoding="utf-8")


def write_launcher_script() -> None:
    script = f"""#!/bin/sh
exec /usr/bin/python3 /opt/{PACKAGE_NAME}/run.py "$@"
"""
    target = BIN_DIR / PACKAGE_NAME
    target.write_text(script, encoding="utf-8")
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_desktop_entry() -> None:
    desktop = f"""[Desktop Entry]
Type=Application
Name=FlitKey
Comment=Fast snippets and text expansion for Linux desktops
Exec=/usr/bin/{PACKAGE_NAME}
Icon={PACKAGE_NAME}
Terminal=false
Categories=Utility;
StartupNotify=true
X-GNOME-Autostart-enabled=true
"""
    target = APPLICATIONS_DIR / f"{PACKAGE_NAME}.desktop"
    target.write_text(desktop, encoding="utf-8")


def copy_icon() -> None:
    source = ROOT / "assets" / "flitkey.svg"
    target = PIXMAPS_DIR / f"{PACKAGE_NAME}.svg"
    shutil.copy2(source, target)


def build_package() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    clean_dir(BUILD_DIR)
    DEBIAN_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    PIXMAPS_DIR.mkdir(parents=True, exist_ok=True)
    APP_INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    copy_project_tree()
    write_control()
    write_launcher_script()
    write_desktop_entry()
    copy_icon()

    subprocess.run(["desktop-file-validate", str(APPLICATIONS_DIR / f"{PACKAGE_NAME}.desktop")], check=True)
    if OUTPUT_DEB.exists():
        OUTPUT_DEB.unlink()
    subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(BUILD_DIR), str(OUTPUT_DEB)], check=True)


if __name__ == "__main__":
    build_package()
    print(OUTPUT_DEB)
