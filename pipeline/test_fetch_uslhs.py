"""Tests for pipeline/fetch_uslhs.py on places shaped like the corpus crawl's places.json."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_uslhs as us  # noqa: E402

CASTLE_HILL = {
    "nid": 3001, "slug": "castle-hill", "name": "Castle Hill", "type": "Light Station", "established": 1890, "existing": True,
    "lat": 41.46167, "lon": -71.36333, "town": "NEWPORT", "state": "RI", "county": "NEWPORT", "owner": "U.S. Coast Guard",
    "open_to_public": False, "tower_established": 1890, "tower_material": "GRANITE BLOCKS", "tower_shape": "CONICAL",
    "tower_foundation": "GRANITE BLOCKS", "focal_height_ft": 40.0, "tower_height_ft": 35.0, "active_aton": True,
    "current_optic": "300 MM", "original_optic": "FIFTH ORDER, FRESNEL", "original_lens_year": 1890, "private_aid": False,
    "automated": 1957, "url": "https://archives.uslhs.org/places/castle-hill", "roster_lines": 3,
}
GONE = {
    "nid": 3002, "slug": "egg-island", "name": "Egg Island", "type": "Light Station", "established": 1837, "existing": False,
    "lat": 39.174, "lon": -75.1355, "state": "NJ", "tower_established": 1878, "tower_foundation": "BRICK PIER",
    "demolished": 1946, "discontinued": 1941, "active_aton": False, "url": "https://archives.uslhs.org/places/egg-island",
}


class FieldTest(unittest.TestCase):
    def test_a_standing_active_light(self):
        r = us.build_record(CASTLE_HILL)
        self.assertEqual((r["key"], r["name"], r["region"], r["kind"], r["status"]), ("uslhs:3001", "Castle Hill", "RI", "lighthouse", "active"))
        self.assertEqual((r["lat"], r["lon"], r["precision"]), (41.46167, -71.36333, "approximate"))
        self.assertEqual(r["county"], "Newport")
        self.assertEqual(r["light"]["first_lit"], 1890)
        self.assertEqual(r["structure"]["built"], 1890)
        self.assertEqual(r["structure"]["material"], "stone")
        self.assertEqual(r["structure"]["height_m"], 10.67)
        self.assertEqual(r["light"]["focal_height_m"], 12.19)
        self.assertEqual((r["agency"], r["ownership"]), ("U.S. Coast Guard", "federal"))
        self.assertIsNone(r["light"]["lens"])                     # "300 MM" is a modern optic, not a lens order
        self.assertEqual(r["access"]["level"], None)              # "not open to the public" is a note, not a level
        self.assertIn("not open to the public", r["access"]["note"])
        events = {(e["year"], e["event"]) for e in r["events"]}
        self.assertEqual(events, {(1890, "first_lit"), (1957, "automated"), (1890, "lens_installed")})
        self.assertEqual(r["links"][0]["url"], "https://archives.uslhs.org/places/castle-hill")

    def test_a_lost_light(self):
        r = us.build_record(GONE)
        self.assertEqual(r["status"], "lost")
        self.assertEqual(r["light"]["deactivated"], 1941)
        self.assertEqual(r["structure"]["built"], 1878)
        self.assertIn((1946, "destroyed"), {(e["year"], e["event"]) for e in r["events"]})
        self.assertNotIn("keepers", str(r))

    def test_existing_but_not_an_active_aid_is_inactive(self):
        r = us.build_record({**CASTLE_HILL, "active_aton": False, "private_aid": False, "open_to_public": True})
        self.assertEqual(r["status"], "inactive")
        self.assertEqual(r["access"]["level"], "public")
        self.assertEqual(r["visit"], {"grounds_open": True})
        r = us.build_record({**CASTLE_HILL, "active_aton": False, "private_aid": True})
        self.assertEqual(r["status"], "active")

    def test_lens(self):
        self.assertEqual(us.parse_lens("THIRD ORDER, FRESNEL"), {"type": "fresnel", "order": "3"})
        self.assertEqual(us.parse_lens("Fourth Order"), {"type": "fresnel", "order": "4"})
        self.assertEqual(us.parse_lens("3rd order fresnel"), {"type": "fresnel", "order": "3"})
        self.assertEqual(us.parse_lens("Third and one-half order"), {"type": "fresnel", "order": "3.5"})
        self.assertIsNone(us.parse_lens("DCB-24"))
        self.assertIsNone(us.parse_lens("REMOVED"))
        self.assertIsNone(us.parse_lens(None))
        r = us.build_record({**CASTLE_HILL, "current_optic": "FOURTH ORDER, FRESNEL"})
        self.assertEqual(r["light"]["lens"], {"type": "fresnel", "order": "4", "status": "in_place", "where": None})

    def test_structure_type_from_foundation_and_shape(self):
        self.assertEqual(us.pick_type("OCTAGONAL", "SCREWPILE", "X"), "screwpile")
        self.assertEqual(us.pick_type(None, "CAST IRON/CONCRETE CAISSON", "X"), "caisson")
        self.assertEqual(us.pick_type("SKELETAL", None, "X"), "skeletal")
        self.assertEqual(us.pick_type("CONICAL", "STONE", "Cleveland Water Intake Crib"), "crib")
        self.assertIsNone(us.pick_type("SQUARE", "STONE", "X"))

    def test_ownership_classes(self):
        self.assertEqual(us.ownership_of("Oregon Parks and Recreation Department"), "state")
        self.assertEqual(us.ownership_of("City of Fernandina Beach"), "local")
        self.assertEqual(us.ownership_of("American Lighthouse Foundation"), "nonprofit")
        self.assertEqual(us.ownership_of("Private owner"), "private")
        self.assertEqual(us.ownership_of("National Park Service - Acadia National Park"), "federal")
        self.assertIsNone(us.ownership_of(None))


class TypeTest(unittest.TestCase):
    def test_types(self):
        ls = us.build_record({"nid": 1, "slug": "diamond-shoal-lightship-station", "name": "Diamond Shoal (Lightship Station)",
                              "type": "Lightship Station", "established": 1897, "discontinued": 1966, "state": "NC",
                              "url": "https://archives.uslhs.org/places/x"})
        self.assertEqual((ls["kind"], ls["name"], ls["lat"], ls["status"]), ("lightship_station", "Diamond Shoal", None, None))
        self.assertEqual((ls["light"]["first_lit"], ls["light"]["deactivated"]), (1897, 1966))
        lss = us.build_record({"nid": 2, "slug": "x", "name": "Cape May Life Saving Station", "type": "Lifesaving Station",
                               "existing": True, "state": "NJ", "established": 1849})
        self.assertEqual((lss["kind"], lss["name"]), ("life_saving_station", "Cape May Life-Saving Station"))
        self.assertEqual([e["event"] for e in lss["events"]], ["built"])
        faux = us.build_record({"nid": 3, "slug": "x", "name": "Boca Chita Key", "type": "Private (Faux) Lighthouse",
                                "existing": True, "state": "FL", "lat": 25.87, "lon": -80.29})
        self.assertTrue(faux["extra"]["enrich_only"] and "decorative_hint" in faux["extra"])
        self.assertIsNone(faux["status"])
        minor = us.build_record({"nid": 4, "slug": "x", "name": "Catskill Reach", "type": "Minor Aid to Navigation",
                                 "existing": False, "state": "NY", "discontinued": 1930})
        self.assertIsNone(minor["status"])                       # a minor aid makes no claim about a station
        self.assertEqual(minor["events"], [])
        rep = us.build_record({"nid": 5, "slug": "x", "name": "Blakistone Island (Replica)", "type": "Replica",
                               "existing": True, "state": "MD", "lat": 38.2, "lon": -76.7})
        self.assertEqual((rep["status"], rep["name"]), ("replica", "Blakistone Island (Replica)"))
        self.assertIsNone(us.build_record({"nid": 6, "slug": "x", "name": "A Museum", "type": "Museum", "state": "ME"}))
        self.assertIsNone(us.build_record({"nid": 7, "slug": "x", "name": "Cuban Light", "type": "Light Station"}))   # no US state

    def test_names(self):
        n = us.read_name("Barcelona (Portland Harbor)", "Light Station")
        self.assertEqual((n["name"], n["alts"]), ("Barcelona", ["Portland Harbor"]))
        n = us.read_name("Grosse Ile Range Front", "Light Station")
        self.assertEqual((n["kind"], n["role"]), ("range_lights", "front_range"))
        n = us.read_name("Cape Henry (Old)", "Light Station")
        self.assertEqual(n["name"], "Cape Henry (Old)")           # which tower stays in the name
        n = us.read_name("Au Sable Pierhead", "Light Station")
        self.assertEqual(n["kind"], "pier_light")

    def test_zero_position_is_none(self):
        r = us.build_record({**CASTLE_HILL, "lat": 0.0, "lon": 0.0})
        self.assertIsNone(r["lat"])


class _Box:
    """A state as a lat/lon box, with the contains() of the Census polygons."""
    def __init__(self, lat0, lat1, lon0, lon1):
        self.b = (lat0, lat1, lon0, lon1)

    def contains(self, lat, lon):
        return self.b[0] <= lat <= self.b[1] and self.b[2] <= lon <= self.b[3]


class _States:
    """Two neighbouring boxes standing in for the boundary file: RI and a land-less 'MA' to its north."""
    polys = {"RI": _Box(41.0, 42.0, -72.0, -71.0), "MA": _Box(42.0, 43.0, -72.0, -70.0)}

    def lookup(self, lat, lon, country=None):
        for code, box in self.polys.items():
            if box.contains(lat, lon):
                return code, "inside", 0.0
        return "RI", "nearest", 40.0      # the nearest coast, for a tower out at sea


class PositionTest(unittest.TestCase):
    rl = _States()

    def test_a_position_in_its_state_stands(self):
        self.assertIsNone(us.plausible_position(self.rl, "RI", 41.46, -71.36))
        self.assertEqual(us.build_record(CASTLE_HILL, self.rl)["lat"], 41.46167)

    def test_an_offshore_tower_belongs_to_the_nearest_coast(self):
        self.assertIsNone(us.plausible_position(self.rl, "RI", 40.95, -71.2))   # off the coast, inside the state's box

    def test_a_point_just_over_the_river_is_not_dropped(self):
        self.assertIsNone(us.plausible_position(self.rl, "MA", 41.95, -71.5))   # inside RI, 5 km from MA

    def test_a_typing_slip_is_dropped_and_said(self):
        why = us.plausible_position(self.rl, "MA", 41.2, -71.5)               # inside RI, 80 km from MA
        self.assertIn("MA", why)
        r = us.build_record({**CASTLE_HILL, "state": "MA", "lat": 41.2, "lon": -71.5}, self.rl)
        self.assertIsNone(r["lat"])
        self.assertIn("41.2, -71.5", r["extra"]["position_dropped"])

    def test_not_a_coordinate(self):
        self.assertEqual(us.plausible_position(None, "VA", 360.87, -76.3), "not a coordinate on Earth")
        self.assertEqual(us.plausible_position(None, "NJ", 39.157, -744.175), "not a coordinate on Earth")

    def test_without_the_boundary_file_only_the_bounding_box_judges(self):
        self.assertIsNone(us.plausible_position(None, "RI", 41.5, -71.5))
        self.assertIn("bounding box", us.plausible_position(None, "RI", 44.1, -74.2))   # Great Beds' slip, NJ filed as NY


if __name__ == "__main__":
    unittest.main()
