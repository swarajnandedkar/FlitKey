from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4


TriggerType = Literal["keyword", "hotkey"]

_HOTKEY_MODIFIER_ALIASES = {
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "win": "Win",
    "windows": "Win",
    "super": "Win",
}
_HOTKEY_KEY_ALIASES = {
    "return": "Enter",
    "enter": "Enter",
    "esc": "Escape",
    "escape": "Escape",
    "space": "Space",
    "backspace": "Backspace",
    "delete": "Delete",
    "pageup": "PageUp",
    "pagedown": "PageDown",
}


def normalize_hotkey(value: str) -> str:
    """Normalize a hotkey string so duplicates compare equal across formats."""
    parts = [part.strip() for part in value.split("+") if part.strip()]
    if not parts:
        return ""

    modifiers = {
        _HOTKEY_MODIFIER_ALIASES[part.lower()]
        for part in parts
        if part.lower() in _HOTKEY_MODIFIER_ALIASES
    }
    keys = [part for part in parts if part.lower() not in _HOTKEY_MODIFIER_ALIASES]
    if not keys:
        return ""
    raw_key = keys[-1]
    lowered_key = raw_key.lower()
    if len(raw_key) == 1:
        key = raw_key.upper()
    elif lowered_key in _HOTKEY_KEY_ALIASES:
        key = _HOTKEY_KEY_ALIASES[lowered_key]
    elif lowered_key.startswith("f") and lowered_key[1:].isdigit():
        key = lowered_key.upper()
    else:
        key = raw_key.title()

    ordered = [name for name in ("Ctrl", "Alt", "Shift", "Win") if name in modifiers]
    return "+".join(ordered + [key])


@dataclass
class Snippet:
    label: str
    expansion_text: str
    trigger_type: TriggerType = "keyword"
    keyword: str = ""
    hotkey: str = ""
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))

    def trigger_value(self) -> str:
        return self.keyword if self.trigger_type == "keyword" else self.hotkey

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "trigger_type": self.trigger_type,
            "keyword": self.keyword,
            "hotkey": self.hotkey,
            "expansion_text": self.expansion_text,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snippet":
        return cls(
            id=data.get("id") or str(uuid4()),
            label=data.get("label", "").strip(),
            trigger_type=data.get("trigger_type", "keyword"),
            keyword=data.get("keyword", ""),
            hotkey=data.get("hotkey", ""),
            expansion_text=data.get("expansion_text", ""),
            enabled=bool(data.get("enabled", True)),
        )


@dataclass
class Settings:
    autostart: bool = False
    start_minimized: bool = True
    paused: bool = False
    case_sensitive: bool = False
    wayland_fallback_mode: str = "hotkeys_and_picker"
    notify_on_expansion: bool = True

    def to_dict(self) -> dict:
        return {
            "autostart": self.autostart,
            "start_minimized": self.start_minimized,
            "paused": self.paused,
            "case_sensitive": self.case_sensitive,
            "wayland_fallback_mode": self.wayland_fallback_mode,
            "notify_on_expansion": self.notify_on_expansion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        return cls(
            autostart=bool(data.get("autostart", False)),
            start_minimized=bool(data.get("start_minimized", True)),
            paused=bool(data.get("paused", False)),
            case_sensitive=bool(data.get("case_sensitive", False)),
            wayland_fallback_mode=data.get("wayland_fallback_mode", "hotkeys_and_picker"),
            notify_on_expansion=bool(data.get("notify_on_expansion", True)),
        )


@dataclass
class CapabilityReport:
    session_type: str
    backend_name: str
    typed_expansion_supported: bool
    global_hotkeys_supported: bool
    tray_supported: bool
    autostart_supported: bool
    status_message: str
