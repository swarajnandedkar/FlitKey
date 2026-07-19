from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from text_expander import config, platform
from text_expander.runtime.windows_backend import WindowsBackend


class WindowsSupportTests(unittest.TestCase):
    def test_windows_hotkey_normalization_matches_common_aliases(self) -> None:
        self.assertEqual(
            WindowsBackend.normalize_hotkey("control + alt + t"),
            "Ctrl+Alt+T",
        )
        self.assertEqual(
            WindowsBackend.normalize_hotkey("Win+Esc"),
            "Win+Escape",
        )

    def test_windows_session_detection(self) -> None:
        with patch.object(platform.sys, "platform", "win32"):
            self.assertEqual(platform.detect_session_type(), "windows")

    def test_windows_config_uses_appdata(self) -> None:
        with patch.object(config.sys, "platform", "win32"), patch.dict(
            os.environ,
            {"APPDATA": r"C:\Users\tester\AppData\Roaming"},
            clear=False,
        ):
            self.assertEqual(
                config._config_home(),
                config.Path(r"C:\Users\tester\AppData\Roaming"),
            )


if __name__ == "__main__":
    unittest.main()
