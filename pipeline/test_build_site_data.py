"""build_site_data: a researched, fact-checked story lifts a station's verification level."""
import json, shutil, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_site_data as b  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
STATION = json.loads((DATA / "stations" / "de" / "us-de-cape-henlopen.json").read_text(encoding="utf-8"))


class VerificationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for d in ("stations/de", "stories", "research", "sources", "out"):
            (self.tmp / d).mkdir(parents=True)
        rec = dict(STATION, verification="unverified")
        (self.tmp / "stations" / "de" / f"{rec['id']}.json").write_text(json.dumps(rec), encoding="utf-8")
        self.rid = rec["id"]

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def build(self):
        b.build(self.tmp / "stations", self.tmp / "stories", self.tmp / "research", self.tmp / "sources",
                DATA / "vocab.json", self.tmp / "out", log=b.Log(quiet=True))
        return json.loads((self.tmp / "out" / "s" / f"{self.rid}.json").read_text(encoding="utf-8"))["verification"]

    def test_no_story_keeps_level(self):
        self.assertEqual(self.build(), "unverified")

    def test_story_without_check_is_researched(self):
        (self.tmp / "stories" / f"{self.rid}.md").write_text("A story.[^1]\n\n[^1]: A source, https://example.org (accessed 2026-10-21).\n")
        self.assertEqual(self.build(), "researched")

    def test_checked_story_is_verified(self):
        (self.tmp / "stories" / f"{self.rid}.md").write_text("A story.[^1]\n\n[^1]: A source, https://example.org (accessed 2026-10-21).\n")
        (self.tmp / "research" / f"{self.rid}.json").write_text(json.dumps(
            {"id": self.rid, "researched": "2026-10-21", "verification": {"checked": "2026-10-21", "verdict": "fixed"}}))
        self.assertEqual(self.build(), "verified")


if __name__ == "__main__":
    unittest.main()
