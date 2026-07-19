from __future__ import annotations

from .branding import APP_NAME
from .platform import install_launcher


def main() -> int:
    target = install_launcher()
    if target is None:
        print(f"{APP_NAME} does not need a source launcher on this platform.")
        return 0
    print(f"Installed {APP_NAME} launcher: {target}")
    return 0
