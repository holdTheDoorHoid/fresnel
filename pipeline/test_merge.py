"""Tests for pipeline/merge.py on small synthetic extracts: joins, ranges, ancillary buildings,
status rules, ids, locked fields, never deleting, and determinism."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge  # noqa: E402

TODAY = "2026-10-21"


def rec(source: str, key: str, name: str | None, lat: float, lon: float, **kw) -> dict:
    r = {
        "key": f"{source}:{key}", "url": None, "name": name, "other_names": [], "country": kw.pop("country", "US"),
        "region": kw.pop("region", "ME"), "county": kw.pop("county", None), "lat": lat, "lon": lon,
        "precision": "exact", "kind": kw.pop("kind", "lighthouse"), "kind_raw": None, "role": kw.pop("role", None),
        "status": kw.pop("status", None), "status_raw": None,
        "structure": kw.pop("structure", {"type": None, "material": None, "built": None, "height_m": None, "status": None}),
        "light": kw.pop("light", {"first_lit": None, "deactivated": None, "characteristic": None,
                                  "focal_height_m": None, "range_nm": None, "fog_signal": None, "lens": None}),
        "setting": None, "registers": kw.pop("registers", []),
        "aton": {"uscg_llnr": None, "arlhs": None, "ccg_list_number": None, "nga": None},
        "agency": None, "ownership": None, "events": kw.pop("events", []), "photos": [], "links": [],
        "relations": kw.pop("relations", {}), "extra": kw.pop("extra", {}),
    }
    assert not kw, kw
    return r


def osm_extra(**kw) -> dict:
    return {"forms": ["man_made=lighthouse"], **kw}


class MergeCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.sources = self.tmp / "sources"
        self.stations = self.tmp / "stations"
        self.sources.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, source: str, records: list[dict]) -> None:
        (self.sources / f"{source}.json").write_text(json.dumps({
            "source": source, "title": source, "url": None, "retrieved": TODAY, "license": "test", "records": records}))

    def run_merge(self, stations: Path | None = None) -> dict:
        return merge.run(self.sources, stations or self.stations, self.tmp / "report.json", TODAY)

    def station_files(self, stations: Path | None = None) -> dict[str, dict]:
        root = stations or self.stations
        return {p.stem: json.loads(p.read_text()) for p in sorted(root.rglob("*.json"))}


class JoinTest(MergeCase):
    def test_wikidata_tag_and_osm_position(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Portland Head Light", 43.6231, -70.2080, county="Cumberland",
                                    light={"first_lit": 1791, "deactivated": None, "characteristic": "Fl W 4s",
                                           "focal_height_m": 31.0, "range_nm": 24.0, "fog_signal": None, "lens": None})])
        self.write("osm", [rec("osm", "way/1", "Portland Head Lighthouse", 43.62311, -70.20787,
                               extra=osm_extra(wikidata="Q1"), status="active",
                               light={"first_lit": None, "deactivated": None, "characteristic": "Fl W 4s",
                                      "focal_height_m": 30.8, "range_nm": 24.0, "fog_signal": "horn", "lens": None})])
        self.run_merge()
        files = self.station_files()
        self.assertEqual(list(files), ["us-me-portland-head"])
        st = files["us-me-portland-head"]
        self.assertEqual(st["name"], "Portland Head Light")
        self.assertEqual(st["location"]["from"], "osm")
        self.assertEqual(st["status"], "active")
        self.assertEqual(st["verification"], "facts")
        self.assertEqual(st["light"]["fog_signal"], "horn")
        self.assertEqual(st["light"]["first_lit"], 1791)
        self.assertEqual(len(st["structures"]), 1)
        self.assertIn("Portland Head Lighthouse", st["other_names"])

    def test_place_and_name_without_tag(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Cape Elizabeth Light", 43.5661, -70.2000)])
        self.write("osm", [rec("osm", "node/1", "Cape Elizabeth Lighthouse", 43.5670, -70.2010, extra=osm_extra())])
        self.run_merge()
        self.assertEqual(len(self.station_files()), 1)

    def test_opposites_stay_apart(self):
        self.write("osm", [rec("osm", "node/1", "Grand Haven North Pierhead Light", 43.05, -86.25, extra=osm_extra()),
                           rec("osm", "node/2", "Grand Haven South Pierhead Light", 43.0505, -86.2505, extra=osm_extra())])
        self.run_merge()
        self.assertEqual(len(self.station_files()), 2)

    def test_other_countries_never_join(self):
        self.write("osm", [rec("osm", "node/1", "Border Light", 45.0, -67.0, extra=osm_extra()),
                           rec("osm", "node/2", "Border Light", 45.0001, -67.0001, country="CA", region="NB", extra=osm_extra())])
        self.run_merge()
        self.assertEqual(sorted(self.station_files()), ["ca-nb-border", "us-me-border"])


class RangeTest(MergeCase):
    def test_front_and_rear_become_one_station(self):
        self.write("wikidata", [
            rec("wikidata", "Q1", "Plum Island Range Front Light", 45.30, -86.95, region="WI", kind="range_lights", role="front_range"),
            rec("wikidata", "Q2", "Plum Island Range Rear Light", 45.305, -86.95, region="WI", kind="range_lights", role="rear_range"),
        ])
        self.run_merge()
        files = self.station_files()
        self.assertEqual(list(files), ["us-wi-plum-island-range"])
        st = files["us-wi-plum-island-range"]
        self.assertEqual(st["kind"], "range_lights")
        self.assertEqual(st["name"], "Plum Island Range Lights")
        self.assertEqual([s["role"] for s in st["structures"]], ["front_range", "rear_range"])
        self.assertIn("location", st["structures"][1])  # the rear stands apart from the pin
        self.assertEqual(st["location"]["lat"], 45.30)   # the pin is the front light
        report = json.loads((self.tmp / "report.json").read_text())
        self.assertEqual(report["range_lights"]["paired"], [{"id": "us-wi-plum-island-range", "name": "Plum Island Range Lights"}])

    def test_whole_range_item_takes_its_halves(self):
        self.write("wikidata", [
            rec("wikidata", "Q1", "Haig Point Range Front Light", 32.134, -80.836, region="SC", kind="range_lights", role="front_range"),
            rec("wikidata", "Q2", "Haig Point Range Rear Light", 32.145, -80.836, region="SC", kind="range_lights", role="rear_range"),
            rec("wikidata", "Q3", "Haig Point Range Lights", 32.140, -80.836, region="SC", kind="range_lights",
                extra={"station_level": True}),
        ])
        self.run_merge()
        files = self.station_files()
        self.assertEqual(list(files), ["us-sc-haig-point-range"])
        self.assertEqual(files["us-sc-haig-point-range"]["name"], "Haig Point Range Lights")
        self.assertEqual(len(files["us-sc-haig-point-range"]["structures"]), 2)

    def test_two_fronts_are_left_apart_and_listed(self):
        self.write("wikidata", [
            rec("wikidata", "Q1", "Craighill Channel Range Front Light", 39.20, -76.40, region="MD", kind="range_lights", role="front_range"),
            rec("wikidata", "Q2", "Craighill Channel Range Front Light", 39.25, -76.45, region="MD", kind="range_lights", role="front_range"),
            rec("wikidata", "Q3", "Craighill Channel Range Rear Light", 39.21, -76.41, region="MD", kind="range_lights", role="rear_range"),
        ])
        self.run_merge()
        self.assertEqual(len(self.station_files()), 3)
        report = json.loads((self.tmp / "report.json").read_text())
        self.assertEqual(len(report["range_lights"]["ambiguous"]), 1)


class StructuresTest(MergeCase):
    def test_successive_towers_are_one_station(self):
        self.write("wikidata", [
            rec("wikidata", "Q1", "Old Cape Henry Light", 36.9256, -76.0083, region="VA",
                structure={"type": "conical_masonry", "material": "stone", "built": 1792, "height_m": 27.0, "status": None}),
            rec("wikidata", "Q2", "Cape Henry Light", 36.9266, -76.0076, region="VA",
                structure={"type": "cast_iron", "material": "cast_iron", "built": 1881, "height_m": 50.0, "status": None},
                light={"first_lit": 1881, "deactivated": None, "characteristic": "Mo(U) W 20s", "focal_height_m": 50.0,
                       "range_nm": 17.0, "fog_signal": None, "lens": None}),
        ])
        self.write("osm", [rec("osm", "way/2", "Cape Henry Lighthouse", 36.92662, -76.00758, extra=osm_extra(), status="active")])
        self.run_merge()
        files = self.station_files()
        self.assertEqual(list(files), ["us-va-cape-henry"])
        st = files["us-va-cape-henry"]
        self.assertEqual(st["name"], "Cape Henry Light")
        self.assertEqual([s["built"] for s in st["structures"]], [1792, 1881])
        self.assertEqual(st["status"], "active")
        # the OSM tower joined the 1881 tower, which is also where the pin is
        self.assertAlmostEqual(st["location"]["lat"], 36.92662)

    def test_station_building_joins_as_a_structure(self):
        self.write("wikidata", [rec("wikidata", "Q1", "West Chop Light", 41.4808, -70.5997, region="MA")])
        self.write("osm", [rec("osm", "way/9", "Keeper's House", 41.4806, -70.5996, region="MA",
                               extra={"forms": ["historic=lighthouse"]}),
                           rec("osm", "way/10", "Rainshed", 41.4807, -70.5990, region="MA",
                               extra={"forms": ["historic=lighthouse"]}),
                           rec("osm", "way/11", "Oil House", 41.60, -70.70, region="MA",
                               extra={"forms": ["historic=lighthouse"]})])
        report = self.run_merge()
        files = self.station_files()
        self.assertEqual(list(files), ["us-ma-west-chop"])
        roles = sorted(s["role"] for s in files["us-ma-west-chop"]["structures"])
        self.assertEqual(roles, ["dwelling", "other", "tower"])
        self.assertEqual([u["key"] for u in report["not_shown"]], ["osm:way/11"])  # far from any light station


class StatusTest(MergeCase):
    def test_lost_and_possibly_lost(self):
        self.write("wikidata", [
            rec("wikidata", "Q1", "Cape Henlopen Light", 38.79, -75.09, region="DE", status=None,
                light={"first_lit": 1767, "deactivated": 1924, "characteristic": None, "focal_height_m": None,
                       "range_nm": None, "fog_signal": None, "lens": None},
                extra={"possibly_lost": True, "p576": 1926}),
            rec("wikidata", "Q2", "Shinnecock Light", 40.85, -72.50, region="NY", status="lost"),
        ])
        self.run_merge()
        files = self.station_files()
        self.assertEqual(files["us-de-cape-henlopen"]["status"], "unknown")
        self.assertIn("may be gone", files["us-de-cape-henlopen"]["status_note"])
        self.assertEqual(files["us-ny-shinnecock"]["status"], "lost")

    def test_osm_map_of_the_structure_means_it_stands(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Cedar Point Light", 38.30, -76.38, region="MD",
                                    light={"first_lit": 1896, "deactivated": 1928, "characteristic": None, "focal_height_m": None,
                                           "range_nm": None, "fog_signal": None, "lens": None},
                                    extra={"possibly_lost": True, "p576": 1996})])
        self.write("osm", [rec("osm", "way/1", "Cedar Point Light", 38.3001, -76.3801, region="MD", extra=osm_extra())])
        self.run_merge()
        self.assertEqual(self.station_files()["us-md-cedar-point"]["status"], "inactive")

    def test_osm_lit_beats_wikidata_retired_with_a_conflict(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Old Light", 44.0, -69.0, status="inactive")])
        self.write("osm", [rec("osm", "node/1", "Old Light", 44.0001, -69.0001, status="active", extra=osm_extra())])
        self.run_merge()
        st = self.station_files()["us-me-old"]
        self.assertEqual(st["status"], "active")
        self.assertEqual([c["field"] for c in st["conflicts"]], ["status"])
        self.assertEqual(st["verification"], "unverified")


class ScopeTest(MergeCase):
    def test_decorative_hidden_and_beacons_not_shown(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Lake Minatare Lighthouse", 41.93, -103.49, region="NE",
                                    extra={"out_of_scope": "Decorative: Wikidata classes it as a faux lighthouse"})])
        self.write("osm", [
            rec("osm", "node/1", None, 45.0, -64.0, country="CA", region="NS", extra=osm_extra()),
            rec("osm", "node/2", "Cap Gribane", 47.0, -70.6, country="CA", region="QC",
                extra=osm_extra(minor_beacon_suspect="fixme=could be a beacon with a light")),
            rec("osm", "node/3", "Pole Light", 44.5, -68.5, extra={"forms": ["seamark:type=light_major"], "enrich_only": "x"}),
        ])
        report = self.run_merge()
        files = self.station_files()
        self.assertEqual(list(files), ["us-ne-lake-minatare"])
        self.assertTrue(files["us-ne-lake-minatare"]["hidden"])
        self.assertIn("faux lighthouse", files["us-ne-lake-minatare"]["hidden_reason"])
        self.assertEqual(sorted(u["key"] for u in report["not_shown"]), ["osm:node/1", "osm:node/2", "osm:node/3"])

    def test_enrich_only_light_joins_a_station(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Point Reyes Light", 37.9955, -123.0230, region="CA")])
        self.write("osm", [rec("osm", "way/5", "Point Reyes Light", 37.9956, -123.0233, region="CA",
                               light={"first_lit": None, "deactivated": None, "characteristic": "Fl W 5s",
                                      "focal_height_m": 9.0, "range_nm": 24.0, "fog_signal": None, "lens": None},
                               extra={"forms": ["seamark:type=light_major"], "enrich_only": "x"})])
        self.run_merge()
        st = self.station_files()["us-ca-point-reyes"]
        self.assertEqual(st["light"]["characteristic"], "Fl W 5s")


class IdsAndMemoryTest(MergeCase):
    def setUp(self):
        super().setUp()
        self.write("wikidata", [
            rec("wikidata", "Q1", "Green Island Light", 44.10, -69.0),
            rec("wikidata", "Q2", "Green Island Light", 44.50, -68.0),    # further north: plain id
            rec("wikidata", "Q3", "Seguin Light", 43.7075, -69.7581),
        ])
        self.write("osm", [rec("osm", "node/7", "Seguin Island Light", 43.7076, -69.7580, extra=osm_extra()),
                           rec("osm", "node/8", "Seguin Light", 43.7077, -69.7581,
                               extra={"forms": ["seamark:type=light_major"], "enrich_only": "x"})])

    def test_numbering_north_to_south(self):
        self.run_merge()
        files = self.station_files()
        self.assertEqual(files["us-me-green-island"]["sources"][0]["key"], "wikidata:Q2")
        self.assertEqual(files["us-me-green-island-2"]["sources"][0]["key"], "wikidata:Q1")

    def test_rerun_writes_nothing_and_from_scratch_is_identical(self):
        self.run_merge()
        first = {p: p.read_text() for p in self.stations.rglob("*.json")}
        report_first = (self.tmp / "report.json").read_text()
        report = self.run_merge()
        self.assertEqual(report["_run"]["files_changed"], 0)
        self.assertEqual({p: p.read_text() for p in self.stations.rglob("*.json")}, first)
        self.assertEqual((self.tmp / "report.json").read_text(), report_first)
        other = self.tmp / "stations2"
        merge.run(self.sources, other, self.tmp / "report2.json", TODAY)
        self.assertEqual({p.relative_to(other): p.read_text() for p in other.rglob("*.json")},
                         {p.relative_to(self.stations): t for p, t in first.items()})

    def test_never_deletes_and_keeps_locked_fields(self):
        self.run_merge()
        path = self.stations / "me" / "us-me-seguin.json"
        st = json.loads(path.read_text())
        st["name"] = "Seguin Island Light Station"
        st["locked"] = ["name", "visit.climbable"]
        st["visit"]["climbable"] = True
        path.write_text(json.dumps(st))
        # The Seguin records vanish from the extracts; the other stations stay as they are.
        self.write("wikidata", [rec("wikidata", "Q1", "Green Island Light", 44.10, -69.0),
                                rec("wikidata", "Q2", "Green Island Light", 44.50, -68.0)])
        self.write("osm", [])
        self.run_merge()
        self.assertTrue(path.exists())
        self.assertEqual(json.loads(path.read_text())["name"], "Seguin Island Light Station")
        # Bring them back: the station takes them again, by memory, and keeps the locked values.
        self.setUp_sources_again()
        self.run_merge()
        st = json.loads(path.read_text())
        self.assertEqual(st["name"], "Seguin Island Light Station")
        self.assertTrue(st["visit"]["climbable"])
        self.assertEqual(sorted(s["key"] for s in st["sources"]), ["osm:node/7", "osm:node/8", "wikidata:Q3"])
        self.assertEqual(len(self.station_files()), 3)

    def setUp_sources_again(self):
        self.write("wikidata", [
            rec("wikidata", "Q1", "Green Island Light", 44.10, -69.0),
            rec("wikidata", "Q2", "Green Island Light", 44.50, -68.0),
            rec("wikidata", "Q3", "Seguin Light", 43.7075, -69.7581),
        ])
        self.write("osm", [rec("osm", "node/7", "Seguin Island Light", 43.7076, -69.7580, extra=osm_extra()),
                           rec("osm", "node/8", "Seguin Light", 43.7077, -69.7581,
                               extra={"forms": ["seamark:type=light_major"], "enrich_only": "x"})])


class NameTest(unittest.TestCase):
    def test_scores(self):
        f = merge.name_forms
        self.assertEqual(merge.name_score(f("Portland Head Light"), f("Portland Head Lighthouse")), 1.0)
        self.assertEqual(merge.name_score(f("Old Cape Henry Light"), f("Cape Henry Light")), 0.95)
        self.assertEqual(merge.name_score(f("Plum Island Range Front Light"), f("Plum Island Range Rear Light")), 0.2)
        self.assertEqual(merge.name_score(f("North Pier Light"), f("South Pier Light")), 0.2)
        self.assertEqual(merge.name_score(f("Station No. 14"), f("Station No. 35")), 0.2)
        self.assertEqual(merge.name_score(f("Phare de l'Île Verte"), f("Île Verte Lighthouse")), 1.0)
        self.assertEqual(merge.name_score(f("Faro de Punta Higüero"), f("Punta Higuero Light")), 1.0)
        self.assertIsNone(merge.name_score(f("Lighthouse"), f("Portland Head Light")))
        self.assertLess(merge.name_score(f("Baccalieu Island Lighthouse (old)"), f("Baccalieu Island Lighthouse")), 1.0)

    def test_slugs_and_range_names(self):
        self.assertEqual(merge.slugify("Portland Head Light", "lighthouse"), "portland-head")
        self.assertEqual(merge.slugify("Faro de Punta Higüero", "lighthouse"), "punta-higuero")
        self.assertEqual(merge.slugify("Phare de Pointe-au-Père", "lighthouse"), "pointe-au-pere")
        self.assertEqual(merge.slugify("Sambro Island Lighthouse", "lighthouse"), "sambro-island")
        self.assertEqual(merge.slugify("Kitty Hawk Life-Saving Station", "life_saving_station"), "kitty-hawk-life-saving-station")
        self.assertEqual(merge.slugify("United States lightship Ambrose (LV-87)", "lightship"), "lightship-ambrose-lv-87")
        self.assertEqual(merge.range_station_name("Haig Point Range front light"), "Haig Point Range Lights")
        self.assertEqual(merge.range_station_name("Nantucket Cliff Front Range Light"), "Nantucket Cliff Range Lights")
        self.assertEqual(merge.range_station_name("Grosse Ile Front Light"), "Grosse Ile Range Lights")

    def test_ancillary_names(self):
        self.assertTrue(merge.is_ancillary_name("2nd Assistant Keeper's Quarters"))
        self.assertTrue(merge.is_ancillary_name("Point Reyes Lighthouse Visitor Center"))
        self.assertTrue(merge.is_ancillary_name("Fog Signal Building"))
        self.assertFalse(merge.is_ancillary_name("Cottage Point Light"))
        self.assertFalse(merge.is_ancillary_name("Barnegat Light"))


if __name__ == "__main__":
    unittest.main()
