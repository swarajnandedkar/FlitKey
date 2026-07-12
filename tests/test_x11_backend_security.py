from __future__ import annotations

import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from text_expander.models import Snippet
from text_expander.runtime.x11_backend import X11Backend


class X11BackendSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        keymap = {
            38: ("a", "A"),
            39: ("s", "S"),
            50: ("Shift_L", "Shift_L"),
            37: ("Control_L", "Control_L"),
            64: ("Alt_L", "Alt_L"),
        }
        with patch.object(X11Backend, "_load_keymap", return_value=keymap), patch(
            "text_expander.runtime.x11_backend.probe_binary", return_value=True
        ):
            self.backend = X11Backend()

    def test_inject_text_passes_untrusted_text_as_single_argument(self) -> None:
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        payload = '$(touch /tmp/pwned); rm -rf / ; "quotes"'
        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            self.assertTrue(self.backend.inject_text(payload))

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-1], payload)
        self.assertEqual(calls[0][:4], ["xdotool", "type", "--clearmodifiers", "--delay"])

    def test_expand_keyword_passes_payload_as_single_argument(self) -> None:
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        snippet = Snippet(
            label="unsafe",
            trigger_type="keyword",
            keyword="/x",
            expansion_text='$(notify-send hacked) && echo bad',
        )
        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            self.backend._expand_keyword(snippet)

        self.assertEqual(calls[0], ["xdotool", "key", "--clearmodifiers", "BackSpace", "BackSpace"])
        self.assertEqual(calls[1][-1], snippet.expansion_text)

    def test_longest_keyword_match_wins(self) -> None:
        triggered = []
        self.backend._snippets = [
            Snippet(label="short", trigger_type="keyword", keyword="abc", expansion_text="SHORT"),
            Snippet(label="long", trigger_type="keyword", keyword="zabc", expansion_text="LONG"),
        ]
        self.backend._buffer = "prefixzabc"
        self.backend._case_sensitive = False

        with patch.object(self.backend, "_expand_keyword", side_effect=lambda snippet: triggered.append(snippet.label)):
            self.backend._check_keyword_match()

        self.assertEqual(triggered, ["long"])

    def test_hotkey_match_requires_explicit_modifier_combo(self) -> None:
        snippet = Snippet(label="paste", trigger_type="hotkey", hotkey="Ctrl+Alt+A", expansion_text="hello")
        self.backend._snippets = [snippet]
        self.backend._pressed_keycodes = {37, 64, 38}

        with patch.object(self.backend, "inject_text", return_value=True) as inject_mock:
            matched = self.backend._is_hotkey_match(38)

        self.assertTrue(matched)
        inject_mock.assert_called_once_with("hello")


if __name__ == "__main__":
    unittest.main()
