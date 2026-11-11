import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from export_web import story_frontmatter


class StoryFrontmatterTests(unittest.TestCase):
    def test_parses_a_family_story(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prvni-rod.md"
            path.write_text('---\ntitle: "První rod"\nlead: Příběh rodiny\nrod: 8\n---\nText.\n', encoding="utf-8")
            story = story_frontmatter(path, "prvni-rod")
            self.assertEqual((story["title"], story["rod"], story["slug"]), ("První rod", 8, "prvni-rod"))

    def test_rejects_invalid_family_or_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "story.md"
            path.write_text('---\ntitle: Příběh\nlead: Úvod\nrod: 7\n---\nText.\n', encoding="utf-8")
            with self.assertRaises(SystemExit):
                story_frontmatter(path, "story")
            path.write_text('---\ntitle: Příběh\nlead: Úvod\nrod: 8\n---\nText.\n', encoding="utf-8")
            with self.assertRaises(SystemExit):
                story_frontmatter(path, "../story")


if __name__ == "__main__":
    unittest.main()
