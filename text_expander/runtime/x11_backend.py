from __future__ import annotations

import re
import subprocess
import threading
import time

from ..models import CapabilityReport, Snippet
from ..placeholders import render_placeholders
from ..platform import probe_binary
from .base import RuntimeBackend


class X11Backend(RuntimeBackend):
    _DETAIL_RE = re.compile(r"detail:\s+(\d+)")

    def __init__(self) -> None:
        self.keymap = self._load_keymap()
        self.required_tools = {
            "xinput": probe_binary("xinput"),
            "xmodmap": probe_binary("xmodmap"),
            "xdotool": probe_binary("xdotool"),
        }
        ready = all(self.required_tools.values())
        report = CapabilityReport(
            session_type="x11",
            backend_name="x11-native",
            typed_expansion_supported=ready,
            global_hotkeys_supported=ready,
            tray_supported=True,
            autostart_supported=True,
            status_message=(
                "X11 backend ready."
                if ready
                else "X11 detected, but required tools are missing: "
                + ", ".join(name for name, ok in self.required_tools.items() if not ok)
            ),
        )
        super().__init__(report)
        self._snippets: list[Snippet] = []
        self._case_sensitive = False
        self._process: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._buffer = ""
        self._pressed_keycodes: set[int] = set()
        self._modifier_keycodes = self._detect_modifier_keycodes()
        self._suppress_until = 0.0

    def _load_keymap(self) -> dict[int, tuple[str, str]]:
        try:
            result = subprocess.run(
                ["xmodmap", "-pke"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return {}

        mapping: dict[int, tuple[str, str]] = {}
        for line in result.stdout.splitlines():
            if not line.startswith("keycode"):
                continue
            parts = line.split("=")
            if len(parts) != 2:
                continue
            keycode = int(parts[0].split()[1])
            symbols = parts[1].split()
            primary = symbols[0] if symbols else ""
            shifted = symbols[1] if len(symbols) > 1 else primary
            mapping[keycode] = (primary, shifted)
        return mapping

    def _detect_modifier_keycodes(self) -> dict[str, set[int]]:
        modifiers = {"shift": set(), "ctrl": set(), "alt": set(), "super": set()}
        for keycode, (primary, _) in self.keymap.items():
            if primary.startswith("Shift"):
                modifiers["shift"].add(keycode)
            elif primary.startswith("Control"):
                modifiers["ctrl"].add(keycode)
            elif primary.startswith("Alt") or primary.startswith("Meta"):
                modifiers["alt"].add(keycode)
            elif primary.startswith("Super"):
                modifiers["super"].add(keycode)
        return modifiers

    def start(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        self._snippets = snippets
        self._case_sensitive = case_sensitive
        if not all(self.required_tools.values()):
            self.status_changed.emit(self.capability_report.status_message)
            return
        if self._running:
            return

        self._running = True
        self._process = subprocess.Popen(
            ["xinput", "test-xi2", "--root"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._thread = threading.Thread(target=self._read_events, daemon=True)
        self._thread.start()
        self.status_changed.emit(self.capability_report.status_message)

    def stop(self) -> None:
        self._running = False
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    def can_inject_text(self) -> bool:
        return self.required_tools.get("xdotool", False)

    def inject_text(self, text: str, preserve_trailing_newline: bool = True) -> bool:
        if not self.can_inject_text():
            return False
        self._suppress_until = time.time() + 0.5
        rendered = render_placeholders(text)
        if not preserve_trailing_newline:
            rendered = self._strip_single_trailing_newline(rendered)

        cursor_index = rendered.find("{{cursor}}")
        if cursor_index != -1:
            before_cursor = rendered[:cursor_index]
            after_cursor = rendered[cursor_index + len("{{cursor}}"):]
            typed_text = before_cursor + after_cursor
            move_left = len(after_cursor)
        else:
            typed_text = rendered
            move_left = 0

        try:
            subprocess.run(
                ["xdotool", "type", "--clearmodifiers", "--delay", "1", typed_text],
                check=True,
                capture_output=True,
                text=True,
            )
            if move_left > 0:
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "--repeat", str(move_left), "Left"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
        return True

    def _strip_single_trailing_newline(self, text: str) -> str:
        if text.endswith("\r\n"):
            return text[:-2]
        if text.endswith("\n") or text.endswith("\r"):
            return text[:-1]
        return text

    def _read_events(self) -> None:
        assert self._process and self._process.stdout
        current_event: str | None = None
        current_detail: int | None = None
        for line in self._process.stdout:
            if not self._running:
                break
            stripped = line.strip()
            if stripped.startswith("EVENT type 13"):
                current_event = "raw_press"
                current_detail = None
            elif stripped.startswith("EVENT type 14"):
                current_event = "raw_release"
                current_detail = None
            elif current_event and stripped.startswith("detail:"):
                match = self._DETAIL_RE.search(stripped)
                if match:
                    current_detail = int(match.group(1))
                    if current_event == "raw_press":
                        self._handle_press(current_detail)
                    elif current_event == "raw_release":
                        self._handle_release(current_detail)
                    current_event = None
                    current_detail = None

    def _handle_press(self, keycode: int) -> None:
        self._pressed_keycodes.add(keycode)
        if self._paused or time.time() < self._suppress_until:
            return

        if self._is_hotkey_match(keycode):
            return

        text = self._keycode_to_text(keycode)
        if text is None:
            return
        if text == "\b":
            self._buffer = self._buffer[:-1]
            return
        if text in {"\n", "\t"}:
            self._buffer = ""
            return

        self._buffer = (self._buffer + text)[-100:]
        self._check_keyword_match()

    def _handle_release(self, keycode: int) -> None:
        self._pressed_keycodes.discard(keycode)

    def _is_hotkey_match(self, keycode: int) -> bool:
        key_name = self._hotkey_name_for_keycode(keycode)
        if not key_name:
            return False

        active_modifiers = []
        if self._pressed_keycodes & self._modifier_keycodes["ctrl"]:
            active_modifiers.append("Ctrl")
        if self._pressed_keycodes & self._modifier_keycodes["alt"]:
            active_modifiers.append("Alt")
        if self._pressed_keycodes & self._modifier_keycodes["shift"]:
            active_modifiers.append("Shift")
        if self._pressed_keycodes & self._modifier_keycodes["super"]:
            active_modifiers.append("Super")

        pressed = "+".join(active_modifiers + [key_name])
        for snippet in self._snippets:
            if not snippet.enabled or snippet.trigger_type != "hotkey" or not snippet.hotkey:
                continue
            if self._normalize_hotkey(snippet.hotkey) != self._normalize_hotkey(pressed):
                continue
            if self.inject_text(snippet.expansion_text):
                self.snippet_triggered.emit(snippet.label)
            return True
        return False

    def _normalize_hotkey(self, value: str) -> str:
        parts = [part.strip().title() for part in value.split("+") if part.strip()]
        if not parts:
            return ""
        key = parts[-1].upper() if len(parts[-1]) == 1 else parts[-1].title()
        mods_order = ["Ctrl", "Alt", "Shift", "Super"]
        modifiers = sorted(
            parts[:-1],
            key=lambda item: mods_order.index(item) if item in mods_order else 99
        )
        return "+".join(modifiers + [key])

    def _hotkey_name_for_keycode(self, keycode: int) -> str | None:
        symbols = self.keymap.get(keycode)
        if not symbols:
            return None
        primary = symbols[0]
        if primary.startswith(("Shift", "Control", "Alt", "Super", "Meta")):
            return None
        if len(primary) == 1:
            return primary.upper()
        special_map = {
            "space": "Space",
            "Return": "Enter",
            "Tab": "Tab",
            "Escape": "Escape",
        }
        return special_map.get(primary)

    def _keycode_to_text(self, keycode: int) -> str | None:
        symbols = self.keymap.get(keycode)
        if not symbols:
            return None

        shift_active = bool(self._pressed_keycodes & self._modifier_keycodes["shift"])
        symbol = symbols[1] if shift_active else symbols[0]
        translation = {
            "space": " ",
            "BackSpace": "\b",
            "Return": "\n",
            "Tab": "\t",
            "minus": "-",
            "underscore": "_",
            "equal": "=",
            "plus": "+",
            "bracketleft": "[",
            "braceleft": "{",
            "bracketright": "]",
            "braceright": "}",
            "semicolon": ";",
            "colon": ":",
            "apostrophe": "'",
            "quotedbl": '"',
            "comma": ",",
            "less": "<",
            "period": ".",
            "greater": ">",
            "slash": "/",
            "question": "?",
            "backslash": "\\",
            "bar": "|",
            "grave": "`",
            "asciitilde": "~",
            "exclam": "!",
            "at": "@",
            "numbersign": "#",
            "dollar": "$",
            "percent": "%",
            "asciicircum": "^",
            "ampersand": "&",
            "asterisk": "*",
            "parenleft": "(",
            "parenright": ")",
        }
        if len(symbol) == 1:
            return symbol
        return translation.get(symbol)

    def _check_keyword_match(self) -> None:
        buffer_value = self._buffer if self._case_sensitive else self._buffer.lower()
        matches = []
        for snippet in self._snippets:
            if not snippet.enabled or snippet.trigger_type != "keyword" or not snippet.keyword:
                continue
            keyword = snippet.keyword if self._case_sensitive else snippet.keyword.lower()
            if buffer_value.endswith(keyword):
                matches.append((len(keyword), snippet))
        if not matches:
            return
        _, snippet = max(matches, key=lambda item: item[0])
        self._expand_keyword(snippet)

    def _expand_keyword(self, snippet: Snippet) -> None:
        trigger_length = len(snippet.keyword)
        self._suppress_until = time.time() + 0.6
        try:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", *["BackSpace"] * trigger_length],
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return
        self.inject_text(snippet.expansion_text, preserve_trailing_newline=False)
        self._buffer = ""
        self.snippet_triggered.emit(snippet.label)
