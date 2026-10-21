"""Tests for pipeline/fetch_ca_lightships_lifesaving.py: positions only where a source gives one,
every record linked to its evidence, the shape the merge reads."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_ca_lightships_lifesaving as f  # noqa: E402


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.records, self.notes = f.build()
        self.by = {r["name"]: r for r in self.records}

    def test_positions_only_where_a_source_gives_one(self):
        placed = {r["name"] for r in self.records if r["lat"] is not None}
        self.assertEqual(placed, {"Lower Traverse", "Lurcher Shoal", "Sable Island Humane Establishment"})
        self.assertEqual(self.by["Lurcher Shoal"]["precision"], "approximate")
        self.assertEqual(self.by["Sable Island Humane Establishment"]["precision"], "approximate")
        for r in self.records:
            self.assertEqual(r["lat"] is None, r["lon"] is None)

    def test_lower_traverse_takes_lighthouse_friends_position(self):
        r = self.by["Lower Traverse"]
        self.assertEqual((r["lat"], r["lon"]), (47.363826, -70.246253))
        self.assertEqual(r["kind"], "lightship_station")
        self.assertEqual(r["extra"]["join_keys"], ["lhf:2354"])

    def test_lights_that_were_lightship_stations_join_by_identifier(self):
        for name, key in [("White Island Reef", "lhf:2365"), ("Prince Shoal", "lhf:1626")]:
            r = self.by[name]
            self.assertEqual((r["kind"], r["lat"], r["extra"]["join_keys"]), ("lighthouse", None, [key]))
            self.assertTrue(r["extra"]["station_level"])
            self.assertTrue(r["events"])

    def test_every_record_has_evidence_and_valid_events(self):
        vocab = __import__("json").loads((Path(__file__).resolve().parent.parent / "data" / "vocab.json").read_text())
        for r in self.records:
            self.assertTrue(r["extra"]["evidence"], r["name"])
            self.assertTrue(r["links"], r["name"])
            self.assertTrue(r["country"] == "CA" and r["region"])
            self.assertIn(r["kind"], vocab["kind"])
            for e in r["events"]:
                self.assertIn(e["event"], vocab["event"], r["name"])
                self.assertIsInstance(e["year"], int)
                self.assertEqual(e["from"], f.SOURCE)
            if r["status"]:
                self.assertIn(r["status"], vocab["status"])

    def test_sable_island(self):
        r = self.by["Sable Island Humane Establishment"]
        self.assertEqual((r["kind"], r["region"], r["status"]), ("life_saving_station", "NS", "lost"))
        self.assertEqual(r["registers"][0]["number"], "16352")
        self.assertEqual({e["year"] for e in r["events"]}, {1801, 1958, 2021})

    def test_unplaced_leads_are_listed(self):
        self.assertIn("Red Island Reef", self.notes["unplaced_leads"])
        self.assertIn("Port Stanley Life-Saving Station", self.notes["unplaced_leads"])
        self.assertEqual(len(self.records), 21)

    def test_unique_keys(self):
        keys = [r["key"] for r in self.records]
        self.assertEqual(len(keys), len(set(keys)))


if __name__ == "__main__":
    unittest.main()
