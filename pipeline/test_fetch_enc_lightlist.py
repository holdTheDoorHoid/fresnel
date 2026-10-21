"""Tests for pipeline/fetch_enc.py and pipeline/fetch_uscg_light_list.py on small synthetic inputs
(the Light List text is a few real rows' layout, rewritten)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_enc as enc  # noqa: E402
import fetch_uscg_light_list as ll  # noqa: E402


def feat(lat, lon, **attrs):
    base = {"OBJNAM": None, "CATLIT": " ", "COLOUR": "1", "LITCHR": 2, "SIGPER": 4.0, "SIGGRP": "(1)", "HEIGHT": 30.8,
            "VALNMR": 14.0, "SECTR1": None, "SECTR2": None, "SORDAT": "20251021", "DSNM": "US2EC04M.000", "INFORM": None}
    base.update(attrs)
    return {"attributes": base, "geometry": {"x": lon, "y": lat}}


class EncCharacteristicTest(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(enc.characteristic({"LITCHR": 2, "COLOUR": "1", "SIGPER": 4.0, "SIGGRP": "(1)"}), "Fl W 4s")
        self.assertEqual(enc.characteristic({"LITCHR": 2, "COLOUR": "1", "SIGPER": 6.0, "SIGGRP": "(2)"}), "Fl(2) W 6s")
        self.assertEqual(enc.characteristic({"LITCHR": 7, "COLOUR": "3", "SIGPER": 6.0}), "Iso R 6s")
        self.assertEqual(enc.characteristic({"LITCHR": 8, "COLOUR": "1", "SIGPER": 2.5, "SIGGRP": "(1)"}), "Oc W 2.5s")
        self.assertEqual(enc.characteristic({"LITCHR": 1, "COLOUR": "4"}), "F G")
        self.assertEqual(enc.characteristic({"LITCHR": 4, "COLOUR": "1", "SIGPER": None}), "Q W")
        self.assertEqual(enc.characteristic({"LITCHR": 4, "COLOUR": "1", "SIGPER": 10.0, "SIGGRP": "(3)"}), "Q(3) W 10s")
        self.assertIsNone(enc.characteristic({"LITCHR": None, "COLOUR": "1"}))


class EncClusterTest(unittest.TestCase):
    def test_main_light_beats_sectors_and_emergency(self):
        group = [
            feat(43.6231, -70.2079, SECTR1=271.3, SECTR2=274.3, COLOUR="3", LITCHR=1, HEIGHT=10.4, SIGPER=None, SIGGRP=None),
            feat(43.6231, -70.2079, CATLIT="emergency", INFORM="Reduced intensity when main light is extinguished", VALNMR=None),
            feat(43.6231, -70.2079, SORDAT="20160202", VALNMR=None),
            feat(43.6231, -70.2079),
        ]
        a, char = enc.main_record(group)
        self.assertEqual(char, "Fl W 4s")
        self.assertEqual((a["HEIGHT"], a["VALNMR"], a["SORDAT"]), (30.8, 14.0, "20251021"))

    def test_sector_only_light_uses_the_white_sector(self):
        group = [feat(43.0, -70.0, SECTR1=10, SECTR2=20, COLOUR="3", LITCHR=2),
                 feat(43.0, -70.0, SECTR1=20, SECTR2=30, COLOUR="1", LITCHR=2)]
        a, char = enc.main_record(group)
        self.assertEqual(char, "Fl W 4s")

    def test_clusters_by_25_m(self):
        feats = [feat(43.6231, -70.2079), feat(43.62311, -70.20791), feat(43.6300, -70.2079)]
        groups = enc.cluster(feats)
        self.assertEqual(sorted(len(g) for g in groups), [1, 2])

    def test_only_lights_near_another_source_are_kept(self):
        feats = [feat(43.6231, -70.2079), feat(44.5, -68.0)]
        recs, stats = enc.build_records(feats, [(43.6232, -70.2080)])
        self.assertEqual(len(recs), 1)
        self.assertEqual(stats["no station near"], 1)
        r = recs[0]
        self.assertIsNone(r["name"])
        self.assertTrue(r["extra"]["enrich_only"] and r["extra"]["quiet_unmatched"])
        self.assertEqual((r["light"]["characteristic"], r["light"]["focal_height_m"], r["light"]["range_nm"]),
                         ("Fl W 4s", 30.8, 14.0))
        everything, _ = enc.build_records(feats, None)
        self.assertEqual(len(everything), 2)


V1_TEXT = """\
 LLNR    Name                     Position         Characteristic Height Range Structure                    Remarks
 7565   Portland Head Light       43-37-23.209N    Fl W 4s       0      19   White tower.                 Lighted throughout 24 hours. HORN: 1 blast ev 15s (2s bl).
                                  070-12-28.323W                                                          Seasonal in winter.
 7570   Portland Head             43-37-23.185N    FRWG          0           At base of Portland Head     Shows red from 271.3 to 274.3.
        Directional Light         070-12-27.576W                             Light.
 7578   Portland Harbor Main      43-37-44.283N    QG                   3    Green.
        Approach Lighted Buoy 070-12-37.671W
        11
 7580   Point Loma Light          32-39-54.258N    Fl (2)W 20s   95     14   Black house on white square
                                  117-14-33.601W
1/2/25, 6:25 AM                                                       Maritime Safety Information Products | Navigation Center
 7590   Charleston Light          32-45-28.551N    Fl (2)W 30s          20   Triangular tower.
                                  079-50-35.682W
"""


class LightListTest(unittest.TestCase):
    def test_parse(self):
        es = ll.parse_text(V1_TEXT)
        by = {e["llnr"]: e for e in es}
        self.assertEqual(sorted(by), ["7565", "7570", "7578", "7580", "7590"])
        e = by["7565"]
        self.assertEqual((e["name"], e["char"], e["height_ft"], e["range_nm"]), ("Portland Head Light", "Fl W 4s", 0.0, 19.0))
        self.assertEqual((e["lat_s"], e["lon_s"]), ("43-37-23.209N", "070-12-28.323W"))
        self.assertIn("HORN", e["text"])
        self.assertEqual(by["7570"]["name"], "Portland Head Directional Light")
        self.assertEqual(by["7578"]["name"], "Portland Harbor Main Approach Lighted Buoy")
        self.assertEqual(by["7580"]["height_ft"], 95.0)
        self.assertEqual((by["7590"]["height_ft"], by["7590"]["range_nm"]), (None, 20.0))   # one number: the range

    def test_what_is_a_light(self):
        es = {e["llnr"]: e for e in ll.parse_text(V1_TEXT)}
        self.assertTrue(ll.is_light_entry(es["7565"]))
        self.assertFalse(ll.is_light_entry(es["7578"]))   # a lighted buoy

    def test_record(self):
        es = {e["llnr"]: e for e in ll.parse_text(V1_TEXT)}
        r = ll.build_record(1, es["7565"])
        self.assertEqual(r["key"], "uscg_light_list:1-7565")
        self.assertEqual(r["aton"]["uscg_llnr"], "1-7565")
        self.assertAlmostEqual(r["lat"], 43.623114, places=5)
        self.assertAlmostEqual(r["lon"], -70.207868, places=5)
        self.assertEqual((r["light"]["characteristic"], r["light"]["range_nm"], r["light"]["fog_signal"]), ("Fl W 4s", 19.0, "horn"))
        self.assertIsNone(r["light"]["focal_height_m"])   # 0 means not printed
        self.assertTrue(r["extra"]["seasonal"])
        pl = ll.build_record(6, es["7580"])
        self.assertEqual(pl["light"]["focal_height_m"], 29.0)
        self.assertEqual(pl["light"]["characteristic"], "Fl(2) W 20s")
        self.assertTrue(ll.build_record(1, es["7570"])["extra"]["secondary"])

    def test_southern_and_eastern_positions(self):
        self.assertAlmostEqual(ll.to_deg("14-17-23.172S"), -14.289770, places=5)
        self.assertAlmostEqual(ll.to_deg("144-51-42.475E"), 144.861799, places=5)
        self.assertIsNone(ll.to_deg("garbage"))

    def test_tidy_characteristic(self):
        self.assertEqual(ll.tidy_characteristic("Fl (2)W 5s"), "Fl(2) W 5s")
        self.assertEqual(ll.tidy_characteristic("FRWG"), "FRWG")
        self.assertIsNone(ll.tidy_characteristic(""))
        self.assertEqual(ll.tidy_characteristic("Mo (A) W"), "Mo(A) W")


if __name__ == "__main__":
    unittest.main()
