from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from text_expander import config
from text_expander.models import Settings, Snippet


class ComplianceControlTests(unittest.TestCase):
    def test_config_is_private_and_supports_export_and_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}, clear=False):
                snippet = Snippet("Private", "local text", keyword=":p")
                config.save_state([snippet], Settings())
                config_file = Path(tmpdir) / "flitkey" / "config.json"

                if os.name == "posix":
                    self.assertEqual(stat.S_IMODE(config_file.stat().st_mode), 0o600)
                    self.assertEqual(stat.S_IMODE(config_file.parent.stat().st_mode), 0o700)

                export_file = Path(tmpdir) / "export.json"
                config.export_state(export_file)
                exported = json.loads(export_file.read_text(encoding="utf-8"))
                self.assertEqual(exported["snippets"][0]["label"], "Private")
                self.assertTrue(config.delete_state())
                self.assertFalse(config_file.exists())
                self.assertFalse(config.delete_state())


if __name__ == "__main__":
    unittest.main()
