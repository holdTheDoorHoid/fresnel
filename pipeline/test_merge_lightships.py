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


class RealDecisionsTest(unittest.TestCase):
    def test_five_fathom_bank_is_pinned_to_the_wikidata_item_and_its_point_set_aside(self):
        self.assertEqual(record_joins.RECORD_JOINS["lightship_stations:five-fathom-bank"], "us-nj-five-fathom-bank")
        self.assertIn("wikidata:Q18150126", record_joins.NO_POSITION)
        self.assertEqual(record_joins.NAME_PICKS["us-nj-five-fathom-bank"], "Five Fathom Bank")

    def test_the_lightship_source_leads_for_position_and_name(self):
        self.assertEqual(merge.PRECEDENCE["location"][0], "lightship_stations")
        names = merge.PRECEDENCE["name"]
        self.assertLess(names.index("lightship_stations"), names.index("uslhs"))


if __name__ == "__main__":
    unittest.main()
