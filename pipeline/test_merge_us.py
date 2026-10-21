"""Tests for the merge rules added for the US sources (DESIGN 3.9, 2.3): joins on a shared register / ARLHS / Light List
number, records with no position, visit / stay / access and register details from records, scale copies, joins of
a unique namesake, and the decisions of record_joins.py (pins, retired ids, wrong positions, statuses, hidden
stations, replicas, successors). Synthetic extracts only."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge  # noqa: E402

TODAY = "2026-10-21"


def rec(source: str, key: str, name: str | None, lat: float | None, lon: float | None, **kw) -> dict:
    r = {
        "key": f"{source}:{key}", "url": None, "name": name, "other_names": kw.pop("other_names", []), "country": "US",
        "region": kw.pop("region", "ME"), "county": None, "lat": lat, "lon": lon,
        "precision": kw.pop("precision", "exact"), "kind": kw.pop("kind", "lighthouse"), "kind_raw": None,
        "role": kw.pop("role", None), "status": kw.pop("status", None), "status_raw": None,
        "structure": kw.pop("structure", {"type": None, "material": None, "built": None, "height_m": None, "status": None}),
        "light": kw.pop("light", {"first_lit": None, "deactivated": None, "characteristic": None, "focal_height_m": None,
                                 "range_nm": None, "fog_signal": None, "lens": None}),
        "setting": None, "registers": kw.pop("registers", []),
        "aton": kw.pop("aton", {"uscg_llnr": None, "arlhs": None, "ccg_list_number": None, "nga": None}),
        "agency": None, "ownership": None, "events": kw.pop("events", []), "photos": [], "links": [],
        "relations": {}, "extra": kw.pop("extra", {}),
    }
    for k in ("visit", "stay", "access"):
        if k in kw:
            r[k] = kw.pop(k)
    assert not kw, kw
    return r


def decisions(**kw):
    d = types.SimpleNamespace(RECORD_JOINS={}, NO_POSITION=set(), KEEP_APART_PAIRS=set(), NAME_PICKS={}, STATUS_PICKS={},
                              HIDE={}, KEEP_VISIBLE=set(), NOT_DUPLICATES=set(), REPLICA_OF={}, SUCCESSION=[])
    for k, v in kw.items():
        setattr(d, k, v)
    return d


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.sources = self.tmp / "sources"
        self.stations = self.tmp / "stations"
        self.sources.mkdir()

    def tearDown(self):
        merge.set_decisions(merge._NoDecisions())
        shutil.rmtree(self.tmp)

    def write(self, source: str, records: list[dict]) -> None:
        (self.sources / f"{source}.json").write_text(json.dumps({
            "source": source, "title": source, "url": None, "retrieved": TODAY, "license": "test", "records": records}))

    def run_merge(self) -> dict:
        return merge.run(self.sources, self.stations, self.tmp / "report.json", TODAY)

    def files(self) -> dict[str, dict]:
        return {p.stem: json.loads(p.read_text()) for p in sorted(self.stations.rglob("*.json"))}


WD_LIGHT = {"first_lit": 1791, "deactivated": None, "characteristic": "Fl W 4s", "focal_height_m": 31.0, "range_nm": 24.0,
            "fog_signal": None, "lens": None}


class JoinKeyTest(Case):
    def test_a_shared_register_number_joins_a_far_and_differently_named_record(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Portland Head Light", 43.6231, -70.2080, registers=[{"register": "NRHP", "number": "73000121", "url": None}])])
        self.write("nrhp", [rec("nrhp", "73000121", "Portland Headlight Complex", 43.65, -70.17, precision="approximate",
                                registers=[{"register": "NRHP", "number": "73000121", "url": "u", "listed": "1973-04-24", "nhl": None, "nomination": "n"}],
                                events=[{"year": 1973, "event": "nrhp_listed", "note": "NRHP", "from": "nrhp"}])])
        self.run_merge()
        f = self.files()
        self.assertEqual(list(f), ["us-me-portland-head"])
        reg = f["us-me-portland-head"]["registers"][0]
        self.assertEqual((reg["number"], reg["listed"], reg["nomination"]), ("73000121", "1973-04-24", "n"))
        self.assertEqual(len(f["us-me-portland-head"]["structures"]), 1)   # the register's point never makes a structure
        self.assertTrue(any(e["event"] == "nrhp_listed" for e in f["us-me-portland-head"]["events"]))

    def test_a_number_is_not_trusted_across_states_unless_it_is_a_register_number(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Cape Ann Light", 42.6368, -70.5749, region="MA", aton={"uscg_llnr": "1-295", "arlhs": None, "ccg_list_number": None, "nga": None})])
        self.write("rowlett", [rec("rowlett", "fl:cosgrove", "Cosgrove Shoal", None, None, region="FL",
                                   aton={"uscg_llnr": "1-295", "arlhs": None, "ccg_list_number": None, "nga": None}, status="active")])
        self.run_merge()
        self.assertEqual(list(self.files()), ["us-ma-cape-ann"])
        self.assertNotIn("rowlett", {s["source"] for s in self.files()["us-ma-cape-ann"]["sources"]})

    def test_record_with_no_position_joins_by_arlhs_and_by_unique_name_in_state(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Goat Island Light", 43.4, -70.4, aton={"uscg_llnr": None, "arlhs": "USA366", "ccg_list_number": None, "nga": None}),
                                rec("wikidata", "Q2", "Nash Island Light", 44.46, -67.95)])
        self.write("rowlett", [rec("rowlett", "me:goat", "A Different Name", None, None, aton={"uscg_llnr": None, "arlhs": "USA-366", "ccg_list_number": None, "nga": None}),
                               rec("rowlett", "me:nash", "Nash Island", None, None, events=[{"year": 1873, "event": "built", "note": None, "from": "rowlett"}]),
                               rec("rowlett", "me:nowhere", "Nowhere Rock", None, None, status="lost")])
        rep = self.run_merge()
        f = self.files()
        self.assertEqual(sorted(f), ["us-me-goat-island", "us-me-nash-island"])
        self.assertEqual({s["source"] for s in f["us-me-nash-island"]["sources"]}, {"wikidata", "rowlett"})
        self.assertEqual(rep["_run"]["record_matches"]["name_region"], 1)
        self.assertEqual([u["name"] for u in rep["not_shown"]], ["Nowhere Rock"])   # no station, no position: listed, not started

    def test_cross_id_joins_two_stations_records(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Cape Elizabeth Light", 43.5661, -70.2000)])
        self.write("lighthousefriends", [rec("lighthousefriends", "547", "Cape Elizabeth Light", 43.5661, -70.2000, extra={"xref": ["lhf:547"]})])
        self.write("rowlett", [rec("rowlett", "me:ce", "Two Lights", None, None, extra={"xref": ["lhf:547"]})])
        self.run_merge()
        f = self.files()
        self.assertEqual(list(f), ["us-me-cape-elizabeth"])
        self.assertEqual({s["source"] for s in f["us-me-cape-elizabeth"]["sources"]}, {"wikidata", "lighthousefriends", "rowlett"})


class FieldTest(Case):
    def test_flags_from_a_source_fill_visit_stay_access_and_a_missing_flag_overrides_nothing(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Seguin Island Light", 43.7078, -69.7586)])
        self.write("lighthousefriends", [rec("lighthousefriends", "1", "Seguin Island", 43.7078, -69.7586,
                                             visit={"climbable": True, "boat_only": True},
                                             access={"level": "private", "note": "LHF: private."},
                                             stay={"type": "keeper_program", "provider": None, "url": None, "season": None, "checked": None, "note": "kp"})])
        self.write("uslhs_passport", [rec("uslhs_passport", "stamp:me:seguin", "Seguin Island", None, None, visit={"passport_stamp": True},
                                          stay={"type": "rental", "provider": None, "url": "https://x.example", "season": None, "checked": TODAY, "note": "r"})])
        self.run_merge()
        s = self.files()["us-me-seguin-island"]
        self.assertEqual((s["visit"]["climbable"], s["visit"]["boat_only"], s["visit"]["passport_stamp"]), (True, True, True))
        self.assertIsNone(s["visit"]["tours"])
        self.assertEqual(s["access"]["level"], "private")
        self.assertEqual(s["stay"]["type"], "rental")      # a place to sleep outranks a volunteer program
        self.assertEqual(s["stay"]["url"], "https://x.example")

    def test_the_charted_light_comes_from_enc_and_the_lens_from_the_first_source_that_has_one(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Portland Head Light", 43.6231, -70.2080, light=dict(WD_LIGHT))])
        self.write("enc", [rec("enc", "a", None, 43.6231, -70.2079, extra={"enrich_only": True, "quiet_unmatched": True},
                               light={**WD_LIGHT, "first_lit": None, "range_nm": 14.0, "focal_height_m": 30.8})])
        self.write("uslhs", [rec("uslhs", "1", "Portland Head", 43.623, -70.208, precision="approximate",
                                 light={**WD_LIGHT, "first_lit": None, "characteristic": None, "focal_height_m": None, "range_nm": None,
                                        "lens": {"type": "fresnel", "order": "4", "status": "in_place", "where": None}})])
        self.run_merge()
        light = self.files()["us-me-portland-head"]["light"]
        self.assertEqual((light["range_nm"], light["focal_height_m"], light["from"]), (14.0, 30.8, "enc"))
        self.assertEqual(light["lens"]["order"], "4")

    def test_a_charted_light_beside_an_inactive_tower_does_not_relight_it(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Marblehead Light", 43.0, -70.0, status="inactive")])
        self.write("uscg_light_list", [rec("uscg_light_list", "1-10", "Marblehead Light", 43.0, -70.0, extra={"enrich_only": True},
                                           light={**WD_LIGHT, "first_lit": None})])
        self.run_merge()
        self.assertEqual(self.files()["us-me-marblehead"]["status"], "inactive")

    def test_status_from_a_source_with_no_position_only_when_nothing_else_says(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Gone Light", 43.0, -70.0), rec("wikidata", "Q2", "Lit Light", 43.2, -70.2, light=dict(WD_LIGHT))])
        self.write("rowlett", [rec("rowlett", "me:gone", "Gone", None, None, status="lost"), rec("rowlett", "me:lit", "Lit", None, None, status="inactive")])
        self.run_merge()
        f = self.files()
        self.assertEqual(f["us-me-gone"]["status"], "lost")
        self.assertEqual(f["us-me-lit"]["status"], "active")     # Wikidata's characteristic outranks a positionless "inactive"

    def test_deactivation_years_that_disagree_are_a_conflict(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Quiet Light", 43.0, -70.0, status="inactive", light={**WD_LIGHT, "characteristic": None, "deactivated": 1950})])
        self.write("rowlett", [rec("rowlett", "me:q", "Quiet", None, None, status="inactive", light={**WD_LIGHT, "first_lit": None, "characteristic": None, "deactivated": 1982})])
        self.run_merge()
        self.assertIn("light.deactivated", [c["field"] for c in self.files()["us-me-quiet"]["conflicts"]])


class ReplicaAndNamesakeTest(Case):
    def test_a_replica_does_not_join_the_light_it_copies(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Old Plantation Flats Light", 37.2288, -76.0469)])
        self.write("lighthousefriends", [rec("lighthousefriends", "1", "Old Plantation Flats (Replica)", 37.2441, -76.0179, status="replica", region="VA")])
        self.run_merge()
        self.assertEqual(len(self.files()), 2)

    def test_a_unique_namesake_a_few_km_away_joins_but_two_candidates_do_not(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Horn Island Light", 30.224, -88.485, region="MS"),
                                rec("wikidata", "Q2", "Dog Island Light", 29.8, -84.6, region="FL"),
                                rec("wikidata", "Q3", "Dog Island Light", 29.81, -84.64, region="FL")])
        self.write("lighthousefriends", [rec("lighthousefriends", "1", "Horn Island", 30.2197, -88.5528, status="lost", region="MS"),
                                         rec("lighthousefriends", "2", "Dog Island", 29.805, -84.62, status="lost", region="FL")])
        rep = self.run_merge()
        f = self.files()
        self.assertEqual(sum(1 for i in f if i.startswith("us-ms-horn-island")), 1)
        self.assertEqual(sum(1 for i in f if i.startswith("us-fl-dog-island")), 3)   # two Wikidata items, and the record that fits neither alone
        self.assertEqual([j["key"] for j in rep["joins_to_review"]["by_unique_namesake"]], ["lighthousefriends:1"])

    def test_successive_towers_with_one_name_and_different_years_are_two_structures(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Punta Borinquen Light", 18.4972, -67.1488, structure={"type": None, "material": None, "built": 1922, "height_m": None, "status": None}),
                                rec("wikidata", "Q2", "Punta Borinquen Light", 18.4973, -67.1489, structure={"type": None, "material": None, "built": 1889, "height_m": None, "status": None})])
        self.run_merge()
        f = self.files()
        self.assertEqual(len(f), 1)
        self.assertEqual(sorted(s["built"] for s in next(iter(f.values()))["structures"]), [1889, 1922])


class DecisionTest(Case):
    def merge_with(self, **kw):
        merge.set_decisions(decisions(**kw))
        return self.run_merge()

    def two_stations(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Navesink North Light", 40.3963, -73.9857), rec("wikidata", "Q2", "Navesink South Light", 40.3961, -73.9858)])

    def test_pins_and_retired_ids(self):
        self.two_stations()
        merge.set_decisions(merge._NoDecisions())
        self.run_merge()
        self.assertEqual(len(self.files()), 2)
        ids = sorted(self.files())
        self.merge_with(RECORD_JOINS={"wikidata:Q2": ids[0]})
        f = self.files()
        self.assertEqual(sorted(f), ids)                                   # ids never go
        retired = f[ids[1]]
        self.assertEqual((retired["merged_into"], retired["hidden"]), (ids[0], True))
        self.assertEqual(len(f[ids[0]]["structures"]), 2)                  # twin lights: two structures in one station

    def test_a_wrong_position_is_not_used(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Ship Shoal Light", 29.015, -89.167)])
        self.write("lighthousefriends", [rec("lighthousefriends", "816", "Ship Shoal", 28.9145, -91.0711, region="ME")])
        self.merge_with(NO_POSITION={"wikidata:Q1"}, RECORD_JOINS={"lighthousefriends:816": "wikidata:Q1"})
        f = self.files()
        self.assertEqual(len(f), 1)
        loc = next(iter(f.values()))["location"]
        self.assertEqual((loc["lat"], loc["from"]), (28.9145, "lighthousefriends"))

    def test_keep_apart_and_not_duplicates(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Twin Light", 43.0, -70.0)])
        self.write("osm", [rec("osm", "n1", "Twin Light", 43.0, -70.0001, extra={"forms": ["man_made=lighthouse"]})])
        self.merge_with(KEEP_APART_PAIRS={frozenset(("wikidata:Q1", "osm:n1"))})
        self.assertEqual(len(self.files()), 2)

    def test_decisions_on_stations(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Lake Copy Light", 34.5, -114.3), rec("wikidata", "Q2", "Real Light", 43.6, -70.2),
                                rec("wikidata", "Q3", "Reviewed Light", 44.0, -69.0), rec("wikidata", "Q4", "Marina Light", 35.0, -100.0),
                                rec("wikidata", "Q5", "Old Presque Isle", 45.34, -83.47), rec("wikidata", "Q6", "New Presque Isle", 45.36, -83.49)])
        merge.set_decisions(merge._NoDecisions())
        self.run_merge()
        ids = {v["name"]: k for k, v in self.files().items()}
        rep = self.merge_with(
            REPLICA_OF={ids["Lake Copy Light"]: ids["Real Light"]}, STATUS_PICKS={ids["Reviewed Light"]: ("lost", "Settled by hand.")},
            HIDE={ids["Marina Light"]: "decorative"}, NAME_PICKS={ids["Real Light"]: "Real Light (The Real One)"},
            SUCCESSION=[(ids["Old Presque Isle"], ids["New Presque Isle"])])
        f = self.files()
        copy, real = f[ids["Lake Copy Light"]], f[ids["Real Light"]]
        self.assertEqual(copy["status"], "replica")
        self.assertIn(("replica_of", ids["Real Light"]), [(r["relation"], r["id"]) for r in copy["related"]])
        self.assertIn(("replica", ids["Lake Copy Light"]), [(r["relation"], r["id"]) for r in real["related"]])
        self.assertEqual(real["name"], "Real Light (The Real One)")
        self.assertEqual((f[ids["Reviewed Light"]]["status"], f[ids["Reviewed Light"]]["status_note"]), ("lost", "Settled by hand."))
        self.assertTrue(f[ids["Marina Light"]]["hidden"])
        self.assertIn(("succeeded_by", ids["New Presque Isle"]), [(r["relation"], r["id"]) for r in f[ids["Old Presque Isle"]]["related"]])
        self.assertIn(("preceded_by", ids["Old Presque Isle"]), [(r["relation"], r["id"]) for r in f[ids["New Presque Isle"]]["related"]])
        self.assertEqual(rep["related"]["decisions"]["ids_not_found"], [])

    def test_a_pin_to_a_record_of_a_later_source_waits_for_it(self):
        self.write("osm", [rec("osm", "n1", "Bay Creek Lighthouse", 37.2442, -76.0179, extra={"forms": ["man_made=lighthouse"]})])
        self.write("lighthousefriends", [rec("lighthousefriends", "1692", "Old Plantation Flats (Replica)", 37.2441, -76.0179, status="replica", region="VA")])
        self.merge_with(RECORD_JOINS={"osm:n1": "lighthousefriends:1692"})
        f = self.files()
        self.assertEqual(len(f), 1)
        self.assertEqual({s["source"] for s in next(iter(f.values()))["sources"]}, {"osm", "lighthousefriends"})


class RangeTest(Case):
    def test_the_item_for_the_whole_range_is_a_record_of_the_station_not_a_third_structure(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Nantucket Reef Range Front Light", 41.28989, -70.09222, kind="range_lights", role="front_range"),
                                rec("wikidata", "Q2", "Nantucket Range Rear Light", 41.2893, -70.0919, kind="range_lights", role="rear_range"),
                                rec("wikidata", "Q3", "Nantucket Harbor Range Lights", 41.28917, -70.09167, kind="range_lights")])
        self.run_merge()
        ids = {v["name"]: k for k, v in self.files().items()}
        target = ids["Nantucket Reef Range Front Light"]
        merge.set_decisions(decisions(RECORD_JOINS={"wikidata:Q2": target, "wikidata:Q3": target}))
        self.run_merge()
        live = [f for f in self.files().values() if not f.get("merged_into")]
        self.assertEqual(len(live), 1)
        self.assertEqual(sorted(s["role"] for s in live[0]["structures"]), ["front_range", "rear_range"])


if __name__ == "__main__":
    unittest.main()
