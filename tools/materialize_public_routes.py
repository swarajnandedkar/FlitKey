#!/usr/bin/env python3
"""Create Netlify-safe public comparison routes from clustered source pages.

The comparison articles are authored under ``blogs/comparisons``.  Netlify
drag-and-drop and some zip-based deploys do not preserve directory symlinks,
so the established root URLs must be regular files in the publish directory.
"""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "FlitKey HP"
SLUGS = (
    "phraseexpress-vs-flitkey",
    "atext-vs-flitkey",
    "textexpander-vs-flitkey",
    "espanso-vs-flitkey",
    "autohotkey-vs-flitkey",
)


def public_html(source: str) -> str:
    """Adapt clustered relative assets to the established root route."""
    return source.replace('href="../../../styles.css"', 'href="../styles.css"').replace(
        'src="../../../script.js"', 'src="../script.js"'
    )


def materialize(slug: str) -> None:
    source_dir = ROOT / "blogs" / "comparisons" / slug
    destination_dir = ROOT / slug
    destination_dir.mkdir(parents=True, exist_ok=True)

    source_index = source_dir / "index.html"
    destination_index = destination_dir / "index.html"
    destination_index.write_text(public_html(source_index.read_text(encoding="utf-8")), encoding="utf-8")

    for asset in source_dir.iterdir():
        if asset.is_file() and asset.name != "index.html":
            shutil.copy2(asset, destination_dir / asset.name)

    print(f"{destination_index} <= {source_index}")


def main() -> None:
    for slug in SLUGS:
        materialize(slug)


if __name__ == "__main__":
    main()
