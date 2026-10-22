"""Tests for pipeline/site_vessels.py and its use in build_site_data.py: which station holds which source record, the vessels listed on a
lightship station, a vessel's page data with its stations resolved, and the list of stations nothing places."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_site_data as bsd  # noqa: E402
import site_vessels as sv  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def station(sid, name, keys=(), **kw):
    return {"id": sid, "name": name, "sources": [{"source": k.split(":")[0], "key": k} for k in keys], **kw}


def vessel(vid, hull, career, berth=None, names=(), fate="survives"):
    return {"id": vid, "hull": hull, "wal": None, "names": list(names), "built": 1900, "retired": 1940, "career": career, "fate": {"status": fate}, "berth": berth,
            "sources": [{"label": "US Lighthouse Society Digital Archive: vessel record", "url": "https://archives.uslhs.org/node/1", "credit": "c"}]}


def line(name, key, start, end):
    return {"station": name, "station_key": key, "start": start, "end": end}


STATIONS = [
    station("us-ma-pollock-rip", "Pollock Rip", ["lightship_stations:pollock-rip", "uslhs:1"]),
    station("us-ma-lightship-nantucket", "United States lightship Nantucket", ["wikidata:Q1"]),
    station("us-ma-hidden", "Hidden", ["lightship_stations:hidden"], hidden=True),
    station("us-ma-retired", "Retired", ["lightship_stations:retired"], merged_into="us-ma-pollock-rip"),
    station("us-ma-nome", "Nome", ["lss_reports:ak-nome"]),
]
VESSELS = {
    "lv-47": vessel("lv-47", "LV-47", [line("Pollock Rip", "lightship_stations:pollock-rip", 1893, 1905), line("Pollock Rip", "lightship_stations:pollock-rip", 1910, 1912),
                                       line("Examination Vessel", None, 1942, 1945), line("Hidden", "lightship_stations:hidden", 1913, 1914)]),
    "lv-112": vessel("lv-112", "LV-112", [line("Pollock Rip", "lightship_stations:pollock-rip", 1905, 1910)], names=["Nantucket"],
                     berth={"station_id": "us-ma-lightship-nantucket", "name": "United States lightship Nantucket", "lat": 42.36, "lon": -71.03, "basis": "hull number"}),
    "lv-9": vessel("lv-9", "LV-9", [], berth={"station_id": "us-xx-not-published", "name": "Elsewhere", "lat": 1.0, "lon": 2.0}),
}


class ScanTest(unittest.TestCase):
    def test_a_station_is_found_by_its_source_keys_and_hidden_or_retired_ones_are_not(self):
        key_to_id, visible = sv.scan(STATIONS)
        self.assertEqual(key_to_id["lightship_stations:pollock-rip"], "us-ma-pollock-rip")
        self.assertEqual(key_to_id["lss_reports:ak-nome"], "us-ma-nome")
        self.assertNotIn("uslhs:1", key_to_id)                                  # only the keys of the sources that carry vessels or reports
        self.assertNotIn("lightship_stations:hidden", key_to_id)
        self.assertNotIn("lightship_stations:retired", key_to_id)
        self.assertEqual(visible["us-ma-pollock-rip"], "Pollock Rip")
        self.assertNotIn("us-ma-hidden", visible)

    def test_a_record_the_site_would_skip_is_not_linked(self):
        key_to_id, visible = sv.scan(STATIONS, usable=lambda r: r["id"] != "us-ma-pollock-rip")
        self.assertNotIn("lightship_stations:pollock-rip", key_to_id)
        self.assertNotIn("us-ma-pollock-rip", visible)


class StationVesselsTest(unittest.TestCase):
    def setUp(self):
        self.key_to_id, self.visible = sv.scan(STATIONS)

    def test_a_station_lists_its_vessels_in_order_of_the_first_year_with_each_stint(self):
        out = sv.station_vessels(VESSELS, self.key_to_id, self.visible)["us-ma-pollock-rip"]
        self.assertEqual([v["id"] for v in out], ["lv-47", "lv-112"])
        self.assertEqual(out[0]["stints"], [{"start": 1893, "end": 1905}, {"start": 1910, "end": 1912}])
        self.assertTrue(all(v["role"] == "served" for v in out))

    def test_a_survivors_berth_station_lists_the_vessel_as_a_berth_not_as_service(self):
        out = sv.station_vessels(VESSELS, self.key_to_id, self.visible)["us-ma-lightship-nantucket"]
        self.assertEqual([(v["id"], v["role"], v["names"]) for v in out], [("lv-112", "berth", ["Nantucket"])])

    def test_a_berth_at_a_station_that_is_not_published_makes_no_link(self):
        out = sv.station_vessels(VESSELS, self.key_to_id, self.visible)
        self.assertNotIn("us-xx-not-published", out)
        self.assertNotIn("us-ma-hidden", out)


class VesselPageTest(unittest.TestCase):
    def setUp(self):
        self.key_to_id, self.visible = sv.scan(STATIONS)

    def test_each_career_line_is_linked_only_to_a_station_that_will_be_published(self):
        page = sv.vessel_page(VESSELS["lv-47"], self.key_to_id, self.visible)
        self.assertEqual([c["station_id"] for c in page["career"]], ["us-ma-pollock-rip", "us-ma-pollock-rip", None, None])
        self.assertEqual(page["career"][2]["station"], "Examination Vessel")        # a line that is no station keeps its words

    def test_the_berth_is_kept_when_its_station_is_published_and_dropped_when_not(self):
        self.assertEqual(sv.vessel_page(VESSELS["lv-112"], self.key_to_id, self.visible)["berth"]["station_id"], "us-ma-lightship-nantucket")
        self.assertNotIn("basis", sv.vessel_page(VESSELS["lv-112"], self.key_to_id, self.visible)["berth"])
        self.assertIsNone(sv.vessel_page(VESSELS["lv-9"], self.key_to_id, self.visible)["berth"])


class BerthPointTest(unittest.TestCase):
    def test_the_berth_shows_the_published_stations_name_and_point_not_a_copy_in_the_record(self):
        stations = [station("us-ma-lightship-nantucket", "Lightship Nantucket (renamed)", [], location={"lat": 42.3612, "lon": -71.0352})]
        points: dict = {}
        key_to_id, visible = sv.scan(stations, points=points)
        page = sv.vessel_page(VESSELS["lv-112"], key_to_id, visible, points)
        self.assertEqual(page["berth"], {"station_id": "us-ma-lightship-nantucket", "name": "Lightship Nantucket (renamed)", "lat": 42.3612, "lon": -71.0352})

    def test_a_record_made_without_a_point_gets_none_when_the_station_has_none(self):
        key_to_id, visible = sv.scan([station("us-ma-lightship-nantucket", "Nantucket")])
        berth = sv.vessel_page({**VESSELS["lv-112"], "berth": {"station_id": "us-ma-lightship-nantucket", "name": "x", "basis": "b"}}, key_to_id, visible)["berth"]
        self.assertEqual(berth, {"station_id": "us-ma-lightship-nantucket", "name": "Nantucket"})


class UnplacedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        base = {"other_names": [], "country": "US", "light": {"first_lit": None, "deactivated": None}, "url": "https://example.org/x"}
        (self.tmp / "lightship_stations.json").write_text(json.dumps({"records": [
            {**base, "key": "lightship_stations:pollock-rip", "kind": "lightship_station", "name": "Pollock Rip", "region": "MA", "lat": 41.5, "lon": -69.9, "extra": {}},
            {**base, "key": "lightship_stations:hedge-fence", "kind": "lightship_station", "name": "Hedge Fence", "region": "MA", "lat": None, "lon": None,
             "light": {"first_lit": 1908, "deactivated": 1933}, "extra": {"unplaced_reason": "no Light List gives a position", "location_text": "Nantucket Sound"}},
            {**base, "key": "lightship_stations:carysfort-reef", "kind": "lightship_station", "name": "Carysfort Reef", "region": "FL", "lat": None, "lon": None, "extra": {"unplaced_reason": "x"}},
            {**base, "key": "lightship_stations:curtis-bay-depot", "kind": "lightship_station", "name": "Curtis Bay Depot", "region": "MD", "lat": None, "lon": None,
             "extra": {"unplaced_reason": "a depot", "not_a_mooring": "a depot"}},
        ]}))
        (self.tmp / "lss_reports.json").write_text(json.dumps({"records": [
            {**base, "key": "lss_reports:ak-nome", "kind": "life_saving_station", "name": "Nome Life-Saving Station", "region": "AK", "lat": None, "lon": None,
             "extra": {"years_listed": [1905, 1906, 1909], "locality": "At Nome", "unplaced_reason": "no position could be read cleanly"}},
            {**base, "key": "lss_reports:ma-city-point", "kind": "life_saving_station", "name": "City Point", "region": "MA", "lat": 42.3, "lon": -71.0, "extra": {"years_listed": [1900]}},
        ]}))

    def test_only_stations_with_no_position_and_no_station_on_the_map_are_listed(self):
        # Carysfort Reef has no position of its own, but a station on the map (Society's point) holds it: it is placed
        key_to_id = {"lightship_stations:carysfort-reef": "us-fl-carysfort-reef-2"}
        out = sv.unplaced(self.tmp, key_to_id, VESSELS)
        self.assertEqual([s["name"] for s in out["stations"]], ["Nome Life-Saving Station", "Hedge Fence", "Curtis Bay Depot"])     # by kind, then region, then name
        self.assertEqual(out["count"], 3)

    def test_each_entry_says_why_and_how_it_can_be_helped(self):
        out = {s["name"]: s for s in sv.unplaced(self.tmp, {}, VESSELS)["stations"]}
        hedge = out["Hedge Fence"]
        self.assertEqual((hedge["reason"], hedge["first"], hedge["last"], hedge["where"], hedge["suggest"]), ("no Light List gives a position", 1908, 1933, "Nantucket Sound", True))
        self.assertFalse(out["Curtis Bay Depot"]["suggest"])                    # a depot has no mooring to suggest
        nome = out["Nome Life-Saving Station"]
        self.assertEqual((nome["kind"], nome["first"], nome["last"], nome["where"]), ("life_saving_station", 1905, 1909, "At Nome"))

    def test_a_station_lists_the_vessels_whose_career_names_it(self):
        vessels = {"lv-1": vessel("lv-1", "LV-1", [line("Hedge Fence", "lightship_stations:hedge-fence", 1908, 1920)])}
        out = {s["name"]: s for s in sv.unplaced(self.tmp, {}, vessels)["stations"]}
        self.assertEqual(out["Hedge Fence"]["vessels"], [{"id": "lv-1", "hull": "LV-1"}])

    def test_a_missing_source_file_is_not_an_error(self):
        self.assertEqual(sv.unplaced(self.tmp / "nowhere", {}, {})["count"], 0)


class BuildSiteDataTest(unittest.TestCase):
    """build_site_data.py with a vessels folder writes v/<id>.json, unplaced.json and the vessels on a station's file."""

    def test_the_outputs(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "stations").mkdir()
        (tmp / "vessels").mkdir()
        (tmp / "sources").mkdir()
        full = {"id": "us-ma-pollock-rip", "name": "Pollock Rip", "country": "US", "region": "MA", "kind": "lightship_station", "status": "lost", "verification": "unverified",
                "location": {"lat": 41.5, "lon": -69.9, "precision": "approximate", "from": "lightship_stations"},
                "sources": [{"source": "lightship_stations", "key": "lightship_stations:pollock-rip", "fields": ["location"]}]}
        (tmp / "stations" / "us-ma-pollock-rip.json").write_text(json.dumps(full))
        for vid, v in VESSELS.items():
            (tmp / "vessels" / f"{vid}.json").write_text(json.dumps(v))
        (tmp / "sources" / "lightship_stations.json").write_text(json.dumps({"records": []}))
        out = tmp / "out"
        bsd.build(tmp / "stations", tmp / "stories", tmp / "research", tmp / "sources", tmp / "vocab.json", out, vessels_dir=tmp / "vessels", log=bsd.Log(quiet=True))
        station_file = json.loads((out / "s" / "us-ma-pollock-rip.json").read_text())
        self.assertEqual([v["id"] for v in station_file["vessels"]], ["lv-47", "lv-112"])
        self.assertEqual(sorted(p.stem for p in (out / "v").glob("*.json")), ["lv-112", "lv-47", "lv-9"])
        page = json.loads((out / "v" / "lv-47.json").read_text())
        self.assertEqual(page["career"][0]["station_id"], "us-ma-pollock-rip")
        self.assertEqual(json.loads((out / "unplaced.json").read_text())["count"], 0)
        self.assertEqual(json.loads((out / "meta.json").read_text())["counts"]["vessels"], 3)

    def test_without_a_vessels_folder_nothing_about_vessels_is_written(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "stations").mkdir()
        (tmp / "sources").mkdir()
        (tmp / "stations" / "a.json").write_text(json.dumps({"id": "us-ma-a", "name": "A", "region": "MA", "kind": "lighthouse", "status": "active", "verification": "unverified",
                                                           "location": {"lat": 42.0, "lon": -70.0}, "sources": []}))
        out = tmp / "out"
        bsd.build(tmp / "stations", tmp / "stories", tmp / "research", tmp / "sources", tmp / "vocab.json", out, log=bsd.Log(quiet=True))
        self.assertFalse((out / "v").exists())
        self.assertFalse((out / "unplaced.json").exists())


if __name__ == "__main__":
    unittest.main()
