"""Tests for how the merge treats the lightship_stations source (DESIGN 2.5, 3.5): its positions lead for a lightship station,
a computed position says so and carries the words it was worked from, a record with no position joins a station of its name (or
waits, unshown), and the Light Lists' name for a station beats the Society's. Synthetic extracts only; the real pins are checked."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge  # noqa: E402
import record_joins  # noqa: E402
from test_merge_us import Case, decisions, rec  # noqa: E402

NOTE = "Computed: 0.9 nautical miles from Monomoy Point Light-House, true bearing 153 degrees as printed. Source text: “0.9 mile 153° from Monomoy Point”"


def ship(key, name, lat, lon, **kw):
    extra = kw.pop("extra", {})
    return rec("lightship_stations", key, name, lat, lon, kind="lightship_station", precision="approximate", region=kw.pop("region", "MA"), extra=extra, **kw)


class PositionTest(Case):
    def test_a_stated_position_is_the_lists_and_keeps_its_note(self):
        note = "Position printed in the Light List 1900, page 42, entry 143: Pollock Rip Light-Vessel, No. 47, 41 32 17 N, 69 54 36 W"
        self.write("lightship_stations", [ship("pollock-rip", "Pollock Rip", 41.53806, -69.91, extra={"position_from": "light_list", "position_note": note})])
        self.run_merge()
        (st,) = self.files().values()
        self.assertEqual(st["kind"], "lightship_station")
        self.assertEqual((st["location"]["from"], st["location"]["precision"]), ("lightship_stations", "approximate"))
        self.assertEqual(st["location"]["note"], note)

    def test_a_computed_position_says_it_was_computed_and_gives_the_source_text(self):
        self.write("lightship_stations", [ship("stonehorse-shoal", "Stonehorse Shoal", 41.54557, -69.98456, extra={"position_from": "computed", "position_note": NOTE})])
        self.run_merge()
        (st,) = self.files().values()
        self.assertEqual((st["location"]["from"], st["location"]["precision"]), ("computed", "approximate"))
        self.assertIn("0.9 mile 153° from Monomoy Point", st["location"]["note"])

    def test_the_lists_position_leads_wikidatas(self):
        # a lightship station Wikidata puts 38 km from where the Light List prints it: pinned together, the Light List's point leads
        self.write("wikidata", [rec("wikidata", "Q1", "Five Fathom Bank light station", 38.8354, -75.0119, kind="lightship_station", region="NJ")])
        self.write("lightship_stations", [ship("five-fathom-bank", "Five Fathom Bank", 38.78889, -74.57667, region="NJ")])
        merge.set_decisions(decisions(RECORD_JOINS={"lightship_stations:five-fathom-bank": "wikidata:Q1"}))
        self.run_merge()
        (st,) = self.files().values()
        self.assertEqual(st["location"]["from"], "lightship_stations")
        self.assertAlmostEqual(st["location"]["lat"], 38.78889, places=4)
        self.assertEqual({s["source"] for s in st["sources"]}, {"wikidata", "lightship_stations"})      # one station, both records

    def test_a_wrong_wikidata_point_set_aside_still_leaves_one_station_at_the_lists_point(self):
        self.write("wikidata", [rec("wikidata", "Q1", "Five Fathom Bank light station", 38.8354, -75.0119, kind="lightship_station", region="NJ")])
        self.write("lightship_stations", [ship("five-fathom-bank", "Five Fathom Bank", 38.78889, -74.57667, region="NJ")])
        merge.set_decisions(decisions(RECORD_JOINS={"lightship_stations:five-fathom-bank": "wikidata:Q1"}, NO_POSITION={"wikidata:Q1"}))
        self.run_merge()
        (st,) = self.files().values()
        self.assertEqual(st["location"]["from"], "lightship_stations")
        self.assertEqual(len(self.files()), 1)


class NameAndJoinTest(Case):
    def test_the_light_lists_name_beats_the_societys(self):
        self.write("uslhs", [rec("uslhs", "9140", "Wreck of Scotland", None, None, kind="lightship_station", region="NJ")])
        self.write("lightship_stations", [ship("wreck-scotland", "Scotland", 40.44667, -73.92139, region="NJ", other_names=["Wreck of Scotland"])])
        self.run_merge()
        (st,) = self.files().values()
        self.assertEqual(st["name"], "Scotland")
        self.assertIn("Wreck of Scotland", st["other_names"])
        self.assertEqual(st["id"], "us-nj-scotland")

    def test_a_record_with_no_position_joins_the_station_of_its_name_and_does_not_start_one(self):
        self.write("lightship_stations", [ship("pollock-rip", "Pollock Rip", 41.53806, -69.91),
                                          ship("hedge-fence", "Hedge Fence", None, None, extra={"unplaced_reason": "no position"})])
        self.write("uslhs", [rec("uslhs", "1", "Pollock Rip", None, None, kind="lightship_station", region="MA")])
        self.run_merge()
        files = self.files()
        self.assertEqual(list(files), ["us-ma-pollock-rip"])                       # Hedge Fence has no position: no station, listed as unplaced instead
        keys = {s["key"] for s in files["us-ma-pollock-rip"]["sources"]}
        self.assertEqual(keys, {"lightship_stations:pollock-rip", "uslhs:1"})


class SwiftsureTest(Case):
    """The surviving lightship Swiftsure (LV-83) was two stations: Wikidata's item (NRHP 75001852) put her 11.0 km from the register's own point
    and Lighthouse Friends', which agree with each other to 30 m at Lake Union. The hard-key join reaches 10 km, so a pin joins them and
    sets Wikidata's point aside; the station that loses its records is retired, never deleted."""

    REG = [{"register": "NRHP", "number": "75001852", "url": "https://npgallery.nps.gov/AssetDetail/NRIS/75001852"}]

    def write_all(self):
        self.write("wikidata", [rec("wikidata", "Q7656131", "Swiftsure", 47.6749, -122.207, kind="lightship", region="WA", registers=self.REG)])
        self.write("lighthousefriends", [rec("lighthousefriends", "185", "Swiftsure", 47.62806, -122.33703, kind="lightship", region="WA", other_names=["Lightship Swiftsure LV 83/WAL 508"])])
        self.write("nrhp", [rec("nrhp", "75001852", "RELIEF (lightship)", 47.628175, -122.336713, kind="lightship", region="WA", precision="approximate",
                                registers=[{**self.REG[0], "listed": "1975-04-23", "nhl": "1989-04-11", "nomination": "n"}])])

    def test_without_the_pin_the_matcher_leaves_two_stations(self):
        self.write_all()
        merge.set_decisions(merge._NoDecisions())
        self.run_merge()
        self.assertEqual(len(self.files()), 2)                      # the gap the pin closes: 11 km is past the hard-key radius

    def test_with_the_pin_there_is_one_station_at_the_registers_point_and_the_other_id_is_kept_and_retired(self):
        self.write_all()
        merge.set_decisions(merge._NoDecisions())
        self.run_merge()
        ids = sorted(self.files())
        keep = next(i for i in ids if any(s["key"] == "wikidata:Q7656131" for s in self.files()[i]["sources"]))
        gone = next(i for i in ids if i != keep)
        merge.set_decisions(decisions(RECORD_JOINS={"lighthousefriends:185": keep, "nrhp:75001852": keep}, NO_POSITION={"wikidata:Q7656131"}))
        self.run_merge()
        files = self.files()
        self.assertEqual(sorted(files), ids)                          # ids never go
        self.assertEqual((files[gone]["merged_into"], files[gone]["hidden"]), (keep, True))
        station = files[keep]
        self.assertEqual({s["key"] for s in station["sources"]}, {"wikidata:Q7656131", "lighthousefriends:185", "nrhp:75001852"})
        self.assertAlmostEqual(station["location"]["lat"], 47.62806, places=4)         # Lake Union, not Wikidata's 47.6749
        self.assertEqual(station["location"]["from"], "lighthousefriends")


class RealDecisionsTest(unittest.TestCase):
    def test_five_fathom_bank_is_pinned_to_the_wikidata_item_and_its_point_set_aside(self):
        self.assertEqual(record_joins.RECORD_JOINS["lightship_stations:five-fathom-bank"], "us-nj-five-fathom-bank")
        self.assertIn("wikidata:Q18150126", record_joins.NO_POSITION)
        self.assertEqual(record_joins.NAME_PICKS["us-nj-five-fathom-bank"], "Five Fathom Bank")

    def test_the_two_swiftsure_stations_are_one(self):
        self.assertEqual(record_joins.RECORD_JOINS["lighthousefriends:185"], "us-wa-swiftsure")
        self.assertEqual(record_joins.RECORD_JOINS["nrhp:75001852"], "us-wa-swiftsure")
        self.assertIn("wikidata:Q7656131", record_joins.NO_POSITION)

    def test_the_lightship_source_leads_for_position_and_name(self):
        self.assertEqual(merge.PRECEDENCE["location"][0], "lightship_stations")
        names = merge.PRECEDENCE["name"]
        self.assertLess(names.index("lightship_stations"), names.index("uslhs"))


if __name__ == "__main__":
    unittest.main()
