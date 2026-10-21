"""Vocabulary tests: data/vocab.json's shape, and every value the fetchers and the merge write
being in it (DESIGN.md 3.4), plus the fetchers' tag and class readings."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_osm as fo  # noqa: E402
import fetch_wikidata as fw  # noqa: E402
import merge  # noqa: E402

VOCAB = json.loads((Path(__file__).resolve().parent.parent / "data" / "vocab.json").read_text(encoding="utf-8"))


class VocabShapeTest(unittest.TestCase):
    def test_lists_are_unique_strings(self):
        for field, values in VOCAB.items():
            if field.startswith("_"):
                continue
            self.assertIsInstance(values, list, field)
            self.assertEqual(len(values), len(set(values)), f"{field} has a repeated value")
            self.assertTrue(all(isinstance(v, str) and v for v in values), field)

    def test_design_values_are_there(self):
        self.assertEqual(VOCAB["kind"], ["lighthouse", "range_lights", "pier_light", "harbor_light",
                                         "lightship_station", "lightship", "life_saving_station"])
        for s in ("active", "inactive", "lost", "ruins", "relocated", "replica", "unknown"):
            self.assertIn(s, VOCAB["status"])
        for t in ("conical_masonry", "cast_iron", "skeletal", "screwpile", "caisson", "crib", "integral",
                  "wood_frame", "concrete", "texas_tower", "other"):
            self.assertIn(t, VOCAB["structure_type"])
        for r in ("tower", "dwelling", "fog_signal", "oil_house", "boathouse", "front_range", "rear_range", "other"):
            self.assertIn(r, VOCAB["structure_role"])


class FetcherValuesInVocabTest(unittest.TestCase):
    def test_wikidata_tables(self):
        self.assertTrue(set(fw.STRUCTURE_TYPE_CLASSES.values()) <= set(VOCAB["structure_type"]))
        self.assertTrue(set(fw.MATERIALS.values()) <= set(VOCAB["structure_material"]))
        self.assertTrue(set(fw.EVENT_ITEMS.values()) <= set(VOCAB["event"]))
        self.assertTrue({s for s, _ in fw.STATE_OF_USE.values()} <= set(VOCAB["status"]))
        self.assertTrue({v for _, v in fw.OWNERSHIP_WORDS} <= set(VOCAB["ownership"]))

    def test_merge_tables(self):
        self.assertTrue(set(merge.KIND_GROUP) == set(VOCAB["kind"]))
        self.assertTrue({r for _, r in merge.ROLE_BY_ANCILLARY} <= set(VOCAB["structure_role"]))
        self.assertTrue(set(merge.EVENT_ORDER) <= set(VOCAB["event"]))

    def test_osm_readings_are_in_vocab(self):
        samples = [
            {"man_made": "lighthouse", "name": "Grand Haven South Pierhead Light"},
            {"man_made": "lighthouse", "name": "Plum Island Range Front Light"},
            {"man_made": "lighthouse", "seamark:type": "light_minor", "name": "Hubbards Cove"},
            {"seamark:type": "light_vessel", "name": "Nantucket"},
            {"man_made": "lighthouse", "name": "Cape Cod Light"},
        ]
        for tags in samples:
            kind, role = fo.kind_and_role(tags, tags["name"])
            self.assertIn(kind, VOCAB["kind"])
            self.assertIn(role, VOCAB["structure_role"] + [None])
        for tags in ({"demolished:man_made": "lighthouse"}, {"ruins": "yes"}, {"disused": "yes", "man_made": "lighthouse"},
                     {"man_made": "lighthouse", "seamark:light:character": "Fl"}, {"man_made": "lighthouse"}):
            status, _ = fo.status_claim(tags)
            self.assertIn(status, VOCAB["status"] + [None])
        stype, mat = fo.structure_type({"tower:construction": "lattice", "building:material": "steel"})
        self.assertEqual(stype, "skeletal")
        self.assertIn(mat, VOCAB["structure_material"])


class OsmReadingTest(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(fo.kind_and_role({}, "Grand Haven South Pierhead Light"), ("pier_light", None))
        self.assertEqual(fo.kind_and_role({}, "Plum Island Range Front Light"), ("range_lights", "front_range"))
        self.assertEqual(fo.kind_and_role({}, "Plum Island Range Rear Light"), ("range_lights", "rear_range"))
        self.assertEqual(fo.kind_and_role({"seamark:light:category": "rear"}, "Caveau Point"), ("range_lights", "rear_range"))
        self.assertEqual(fo.kind_and_role({"man_made": "lighthouse", "seamark:type": "light_minor"}, "Hubbards Cove")[0], "harbor_light")
        # a light_minor that its name calls a lighthouse stays a lighthouse
        self.assertEqual(fo.kind_and_role({"man_made": "lighthouse", "seamark:type": "light_minor"}, "Cape Forchu Lighthouse")[0], "lighthouse")

    def test_status(self):
        self.assertEqual(fo.status_claim({"demolished:man_made": "lighthouse"})[0], "lost")
        self.assertEqual(fo.status_claim({"razed:man_made": "lighthouse"})[0], "lost")
        self.assertEqual(fo.status_claim({"man_made": "lighthouse", "ruins": "yes"})[0], "ruins")
        self.assertEqual(fo.status_claim({"disused:man_made": "lighthouse"})[0], "inactive")
        self.assertEqual(fo.status_claim({"man_made": "lighthouse", "seamark:light:colour": "white"})[0], "active")
        self.assertIsNone(fo.status_claim({"man_made": "lighthouse"})[0])

    def test_characteristic(self):
        self.assertEqual(fo.characteristic({"seamark:light:character": "Fl", "seamark:light:group": "2",
                                            "seamark:light:colour": "white", "seamark:light:period": "10"}), "Fl(2) W 10s")
        self.assertEqual(fo.characteristic({"seamark:light:character": "Oc", "seamark:light:colour": "red",
                                            "seamark:light:period": "4"}), "Oc R 4s")
        self.assertEqual(fo.characteristic({"seamark:light:character": "Al.Fl", "seamark:light:colour": "white;red",
                                            "seamark:light:period": "30"}), "Al.Fl WR 30s")
        self.assertEqual(fo.characteristic({"seamark:light:character": "F", "seamark:light:colour": "white"}), "F W")
        self.assertIsNone(fo.characteristic({"seamark:light:colour": "white"}))
        char, height, rng, sectors = fo.light_tags({"seamark:light:1:character": "Fl", "seamark:light:1:colour": "white",
                                                    "seamark:light:1:period": "5", "seamark:light:1:range": "16",
                                                    "seamark:light:2:character": "Fl", "seamark:light:2:colour": "red",
                                                    "seamark:light:2:period": "5", "seamark:light:2:range": "12",
                                                    "seamark:light:height": "31"})
        self.assertEqual((char, height, rng, sectors), ("Fl W 5s", 31.0, 16.0, ["Fl W 5s", "Fl R 5s"]))

    def test_geometry_and_lengths(self):
        self.assertEqual(fo.wkt_point("POINT(-70.2 43.6)"), (43.6, -70.2))
        lat, lon = fo.wkt_point("POLYGON((0 0,2 0,2 2,0 2,0 0))")
        self.assertAlmostEqual(lat, 1.0)
        self.assertAlmostEqual(lon, 1.0)
        self.assertEqual(fo.parse_length_m("80 ft"), 24.38)
        self.assertEqual(fo.parse_length_m("24.384"), 24.38)

    def test_flags(self):
        self.assertIsNotNone(fo.minor_beacon_hint({"fixme": "could be a beacon with a light"}, "Cap Gribane"))
        self.assertIsNone(fo.minor_beacon_hint({"fixme": "could be a beacon with a light", "wikidata": "Q1"}, "X"))
        self.assertIsNotNone(fo.minor_beacon_hint({"seamark:type": "light_minor"}, None))
        self.assertIsNotNone(fo.decorative_hint({"leisure": "miniature_golf"}, "Lighthouse"))
        self.assertIsNotNone(fo.decorative_hint({}, "Brant Point Replica Lighthouse"))


class WikidataReadingTest(unittest.TestCase):
    def test_years(self):
        self.assertEqual(fw.parse_year("1872-01-01T00:00:00Z"), 1872)
        self.assertIsNone(fw.parse_year("-0500-01-01T00:00:00Z"))
        self.assertIsNone(fw.parse_year("somevalue"))
        self.assertEqual(fw.min_year(["1880-01-01T00:00:00Z", "1791-01-01T00:00:00Z"]), 1791)

    def test_names(self):
        self.assertEqual(fw.name_kind("Kitty Hawk Life-Saving Station"), "life_saving_station")
        self.assertEqual(fw.name_kind("United States lightship Ambrose (LV-87)"), "lightship")
        self.assertEqual(fw.name_kind("Haig Point Range front light"), "range_lights")
        self.assertEqual(fw.name_kind("Racine North Breakwater Light"), "pier_light")
        self.assertIsNone(fw.name_kind("Portland Head Light"))
        self.assertEqual(fw.name_role("Haig Point Range front light"), "front_range")
        self.assertEqual(fw.name_role("Nantucket Range Rear Light"), "rear_range")
        self.assertIsNone(fw.name_role("Haig Point Range Lights"))

    def test_characteristic_choice(self):
        vals = sorted(["FF WRG (secteurs)", "Fl W 4s", "Fl W 4s, R sector"], key=fw.characteristic_rank)
        self.assertEqual(vals[0], "Fl W 4s")

    def test_quantities(self):
        rows = [{"prop": {"value": "range"}, "amount": {"value": "24"}, "unit": {"value": fw.WD + "Q93318"},
                 "colour": {"value": fw.WD + "Q23444"}},
                {"prop": {"value": "range"}, "amount": {"value": "20"}, "unit": {"value": fw.WD + "Q253276"}},
                {"prop": {"value": "height"}, "amount": {"value": "80"}, "unit": {"value": fw.WD + "Q3710"}}]
        best, seen = fw.quantity(rows, "range", fw.UNIT_NM)
        self.assertEqual(best, 24.0)              # nautical miles beat 20 statute miles (17.38 nmi)
        self.assertEqual(len(seen), 2)
        self.assertEqual(fw.quantity(rows, "height", fw.UNIT_M)[0], 24.38)

    def test_wkt(self):
        self.assertEqual(fw.wkt_to_coord("POINT(-70.207778 43.623056)"), "43.623056 -70.207778 - NormalRank -")
        self.assertEqual(fw.parse_coords(["43.623056 -70.207778 - NormalRank -"])[0]["lat"], 43.623056)

    def test_region_and_county(self):
        def row(depth, a, label, iso=None, cls=""):
            r = {"depth": {"value": str(depth)}, "a": {"value": fw.WD + a}, "aLabel": {"value": label}, "cls": {"value": cls}}
            if iso:
                r["iso"] = {"value": iso}
            return r
        rows = [row(1, "Q1", "Cape Elizabeth", cls="town in the United States"),
                row(2, "Q2", "Cumberland County", cls="county of Maine"),
                row(3, "Q724", "Maine", iso="US-ME", cls="U.S. state")]
        self.assertEqual(fw.region_and_county(rows, "US")[:2], ("ME", "Cumberland"))
        rows = [row(1, "Q1183", "Puerto Rico", cls="unincorporated territory")]
        self.assertEqual(fw.region_and_county(rows, "US")[0], "PR")


if __name__ == "__main__":
    unittest.main()
