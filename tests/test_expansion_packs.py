import unittest
from pathlib import Path
from text_expander.models import Snippet
from text_expander.packs import (
    get_builtin_packs_dir,
    list_available_packs,
    load_pack_snippets,
    merge_pack_snippets,
)


class TestExpansionPacks(unittest.TestCase):
    def test_list_builtin_packs(self):
        packs = list_available_packs()
        pack_ids = {p.pack_id for p in packs}
        expected_ids = {"ai_prompts", "developer", "artist", "support", "sysadmin", "productivity"}
        self.assertTrue(expected_ids.issubset(pack_ids), f"Missing pack IDs. Found: {pack_ids}")

    def test_load_ai_prompts_pack(self):
        builtin_dir = get_builtin_packs_dir()
        ai_pack_file = builtin_dir / "ai_prompts.json"
        self.assertTrue(ai_pack_file.exists())

        snippets = load_pack_snippets(ai_pack_file)
        self.assertGreaterEqual(len(snippets), 10)
        keywords = {s.keyword for s in snippets}
        self.assertIn(":airole", keywords)
        self.assertIn(":aixplain", keywords)
        self.assertIn(":airefactor", keywords)

    def test_platform_filtering(self):
        builtin_dir = get_builtin_packs_dir()
        dev_pack_file = builtin_dir / "developer.json"

        # Load for linux
        linux_snippets = load_pack_snippets(dev_pack_file, target_platform="linux")
        linux_keywords = {s.keyword for s in linux_snippets}
        self.assertIn(":shebang", linux_keywords)
        self.assertNotIn(":pshead", linux_keywords)

        # Load for windows
        win_snippets = load_pack_snippets(dev_pack_file, target_platform="win32")
        win_keywords = {s.keyword for s in win_snippets}
        self.assertIn(":pshead", win_keywords)
        self.assertNotIn(":shebang", win_keywords)

        # Load for all
        all_snippets = load_pack_snippets(dev_pack_file, target_platform="all")
        all_keywords = {s.keyword for s in all_snippets}
        self.assertIn(":shebang", all_keywords)
        self.assertIn(":pshead", all_keywords)

    def test_merge_snippets_deduplication(self):
        existing = [
            Snippet(label="My Custom Commit", trigger_type="keyword", keyword=":gcm", expansion_text="custom commit")
        ]
        builtin_dir = get_builtin_packs_dir()
        dev_pack_file = builtin_dir / "developer.json"
        new_snippets = load_pack_snippets(dev_pack_file, target_platform="all")

        merged, added_count = merge_pack_snippets(existing, new_snippets)
        self.assertEqual(len(merged), len(existing) + len(new_snippets) - 1)
        self.assertEqual(merged[0].expansion_text, "custom commit")


if __name__ == "__main__":
    unittest.main()
