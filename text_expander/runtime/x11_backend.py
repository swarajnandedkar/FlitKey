from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import threading
import time

from ..models import CapabilityReport, Snippet, normalize_hotkey
from ..placeholders import render_placeholders
from ..platform import probe_binary
from .base import RuntimeBackend


class X11Backend(RuntimeBackend):
    _DETAIL_RE = re.compile(r"detail:\s+(\d+)")
    _KEYMAP_REFRESH_INTERVAL = 30.0

    # Keys that move the cursor or otherwise invalidate what's on screen,
    # mirroring the Windows backend's _BUFFER_RESET_VKS.
    _BUFFER_RESET_SYMBOLS = frozenset(
        {
            "Left",
            "Right",
            "Up",
            "Down",
            "Home",
            "End",
            "Prior",
            "Next",
            "Delete",
            "Escape",
        }
    )

    _TERMINAL_NAMES = frozenset(
        {
            "gnome-terminal",
            "gnome-terminal-server",
            "ptyxis",
            "konsole",
            "alacritty",
            "kitty",
            "wezterm-gui",
            "xterm",
            "uxterm",
            "rxvt",
            "urxvt",
            "tilix",
            "xfce4-terminal",
            "terminator",
            "foot",
            "st",
            "mate-terminal",
            "lxterminal",
            "qterminal",
            "tilda",
            "guake",
            "yakuake",
            "hyper",
            "tabby",
        }
    )

    _TERMINAL_CLASSES = frozenset(
        {
            "terminal",
            "konsole",
            "alacritty",
            "kitty",
            "wezterm",
            "xterm",
            "urxvt",
            "tilix",
            "terminator",
            "ptyxis",
            "qterminal",
            "tilda",
            "guake",
            "yakuake",
        }
    )

    def __init__(self) -> None:
        self.keymap = self._load_keymap()
        self.required_tools = {
            "xinput": probe_binary("xinput"),
            "xmodmap": probe_binary("xmodmap"),
            "xdotool": probe_binary("xdotool"),
        }
        self.has_clipboard_tool = probe_binary("xclip") or probe_binary("xsel")
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
        # True while an expansion round-trip is in flight; prevents
        # keystrokes queued during injection from re-triggering the snippet.
        self._expanding = False
        # Keymap is rebuilt by the listener thread on layout change; readers
        # take a snapshot reference so they always see a consistent map.
        self._keymap_lock = threading.RLock()

    def _load_keymap(self) -> dict[int, tuple[str, str]]:
        try:
            result = subprocess.run(
                ["xmodmap", "-pke"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
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

    def _maybe_reload_keymap(self) -> None:
        """Re-run xmodmap if the keymap changed (layout switch, remap).

        Runs on interval or when encountering unmapped keycodes.
        Also rebuilds the modifier-keycode sets so hotkey detection tracks the new map.
        """
        fresh = self._load_keymap()
        if not fresh:
            return
        with self._keymap_lock:
            if fresh == self.keymap:
                return
            self.keymap = fresh
            self._modifier_keycodes = self._detect_modifier_keycodes()
            # Buffer may contain characters decoded under the old layout.
            self._buffer = ""
        self.status_changed.emit("Keyboard layout changed; keymap refreshed.")

    def start(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        with self._state_lock:
            self._snippets = list(snippets)
            self._case_sensitive = case_sensitive
        if not all(self.required_tools.values()):
            self.status_changed.emit(self.capability_report.status_message)
            return
        with self._state_lock:
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

    def reload(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        # Snippets are snapshotted under the lock by every handler, so a
        # running listener can pick up new data without being torn down —
        # no keystroke gap, no xinput respawn per edit.
        if self._is_running():
            with self._state_lock:
                self._snippets = list(snippets)
                self._case_sensitive = case_sensitive
            return
        self.stop()
        self.start(snippets, case_sensitive)

    def stop(self) -> None:
        with self._state_lock:
            self._running = False
            process = self._process
            self._process = None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=2.0)
        self._thread = None
        with self._state_lock:
            self._buffer = ""
            self._pressed_keycodes.clear()

    def can_inject_text(self) -> bool:
        return self.required_tools.get("xdotool", False)

    def _get_clipboard(self) -> str | None:
        if probe_binary("xclip"):
            try:
                res = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=0.5,
                )
                if res.returncode == 0:
                    return res.stdout.decode("utf-8", errors="replace")
            except Exception:
                pass
        if probe_binary("xsel"):
            try:
                res = subprocess.run(
                    ["xsel", "--clipboard", "--output"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=0.5,
                )
                if res.returncode == 0:
                    return res.stdout.decode("utf-8", errors="replace")
            except Exception:
                pass
        return None

    def _set_clipboard(self, text: str) -> bool:
        encoded = text.encode("utf-8")
        success = False
        if probe_binary("xclip"):
            try:
                res1 = subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=encoded,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1.0,
                )
                res2 = subprocess.run(
                    ["xclip", "-selection", "primary"],
                    input=encoded,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1.0,
                )
                success = (res1.returncode == 0)
            except Exception:
                pass
        if not success and probe_binary("xsel"):
            try:
                res1 = subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=encoded,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1.0,
                )
                res2 = subprocess.run(
                    ["xsel", "--primary", "--input"],
                    input=encoded,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1.0,
                )
                success = (res1.returncode == 0)
            except Exception:
                pass
        return success

    def _is_terminal_window(self) -> bool:
        try:
            pid_res = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowpid"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=0.3,
            )
            if pid_res.returncode == 0 and pid_res.stdout.strip().isdigit():
                pid = int(pid_res.stdout.strip())
                comm_path = Path(f"/proc/{pid}/comm")
                if comm_path.exists():
                    comm = comm_path.read_text(encoding="utf-8", errors="ignore").strip().lower()
                    if any(term in comm for term in self._TERMINAL_NAMES):
                        return True
        except Exception:
            pass

        try:
            win_res = subprocess.run(
                ["xdotool", "getactivewindow"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=0.3,
            )
            if win_res.returncode == 0 and win_res.stdout.strip().isdigit():
                win_id = win_res.stdout.strip()
                prop_res = subprocess.run(
                    ["xprop", "-id", win_id, "WM_CLASS"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=0.3,
                )
                if prop_res.returncode == 0:
                    prop_lower = prop_res.stdout.lower()
                    if any(term in prop_lower for term in self._TERMINAL_CLASSES):
                        return True
        except Exception:
            pass
        return False

    def inject_text(self, text: str, preserve_trailing_newline: bool = True) -> bool:
        if not self.can_inject_text():
            return False
        with self._state_lock:
            self._suppress_until = time.time() + 1.0
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

        # Fast atomic clipboard injection: avoids slow character-by-character typing
        # and prevents chat/web text fields from submitting on paragraph newlines.
        if self._inject_via_clipboard(typed_text, move_left):
            return True

        # Fallback to simulated typing if clipboard tools are unavailable
        return self._inject_via_typing(typed_text, move_left)

    def _inject_via_clipboard(self, text: str, move_left: int = 0) -> bool:
        if not (probe_binary("xclip") or probe_binary("xsel")):
            return False

        if not text:
            return True

        if not self._set_clipboard(text):
            return False

        # Brief pause to ensure X11 clipboard ownership is settled
        time.sleep(0.02)

        is_terminal = self._is_terminal_window()
        paste_key = "ctrl+shift+v" if is_terminal else "ctrl+v"

        pasted = False
        try:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", paste_key],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
            pasted = True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            try:
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "Shift+Insert"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                )
                pasted = True
            except Exception:
                pasted = False

        if not pasted:
            return False

        # Brief delay to allow target application to process paste event
        time.sleep(0.04)

        if move_left > 0:
            try:
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "--repeat", str(move_left), "Left"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                )
            except Exception:
                pass

        return True

    def _inject_via_typing(self, text: str, move_left: int = 0) -> bool:
        try:
            # If text has multiple paragraphs/lines, never send Return keys.
            # Split by line and type line by line with Shift+Return to avoid early submit.
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if line:
                    subprocess.run(
                        ["xdotool", "type", "--clearmodifiers", "--delay", "0", line],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=10.0,
                    )
                if i < len(lines) - 1:
                    # Use Shift+Return instead of plain Return so it creates a line break
                    # without submitting forms or sending chat messages
                    subprocess.run(
                        ["xdotool", "key", "--clearmodifiers", "Shift+Return"],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2.0,
                    )

            if move_left > 0:
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "--repeat", str(move_left), "Left"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
        return True

    def _strip_single_trailing_newline(self, text: str) -> str:
        if text.endswith("\r\n"):
            return text[:-2]
        if text.endswith("\n") or text.endswith("\r"):
            return text[:-1]
        return text

    def _read_events(self) -> None:
        with self._state_lock:
            process = self._process
        if not process or not process.stdout:
            return
        stream = process.stdout
        current_event: str | None = None
        current_detail: int | None = None
        last_keymap_check = time.time()
        for line in stream:
            if not self._is_running():
                break
            # Periodically refresh the keymap so layout switches and
            # remaps are picked up without an app restart.
            if time.time() - last_keymap_check >= self._KEYMAP_REFRESH_INTERVAL:
                last_keymap_check = time.time()
                self._maybe_reload_keymap()

            stripped = line.strip()
            # EVENT type 4/5 are XI2 raw button press/release; a mouse click
            # moves the cursor, so the typed-text buffer is no longer valid.
            if stripped.startswith("EVENT type 4"):
                current_event = "button_press"
                current_detail = None
            elif stripped.startswith("EVENT type 5"):
                current_event = None
                current_detail = None
                self._buffer = ""
            elif stripped.startswith("EVENT type 13"):
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

    def _is_running(self) -> bool:
        with self._state_lock:
            return self._running and self._process is not None

    def _handle_press(self, keycode: int) -> None:
        with self._state_lock:
            self._pressed_keycodes.add(keycode)
            if self._paused or self._expanding or time.time() < self._suppress_until:
                return

            if self._is_hotkey_match(keycode):
                return

            # Navigation/clearing keys invalidate the on-screen text the buffer
            # is modelling, same as the Windows backend.
            symbols = self.keymap.get(keycode)
            if symbols and symbols[0] in self._BUFFER_RESET_SYMBOLS:
                self._buffer = ""
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
        with self._state_lock:
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
            active_modifiers.append("Win")

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

    # Shared normalizer lives in models so duplicate detection and
    # trigger matching can never diverge.
    _normalize_hotkey = staticmethod(normalize_hotkey)

    def _hotkey_name_for_keycode(self, keycode: int) -> str | None:
        symbols = self.keymap.get(keycode)
        if not symbols:
            # Unknown keycode: the layout may have changed since startup.
            self._maybe_reload_keymap()
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
            # Unknown keycode: the layout may have changed since startup.
            self._maybe_reload_keymap()
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
        with self._state_lock:
            if self._expanding:
                return
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
            # Claim the expansion so queued keypresses during the injection
            # round-trip cannot trigger a second (duplicate) expansion.
            self._expanding = True
        try:
            self._expand_keyword(snippet)
        finally:
            with self._state_lock:
                self._expanding = False

    def _expand_keyword(self, snippet: Snippet) -> None:
        trigger_length = len(snippet.keyword)
        with self._state_lock:
            self._suppress_until = time.time() + 1.0
        try:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", *["BackSpace"] * trigger_length],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return
        time.sleep(0.015)
        self.inject_text(snippet.expansion_text, preserve_trailing_newline=False)
        with self._state_lock:
            self._buffer = ""
            self._suppress_until = time.time() + 0.1
        self.snippet_triggered.emit(snippet.label)
