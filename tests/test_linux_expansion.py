from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from text_expander.models import Snippet
from text_expander.runtime.x11_backend import X11Backend


class LinuxExpansionTests(unittest.TestCase):
    def setUp(self) -> None:
        keymap = {
            38: ("a", "A"),
            39: ("s", "S"),
            22: ("BackSpace", "BackSpace"),
            36: ("Return", "Return"),
        }
        with patch.object(X11Backend, "_load_keymap", return_value=keymap), patch(
            "text_expander.runtime.x11_backend.probe_binary", return_value=True
        ):
            self.backend = X11Backend()

    def test_multi_paragraph_expansion_uses_atomic_clipboard_paste(self) -> None:
        multi_paragraph_text = (
            "Dear Team,\n\n"
            "This is paragraph one with important information.\n\n"
            "This is paragraph two with further details.\n\n"
            "Best regards,\n"
            "Swaraj"
        )
        calls = []
        clipboard_set = []

        def fake_run(cmd, input=None, **kwargs):
            calls.append((cmd, input))
            if input is not None:
                clipboard_set.append(input.decode("utf-8"))
            return SimpleNamespace(returncode=0, stdout=b"")

        snippet = Snippet(
            label="Team Update",
            trigger_type="keyword",
            keyword=":update",
            expansion_text=multi_paragraph_text,
        )
        self.backend._snippets = [snippet]

        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            self.backend._expand_keyword(snippet)

        # 1. Backspaces were sent to erase trigger keyword
        self.assertEqual(calls[0][0], ["xdotool", "key", "--clearmodifiers", *["BackSpace"] * len(":update")])

        # 2. Entire multi-paragraph text was copied to clipboard intact (no character-by-character typing)
        self.assertIn(multi_paragraph_text, clipboard_set)

        # 3. Paste key was sent
        paste_calls = [cmd for cmd, _ in calls if cmd[:3] == ["xdotool", "key", "--clearmodifiers"] and "ctrl+v" in cmd]
        self.assertEqual(len(paste_calls), 1)

    def test_terminal_window_uses_terminal_paste_key(self) -> None:
        calls = []

        def fake_run(cmd, input=None, **kwargs):
            calls.append(cmd)
            # If xdotool getactivewindow getwindowpid or xprop is called, mock terminal response
            if "getwindowpid" in cmd:
                return SimpleNamespace(returncode=0, stdout="99999\n")
            return SimpleNamespace(returncode=0, stdout=b"")

        with patch("text_expander.runtime.x11_backend.Path.exists", return_value=True):
            with patch("text_expander.runtime.x11_backend.Path.read_text", return_value="gnome-terminal-server\n"):
                with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
                    self.assertTrue(self.backend.inject_text("ls -la"))

        paste_calls = [cmd for cmd in calls if cmd == ["xdotool", "key", "--clearmodifiers", "ctrl+shift+v"]]
        self.assertEqual(len(paste_calls), 1)

    def test_cursor_placement_in_multi_paragraph_snippet(self) -> None:
        snippet_text = "Header\n\n{{cursor}}\n\nFooter"
        calls = []

        def fake_run(cmd, input=None, **kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=0, stdout=b"")

        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            self.assertTrue(self.backend.inject_text(snippet_text))

        # after_cursor is "\n\nFooter" which has len 8
        cursor_calls = [cmd for cmd in calls if cmd == ["xdotool", "key", "--clearmodifiers", "--repeat", "8", "Left"]]
        self.assertEqual(len(cursor_calls), 1)

    def test_fallback_to_typing_when_clipboard_fails(self) -> None:
        calls = []

        def fake_run(cmd, input=None, **kwargs):
            calls.append(cmd)
            # Simulate xclip error
            if "xclip" in cmd[0] or "xsel" in cmd[0]:
                raise FileNotFoundError("xclip not found")
            return SimpleNamespace(returncode=0)

        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            self.assertTrue(self.backend.inject_text("multi\nline"))

        # Fallback typing was used with --delay 0 and Shift+Return for line break (no plain Return)
        type_calls = [cmd for cmd in calls if cmd[:4] == ["xdotool", "type", "--clearmodifiers", "--delay"]]
        self.assertEqual(len(type_calls), 2)
        self.assertEqual(type_calls[0][5], "multi")
        self.assertEqual(type_calls[1][5], "line")

        newline_calls = [cmd for cmd in calls if cmd == ["xdotool", "key", "--clearmodifiers", "Shift+Return"]]
        self.assertEqual(len(newline_calls), 1)

    def test_keystrokes_ignored_while_expanding(self) -> None:
        self.backend._buffer = "test"
        self.backend._expanding = True
        # Press key 'a' (keycode 38) while expanding
        self.backend._handle_press(38)
        # Buffer should remain unchanged because _expanding was True
        self.assertEqual(self.backend._buffer, "test")


if __name__ == "__main__":
    unittest.main()
