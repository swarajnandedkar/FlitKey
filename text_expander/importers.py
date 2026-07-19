from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Sequence

from .models import Snippet


def parse_espanso_yaml(content: str) -> list[Snippet]:
    """Parse Espanso YML/YAML configuration files."""
    snippets: list[Snippet] = []

    # Try PyYAML if installed
    try:
        import yaml
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            matches = data.get("matches", [])
            if isinstance(matches, list):
                for item in matches:
                    if not isinstance(item, dict):
                        continue
                    replace_text = item.get("replace") or item.get("form") or ""
                    label = item.get("label") or ""
                    
                    # Single trigger
                    trigger = item.get("trigger")
                    if isinstance(trigger, str) and trigger:
                        lbl = label or f"Espanso: {trigger}"
                        snippets.append(Snippet(label=lbl, trigger_type="keyword", keyword=trigger, expansion_text=replace_text))
                    
                    # Multiple triggers
                    triggers = item.get("triggers")
                    if isinstance(triggers, list):
                        for trg in triggers:
                            if isinstance(trg, str) and trg:
                                lbl = label or f"Espanso: {trg}"
                                snippets.append(Snippet(label=lbl, trigger_type="keyword", keyword=trg, expansion_text=replace_text))
                if snippets:
                    return snippets
    except ImportError:
        pass

    # Built-in lightweight fallback parser for Espanso YAML
    current_trigger: str | None = None
    current_triggers: list[str] = []
    current_replace: str | None = None
    current_label: str | None = None

    def flush_current():
        nonlocal current_trigger, current_triggers, current_replace, current_label
        exp = current_replace or ""
        if current_trigger and exp:
            lbl = current_label or f"Espanso: {current_trigger}"
            snippets.append(Snippet(label=lbl, trigger_type="keyword", keyword=current_trigger, expansion_text=exp))
        elif current_triggers and exp:
            for trg in current_triggers:
                lbl = current_label or f"Espanso: {trg}"
                snippets.append(Snippet(label=lbl, trigger_type="keyword", keyword=trg, expansion_text=exp))
        current_trigger = None
        current_triggers = []
        current_replace = None
        current_label = None

    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- "):
            flush_current()
            stripped = stripped[2:].strip()

        # Parse key-value pairs
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip("'\"")

            if key == "trigger":
                current_trigger = val
            elif key == "label":
                current_label = val
            elif key == "replace":
                current_replace = val
            elif key == "triggers":
                # Check for inline list like [":date", ":d"]
                if val.startswith("[") and val.endswith("]"):
                    items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
                    current_triggers = items

    flush_current()
    return snippets


def parse_autohotkey(content: str) -> list[Snippet]:
    """Parse AutoHotkey (.ahk) script files for hotstrings and hotkeys."""
    snippets: list[Snippet] = []

    # Match AHK Hotstrings like :*:keyword::expansion or ::keyword::expansion
    # Options can be :*:, ::, :C:, :B0:, etc.
    hotstring_pattern = re.compile(r"^:(?P<opts>[^:]*):(?P<trigger>[^:]+)::(?P<replace>.*)$")
    
    # Match AHK Hotkeys like ^!a::Send, text
    hotkey_pattern = re.compile(r"^(?P<hk>[^:]+)::\s*(?:Send(?:Input|Play|Event)?\s*,?\s*)?(?P<replace>.*)$")

    lines = content.splitlines()
    in_multiline = False
    ml_trigger = ""
    ml_type = "keyword"
    ml_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if in_multiline:
            if stripped.lower() in ("return", "} "):
                exp = "\n".join(ml_lines)
                label = f"AHK: {ml_trigger}"
                if ml_type == "keyword":
                    snippets.append(Snippet(label=label, trigger_type="keyword", keyword=ml_trigger, expansion_text=exp))
                else:
                    snippets.append(Snippet(label=label, trigger_type="hotkey", hotkey=ml_trigger, expansion_text=exp))
                in_multiline = False
                ml_lines = []
            else:
                # Strip Send commands if present
                clean_line = re.sub(r"^\s*Send(?:Input|Play|Event)?\s*,?\s*", "", line)
                ml_lines.append(clean_line)
            continue

        if not stripped or stripped.startswith(";") or stripped.startswith("//"):
            continue

        # Try Hotstring
        hs_match = hotstring_pattern.match(stripped)
        if hs_match:
            trigger = hs_match.group("trigger").strip()
            replace = hs_match.group("replace").strip()
            if replace:
                snippets.append(Snippet(label=f"AHK: {trigger}", trigger_type="keyword", keyword=trigger, expansion_text=replace))
            else:
                # Multi-line hotstring block
                in_multiline = True
                ml_trigger = trigger
                ml_type = "keyword"
                ml_lines = []
            continue

        # Try Hotkey
        hk_match = hotkey_pattern.match(stripped)
        if hk_match:
            hk = _convert_ahk_hotkey(hk_match.group("hk").strip())
            replace = hk_match.group("replace").strip()
            if replace:
                snippets.append(Snippet(label=f"AHK: {hk}", trigger_type="hotkey", hotkey=hk, expansion_text=replace))
            else:
                in_multiline = True
                ml_trigger = hk
                ml_type = "hotkey"
                ml_lines = []
            continue

    return snippets


def _convert_ahk_hotkey(ahk_hk: str) -> str:
    """Convert AHK hotkey symbols (^!+a) to FlitKey format (Ctrl+Alt+Shift+A)."""
    mods = []
    key = ahk_hk
    if "^" in key:
        mods.append("Ctrl")
        key = key.replace("^", "")
    if "!" in key:
        mods.append("Alt")
        key = key.replace("!", "")
    if "+" in key:
        mods.append("Shift")
        key = key.replace("+", "")
    if "#" in key:
        mods.append("Win")
        key = key.replace("#", "")

    key_clean = key.strip().upper()
    return "+".join(mods + [key_clean]) if mods else key_clean.title()


def parse_csv_tsv(content: str, delimiter: str = ",") -> list[Snippet]:
    """Parse CSV or TSV files containing label/trigger/expansion rows."""
    snippets: list[Snippet] = []
    reader = csv.reader(content.splitlines(), delimiter=delimiter)
    for row in reader:
        if not row or all(not cell.strip() for cell in row):
            continue

        # Skip header if present
        first = row[0].strip().lower()
        if first in ("label", "trigger", "keyword", "shortcut", "name"):
            continue

        if len(row) == 1:
            continue
        elif len(row) == 2:
            trigger = row[0].strip()
            expansion = row[1].strip()
            label = f"Import: {trigger}"
            snippets.append(Snippet(label=label, trigger_type="keyword", keyword=trigger, expansion_text=expansion))
        else:
            label = row[0].strip()
            trigger = row[1].strip()
            expansion = row[2].strip()
            snippets.append(Snippet(label=label, trigger_type="keyword", keyword=trigger, expansion_text=expansion))
    return snippets


def parse_json_snippets(content: str) -> list[Snippet]:
    """Parse JSON format (FlitKey export or generic list of snippet objects)."""
    snippets: list[Snippet] = []
    try:
        data = json.loads(content)
        items = data.get("snippets") if isinstance(data, dict) else data
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    # Check if it's already a FlitKey snippet dict
                    if "label" in item and ("keyword" in item or "hotkey" in item or "trigger" in item):
                        kw = item.get("keyword") or item.get("trigger") or ""
                        hk = item.get("hotkey") or ""
                        tt = item.get("trigger_type") or ("hotkey" if hk else "keyword")
                        exp = item.get("expansion_text") or item.get("expansion") or item.get("text") or ""
                        lbl = item.get("label") or f"Import: {kw or hk}"
                        snippets.append(Snippet(label=lbl, trigger_type=tt, keyword=kw, hotkey=hk, expansion_text=exp))
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return snippets


def import_snippets_from_file(file_path: Path) -> list[Snippet]:
    """Detect file type by extension or content and parse snippets."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    ext = file_path.suffix.lower()

    if ext in (".yml", ".yaml"):
        return parse_espanso_yaml(text)
    elif ext == ".ahk":
        return parse_autohotkey(text)
    elif ext == ".csv":
        return parse_csv_tsv(text, delimiter=",")
    elif ext == ".tsv":
        return parse_csv_tsv(text, delimiter="\t")
    elif ext == ".json":
        return parse_json_snippets(text)
    else:
        # Autodetect by content
        if "matches:" in text:
            return parse_espanso_yaml(text)
        elif "::" in text:
            return parse_autohotkey(text)
        elif text.strip().startswith("{") or text.strip().startswith("["):
            return parse_json_snippets(text)
        else:
            return parse_csv_tsv(text, delimiter="," if "," in text else "\t")
