from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from text_expander import platform


class PlatformSecurityTests(unittest.TestCase):
    def test_desktop_exec_arg_quotes_spaces_and_quotes(self) -> None:
        value = Path('/tmp/path with spaces/"quoted"/run.py')
        escaped = platform._desktop_exec_arg(value)
        self.assertTrue(escaped.startswith('"'))
        self.assertTrue(escaped.endswith('"'))
        self.assertIn('path with spaces', escaped)
        self.assertIn('\\"quoted\\"', escaped)

    def test_launcher_command_quotes_workspace_paths(self) -> None:
        with patch.object(platform, "app_root", return_value=Path("/tmp/has spaces/app")):
            command = platform.launcher_command()
        self.assertIn('"/tmp/has spaces/app/run.py"', command)
        self.assertTrue(command.startswith('"'))

    def test_desktop_entry_uses_quoted_exec_line(self) -> None:
        with patch.object(platform, "app_root", return_value=Path("/tmp/demo path")):
            content = platform.desktop_entry_content()
        self.assertIn("Name=FlitKey", content)
        exec_line = next(line for line in content.splitlines() if line.startswith("Exec="))
        self.assertIn('"/tmp/demo path/run.py"', exec_line)


if __name__ == "__main__":
    unittest.main()
