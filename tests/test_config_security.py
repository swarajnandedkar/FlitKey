from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from text_expander import config
from text_expander.models import Settings, Snippet


class ConfigSecurityTests(unittest.TestCase):
    def test_load_state_ignores_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}, clear=False):
                target = Path(tmpdir) / "typeflux" / "config.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("{not valid json", encoding="utf-8")

                snippets, settings = config.load_state()

                self.assertEqual(snippets, [])
                self.assertIsInstance(settings, Settings)
                self.assertFalse(settings.autostart)

    def test_load_state_ignores_unexpected_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}, clear=False):
                target = Path(tmpdir) / "typeflux" / "config.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps({"snippets": {"bad": True}, "settings": []}), encoding="utf-8")

                snippets, settings = config.load_state()

                self.assertEqual(snippets, [])
                self.assertIsInstance(settings, Settings)

    def test_save_state_preserves_untrusted_text_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}, clear=False):
                snippet = Snippet(
                    label="danger",
                    trigger_type="keyword",
                    keyword="/danger",
                    expansion_text='$(touch /tmp/pwned); rm -rf / ; "quotes"',
                )

                config.save_state([snippet], Settings())
                saved = (Path(tmpdir) / "typeflux" / "config.json").read_text(encoding="utf-8")
                self.assertIn('"expansion_text": "$(touch /tmp/pwned); rm -rf / ; \\"quotes\\""', saved)

                snippets, _ = config.load_state()
                self.assertEqual(snippets[0].expansion_text, snippet.expansion_text)

    def test_legacy_config_migrates_to_typeflux_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}, clear=False):
                legacy_dir = Path(tmpdir) / "linux-text-expander"
                legacy_dir.mkdir(parents=True, exist_ok=True)
                payload = {
                    "snippets": [
                        {
                            "id": "1",
                            "label": "legacy",
                            "trigger_type": "keyword",
                            "keyword": "/old",
                            "hotkey": "",
                            "expansion_text": "Legacy text",
                            "enabled": True,
                        }
                    ],
                    "settings": {"autostart": True, "start_minimized": True, "paused": False, "case_sensitive": False},
                }
                (legacy_dir / "config.json").write_text(json.dumps(payload), encoding="utf-8")

                snippets, settings = config.load_state()

                self.assertEqual(snippets[0].label, "legacy")
                self.assertTrue(settings.autostart)
                migrated = Path(tmpdir) / "typeflux" / "config.json"
                self.assertTrue(migrated.exists())


if __name__ == "__main__":
    unittest.main()
