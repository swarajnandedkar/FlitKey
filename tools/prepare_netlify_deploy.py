#!/usr/bin/env python3
"""Build and validate the static marketing site before a Netlify deploy."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from materialize_public_routes import main as materialize_public_routes


PROJECT = Path(__file__).resolve().parents[1]
SITE = PROJECT / "FlitKey HP"


def run(script: str, *arguments: str) -> None:
    subprocess.run([sys.executable, str(PROJECT / "tools" / script), *arguments], check=True)


def main() -> None:
    # Hub and index builders are deterministic; rebuild them before validating.
    run("build_content_hubs.py")
    materialize_public_routes()
    run("build_blog_index.py")
    run("site_audit.py", str(SITE))
    print(f"Netlify publish directory is ready: {SITE}")


if __name__ == "__main__":
    main()
