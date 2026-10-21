"""Tests for research/roster.py: parsers on trimmed samples, role normalisation, fuzzy name matching,
station-id resolution. Run: python3 -m unittest research.test_roster  (or python3 research/test_roster.py)"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("FRESNEL_RAW_ROOT", tempfile.mkdtemp(prefix="fresnel-test-raw-"))
import roster  # noqa: E402

TD = os.path.join(HERE, "testdata")


def read(name):
    with open(os.path.join(TD, name), encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class ParsePlace(unittest.TestCase):
    def test_portland_head_facts(self):
        p = roster.parse_place(read("place_portland_head.html"), "portland-head")
        self.assertEqual(p["nid"], 2931)
        self.assertEqual(p["roster_id"], 2931)
        self.assertEqual(p["type"], "Light Station")
        self.assertEqual(p["state"], "ME")
        self.assertEqual(p["established"], 1791)
        self.assertTrue(p["existing"])
        self.assertTrue(p["open_to_public"])
        self.assertEqual(p["automated"], 1989)
        self.assertEqual(p["focal_height_ft"], 101.0)
        self.assertEqual(p["tower_shape"], "CONICAL")
        self.assertAlmostEqual(p["lat"], 43.62333, places=4)
        self.assertAlmostEqual(p["lon"], -70.20833, places=4)
        self.assertEqual(p["url"], "https://archives.uslhs.org/places/portland-head")

    def test_seconds_and_discontinued(self):
        p = roster.parse_place(read("place_point_reyes.html"), "point-reyes")
        self.assertAlmostEqual(p["lat"], 37 + 59 / 60 + 39 / 3600, places=4)
        self.assertAlmostEqual(p["lon"], -(123 + 1 / 60 + 24 / 3600), places=4)
        self.assertEqual(p["discontinued"], 1975)

    def test_prose_is_not_kept(self):
        # only mapped, factual labels survive; nothing like a description field
        p = roster.parse_place(read("place_portland_head.html"), "portland-head")
        self.assertFalse(any(k in p for k in ("description", "history", "comments")))

    def test_coordinates_hemispheres(self):
        self.assertEqual(roster.signed_latlon("14° 16'", "170° 42'", "American Samoa"), (-14.26667, -170.7))
        lat, lon = roster.signed_latlon("13° 26'", "144° 39'", "Guam")
        self.assertGreater(lon, 0)
        self.assertEqual(roster.parse_coord("43° 37.4'")[0], 43.62333)
        self.assertEqual(roster.parse_coord("")[0], None)
        self.assertEqual(roster.parse_coord("47.3333 N"), (47.3333, "N"))

    def test_state_codes(self):
        self.assertEqual(roster.state_code("Maine"), "ME")
        self.assertEqual(roster.state_code("Puerto Rico"), "PR")
        self.assertEqual(roster.state_code("us virgin islands"), "VI")
        self.assertEqual(roster.state_code("mn"), "MN")
        self.assertIsNone(roster.state_code("Narnia"))


class ParseIndexAndRoster(unittest.TestCase):
    def test_index_rows(self):
        html = read("places_index.html")
        rows = roster.parse_index(html)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["slug"], "12th-street-crib")
        self.assertEqual(rows[0]["type"], "Minor Aid to Navigation")
        self.assertEqual(rows[0]["state"], "Illinois")
        self.assertEqual(roster.parse_last_page(html), 76)
        self.assertEqual(roster.parse_total(html), 2299)

    def test_span_variants(self):
        self.assertEqual(roster.parse_span("(1791-1795)"), (1791, 1795, False, False))
        self.assertEqual(roster.parse_span("(at  least 1950-1951)"), (1950, 1951, True, False))
        self.assertEqual(roster.parse_span("(1956-at least 1957)"), (1956, 1957, False, True))
        self.assertEqual(roster.parse_span("(1904- )"), (1904, None, False, False))
        self.assertEqual(roster.parse_span("( - )"), (None, None, False, False))

    def test_roster_lines(self):
        lines = roster.parse_roster(read("showpeople_portland_head.json"))
        names = [l["name"] for l in lines]
        self.assertIn("Joshua F. Strout", names)
        strout = next(l for l in lines if l["name"] == "Joshua F. Strout")
        self.assertEqual((strout["from"], strout["to"]), (1869, 1904))
        self.assertEqual(strout["span"], "1869-1904")
        self.assertEqual(strout["person"], "joshua-f-strout")
        self.assertEqual(strout["role_raw"], "Principal Lighthouse Keeper")

    def test_approx_flags(self):
        lines = roster.parse_roster(read("showpeople_point_reyes.json"))
        g = next(l for l in lines if l["name"] == "Arleigh D. Garrison")
        self.assertTrue(g["from_approx"] and g["to_approx"])
        b = next(l for l in lines if l["name"] == "Alan Barras")
        self.assertIsNone(b["to"])

    def test_garbage_reply(self):
        self.assertEqual(roster.parse_roster("not json"), [])
        self.assertEqual(roster.parse_roster("[]"), [])


class Roles(unittest.TestCase):
    def test_vocabulary(self):
        n = roster.normalise_role
        self.assertEqual(n("Principal Lighthouse Keeper", True), "head keeper")
        self.assertEqual(n("Principal Lighthouse Keeper", False), "keeper")
        self.assertEqual(n("Acting Principal Lighthouse Keeper"), "acting keeper")
        self.assertEqual(n("1st Assistant Lighthouse Keeper"), "first assistant")
        self.assertEqual(n("2nd Assistant Lighthouse Keeper"), "second assistant")
        self.assertEqual(n("3rd Assistant Lighthouse Keeper"), "third assistant")
        self.assertEqual(n("4th Assistant Lighthouse Keeper"), "fourth assistant")
        self.assertEqual(n("Assistant Lighthouse Keeper"), "assistant")
        self.assertEqual(n("Laborer"), "laborer")
        self.assertEqual(n("Master"), "master")
        self.assertEqual(n("USCG"), "other")
        self.assertEqual(n("Contractor"), "other")

    def test_lines_get_role_note_for_other(self):
        raw = roster.parse_roster(read("showpeople_point_reyes.json"))
        lines = roster.roster_lines(raw)
        cg = next(l for l in lines if l["role_raw"] == "USCG")
        self.assertEqual(cg["role"], "other")
        self.assertIn("Coast Guard", cg["role_note"])
        # a station with assistants calls its principal keepers "head keeper"
        self.assertEqual(lines[0]["role"], "head keeper")


class Matching(unittest.TestCase):
    def test_name_scores(self):
        s = roster.name_score
        self.assertEqual(s("Portland Head Light", "Portland Head"), 1.0)
        self.assertEqual(s("Point Reyes Lighthouse", "Point Reyes"), 1.0)
        self.assertEqual(s("Pt. Reyes", "Point Reyes"), 1.0)
        self.assertEqual(s("St. Augustine Light", "Saint Augustine"), 1.0)
        self.assertGreater(s("Split Rock Light", "Split Rock Point"), 0.7)
        self.assertLess(s("Point Reyes", "Split Rock"), 0.55)
        self.assertLess(s("Portland Head", "Portland Breakwater"), 0.8)

    def test_distance(self):
        d = roster.haversine_km(43.6231, -70.2079, 43.6233, -70.2083)
        self.assertLess(d, 0.1)
        self.assertAlmostEqual(roster.haversine_km(0, 0, 0, 1), 111.19, delta=0.2)

    def places(self):
        return [
            {"nid": 1, "slug": "split-rock", "name": "Split Rock", "type": "Light Station", "state": "MN", "lat": 47.2, "lon": -91.37, "roster_lines": 60},
            {"nid": 2, "slug": "split-rock-ny", "name": "Split Rock", "type": "Light Station", "state": "NY", "lat": 44.26, "lon": -73.3, "roster_lines": 5},
            {"nid": 3, "slug": "point-reyes", "name": "Point Reyes", "type": "Light Station", "state": "CA", "lat": 37.99, "lon": -123.02, "roster_lines": 240},
            {"nid": 4, "slug": "point-reyes-lifesaving-station", "name": "Point Reyes Life-Saving Station", "type": "Lifesaving Station", "state": "CA", "lat": 38.0, "lon": -122.97, "roster_lines": 10},
        ]

    def test_state_separates_namesakes(self):
        c = roster.rank_candidates(self.places(), ["Split Rock Light"], state="MN")
        self.assertEqual([x[3]["slug"] for x in c], ["split-rock"])
        both = roster.rank_candidates(self.places(), ["Split Rock"], near=(44.3, -73.3))
        self.assertEqual(both[0][3]["slug"], "split-rock-ny")

    def test_station_id_resolves_by_name_and_position(self):
        os.environ["FRESNEL_STATIONS_DIR"] = tempfile.mkdtemp()
        os.makedirs(os.path.join(os.environ["FRESNEL_STATIONS_DIR"], "mn"))
        write(os.path.join(os.environ["FRESNEL_STATIONS_DIR"], "mn", "us-mn-split-rock.json"), json.dumps(
            {"id": "us-mn-split-rock", "name": "Split Rock Light", "kind": "lighthouse", "region": "MN",
             "location": {"lat": 47.2008, "lon": -91.3672}}))
        p, cands, msg = roster.resolve_station("us-mn-split-rock", self.places())
        self.assertEqual(p["slug"], "split-rock")
        self.assertIn("km", msg)

    def test_exact_unrivalled_name_within_30_km_is_accepted_with_a_warning(self):
        os.environ["FRESNEL_STATIONS_DIR"] = tempfile.mkdtemp()
        os.makedirs(os.path.join(os.environ["FRESNEL_STATIONS_DIR"], "mn"))
        write(os.path.join(os.environ["FRESNEL_STATIONS_DIR"], "mn", "us-mn-split-rock.json"), json.dumps(
            {"id": "us-mn-split-rock", "name": "Split Rock Light", "kind": "lighthouse", "region": "MN",
             "location": {"lat": 47.35, "lon": -91.6}}))  # about 17 km from the USLHS position
        places = self.places()
        places[0]["lat"], places[0]["lon"] = 47.2, -91.37
        p, cands, msg = roster.resolve_station("us-mn-split-rock", places)
        self.assertEqual(p["slug"], "split-rock")
        self.assertIn("only to the minute", msg)

    def test_station_id_without_record_uses_the_id_name(self):
        os.environ["FRESNEL_STATIONS_DIR"] = tempfile.mkdtemp()
        p, cands, msg = roster.resolve_station("us-ca-point-reyes", self.places())
        self.assertEqual(p["slug"], "point-reyes")  # the light, not the life-saving station of the same name

    def test_far_position_is_unsure(self):
        os.environ["FRESNEL_STATIONS_DIR"] = tempfile.mkdtemp()
        os.makedirs(os.path.join(os.environ["FRESNEL_STATIONS_DIR"], "ca"))
        write(os.path.join(os.environ["FRESNEL_STATIONS_DIR"], "ca", "us-ca-point-reyes.json"), json.dumps(
            {"id": "us-ca-point-reyes", "name": "Point Reyes", "kind": "lighthouse", "region": "CA",
             "location": {"lat": 33.0, "lon": -118.0}}))
        p, cands, msg = roster.resolve_station("us-ca-point-reyes", self.places())
        self.assertIsNone(p)
        self.assertTrue(cands)

    def test_canada_is_out_of_scope(self):
        p, cands, msg = roster.resolve_station("ca-ns-sambro-island", self.places())
        self.assertIsNone(p)
        self.assertIn("United States only", msg)


class ServedText(unittest.TestCase):
    def test_place_text_contains_roster_lines_as_printed(self):
        raw = tempfile.mkdtemp()
        os.environ["FRESNEL_RAW_ROOT"] = raw
        for sub in ("place", "people"):
            os.makedirs(os.path.join(raw, "uslhs", sub))
        write(os.path.join(raw, "uslhs", "place", "portland-head.html"), read("place_portland_head.html"))
        write(os.path.join(raw, "uslhs", "people", "2931.json"), read("showpeople_portland_head.json"))
        t = roster.local_text_for_url("https://archives.uslhs.org/places/portland-head")
        self.assertIn("Joshua F. Strout (1869-1904)", t)
        self.assertIn("Year Established: 1791", t)
        self.assertIsNone(roster.local_text_for_url("https://archives.uslhs.org/places/never-heard-of-it"))
        self.assertIsNone(roster.local_text_for_url("https://example.com/places/portland-head"))
        t2 = roster.local_text_for_url("https://archives.uslhs.org/general/showPeople/2931")
        self.assertIn("Joseph K. Greenleaf (1791-1795)", t2)


if __name__ == "__main__":
    unittest.main()
