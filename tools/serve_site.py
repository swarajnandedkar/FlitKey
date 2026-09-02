#!/usr/bin/env python3
"""Preview the static site with extensionless and directory-index routing."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


class PrettyRouteHandler(SimpleHTTPRequestHandler):
    site_root: Path

    def translate_path(self, request_path: str) -> str:
        route = unquote(urlparse(request_path).path).lstrip("/")
        relative = Path(route)
        candidates = []
        if not route:
            candidates.append(Path("index.html"))
        elif route.endswith("/"):
            candidates.append(relative / "index.html")
        else:
            candidates.extend((relative, Path(f"{route}.html"), relative / "index.html"))

        for candidate in candidates:
            resolved = (self.site_root / candidate).resolve()
            if resolved.is_relative_to(self.site_root) and resolved.is_file():
                return str(resolved)
        return str((self.site_root / relative).resolve())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="FlitKey HP")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    PrettyRouteHandler.site_root = Path(args.directory).resolve()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), PrettyRouteHandler)
    print(f"Serving {PrettyRouteHandler.site_root} at http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
