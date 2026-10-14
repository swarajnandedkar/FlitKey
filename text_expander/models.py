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
    "meta": "Win",
}
_HOTKEY_KEY_ALIASES = {
    "return": "Enter",
    "enter": "Enter",
    "esc": "Escape",
    "escape": "Escape",
    "space": "Space",
    "backspace": "Backspace",
    "del": "Delete",
    "delete": "Delete",
    "pgup": "PageUp",
    "pageup": "PageUp",
    "pgdown": "PageDown",
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
    pack_id: str = ""
    use_count: int = 0
    word_boundary: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))

    def keystrokes_saved_per_use(self) -> int:
        return max(len(self.expansion_text) - len(self.trigger_value()), 0)

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
            "pack_id": self.pack_id,
            "use_count": self.use_count,
            "word_boundary": self.word_boundary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snippet":
        raw_id = data.get("id")
        try:
            snippet_id = str(raw_id) if raw_id else str(uuid4())
        except Exception:
            snippet_id = str(uuid4())

        raw_label = data.get("label", "")
        if raw_label is None:
            raw_label = ""
        elif not isinstance(raw_label, str):
            try:
                raw_label = str(raw_label)
            except Exception:
                raw_label = ""
        label = raw_label.strip()

        trigger_type = data.get("trigger_type", "keyword")
        if trigger_type not in ("keyword", "hotkey"):
            trigger_type = "keyword"

        def _safe_str(key: str, default: str = "") -> str:
            value = data.get(key, default)
            if value is None:
                return default
            if isinstance(value, str):
                return value
            try:
                return str(value)
            except Exception:
                return default

        raw_use_count = data.get("use_count", 0)
        try:
            use_count = max(int(raw_use_count or 0), 0)
        except (ValueError, TypeError):
            use_count = 0

        return cls(
            id=snippet_id,
            label=label,
            trigger_type=trigger_type,  # type: ignore[arg-type]
            keyword=_safe_str("keyword"),
            hotkey=_safe_str("hotkey"),
            expansion_text=_safe_str("expansion_text"),
            enabled=bool(data.get("enabled", True)),
            pack_id=_safe_str("pack_id"),
            use_count=use_count,
            word_boundary=bool(data.get("word_boundary", False)),
        )


def usage_stats(snippets: list[Snippet]) -> tuple[int, int]:
    """Return (total uses, total keystrokes saved) across all snippets."""
    uses = sum(s.use_count for s in snippets)
    saved = sum(s.use_count * s.keystrokes_saved_per_use() for s in snippets)
    return uses, saved


DEFAULT_EXCLUDED_APPS: list[str] = [
    # Password managers & authenticators
    "keepassxc",
    "keepass",
    "1password",
    "bitwarden",
    "lastpass",
    "dashlane",
    "enpass",
    "keypass",
    "authenticator",
    # Authentication & credential dialogs
    "pinentry",
    "polkit",
    "gcr-prompter",
    "ssh-askpass",
    "ksshaskpass",
    "gnome-keyring",
    "kwallet",
    "credentialhelper",
    "pageant",
    "winlogon",
    "logonui",
    "consent.exe",
    # Remote access & virtualization
    "mstsc.exe",
    "teamviewer",
    "anydesk",
    "vncviewer",
    "remmina",
    "putty",
    # Administrative consoles & shells
    "cmd.exe",
    "powershell.exe",
    "powershell_ise.exe",
    "wt.exe",
]


@dataclass
class Settings:
    autostart: bool = False
    start_minimized: bool = True
    paused: bool = False
    case_sensitive: bool = False
    wayland_fallback_mode: str = "hotkeys_and_picker"
    notify_on_expansion: bool = True
    excluded_apps: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDED_APPS))
    pause_hotkey: str = "Ctrl+Alt+P"

    def to_dict(self) -> dict:
        return {
            "autostart": self.autostart,
            "start_minimized": self.start_minimized,
            "paused": self.paused,
            "case_sensitive": self.case_sensitive,
            "wayland_fallback_mode": self.wayland_fallback_mode,
            "notify_on_expansion": self.notify_on_expansion,
            "excluded_apps": list(self.excluded_apps),
            "pause_hotkey": self.pause_hotkey,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        raw_excluded = data.get("excluded_apps")
        if raw_excluded is None or not isinstance(raw_excluded, list):
            excluded_apps = list(DEFAULT_EXCLUDED_APPS)
        else:
            excluded_apps = [str(x).strip() for x in raw_excluded if str(x).strip()]

        raw_pause_hk = str(data.get("pause_hotkey") or "Ctrl+Alt+P").strip()
        pause_hotkey = normalize_hotkey(raw_pause_hk) or "Ctrl+Alt+P"

        raw_mode = data.get("wayland_fallback_mode", "hotkeys_and_picker")
        if not isinstance(raw_mode, str) or not raw_mode.strip():
            raw_mode = "hotkeys_and_picker"

        return cls(
            autostart=bool(data.get("autostart", False)),
            start_minimized=bool(data.get("start_minimized", True)),
            paused=bool(data.get("paused", False)),
            case_sensitive=bool(data.get("case_sensitive", False)),
            wayland_fallback_mode=raw_mode,
            notify_on_expansion=bool(data.get("notify_on_expansion", True)),
            excluded_apps=excluded_apps,
            pause_hotkey=pause_hotkey,
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
