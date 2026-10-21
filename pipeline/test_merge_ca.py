"""Tests for pipeline/merge_ca.py through merge.run() on small synthetic Canadian extracts:
identifier joins, position-less records, the Coast Guard list's small aids, staffing and access,
Lighthouse Friends' flags, curation (rekind, join, apart, hide, merge_stations) and precedence."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge  # noqa: E402
import merge_ca  # noqa: E402
from test_merge import MergeCase, rec  # noqa: E402

LIGHT = {"first_lit": None, "deactivated": None, "characteristic": None, "focal_height_m": None, "range_nm": None,
         "fog_signal": None, "lens": None}


def ca(source: str, key: str, name: str | None, lat: float | None, lon: float | None, **kw) -> dict:
    kw.setdefault("country", "CA")
    kw.setdefault("region", "NS")
    aton = kw.pop("aton", None)
    r = rec(source, key, name, lat if lat is not None else 0.0, lon if lon is not None else 0.0, **kw)
    if lat is None:
        r["lat"] = r["lon"] = None
    if aton:
        r["aton"] = {"uscg_llnr": None, "arlhs": None, "ccg_list_number": None, "nga": None, **aton}
    return r


class IdentifierTest(unittest.TestCase):
    def test_normalisation(self):
        self.assertEqual(merge_ca.norm_ccg("A-0456"), "A456")
        self.assertEqual(merge_ca.norm_ccg("N1"), "N1")
        self.assertIsNone(merge_ca.norm_ccg("1600"))                      # no volume letter: no key
        self.assertEqual(merge_ca.norm_adm("H 0443.4"), "H443.4")
        self.assertEqual(merge_ca.norm_arlhs("CAN-055"), "CAN55")

    def test_keys_from_wikidata_style_records(self):
        raw = ca("wikidata", "Q1", "X", 44.0, -64.0, aton={"arlhs": "CAN055", "ccg_list_number": "A247"},
                 registers=[{"register": "Heritage Lighthouse (Canada)", "number": "14935", "url": None}])
        self.assertEqual(sorted(merge_ca.identifiers(raw)), ["arlhs:CAN55", "ccg:A247", "hl:14935"])

    def test_us_records_have_none(self):
        self.assertEqual(merge_ca.identifiers(rec("wikidata", "Q1", "X", 40.0, -70.0)), [])


class JoinTest(MergeCase):
    def test_positionless_record_joins_by_identifier(self):
        self.write("wikidata", [ca("wikidata", "Q1", "Port Maitland Light", 43.986, -66.162, aton={"arlhs": "CAN1211"})])
        row = ca("rowlett", "ns:port-maitland", "Port Maitland", None, None, aton={"arlhs": "CAN1211", "ccg_list_number": "A247"},
                 extra={"station_level": True, "join_keys": ["arlhs:CAN1211", "ccg:A247", "adm:H3840"]},
                 events=[{"year": 1884, "event": "first_lit", "note": None, "from": "rowlett"}])
        row["aton"]["admiralty"] = "H3840"
        self.write("rowlett", [row])
        report = self.run_merge()
        files = self.station_files()
        self.assertEqual(len(files), 1)
        st = next(iter(files.values()))
        self.assertEqual(st["aton"]["admiralty"], "H3840")
        self.assertEqual(st["aton"]["ccg_list_number"], "A247")
        self.assertIn({"year": 1884, "event": "first_lit", "note": None, "from": "rowlett"}, st["events"])
        self.assertEqual(len(st["structures"]), 1)                       # a station-level record adds no structure
        self.assertEqual(report["_run"]["canada"]["joined_by"]["identifier"], 1)

    def test_unjoined_positionless_record_is_listed_not_started(self):
        self.write("rowlett", [ca("rowlett", "ns:lost-light", "Lost Light", None, None, extra={"station_level": True})])
        self.run_merge()
        self.assertEqual(self.station_files(), {})
        report = json.loads((self.tmp / "report.json").read_text())
        self.assertIn("no position", report["not_shown"][0]["reason"])

    def test_unique_name_joins_a_positionless_record_and_two_do_not(self):
        self.write("osm", [ca("osm", "node/1", "Cape Sharp Lighthouse", 45.36, -64.39, extra={"forms": ["man_made=lighthouse"]}),
                           ca("osm", "node/2", "Green Island Lighthouse", 45.0, -63.0, extra={"forms": ["man_made=lighthouse"]}),
                           ca("osm", "node/3", "Green Island Light", 45.5, -62.0, extra={"forms": ["man_made=lighthouse"]})])
        self.write("rowlett", [ca("rowlett", "ns:cape-sharp", "Cape Sharp", None, None, extra={"station_level": True}, events=[{"year": 1900, "event": "built", "note": None, "from": "rowlett"}]),
                               ca("rowlett", "ns:green-island", "Green Island", None, None, extra={"station_level": True})])
        report = self.run_merge()
        self.assertEqual([j["name"] for j in report["_run"]["canada"]["joined_by_name_only"]], ["Cape Sharp"])
        self.assertEqual([u["name"] for u in report["not_shown"]], ["Green Island"])   # two stations of that name: ambiguous

    def test_identifier_far_away_does_not_join(self):
        self.write("wikidata", [ca("wikidata", "Q1", "Sisters Islets Light", 49.0, -124.0, aton={"ccg_list_number": "P493"})])
        self.write("ccg_list_of_lights", [ca("ccg_list_of_lights", "P493", "Sisters Islets", 49.1, -124.0, aton={"ccg_list_number": "P493"},
                                              extra={"clear_lighthouse": False, "join_keys": ["ccg:P493"]})])
        report = self.run_merge()
        self.assertEqual(report["_run"]["canada"]["identifier_far"][0]["key"], "ccg_list_of_lights:P493")


class CoastGuardListTest(MergeCase):
    def test_small_aid_alone_is_not_a_station_but_a_clear_lighthouse_is(self):
        self.write("ccg_list_of_lights", [
            ca("ccg_list_of_lights", "A1", "Parrsboro Wharf", 45.39, -64.31, extra={"clear_lighthouse": False}, kind="pier_light"),
            ca("ccg_list_of_lights", "N1", "Cape Race Light Station", 46.65, -53.07, extra={"clear_lighthouse": True}, region="NL")])
        self.run_merge()
        self.assertEqual(list(self.station_files()), ["ca-nl-cape-race"])
        report = json.loads((self.tmp / "report.json").read_text())
        self.assertEqual(len(report["not_shown"]), 1)
        self.assertIn("Coast Guard", report["not_shown"][0]["reason"])

    def test_charted_light_comes_from_the_list_over_osm_and_wikidata(self):
        light = dict(LIGHT, characteristic="Fl W 4s", focal_height_m=20.0)
        self.write("wikidata", [ca("wikidata", "Q1", "Cape Sharp Lighthouse", 45.36, -64.39, light=dict(LIGHT, characteristic="Fl W 5s"))])
        self.write("osm", [ca("osm", "node/1", "Cape Sharp Lighthouse", 45.3601, -64.3901, extra={"forms": ["man_made=lighthouse"], "wikidata": "Q1"},
                              status="active", light=dict(LIGHT, characteristic="Fl W 6s"))])
        self.write("ccg_list_of_lights", [ca("ccg_list_of_lights", "A171", "Cape Sharp", 45.3601, -64.3901, light=light, status="active",
                                              extra={"clear_lighthouse": False, "join_keys": ["ccg:A171"]}, aton={"ccg_list_number": "A171"})])
        self.run_merge()
        st = self.station_files()["ca-ns-cape-sharp"]
        self.assertEqual((st["light"]["characteristic"], st["light"]["focal_height_m"], st["light"]["from"]), ("Fl W 4s", 20.0, "ccg_list_of_lights"))
        self.assertEqual(st["aton"]["ccg_list_number"], "A171")

    def test_lost_structure_with_a_list_entry_gets_a_note(self):
        self.write("lighthousefriends", [ca("lighthousefriends", "99", "Betty Island", 45.0, -61.0, status="lost")])
        self.write("ccg_list_of_lights", [ca("ccg_list_of_lights", "A5", "Betty Island", 45.0001, -61.0, status="active",
                                              aton={"ccg_list_number": "A5"}, extra={"clear_lighthouse": True})])
        self.run_merge()
        st = self.station_files()["ca-ns-betty-island"]
        self.assertEqual(st["status"], "lost")
        self.assertIn("List of Lights still shows a light here", st["status_note"])


class StaffingAndAccessTest(MergeCase):
    def setUp(self):
        super().setUp()
        self.write("wikidata", [ca("wikidata", "Q1", "Cape Race Lighthouse", 46.658, -53.073, region="NL", aton={"ccg_list_number": "N1"}),
                                ca("wikidata", "Q2", "Carmanah Point Light", 48.611, -124.751, region="BC", aton={"ccg_list_number": "P180"})])
        note = "Staffed lightstation: the keepers' home and workplace. Visit only where the station welcomes visitors, and never land uninvited."
        ev = [{"label": "L", "url": "https://x", "date": "2010-04"}]
        self.staffed = [
            ca("ca_staffed_lightstations", "nl-cape-race", "Cape Race", 46.6586, -53.0736, region="NL",
               extra={"station_level": True, "join_keys": ["ccg:N1"], "staffing": {"status": "staffed", "as_of": "2010"},
                      "access": {"level": "restricted", "note": note}, "evidence": ev, "basis": "b", "check": True}),
            ca("ca_staffed_lightstations", "bc-carmanah", "Carmanah Point", 48.6118, -124.7513, region="BC",
               extra={"station_level": True, "join_keys": ["ccg:P180"], "staffing": {"status": "automated", "as_of": "2024"},
                      "access": {"level": "restricted", "note": "ended"}, "evidence": ev, "basis": "b", "check": False})]
        self.write("ca_staffed_lightstations", self.staffed)

    def test_staffing_access_and_flag(self):
        self.run_merge()
        files = self.station_files()
        race = files["ca-nl-cape-race"]
        self.assertEqual(race["staffing"]["status"], "staffed")
        self.assertEqual(race["staffing"]["as_of"], "2010")
        self.assertTrue(race["staffing"]["check"])
        self.assertEqual(race["access"]["level"], "restricted")
        self.assertTrue(race["access"]["note"].startswith("Staffed lightstation: the keepers' home and workplace."))
        carmanah = files["ca-bc-carmanah-point"]
        self.assertEqual(carmanah["staffing"]["status"], "automated")
        report = json.loads((self.tmp / "report.json").read_text())["canada"]["staffed"]
        self.assertEqual(report["staffed_stations"], 1)
        self.assertEqual(report["rest_only_on_the_2010_list"], ["ca-nl-cape-race"])
        self.assertEqual(report["destaffed_2024"], ["ca-bc-carmanah-point"])
        self.assertEqual(report["not_joined_to_a_station"], [])

    def test_staffed_record_without_a_station_is_listed(self):
        (self.sources / "wikidata.json").unlink()
        self.run_merge()
        # the curated record has a position and a name, so it starts a station of its own
        self.assertEqual(sorted(self.station_files()), ["ca-bc-carmanah-point", "ca-nl-cape-race"])


class FlagsTest(MergeCase):
    def test_lighthouse_friends_flags_and_directory_wording(self):
        self.write("lighthousefriends", [ca("lighthousefriends", "1", "Seal Island", 43.4, -66.0, extra={"flags": ["boat", "private", "lodging"]}),
                                         ca("lighthousefriends", "2", "Cape d'Or", 45.29, -64.77, extra={"flags": ["climb", "interior_open"]}),
                                         ca("lighthousefriends", "3", "Quiet Point", 45.0, -63.0, extra={"flags": []})])
        self.write("rowlett", [ca("rowlett", "ns:seal", "Seal Island", None, None, extra={"station_level": True, "access": {"boat_only": True, "site": "closed", "tower": "closed"}}),
                               ca("rowlett", "ns:d-or", "Cape d'Or", None, None, extra={"station_level": True, "access": {"site": "open", "tower": "open"}}),
                               ca("rowlett", "ns:quiet", "Quiet Point", None, None, extra={"station_level": True, "access": {"site": "closed", "tower": "closed"}})])
        self.run_merge()
        files = self.station_files()
        seal, dor, quiet = files["ca-ns-seal-island"], files["ca-ns-cape-dor"], files["ca-ns-quiet-point"]
        self.assertTrue(seal["visit"]["boat_only"])
        self.assertEqual(seal["access"]["level"], "private")
        self.assertEqual(seal["stay"]["type"], "inn")
        self.assertTrue(dor["visit"]["climbable"])
        self.assertEqual(dor["access"]["level"], "public")
        self.assertEqual(quiet["access"]["level"], "closed")
        self.assertFalse(quiet["visit"]["grounds_open"])
        self.assertIsNone(quiet["visit"]["boat_only"])                  # unknown stays unknown


class HeritageTest(MergeCase):
    def test_a_designated_lighthouse_stands(self):
        wd = ca("wikidata", "Q1", "Fisgard Lighthouse", 48.431, -123.447, region="BC", status=None, extra={"possibly_lost": True, "p576": 1950},
                light=dict(LIGHT, deactivated=1950, characteristic=None))
        self.write("wikidata", [wd])
        self.write("parks_canada_hl", [ca("parks_canada_hl", "14432", "Fisgard Lighthouse", 48.43098, -123.44703, region="BC",
                                          extra={"standing": True, "join_keys": ["hl:14432"]},
                                          registers=[{"register": "Heritage Lighthouse (Canada)", "number": "14432", "url": "u"}])])
        self.run_merge()
        st = self.station_files()["ca-bc-fisgard"]
        self.assertEqual(st["status"], "inactive")                  # not "unknown, may be gone": a designated heritage lighthouse stands
        self.assertEqual(st["structures"][0]["status"], "standing")


class RangeHalfTest(MergeCase):
    def test_a_second_source_rear_joins_the_station_that_has_the_front(self):
        self.write("wikidata", [ca("wikidata", "Q1", "Saugeen River Front Range Lighthouse", 44.5015, -81.3753, region="ON", kind="range_lights", role="front_range"),
                                ca("wikidata", "Q2", "Saugeen River Rear Range Lighthouse", 44.5009, -81.3662, region="ON", kind="range_lights", role="rear_range")])
        self.write("lighthousefriends", [ca("lighthousefriends", "1052", "Saugeen River Range Front", 44.5015, -81.3755, region="ON", kind="range_lights", role="front_range"),
                                         ca("lighthousefriends", "1053", "Saugeen River Range Rear", 44.50094, -81.36646, region="ON", kind="range_lights", role="rear_range")])
        self.run_merge()
        files = self.station_files()
        self.assertEqual(len(files), 1)
        self.assertEqual([s["role"] for s in next(iter(files.values()))["structures"]], ["front_range", "rear_range"])


class NameTest(unittest.TestCase):
    def test_possessive_is_not_south(self):
        a = merge.name_forms("St. Shott's Lightstation")
        b = merge.name_forms("St. Shotts")
        self.assertEqual(merge.name_score(a, b), 1.0)
        self.assertEqual(merge.name_tokens("Devil's Island"), ["devils", "island"])
        self.assertEqual(merge.name_tokens("S. Point"), ["south", "point"])          # a real abbreviation still expands
        self.assertEqual(merge.name_tokens("Île de l'Ouest"), ["ile", "de", "l", "ouest"])


class PrecedenceTest(unittest.TestCase):
    def test_register_places_sources_around_osm(self):
        prec = {"charted": ["noaa", "osm", "wikidata"], "name": ["wikidata", "osm"], "location": ["osm", "wikidata"]}
        merge_ca.register(prec)
        self.assertEqual(prec["charted"], ["noaa", "ccg_list_of_lights", "osm", "wikidata"])
        self.assertEqual(prec["name"][:2], ["wikidata", "osm"])
        self.assertEqual(prec["location"][:3], ["osm", "ccg_list_of_lights", "parks_canada_hl"])
        merge_ca.register(prec)  # idempotent
        self.assertEqual(prec["charted"].count("ccg_list_of_lights"), 1)

    def test_merge_registered_its_sources(self):
        self.assertEqual(merge.PRECEDENCE["charted"][0], "ccg_list_of_lights")
        for field in ("name", "location", "kind", "structure", "region", "other"):
            self.assertIn("parks_canada_hl", merge.PRECEDENCE[field], field)


class CurationTest(MergeCase):
    def curation(self, data: dict) -> None:
        (self.tmp / "curation_ca.json").write_text(json.dumps(data))

    def test_every_entry_needs_a_reason(self):
        self.curation({"hide": [{"id": "ca-ns-x"}]})
        with self.assertRaises(SystemExit):
            self.run_merge()

    def test_hide_by_id_and_by_key(self):
        self.write("osm", [ca("osm", "node/1", "Clearwater Park Lighthouse", 51.05, -113.8, region="AB", extra={"forms": ["man_made=lighthouse"]}),
                           ca("osm", "node/2", "Lighthouse Landing", 51.16, -114.06, region="AB", extra={"forms": ["man_made=lighthouse"]})])
        self.curation({"hide": [{"id": "ca-ab-clearwater-park", "reason": "private ornament"}, {"key": "osm:node/2", "reason": "a condo community"}]})
        self.run_merge()
        files = self.station_files()
        self.assertTrue(all(f["hidden"] for f in files.values()))
        self.assertEqual({f["hidden_reason"] for f in files.values()}, {"private ornament", "a condo community"})

    def test_rekind(self):
        self.write("lighthousefriends", [ca("lighthousefriends", "2354", "Lower Traverse", 47.36, -70.25, region="QC")])
        self.write("ca_lightships_lifesaving", [ca("ca_lightships_lifesaving", "lower-traverse", "Lower Traverse", 47.36, -70.25, region="QC", kind="lightship_station")])
        self.curation({"rekind": [{"key": "lighthousefriends:2354", "kind": "lightship_station", "reason": "the page is about the vessel"}]})
        self.run_merge()
        files = self.station_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(next(iter(files.values()))["kind"], "lightship_station")

    def test_join_and_apart(self):
        self.write("lighthousefriends", [ca("lighthousefriends", "1", "Medway Head", 44.1024, -64.5394, region="NS"),
                                         ca("lighthousefriends", "2", "Medway Head (1927)", 44.1029, -64.5398, region="NS")])
        self.run_merge()
        self.assertEqual(len(self.station_files()), 2)            # two LHF entries of one source: not joined by name alone
        shutil_dir = self.tmp / "second"
        self.curation({"join": [{"keys": ["lighthousefriends:1", "lighthousefriends:2"], "reason": "successive towers"}]})
        merge.run(self.sources, shutil_dir, self.tmp / "r2.json", "2026-10-21")
        self.assertEqual(len(self.station_files(shutil_dir)), 1)
        self.curation({"apart": [{"keys": ["lighthousefriends:1", "lighthousefriends:2"], "reason": "different lights"}]})
        merge.run(self.sources, self.tmp / "third", self.tmp / "r3.json", "2026-10-21")
        self.assertEqual(len(self.station_files(self.tmp / "third")), 2)

    def test_detach_moves_a_record_out_of_the_station_an_earlier_run_filed_it_under(self):
        self.write("wikidata", [ca("wikidata", "Q1", "Flower's Cove Lighthouse", 48.457, -58.489, region="NL", aton={"arlhs": "CAN657"})])
        self.write("lighthousefriends", [ca("lighthousefriends", "1256", "Harbour Point", 48.4573, -58.4888, region="NL"),
                                         ca("lighthousefriends", "1278", "Flowers Cove", 51.308, -56.749, region="NL")])
        self.run_merge()
        first = self.station_files()
        self.assertEqual(sorted(first), ["ca-nl-flowers-cove", "ca-nl-flowers-cove-2"])
        holder = next(i for i, f in first.items() if any(s["key"] == "wikidata:Q1" for s in f["sources"]))
        self.assertEqual(holder, "ca-nl-flowers-cove")                     # filed by position: with Harbour Point
        self.curation({"detach": [{"key": "wikidata:Q1", "from_station": "ca-nl-flowers-cove", "reason": "its identifiers say Flowers Cove"}],
                       "join": [{"keys": ["wikidata:Q1", "lighthousefriends:1278"], "reason": "the same light"}]})
        for _ in range(2):                                                  # and it stays moved on the next run
            self.run_merge()
            files = self.station_files()
            self.assertEqual([s["key"] for s in files["ca-nl-flowers-cove"]["sources"]], ["lighthousefriends:1256"])
            self.assertEqual(sorted(s["key"] for s in files["ca-nl-flowers-cove-2"]["sources"]), ["lighthousefriends:1278", "wikidata:Q1"])

    def test_merge_stations_retires_one_id_and_keeps_both_files(self):
        self.write("wikidata", [ca("wikidata", "Q1", "Richibucto Head Lighthouse", 46.6698, -64.7116, region="NB"),
                                ca("wikidata", "Q2", "Cap-Lumière lighthouse", 46.6720, -64.7117, region="NB")])
        self.run_merge()
        self.assertEqual(len(self.station_files()), 2)
        self.curation({"merge_stations": [{"keep": "ca-nb-richibucto-head", "retire": "ca-nb-cap-lumiere", "reason": "the same light"}]})
        self.run_merge()
        files = self.station_files()
        self.assertEqual(sorted(files), ["ca-nb-cap-lumiere", "ca-nb-richibucto-head"])    # never deleted
        self.assertEqual(files["ca-nb-cap-lumiere"]["merged_into"], "ca-nb-richibucto-head")
        self.assertEqual(len(files["ca-nb-richibucto-head"]["structures"]), 2)
        self.assertNotIn("merged_into", files["ca-nb-richibucto-head"])


if __name__ == "__main__":
    unittest.main()
