"""Tests for pipeline/build_vessels.py and the vessel records it wrote (data/vessels/<id>.json, DESIGN.md 3.5): hull-number ids,
names, fates, the berth of a survivor, and the consistency of the committed records with the lightship stations they name."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_vessels as B  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


class HullIdTest(unittest.TestCase):
    def test_a_numbered_hull_is_its_own_id(self):
        self.assertEqual(B.hull_id("Lightship: LV-112 More Information", "LV-112", "WAL-534"), ("lv-112", "LV-112", "WAL-534"))
        self.assertEqual(B.hull_id("Lightship: LV-087", "LV-87", None), ("lv-87", "LV-87", None))     # leading zeros are dropped

    def test_a_vessel_the_society_numbers_wlv_or_wal_keeps_that_prefix(self):
        self.assertEqual(B.hull_id("Lightship: WLV-604", "WLV-604", None), ("wlv-604", "WLV-604", None))
        self.assertEqual(B.hull_id("Lightship: WAL-612", "WAL-612", None), ("wal-612", "WAL-612", None))

    def test_a_ship_the_society_knows_by_a_letter_or_a_name(self):
        self.assertEqual(B.hull_id("Lightship: LV- ZZ (Aurora Borealis)", None, None)[0], "lv-zz")
        self.assertEqual(B.hull_id("Lightship: LV- Kewaunee (Privately Owned)", None, None)[:2], ("kewaunee", "Kewaunee"))

    def test_a_title_nothing_reads_still_gets_a_usable_id(self):
        vid, label, _ = B.hull_id("Lightship: Something Else", None, None)
        self.assertTrue(vid.endswith("-vessel"))
        self.assertRegex(vid, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def test_names_come_from_parentheses_but_notes_are_not_names(self):
        self.assertEqual(B.vessel_names("Lightship: LV- AA (Caesar)"), ["Caesar"])
        self.assertEqual(B.vessel_names("Lightship: LV- Kewaunee (Privately Owned)"), [])
        self.assertEqual(B.vessel_names("Lightship: LV-1 (USRC Gallatin)"), ["Gallatin"])


class FateTest(unittest.TestCase):
    def test_a_hull_that_exists_survives(self):
        self.assertEqual(B.fate_of({"existing": True, "remarks": None}), {"status": "survives", "year": None, "existing": True})

    def test_lost_scrapped_sold_and_unknown_are_told_apart_and_the_year_is_kept(self):
        self.assertEqual(B.fate_of({"existing": False, "remarks": "Sunk in a hurricane in 1944", "retired": 1940})["status"], "lost")
        self.assertEqual(B.fate_of({"existing": False, "remarks": "Sunk in a hurricane in 1944", "retired": 1940})["year"], 1944)
        self.assertEqual(B.fate_of({"existing": False, "remarks": "Scrapped 1950"})["status"], "scrapped")
        self.assertEqual(B.fate_of({"existing": False, "remarks": "Sold to a private owner 1931"})["status"], "sold")
        self.assertEqual(B.fate_of({"existing": False, "remarks": None})["status"], "unknown")

    def test_the_societys_own_words_are_not_kept(self):
        self.assertNotIn("remarks", B.fate_of({"existing": False, "remarks": "Sunk in 1944"}))

    def test_a_survivor_the_society_doubts_is_marked_doubtful(self):
        fate = B.fate_of({"existing": True, "remarks": "Privately Owned, Unmanned after Nov. 22, 1924, Possibly Scrapped 2013"})
        self.assertEqual(fate, {"status": "survives", "year": 2013, "existing": True, "doubtful": True})


class BerthTest(unittest.TestCase):
    STATIONS = [
        {"id": "us-ma-lightship-nantucket", "name": "Lightship Nantucket LV 112/WAL 534", "lat": 42.36, "lon": -71.03, "hulls": B.hull_numbers_of_station({"name": "Lightship Nantucket LV 112/WAL 534"}), "status": "active", "sources": []},
        {"id": "us-wa-swiftsure", "name": "Swiftsure Bank", "lat": 48.0, "lon": -125.0, "hulls": B.hull_numbers_of_station({"name": "Swiftsure Bank", "other_names": ["Lightship No. 83"]}), "status": "active", "sources": []},
    ]

    def test_hull_numbers_are_read_from_a_stations_names(self):
        self.assertEqual(B.hull_numbers_of_station({"name": "Lightship Nantucket LV 112/WAL 534"}), {112, 534})
        self.assertEqual(B.hull_numbers_of_station({"name": "Swiftsure", "other_names": ["Lightship No. 83", "LIGHT VESSEL 83"]}), {83})
        self.assertEqual(B.hull_numbers_of_station({"name": "Portland Head Light"}), set())

    def test_a_survivor_berths_at_the_station_that_carries_its_hull_number(self):
        berth = B.berth_of({"id": "lv-112", "hull": "LV-112", "wal": "WAL-534"}, self.STATIONS)
        self.assertEqual(berth["station_id"], "us-ma-lightship-nantucket")
        self.assertIn("hull number", berth["basis"])

    def test_a_hull_no_station_carries_has_no_berth(self):
        self.assertIsNone(B.berth_of({"id": "lv-75", "hull": "LV-75", "wal": None}, self.STATIONS))

    def test_a_wlv_number_is_not_matched_to_an_ordinary_lightships_number(self):
        # WLV-83 is not LV-83: a Coast Guard hull number is three digits (190 and up)
        self.assertIsNone(B.berth_of({"id": "wlv-83", "hull": "WLV-83", "wal": None}, self.STATIONS))


class CommittedRecordsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vessels = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted((REPO / "data" / "vessels").glob("*.json"))}

    def test_every_record_is_filed_under_its_id_and_ids_are_url_safe(self):
        self.assertGreaterEqual(len(self.vessels), 150)
        for fid, v in self.vessels.items():
            self.assertEqual(v["id"], fid)
            self.assertRegex(fid, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def test_every_record_has_its_fields_and_a_link_to_the_societys_page(self):
        for fid, v in self.vessels.items():
            for key in ("hull", "names", "built", "retired", "career", "fate", "berth", "sources"):
                self.assertIn(key, v, fid)
            self.assertIn(v["fate"]["status"], ("survives", "lost", "scrapped", "sold", "unknown"), fid)
            self.assertTrue(v["sources"] and v["sources"][0]["url"].startswith("https://archives.uslhs.org/node/"), fid)

    def test_a_careers_years_run_forward(self):
        for fid, v in self.vessels.items():
            for line in v["career"]:
                if line["start"] and line["end"]:
                    self.assertLessEqual(line["start"], line["end"], (fid, line))

    def test_the_survivors_and_their_berths(self):
        survivors = {fid for fid, v in self.vessels.items() if v["fate"]["status"] == "survives"}
        self.assertEqual(len(survivors), 16)
        berthed = {fid for fid in survivors if self.vessels[fid]["berth"]}
        self.assertEqual(survivors - berthed, {"lv-75"})                       # the one survivor no source gives a berth for
        self.assertTrue(self.vessels["lv-75"]["fate"].get("doubtful"))
        for fid in berthed:
            self.assertRegex(self.vessels[fid]["berth"]["station_id"], r"^us-[a-z]{2}-[a-z0-9-]+$")

    def test_a_worked_record(self):
        v = self.vessels["lv-112"]
        self.assertEqual((v["hull"], v["wal"], v["names"], v["built"]), ("LV-112", "WAL-534", ["Nantucket"], 1936))
        self.assertEqual(v["berth"]["station_id"], "us-ma-lightship-nantucket")
        keys = [c["station_key"] for c in v["career"]]
        self.assertEqual(keys.count("lightship_stations:nantucket-shoals"), 3)            # three stints on Nantucket Shoals
        self.assertIn(None, keys)                                                           # the war years as an examination vessel are not a station

    def test_a_career_is_joined_to_stations_the_lightship_source_has(self):
        path = REPO / "data" / "sources" / "lightship_stations.json"
        keys = {r["key"] for r in json.loads(path.read_text(encoding="utf-8"))["records"]}
        joined = [c["station_key"] for v in self.vessels.values() for c in v["career"] if c["station_key"]]
        self.assertGreater(len(joined), 300)
        self.assertEqual(sorted({k for k in joined if k not in keys}), [])

    def test_a_vessels_career_is_the_stations_own_list_of_vessels(self):
        """The two records say the same thing from two sides: a station's page lists a vessel for years, the vessel's page lists the station."""
        path = REPO / "data" / "sources" / "lightship_stations.json"
        recs = {r["key"]: r for r in json.loads(path.read_text(encoding="utf-8"))["records"]}
        rec = recs["lightship_stations:pollock-rip"]
        served = {B.hull_id(v["label"], None, None)[0] for v in rec["extra"]["vessels"]}
        by_vessel = {fid for fid, v in self.vessels.items() if any(c["station_key"] == "lightship_stations:pollock-rip" for c in v["career"])}
        self.assertEqual(served, by_vessel)


if __name__ == "__main__":
    unittest.main()
