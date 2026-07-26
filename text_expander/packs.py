from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .config import app_config_dir
from .models import Snippet


@dataclass
class PackMetadata:
    pack_id: str
    name: str
    description: str
    version: str
    snippet_count: int
    file_path: Path


def get_builtin_packs_dir() -> Path:
    return Path(__file__).parent / "packs"


def get_user_packs_dir() -> Path:
    user_packs = app_config_dir() / "packs"
    user_packs.mkdir(parents=True, exist_ok=True)
    return user_packs


def list_available_packs() -> list[PackMetadata]:
    """Scan built-in and user pack directories for expansion pack JSON files."""
    packs: list[PackMetadata] = []
    seen_ids: set[str] = set()

    search_dirs = [get_user_packs_dir(), get_builtin_packs_dir()]
    for pdir in search_dirs:
        if not pdir.exists():
            continue
        for json_file in sorted(pdir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "pack_id" in data and "snippets" in data:
                    pid = data["pack_id"]
                    if pid in seen_ids:
                        continue
                    seen_ids.add(pid)
                    snippets_list = data.get("snippets", [])
                    packs.append(
                        PackMetadata(
                            pack_id=pid,
                            name=data.get("name", pid.title()),
                            description=data.get("description", ""),
                            version=data.get("version", "1.0.0"),
                            snippet_count=len(snippets_list) if isinstance(snippets_list, list) else 0,
                            file_path=json_file,
                        )
                    )
            except (json.JSONDecodeError, OSError):
                continue

    return packs


def load_pack_snippets(file_path: Path, target_platform: str | None = None) -> list[Snippet]:
    """Load snippets from a pack JSON file, applying platform filtering if requested."""
    snippets: list[Snippet] = []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return snippets

    raw_snippets = data.get("snippets", [])
    if not isinstance(raw_snippets, list):
        return snippets

    # Resolve platform query string
    current_os = target_platform or sys.platform
    if current_os.startswith("win"):
        current_os_key = "windows"
    elif current_os.startswith("linux"):
        current_os_key = "linux"
    else:
        current_os_key = "all"

    for item in raw_snippets:
        if not isinstance(item, dict):
            continue
        platform = item.get("platform", "all").lower()
        if platform != "all" and current_os_key != "all" and platform != current_os_key:
            continue

        label = item.get("label", "").strip()
        kw = item.get("keyword", "").strip()
        hk = item.get("hotkey", "").strip()
        tt = item.get("trigger_type", "keyword")
        exp = item.get("expansion_text", "")
        enabled = bool(item.get("enabled", True))

        if label and (kw or hk) and exp:
            snippets.append(
                Snippet(
                    label=label,
                    trigger_type=tt,
                    keyword=kw,
                    hotkey=hk,
                    expansion_text=exp,
                    enabled=enabled,
                )
            )

    return snippets


def merge_pack_snippets(
    current_snippets: Sequence[Snippet], new_snippets: Sequence[Snippet]
) -> tuple[list[Snippet], int]:
    """Merge new snippets into existing snippets, preventing duplicate triggers."""
    existing_triggers = {
        (s.trigger_type, s.keyword.lower() if s.trigger_type == "keyword" else s.hotkey.lower())
        for s in current_snippets
    }

    result = list(current_snippets)
    added_count = 0

    for snippet in new_snippets:
        trg_val = snippet.keyword.lower() if snippet.trigger_type == "keyword" else snippet.hotkey.lower()
        trg_key = (snippet.trigger_type, trg_val)
        if trg_key not in existing_triggers:
            existing_triggers.add(trg_key)
            result.append(snippet)
            added_count += 1

    return result, added_count
