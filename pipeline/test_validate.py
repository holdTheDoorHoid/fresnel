"""Tests for pipeline/validate.py and pipeline/build_site_data.py on the web fixtures and on
broken copies of them."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_site_data as bsd  # noqa: E402
import validate  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "web" / "fixtures"
VOCAB = REPO / "data" / "vocab.json"


class ValidateCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for name in ("stations", "research", "stories"):
            shutil.copytree(FIX / name, self.tmp / name)
        (self.tmp / "sources").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def problems(self) -> validate.Problems:
        return validate.validate(self.tmp / "stations", self.tmp / "research", self.tmp / "stories",
                                 self.tmp / "sources", VOCAB)

    def edit(self, rel: str, fn) -> None:
        path = self.tmp / "stations" / rel
        rec = json.loads(path.read_text())
        fn(rec)
        path.write_text(json.dumps(rec))

    def assertError(self, needle: str) -> None:
        errors = self.problems().errors
        self.assertTrue(any(needle in e for e in errors), f"no error mentioning {needle!r} in {errors}")


class ValidateTest(ValidateCase):
    def test_fixtures_pass(self):
        p = self.problems()
        self.assertEqual(p.errors, [])

    def test_vocabulary(self):
        self.edit("me/us-me-example-head.json", lambda r: r.update(status="standing"))
        self.assertError("status 'standing' is not in data/vocab.json")

    def test_structure_vocabulary(self):
        self.edit("me/us-me-example-head.json", lambda r: r["structures"][0].update(type="lattice"))
        self.assertError("structure_type 'lattice'")

    def test_id_and_folder(self):
        src = self.tmp / "stations" / "me" / "us-me-example-head.json"
        (self.tmp / "stations" / "nh").mkdir()
        src.rename(self.tmp / "stations" / "nh" / "us-me-example-head.json")
        self.assertError("should be in data/stations/me/")

    def test_position_outside_country(self):
        self.edit("me/us-me-example-head.json", lambda r: r["location"].update(lon=70.21))
        self.assertError("lon_positive_sign")

    def test_region_of_another_country(self):
        self.edit("me/us-me-example-head.json", lambda r: r.update(region="NS"))
        self.assertError("region NS is not in country US")

    def test_keepers_roster(self):
        path = self.tmp / "research" / "us-me-example-head.json"
        res = json.loads(path.read_text())
        res["keepers"][0]["cite"] = [9]
        res["keepers"][1]["from"] = "about 1795"
        del res["keepers"][2]["name"]
        path.write_text(json.dumps(res))
        errors = "\n".join(self.problems().errors)
        self.assertIn("which the file's sources do not have", errors)
        self.assertIn("is not a year", errors)
        self.assertIn("name is missing", errors)

    def test_story_footnotes_and_orphans(self):
        (self.tmp / "stories" / "us-me-example-head.md").write_text("Text.[^1][^2]\n\n[^1]: A source.\n")
        (self.tmp / "stories" / "us-me-nowhere.md").write_text("Text.\n")
        errors = "\n".join(self.problems().errors)
        self.assertIn("footnote [^2] has no definition", errors)
        self.assertIn("story file for us-me-nowhere, which is not a station", errors)


class BuildSiteDataTest(ValidateCase):
    def test_build_from_fixtures(self):
        out = self.tmp / "out"
        meta = bsd.build(self.tmp / "stations", self.tmp / "stories", self.tmp / "research", self.tmp / "sources",
                         VOCAB, out, fixtures=True, log=bsd.Log(quiet=True))
        geo = json.loads((out / "stations.geojson").read_text())
        ids = [f["properties"]["i"] for f in geo["features"]]
        hidden = [p.stem for p in (self.tmp / "stations").rglob("*.json") if json.loads(p.read_text()).get("hidden")]
        self.assertTrue(hidden)
        self.assertFalse(set(hidden) & set(ids))
        self.assertEqual(meta["counts"]["total"], len(ids))
        self.assertTrue(meta["fixtures"])
        page = json.loads((out / "s" / "us-me-example-head.json").read_text())
        self.assertIn('<h3 id="s-the-keepers">', page["story_html"])
        self.assertEqual([c["title"] for c in page["chapters"]][:2], ["The place", "Building the light"])
        self.assertEqual(page["keepers"][0]["name"], "Joseph Example")
        self.assertEqual(page["research_sources"][0]["n"], 1)
        props = next(f["properties"] for f in geo["features"] if f["properties"]["i"] == "us-me-example-head")
        self.assertEqual((props["s"], props["k"], props.get("cl"), props.get("sy"), props.get("st")),
                         ("active", "lighthouse", 1, 1, 1))
        ns = next(f["properties"] for f in geo["features"] if f["properties"]["i"] == "ca-ns-fixture-island")
        self.assertEqual((ns.get("cc"), ns.get("sf"), ns.get("bo")), ("CA", "staffed", 1))
        regions_listed = [r["code"] for c in meta["regions"]["countries"] for r in c["regions"]]
        self.assertEqual(regions_listed.index("PR") > regions_listed.index("WY"), True)  # territories after the states

    def test_year_range(self):
        rec = {"status": "lost", "light": {"first_lit": 1867, "deactivated": None},
               "events": [{"year": 1918, "event": "destroyed"}], "structures": []}
        self.assertEqual(bsd.year_range(rec), (1867, 1918))
        rec = {"status": "active", "light": {"first_lit": 1791}, "events": [], "structures": []}
        self.assertEqual(bsd.year_range(rec), (1791, None))


if __name__ == "__main__":
    unittest.main()
