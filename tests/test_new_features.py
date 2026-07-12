from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication
from text_expander.models import Snippet
from text_expander.placeholders import render_placeholders
from text_expander.runtime.x11_backend import X11Backend
from text_expander.gui.main_window import MainWindow

# Initialize headless QApplication for QWidget testing
app = QApplication.instance() or QApplication(["-platform", "offscreen"])


class NewFeaturesTests(unittest.TestCase):
    def setUp(self) -> None:
        keymap = {
            38: ("a", "A"),
            39: ("s", "S"),
        }
        with patch.object(X11Backend, "_load_keymap", return_value=keymap), patch(
            "text_expander.runtime.x11_backend.probe_binary", return_value=True
        ):
            self.backend = X11Backend()

    def test_render_placeholders_clipboard(self) -> None:
        # Mock the QGuiApplication clipboard
        mock_clipboard = MagicMock()
        mock_clipboard.text.return_value = "hello_clip"

        with patch("PyQt6.QtGui.QGuiApplication.clipboard", return_value=mock_clipboard):
            result = render_placeholders("copied: {{clipboard}}")
            self.assertEqual(result, "copied: hello_clip")

    def test_inject_text_with_cursor_sends_repeat_left(self) -> None:
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            # Expands print({{cursor}}) and moves left 1 character (for the closing parenthesis)
            self.assertTrue(self.backend.inject_text("print({{cursor}})"))

        self.assertEqual(len(calls), 2)

        # Check type call (removes {{cursor}})
        self.assertEqual(calls[0][:4], ["xdotool", "type", "--clearmodifiers", "--delay"])
        self.assertEqual(calls[0][-1], "print()")

        # Check cursor movement call (moves left 1 keypress)
        self.assertEqual(calls[1], ["xdotool", "key", "--clearmodifiers", "--repeat", "1", "Left"])

    def test_inject_text_without_cursor(self) -> None:
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            self.assertTrue(self.backend.inject_text("simple text"))

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-1], "simple text")

    def test_search_filtering_in_main_window(self) -> None:
        window = MainWindow()
        snippets = [
            Snippet(
                label="Email Signature",
                trigger_type="keyword",
                keyword=";sig",
                expansion_text="Best regards,\nSwaraj"
            ),
            Snippet(label="Greeting", trigger_type="keyword", keyword=";hi", expansion_text="Hello there!"),
            Snippet(label="Command", trigger_type="hotkey", hotkey="Ctrl+Alt+C", expansion_text="clear"),
        ]
        window.update_snippets(snippets)

        # Initially all rows are visible
        for row in range(3):
            self.assertFalse(window.snippet_table.isRowHidden(row))

        # Filter for "sig" - only row 0 should match
        window.search_input.setText("sig")
        self.assertFalse(window.snippet_table.isRowHidden(0))
        self.assertTrue(window.snippet_table.isRowHidden(1))
        self.assertTrue(window.snippet_table.isRowHidden(2))

        # Filter for "hotkey" - only row 2 should match
        window.search_input.setText("hotkey")
        self.assertTrue(window.snippet_table.isRowHidden(0))
        self.assertTrue(window.snippet_table.isRowHidden(1))
        self.assertFalse(window.snippet_table.isRowHidden(2))

        # Clear search filter - all rows visible again
        window.search_input.setText("")
        for row in range(3):
            self.assertFalse(window.snippet_table.isRowHidden(row))


if __name__ == "__main__":
    unittest.main()
