from __future__ import annotations

from .branding import APP_NAME
from .platform import install_launcher


def main() -> int:
    target = install_launcher()
    print(f"Installed {APP_NAME} launcher: {target}")
    return 0
