"""Tests for pipeline/fetch_ca_staffed_lightstations.py: the table's counts, the 2024 change, the
flag for stations that rest only on the 2010 list, and that its identifiers exist in the extracts."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_ca_staffed_lightstations as f  # noqa: E402

SOURCES = Path(__file__).resolve().parent.parent / "data" / "sources"


class TableTest(unittest.TestCase):
    def setUp(self):
        self.records, self.notes = f.build()
        self.by_name = {(r["region"], r["name"]): r for r in self.records}

    def test_counts(self):
        self.assertEqual(len(self.records), 51)                           # 27 BC + 23 NL + Machias
        self.assertEqual(self.notes["by_region"], {"BC": 25, "NL": 23, "NB": 1})
        self.assertEqual(self.notes["destaffed_2024"], ["Carmanah Point", "Pachena Point"])

    def test_the_two_destaffed_stations(self):
        for name in f.DESTAFFED:
            r = self.by_name[("BC", name)]
            self.assertEqual(r["extra"]["staffing"], {"status": "automated", "as_of": "2024"})
            self.assertFalse(r["extra"]["check"])
            self.assertIn("31 July 2024", r["extra"]["access"]["note"])

    def test_staffed_stations_get_the_access_note(self):
        r = self.by_name[("NL", "Cape Race")]
        self.assertEqual(r["extra"]["access"]["level"], "restricted")
        self.assertEqual(r["extra"]["access"]["note"],
                         "Staffed lightstation: the keepers' home and workplace. Visit only where the station welcomes visitors, "
                         "and never land uninvited.")
        self.assertEqual(r["extra"]["staffing"], {"status": "staffed", "as_of": "2010"})

    def test_flag_for_the_2010_list(self):
        flagged = {(r["region"], r["name"]) for r in self.records if r["extra"]["check"]}
        self.assertEqual(len(flagged), 44)
        for k in [("BC", "Cape Beale"), ("BC", "Triple Island"), ("BC", "Estevan Point"), ("NL", "Long Point (Twillingate)"),
                  ("NB", "Machias Seal Island"), ("BC", "Carmanah Point")]:
            self.assertNotIn(k, flagged)
        self.assertEqual(self.by_name[("BC", "Cape Beale")]["extra"]["staffing"]["as_of"], "2025")
        self.assertEqual(self.by_name[("BC", "Lennard Island")]["extra"]["staffing"]["as_of"], "2024")  # count only
        self.assertEqual(self.by_name[("NL", "Fort Amherst")]["extra"]["staffing"]["as_of"], "2010")

    def test_every_record_has_evidence_links(self):
        for r in self.records:
            self.assertTrue(r["extra"]["evidence"])
            self.assertTrue(all(e["url"].startswith("https://") and e["date"] for e in r["extra"]["evidence"]))
            self.assertEqual(len(r["extra"]["join_keys"]), 2)

    def test_keys_unique(self):
        keys = [r["key"] for r in self.records]
        self.assertEqual(len(keys), len(set(keys)))


class IdentifiersExistTest(unittest.TestCase):
    def test_ccg_numbers_and_friends_ids_are_in_the_extracts(self):
        records, _ = f.build()
        ccg_path, lhf_path = SOURCES / "ccg_list_of_lights.json", SOURCES / "lighthousefriends.json"
        if not (ccg_path.exists() and lhf_path.exists()):
            self.skipTest("extracts not present")
        ccg = {r["aton"]["ccg_list_number"]: r for r in json.loads(ccg_path.read_text())["records"]}
        lhf = {r["extra"]["lhf_id"]: r for r in json.loads(lhf_path.read_text())["records"] if r["country"] == "CA"}
        for r in records:
            c_key, l_key = (k.split(":")[1] for k in r["extra"]["join_keys"])
            self.assertTrue(c_key in ccg, r["name"])
            self.assertTrue(l_key in lhf, r["name"])
            self.assertEqual(lhf[l_key]["region"], r["region"], r["name"])
            self.assertIsNotNone(r["lat"], r["name"])


if __name__ == "__main__":
    unittest.main()
