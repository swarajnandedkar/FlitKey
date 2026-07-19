from __future__ import annotations

import unittest
from pathlib import Path

from text_expander.importers import (
    import_snippets_from_file,
    parse_autohotkey,
    parse_csv_tsv,
    parse_espanso_yaml,
    parse_json_snippets,
)


class ImportersTests(unittest.TestCase):
    def test_parse_espanso_yaml_single_and_multiple_triggers(self):
        sample = """
matches:
  - trigger: ":esp"
    replace: "Espanso test"
    label: "Espanso Label"
  - triggers: [":d1", ":d2"]
    replace: "Multi trigger text"
"""
        snippets = parse_espanso_yaml(sample)
        self.assertEqual(len(snippets), 3)
        self.assertEqual(snippets[0].keyword, ":esp")
        self.assertEqual(snippets[0].expansion_text, "Espanso test")
        self.assertEqual(snippets[0].label, "Espanso Label")
        self.assertEqual(snippets[1].keyword, ":d1")
        self.assertEqual(snippets[2].keyword, ":d2")

    def test_parse_autohotkey_hotstrings_and_hotkeys(self):
        sample = """
:*:btw::by the way
::email::test@example.com
^!a::Send, Hello World
"""
        snippets = parse_autohotkey(sample)
        self.assertEqual(len(snippets), 3)
        self.assertEqual(snippets[0].trigger_type, "keyword")
        self.assertEqual(snippets[0].keyword, "btw")
        self.assertEqual(snippets[0].expansion_text, "by the way")

        self.assertEqual(snippets[1].keyword, "email")
        self.assertEqual(snippets[1].expansion_text, "test@example.com")

        self.assertEqual(snippets[2].trigger_type, "hotkey")
        self.assertEqual(snippets[2].hotkey, "Ctrl+Alt+A")
        self.assertEqual(snippets[2].expansion_text, "Hello World")

    def test_parse_csv_tsv(self):
        sample = """Label,Trigger,Expansion
Greeting,:hello,Hello World!
Signature,:sig,Best regards, FlitKey Team
"""
        snippets = parse_csv_tsv(sample)
        self.assertEqual(len(snippets), 2)
        self.assertEqual(snippets[0].label, "Greeting")
        self.assertEqual(snippets[0].keyword, ":hello")
        self.assertEqual(snippets[0].expansion_text, "Hello World!")

    def test_parse_json_snippets(self):
        sample = """{
  "snippets": [
    {"label": "Test JSON", "keyword": ":jtest", "expansion_text": "JSON Output"}
  ]
}"""
        snippets = parse_json_snippets(sample)
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0].label, "Test JSON")
        self.assertEqual(snippets[0].keyword, ":jtest")
        self.assertEqual(snippets[0].expansion_text, "JSON Output")


if __name__ == "__main__":
    unittest.main()
