from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from text_expander import ipc
from text_expander.runtime.wayland_backend import WaylandBackend

app = QApplication.instance() or QApplication(["-platform", "offscreen"])


class WaylandBackendTests(unittest.TestCase):
    def test_no_tools_means_clipboard_fallback(self) -> None:
        with patch("text_expander.runtime.wayland_backend.probe_binary", return_value=False):
            backend = WaylandBackend()
        self.assertFalse(backend.can_inject_text())
        self.assertFalse(backend.inject_text("x"))
        self.assertIn("clipboard", backend.capability_report.backend_name)

    def test_wtype_types_text_and_moves_cursor_back(self) -> None:
        with patch("text_expander.runtime.wayland_backend.probe_binary", side_effect=lambda n: n == "wtype"):
            backend = WaylandBackend()
        self.assertTrue(backend.can_inject_text())
        with patch("text_expander.runtime.wayland_backend.subprocess.run") as run:
            ok = backend.inject_text(
                "Hi {{field:Name}}!{{cursor}}?\n", preserve_trailing_newline=False, values={"Name": "Ada"}
            )
        self.assertTrue(ok)
        type_call, left_call = run.call_args_list
        self.assertEqual(type_call.args[0], ["wtype", "-"])
        self.assertEqual(type_call.kwargs["input"], "Hi Ada!?")
        self.assertEqual(left_call.args[0], ["wtype", "-k", "Left"])

    def test_ydotool_uses_evdev_left_key(self) -> None:
        with patch("text_expander.runtime.wayland_backend.probe_binary", side_effect=lambda n: n == "ydotool"):
            backend = WaylandBackend()
        with patch("text_expander.runtime.wayland_backend.subprocess.run") as run:
            backend.inject_text("ab{{cursor}}cd")
        self.assertEqual(run.call_args_list[0].args[0], ["ydotool", "type", "--", "abcd"])
        self.assertEqual(run.call_args_list[1].args[0], ["ydotool", "key", "105:1", "105:0", "105:1", "105:0"])


class IpcTests(unittest.TestCase):
    def test_second_invocation_reaches_running_instance(self) -> None:
        received: list[str] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            name = os.path.join(tmpdir, "ipc.sock")
            server = ipc.serve(name, received.append)
            self.assertIsNotNone(server)
            try:
                self.assertTrue(ipc.send(name, "picker"))
                self.assertTrue(ipc.send(name, "rm -rf /"))  # unknown commands are dropped
                for _ in range(20):
                    app.processEvents()
                    if len(received) == 1:
                        break
            finally:
                server.close()
        self.assertEqual(received, ["picker"])
        self.assertFalse(ipc.send(name, "show"))


if __name__ == "__main__":
    unittest.main()
