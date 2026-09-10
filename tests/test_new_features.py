from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication
from text_expander.models import Snippet
from text_expander.placeholders import collect_fields, render_placeholders
from text_expander.gui.fill_dialog import FillDialog
from datetime import datetime, timedelta
from text_expander.runtime.x11_backend import X11Backend
from text_expander.gui.main_window import MainWindow
from text_expander.gui.snippet_dialog import SnippetDialog
from text_expander.gui.picker_dialog import SnippetPickerDialog
from text_expander.models import usage_stats

# Initialize headless QApplication for QWidget testing
app = QApplication.instance() or QApplication(["-platform", "offscreen"])

LINUX_ONLY = unittest.skipIf(sys.platform == "win32", "X11 backend is Linux-only")


class NewFeaturesTests(unittest.TestCase):
    def setUp(self) -> None:
        if sys.platform != "win32":
            keymap = {
                38: ("a", "A"),
                39: ("s", "S"),
            }
            self.enterContext(patch.object(X11Backend, "_load_keymap", return_value=keymap))
            self.enterContext(patch("text_expander.runtime.x11_backend.probe_binary", return_value=True))
            self.backend = X11Backend()

    def test_snippet_dialog_hotkey_round_trips_through_capture_widget(self) -> None:
        stored = Snippet(label="x", trigger_type="hotkey", hotkey="super+shift+return", expansion_text="y")
        dialog = SnippetDialog(None, stored)
        self.assertFalse(dialog.hotkey_edit.keySequence().isEmpty())
        self.assertEqual(dialog.snippet().hotkey, "Shift+Win+Enter")

    def test_render_date_offsets_and_formats(self) -> None:
        week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        self.assertEqual(render_placeholders("{{date:+7d}}"), week)
        self.assertEqual(render_placeholders("{{date:%Y}}"), datetime.now().strftime("%Y"))
        self.assertEqual(render_placeholders("{{date:-1w %Y}}"), (datetime.now() - timedelta(weeks=1)).strftime("%Y"))
        self.assertEqual(render_placeholders("a {{cursor}} {{nope}}"), "a {{cursor}} {{nope}}")

    def test_fill_in_fields_collect_render_and_dialog(self) -> None:
        text = "Hi {{field:Name}}, {{choice:Tone=Formal|Casual}} — bye {{field:Name}} {{field:Sign=Me}}"
        fields = collect_fields(text)
        self.assertEqual([(f.name, f.kind) for f in fields], [("Name", "field"), ("Tone", "choice"), ("Sign", "field")])
        self.assertEqual(fields[1].options, ["Formal", "Casual"])

        self.assertEqual(render_placeholders(text, {"Name": "Ada"}), "Hi Ada, Formal — bye Ada Me")

        dialog = FillDialog("t", fields)
        dialog._inputs["Name"].setText("Bob")
        dialog._inputs["Tone"].setCurrentIndex(1)
        self.assertEqual(dialog.values(), {"Name": "Bob", "Tone": "Casual", "Sign": "Me"})

    @LINUX_ONLY
    def test_x11_defers_to_fill_request_for_field_snippets(self) -> None:
        snippet = Snippet(label="f", keyword=";f", expansion_text="Hi {{field:Name}}")
        self.backend._snippets = [snippet]
        requests: list[tuple[str, bool]] = []
        self.backend.fill_requested.connect(lambda sid, keep: requests.append((sid, keep)))
        with patch("text_expander.runtime.x11_backend.subprocess.run"), patch.object(
            self.backend, "inject_text"
        ) as inject:
            self.backend._expand_keyword(snippet)
        inject.assert_not_called()
        self.assertEqual(requests, [(snippet.id, False)])

    def test_render_placeholders_clipboard(self) -> None:
        # Mock the QGuiApplication clipboard
        mock_clipboard = MagicMock()
        mock_clipboard.text.return_value = "hello_clip"

        with patch("PyQt6.QtGui.QGuiApplication.clipboard", return_value=mock_clipboard):
            result = render_placeholders("copied: {{clipboard}}")
            self.assertEqual(result, "copied: hello_clip")

    @LINUX_ONLY
    def test_inject_text_via_clipboard_with_cursor_sends_repeat_left(self) -> None:
        calls = []
        clipboard_contents = []

        def fake_run(cmd, input=None, **kwargs):
            calls.append((cmd, input))
            if input is not None:
                clipboard_contents.append(input.decode("utf-8"))
            return SimpleNamespace(returncode=0, stdout=b"old_clip\n")

        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            # Expands print({{cursor}}) and moves left 1 character (for the closing parenthesis)
            self.assertTrue(self.backend.inject_text("print({{cursor}})"))

        # Injected clipboard should have had {{cursor}} removed
        self.assertIn("print()", clipboard_contents)

        # Check paste key call
        paste_calls = [cmd for cmd, _ in calls if cmd[:3] == ["xdotool", "key", "--clearmodifiers"] and "ctrl+v" in cmd]
        self.assertEqual(len(paste_calls), 1)

        # Check cursor movement call (moves left 1 keypress)
        cursor_calls = [cmd for cmd, _ in calls if cmd == ["xdotool", "key", "--clearmodifiers", "--repeat", "1", "Left"]]
        self.assertEqual(len(cursor_calls), 1)

    @LINUX_ONLY
    def test_inject_text_fallback_typing_with_cursor(self) -> None:
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        with patch("text_expander.runtime.x11_backend.probe_binary", side_effect=lambda name: name == "xdotool"):
            with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
                self.assertTrue(self.backend.inject_text("print({{cursor}})"))

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][:4], ["xdotool", "type", "--clearmodifiers", "--delay"])
        self.assertEqual(calls[0][-1], "print()")
        self.assertEqual(calls[1], ["xdotool", "key", "--clearmodifiers", "--repeat", "1", "Left"])

    @LINUX_ONLY
    def test_inject_text_via_clipboard_without_cursor(self) -> None:
        calls = []
        clipboard_contents = []

        def fake_run(cmd, input=None, **kwargs):
            calls.append((cmd, input))
            if input is not None:
                clipboard_contents.append(input.decode("utf-8"))
            return SimpleNamespace(returncode=0, stdout=b"")

        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            self.assertTrue(self.backend.inject_text("simple text"))

        self.assertIn("simple text", clipboard_contents)
        paste_calls = [cmd for cmd, _ in calls if cmd[:3] == ["xdotool", "key", "--clearmodifiers"] and "ctrl+v" in cmd]
        self.assertEqual(len(paste_calls), 1)

    @LINUX_ONLY
    def test_inject_text_fallback_typing_without_cursor(self) -> None:
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        with patch("text_expander.runtime.x11_backend.probe_binary", side_effect=lambda name: name == "xdotool"):
            with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
                self.assertTrue(self.backend.inject_text("simple text"))

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-1], "simple text")

    @LINUX_ONLY
    def test_inject_text_strips_single_trailing_newline_for_keyword_expansion(self) -> None:
        clipboard_contents = []

        def fake_run(cmd, input=None, **kwargs):
            if input is not None:
                clipboard_contents.append(input.decode("utf-8"))
            return SimpleNamespace(returncode=0, stdout=b"")

        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            self.assertTrue(self.backend.inject_text("line one\n", preserve_trailing_newline=False))

        self.assertIn("line one", clipboard_contents)

    @LINUX_ONLY
    def test_inject_text_multi_paragraph_expansion(self) -> None:
        multi_para = "Paragraph 1\n\nParagraph 2 with details\n\nParagraph 3 end."
        clipboard_contents = []

        def fake_run(cmd, input=None, **kwargs):
            if input is not None:
                clipboard_contents.append(input.decode("utf-8"))
            return SimpleNamespace(returncode=0, stdout=b"")

        with patch("text_expander.runtime.x11_backend.subprocess.run", side_effect=fake_run):
            self.assertTrue(self.backend.inject_text(multi_para, preserve_trailing_newline=False))

        # Full multi-paragraph text is placed in clipboard atomically without early newline submission
        self.assertIn(multi_para, clipboard_contents)

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

    def test_usage_stats_and_picker_ordering(self) -> None:
        rare = Snippet(label="Rare", keyword=";r", expansion_text="ab", use_count=1)
        common = Snippet(label="Common", keyword=";c", expansion_text="abcdefgh", use_count=5)
        self.assertEqual(Snippet.from_dict(common.to_dict()).use_count, 5)
        self.assertEqual(usage_stats([rare, common]), (6, 1 * 0 + 5 * 6))

        picker = SnippetPickerDialog([rare, common])
        self.assertEqual(picker.list_widget.item(0).text(), "Common [;c]")

        window = MainWindow()
        window.update_snippets([rare, common])
        self.assertIn("6 uses", window.count_label.text())
        self.assertIn("30 keystrokes saved", window.count_label.text())

    def test_pack_filter_in_main_window(self) -> None:
        window = MainWindow()
        window.update_snippets(
            [
                Snippet(label="Mine", keyword=";a", expansion_text="x"),
                Snippet(label="Dev", keyword=";b", expansion_text="y", pack_id="developer"),
                Snippet(label="Support", keyword=";c", expansion_text="z", pack_id="support"),
            ]
        )
        self.assertFalse(window.remove_pack_button.isVisibleTo(window))

        window.pack_filter.setCurrentIndex(window.pack_filter.findData("developer"))
        self.assertEqual([window.snippet_table.isRowHidden(r) for r in range(3)], [True, False, True])
        self.assertTrue(window.remove_pack_button.isVisibleTo(window))

        window.pack_filter.setCurrentIndex(window.pack_filter.findData(""))
        self.assertEqual([window.snippet_table.isRowHidden(r) for r in range(3)], [False, True, True])
        self.assertFalse(window.remove_pack_button.isVisibleTo(window))


if __name__ == "__main__":
    unittest.main()
