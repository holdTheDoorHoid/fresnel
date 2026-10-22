"""Tests for pipeline/fetch_lightship_stations.py: station names as the Society files them, tying a Light List entry to a
station by vessel number and year, a printed position and a computed one (the 1900 Pollock Rip worked example), and the
transcription files the positions come from."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_lightship_stations as F  # noqa: E402
import geo  # noqa: E402


def station(slug, name, established, discontinued, vessels):
    return {"slug": slug, "name": name, "alts": [], "never_built": False, "established": established, "discontinued": discontinued,
            "vessels": [{"node": n, "label": f"Lightship: LV-{n:03d}", "start": s, "end": e} for n, s, e in vessels]}


POLLOCK_RIP = {"list": "ll1900", "leaf": 50, "page": 42, "number": 143, "name": "Pollock Rip Light-Vessel, No. 47", "vessel_no": 47,
               "lat": [41, 32, 17], "lon": [69, 54, 36], "approx": [True, True],
               "location": "Moored in 36 feet of water to the southward and eastward of the E. end of Pollock Rip Shoal, about 4 miles SE. by E. 1/4 E. from Monomoy Point Light-House, Mass.",
               "state": "MA"}


class NamesTest(unittest.TestCase):
    def test_the_societys_titles_become_station_names(self):
        self.assertEqual(F.station_name("Pollock Rip (Lightship Station)"), ("Pollock Rip", [], False))
        self.assertEqual(F.station_name("Cross Ledge (Upper Middle) (Lightship Station)"), ("Cross Ledge", ["Upper Middle"], False))
        self.assertEqual(F.station_name("Ohio Ledge (Lightship Station) (Never Built)")[2], True)
        self.assertEqual(F.station_name("Carysfort Reef Light Vessel Station")[0], "Carysfort Reef")

    def test_hull_numbers_read_as_the_society_writes_them(self):
        self.assertEqual(F.hull_of("Lightship: LV-087"), ("LV", 87))
        self.assertEqual(F.hull_of("Lightship: WLV-196"), ("WLV", 196))
        self.assertEqual(F.hull_of("Lightship: WAL 512"), ("WAL", 512))
        self.assertEqual(F.hull_of("Lightship: LV- ZZ (Aurora Borealis)"), ("LV", None))

    def test_squash_ignores_punctuation_and_case(self):
        self.assertEqual(F.squash("Five-Fathom Bank"), F.squash("five fathom bank"))

    def test_a_stub_and_a_renamed_station_are_declared_for_places_that_exist_in_the_societys_list(self):
        # "Cape Hatteras" is the Society's stub for Diamond Shoal (LV-72 only, no years); the Light Lists call Wreck of Scotland "Scotland"
        self.assertEqual(F.FOLDED_STUBS["cape-hatteras-lightship-station"], "diamond-shoal-lightship-station")
        self.assertEqual(F.NAME_FIX["wreck-scotland-lightship-station"][0], "Scotland")
        self.assertIn("Wreck of Scotland", F.NAME_FIX["wreck-scotland-lightship-station"][1])


class EntryTieTest(unittest.TestCase):
    """An entry belongs to the station whose name it carries and whose assignment for that vessel number covers the list's year."""

    def setUp(self):
        self.stations = {
            "pollock-rip-lightship-station": station("pollock-rip-lightship-station", "Pollock Rip", 1849, 1969, [(47, 1893, 1905), (11, 1905, 1920)]),
            "pollock-rip-slue-lightship-station": station("pollock-rip-slue-lightship-station", "Pollock Rip Slue", 1913, 1923, [(60, 1913, 1923)]),
            "boston-lightship-station": station("boston-lightship-station", "Boston", 1893, 1970, [(54, 1893, 1910)]),
        }

    def test_vessel_number_year_and_name_tie_the_entry(self):
        slug, how = F.entry_station(POLLOCK_RIP, self.stations)
        self.assertEqual(slug, "pollock-rip-lightship-station")
        self.assertIn("vessel number and year agree", how)

    def test_the_name_alone_ties_an_entry_with_no_vessel_number(self):
        e = {**POLLOCK_RIP, "vessel_no": None, "name": "Boston Light-Vessel"}
        slug, how = F.entry_station(e, self.stations)
        self.assertEqual(slug, "boston-lightship-station")
        self.assertIn("no vessel number", how)

    def test_a_station_not_yet_established_in_the_year_is_not_tied(self):
        only_slue = {"pollock-rip-slue-lightship-station": self.stations["pollock-rip-slue-lightship-station"]}     # began in 1913; the list is of 1900
        e = {**POLLOCK_RIP, "vessel_no": None, "name": "Pollock Rip Slue Light-Vessel"}
        slug, _ = F.entry_station(e, only_slue)
        self.assertIsNone(slug)

    def test_an_entry_two_stations_could_own_is_left_untied(self):
        self.stations["boston-2"] = station("boston-2", "Boston", 1850, 1950, [])
        e = {**POLLOCK_RIP, "vessel_no": None, "name": "Boston Light-Vessel"}
        slug, why = F.entry_station(e, self.stations)
        self.assertIsNone(slug)
        self.assertIn("2 stations", why)


class PrintedPositionTest(unittest.TestCase):
    def test_a_printed_position_is_read_in_degrees_and_cites_page_and_entry(self):
        pos = F.stated_position(POLLOCK_RIP)
        self.assertAlmostEqual(pos["lat"], 41 + 32 / 60 + 17 / 3600, places=4)
        self.assertAlmostEqual(pos["lon"], -(69 + 54 / 60 + 36 / 3600), places=4)
        self.assertEqual(pos["basis"], "stated")
        self.assertIn("page 42, entry 143", pos["note"])
        self.assertIn("41 32 17 N, 69 54 36 W", pos["note"])
        self.assertIn("the seconds are in brackets", pos["note"])         # the Light List prints them in brackets: they vary
        self.assertIn("Location as printed: Moored in 36 feet", pos["note"])

    def test_a_position_given_to_the_minute_says_so(self):
        e = {**POLLOCK_RIP, "list": "ll1934", "lat": [41, 33, 0], "lon": [69, 59, 0], "to_minute": True, "approx": [False, False]}
        note = F.stated_position(e)["note"]
        self.assertIn("41 33 N, 69 59 W (to the minute)", note)
        self.assertNotIn("brackets", note)


class ComputedPositionTest(unittest.TestCase):
    """The worked example: Pollock Rip Light-Vessel No. 47, Light List 1900. "About 4 miles SE. by E. 1/4 E. from Monomoy
    Point Light-House" (printed at 41 33 34 N, 69 59 39 W) must land where the entry itself prints the vessel."""

    LIGHT = {"name": "Monomoy Point Light-House", "lat": 41 + 33 / 60 + 34 / 3600, "lon": -(69 + 59 / 60 + 39 / 3600), "source": "Light List 1900, page 42, entry 144"}
    PRINTED = (41 + 32 / 60 + 17 / 3600, -(69 + 54 / 60 + 36 / 3600))

    def test_a_magnetic_bearing_is_turned_true_and_lands_on_the_printed_position(self):
        pos = F.computed_position({"from_light": self.LIGHT, "point": "SE. by E. 1/4 E.", "nm": 4.0, "list": "ll1900", "year": 1900, "reference": "magnetic",
                                   "text": "about 4 miles SE. by E. 1/4 E. from Monomoy Point Light-House"})
        self.assertEqual(pos["basis"], "computed")
        self.assertLess(geo.distance_nm(pos["lat"], pos["lon"], *self.PRINTED), 0.1)       # 0.05 nm, 80 m
        self.assertIn("magnetic; the list says so", pos["note"])
        self.assertIn("IGRF-14 declination of 1900", pos["note"])
        self.assertIn("4 nautical miles from Monomoy Point Light-House", pos["note"])
        self.assertIn("about 4 miles SE. by E. 1/4 E. from Monomoy Point Light-House", pos["note"])     # the source text is kept

    def test_without_the_declination_she_would_be_a_mile_out(self):
        mag = geo.compass_degrees("SE. by E. 1/4 E.")
        lat, lon = geo.destination(self.LIGHT["lat"], self.LIGHT["lon"], mag, 4.0)
        self.assertGreater(geo.distance_nm(lat, lon, *self.PRINTED), 0.8)

    def test_a_true_bearing_is_used_as_printed(self):
        # Stone Horse Shoal, Local Light and Buoy List 1934: "0.9 mile 153 degrees from Monomoy Point Unused Lighthouse"; printed "41 33 69 59"
        pos = F.computed_position({"from_light": {**self.LIGHT, "lat": 41.559444, "lon": -69.994167}, "degrees": 153.0, "nm": 0.9, "list": "ll1934",
                                   "year": 1934, "reference": "true", "text": "0.9 mile 153° from Monomoy Point Unused Lighthouse"})
        self.assertLess(geo.distance_nm(pos["lat"], pos["lon"], 41 + 33 / 60, -(69 + 59 / 60)), 0.6)     # the printed position is to the minute
        self.assertIn("true bearing 153 degrees as printed", pos["note"])

    def test_the_two_computed_stations_on_file_have_what_a_reader_needs_to_check_them(self):
        computed = json.loads(F.COMPUTED.read_text(encoding="utf-8"))
        self.assertEqual(sorted(computed), ["lake-huron-lightship-station", "stonehorse-shoal-lightship-station"])
        for slug, c in computed.items():
            for key in ("from_light", "reference", "nm", "list", "year", "text"):
                self.assertIn(key, c, (slug, key))
            self.assertIn(c["reference"], ("magnetic", "true"))
            self.assertIn(c["list"], F.LISTS)
            for key in ("name", "lat", "lon", "source"):
                self.assertIn(key, c["from_light"], (slug, key))
            pos = F.computed_position(c)
            self.assertLess(geo.distance_nm(pos["lat"], pos["lon"], c["from_light"]["lat"], c["from_light"]["lon"]), 2.0, slug)   # a light vessel lies near its light


class BuildPositionsTest(unittest.TestCase):
    def test_the_newest_list_gives_the_position_and_earlier_ones_are_kept(self):
        older = {**POLLOCK_RIP, "list": "ll1893", "number": 120, "lat": [41, 32, 20], "lon": [69, 54, 30]}
        stations = {"pollock-rip-lightship-station": station("pollock-rip-lightship-station", "Pollock Rip", 1849, 1969, [(47, 1890, 1905)])}
        with mock.patch.object(F, "load_entries", return_value=[older, POLLOCK_RIP]), mock.patch.object(F, "COMPUTED", Path("/nonexistent")):
            out, unmatched = F.build_positions(stations)
        pos = out["pollock-rip-lightship-station"]
        self.assertEqual(unmatched, [])
        self.assertEqual(pos["list"], "ll1900")
        self.assertEqual([a["list"] for a in pos["also"]], ["ll1893"])

    def test_an_entry_that_ties_to_no_station_goes_to_the_review(self):
        with mock.patch.object(F, "load_entries", return_value=[POLLOCK_RIP]), mock.patch.object(F, "COMPUTED", Path("/nonexistent")):
            out, unmatched = F.build_positions({})
        self.assertEqual(out, {})
        self.assertEqual(unmatched[0]["entry"], "ll1900:143")

    def test_a_computed_position_is_used_only_where_no_list_prints_one(self):
        stations = {"pollock-rip-lightship-station": station("pollock-rip-lightship-station", "Pollock Rip", 1849, 1969, [(47, 1890, 1905)])}
        computed = {"pollock-rip-lightship-station": {"from_light": TestComputed.LIGHT, "point": "SE.", "nm": 4.0, "list": "ll1900", "year": 1900,
                                                       "reference": "magnetic", "text": "4 miles SE."}}
        with mock.patch.object(F, "load_entries", return_value=[POLLOCK_RIP]), mock.patch.object(F, "COMPUTED") as path:
            path.exists.return_value = True
            path.read_text.return_value = json.dumps(computed)
            out, _ = F.build_positions(stations)
        self.assertEqual(out["pollock-rip-lightship-station"]["basis"], "stated")


TestComputed = ComputedPositionTest


class TranscriptionTest(unittest.TestCase):
    """The Light List entries read from the page images: every line must be usable and plausible."""

    def setUp(self):
        self.entries = F.load_entries()

    def test_there_are_entries_for_each_list_read(self):
        self.assertGreaterEqual(len(self.entries), 40)
        self.assertEqual({e["list"] for e in self.entries} - set(F.LISTS), set())
        self.assertTrue({"ll1893", "ll1900", "gl1925", "gl1928", "ll1934"} <= {e["list"] for e in self.entries})

    def test_every_entry_has_a_page_a_number_a_name_and_a_place_in_range(self):
        for e in self.entries:
            tag = f"{e['list']}:{e['number']}"
            for key in ("leaf", "page", "number", "name", "lat", "lon"):
                self.assertIn(key, e, tag)
            self.assertTrue(24 <= e["lat"][0] <= 49, tag)               # the coasts and lakes of the United States
            self.assertTrue(66 <= e["lon"][0] <= 125, tag)
            self.assertTrue(0 <= e["lat"][1] < 60 and 0 <= e["lat"][2] < 60 and 0 <= e["lon"][1] < 60 and 0 <= e["lon"][2] < 60, tag)
            self.assertTrue(e["vessel_no"] is None or isinstance(e["vessel_no"], int), tag)

    def test_no_entry_is_listed_twice(self):
        keys = [(e["list"], e["number"]) for e in self.entries]
        self.assertEqual(len(keys), len(set(keys)))

    def test_the_worked_example_is_on_file_as_printed(self):
        e = next(e for e in self.entries if e["list"] == "ll1900" and e["number"] == 143)
        self.assertEqual((e["name"], e["page"], e["lat"], e["lon"]), ("Pollock Rip Light-Vessel, No. 47", 42, [41, 32, 17], [69, 54, 36]))
        self.assertIn("SE. by E. 1/4 E.", e["location"])

    def test_every_list_names_an_archive_page_a_reader_can_open(self):
        for key, L in F.LISTS.items():
            self.assertTrue(L["url"].startswith("https://archive.org/details/" + L["id"]), key)
            self.assertIn(L["bearings"], ("magnetic", "true"))


if __name__ == "__main__":
    unittest.main()
