"""Tests for pipeline/fetch_lss_reports.py: reading a report, putting the years together, the checks on a position,
and the record it writes. The OCR snippets are shortened copies of the 1909 report."""
from __future__ import annotations

import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import fetch_lss_reports as F  # noqa: E402


def two_spaces(text: str) -> str:
    return "\n".join(ln.replace(" ", "  ") + " " for ln in text.split("\n"))


REPORT = two_spaces("""Classification of Districts and Stations.
First, district (coasts of Maine and New Hampshire) . 3
Second district (coast of Massachusetts) . 3
LIFE-SAVING DISTRICTS AND STATIONS IN THE UNITED STATES
FIRST DISTRICT.
COASTS OF MAINE AND NEW HAMPSHIRE.
Name of station.
State.
Locality.
Approximate
position.
Lati-
tude,
north.
Longi-
tude,
west.
Quoddy Head .
Maine .
Carrying Point Cove ....
44 48 40
66 58 50
Cross Island .
. do .
Off Machiasport .
44 36 45
67 16 30
Wallis Sands .
New Hampshire .
2 miles south of Odiornes Point .
43 01 15
70 44 00
SECOND DISTRICT.
COAST OF MASSACHUSETTS.
Plum Island .
Massachusetts .
North end of Plum Island .
42 48 30
70 49 00
Nahant b .
. do .
On the neck .
42 25 45
70 56 00
Bolinas Bay .
. do .
Floating .
INSTRUCTIONS TO MARINERS IN CASE OF SHIPWRECK
""")


def reading(name, state, lat, lon, year, volume, *, district=1, pos=0, clean=True, footnote=None):
    return {"district": district, "pos": pos, "name": name, "mark": None, "state": state, "locality": None, "lat": lat, "lon": lon,
            "clean": clean and lat is not None, "problem": None, "state_inferred": False, "footnote": footnote, "year": year, "volume": volume}


class StubLookup:
    """A state lookup with boxes instead of boundary files: ME above 43.0 N and east of 71 W; MA the rest to 41 N."""
    def lookup(self, lat, lon, country=None):
        if lat >= 43.0 and lon > -71.0:
            return "ME", "inside", 0.0
        if 41.0 <= lat < 43.0 and -73.0 < lon < -69.5:
            return "MA", "inside", 0.0
        return None, "none_near", None

    def _hits(self, lat, lon, country=None):
        r = self.lookup(lat, lon)[0]
        return [r] if r else []


class ReadVolumeTest(unittest.TestCase):
    def test_a_report_is_read_into_rows_district_by_district(self):
        """The shortened 1909 report: two districts, a footnote mark on a name, a station with no position."""
        rows = F.read_volume(REPORT.split("\n"))
        names = [(r["district"], r["name"], r["state"]) for r in rows]
        self.assertEqual(names, [(1, "Quoddy Head", "ME"), (1, "Cross Island", "ME"), (1, "Wallis Sands", "NH"),
                                 (2, "Plum Island", "MA"), (2, "Nahant", "MA"), (2, "Bolinas Bay", "MA")])
        self.assertEqual([r["clean"] for r in rows], [True, True, True, True, True, False])
        self.assertEqual(rows[4]["mark"], "b")                       # the footnote mark came off the name

    def test_the_districts_own_count_of_stations(self):
        counts = F.expected_counts(REPORT.split("\n"))
        self.assertEqual(counts, {1: 3, 2: 3})

    def test_list_positions_only_where_the_district_was_read_whole(self):
        rows = F.read_volume(REPORT.split("\n"))
        for r in rows:
            r.update(year=1909, volume="x")
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "corpus").mkdir()
            (Path(d) / "corpus" / "x.txt").write_text(REPORT, encoding="utf-8")
            with mock.patch.object(c, "RAW_ROOT", Path(d)):
                ranks = F.list_ranks(rows, {"identifier": "x", "path": "x.txt"})
        by_name = {r["name"]: ranks.get(id(r)) for r in rows}
        self.assertEqual(by_name["Quoddy Head"], (1, 3))
        self.assertEqual(by_name["Wallis Sands"], (3, 3))
        self.assertEqual(by_name["Nahant"], (2, 3))
        self.assertEqual(len(ranks), 6)
        # a district read with a row too many or too few gets no positions at all
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "corpus").mkdir()
            (Path(d) / "corpus" / "x.txt").write_text(REPORT.replace("Second  district  (coast  of  Massachusetts)  .  3", "Second  district  (coast  of  Massachusetts)  .  4"), encoding="utf-8")
            with mock.patch.object(c, "RAW_ROOT", Path(d)):
                ranks = F.list_ranks(rows, {"identifier": "x", "path": "x.txt"})
        self.assertEqual(sorted(by_name_ for by_name_ in {r["district"] for r in rows if id(r) in ranks}), [1])


class ClusterTest(unittest.TestCase):
    def test_a_renamed_station_stays_one_station_and_a_reused_name_is_two(self):
        rs = [reading("Plum Island", "MA", 42.8083, -70.8167, y, f"v{y}") for y in (1890, 1895, 1900)]
        rs += [reading("Newburyport", "MA", 42.8083, -70.8167, y, f"v{y}") for y in (1903, 1909)]
        rs += [reading("Knobbs Beach", "MA", 42.7333, -70.7875, y, f"v{y}") for y in (1895, 1900)]
        rs += [reading("Plum Island", "MA", 42.7333, -70.7875, y, f"v{y}") for y in (1903, 1909)]
        cl = F.position_clusters(rs)
        self.assertEqual(len(cl), 2)
        old, new = sorted(cl, key=lambda c_: -c_["lat"])
        self.assertEqual([n["name"] for n in F.name_votes(old["members"])], ["Newburyport", "Plum Island"])
        self.assertEqual([n["name"] for n in F.name_votes(new["members"])], ["Plum Island", "Knobbs Beach"])

    def test_positions_a_few_seconds_apart_are_one_position_and_the_newest_report_wins(self):
        rs = [reading("Coskata", "MA", 41.3667, -70.0222, 1895, "a"), reading("Coskata", "MA", 41.3667, -70.0208, 1909, "b")]
        (cl,) = F.position_clusters(rs)
        self.assertEqual((cl["lon"], cl["n_readings"]), (-70.0208, 2))

    def test_an_ocr_slip_of_a_degree_is_a_cluster_of_its_own(self):
        rs = [reading("Gloucester", "MA", 42.5917, -70.6861, 1909, "d"), reading("Gloucester", "MA", 43.5917, -70.6861, 1902, "a"),
              reading("Gloucester", "MA", 43.5917, -70.6861, 1903, "b")]
        cl = F.position_clusters(rs)
        self.assertEqual(sorted(c_["n_readings"] for c_ in cl), [1, 2])

    def test_a_row_whose_name_is_really_a_locality_is_not_a_reading(self):
        rs = [reading("5 miles north of Fort Gratiot light", "MI", 43.0, -82.4, 1909, "a")]
        self.assertEqual(F.position_clusters(rs), [])


class NameTest(unittest.TestCase):
    def test_aliases_are_names_in_other_years_next_to_the_main_name(self):
        old = [reading("Gap Cove", "MA", 42.6583, -70.6, y, f"v{y}") for y in (1900, 1902)]
        new = [reading("Straitsmouth", "MA", 42.6583, -70.6, y, f"v{y}") for y in (1903, 1905)]
        votes = F.name_votes(old + new)
        main, single = F.pick_name(votes)
        self.assertEqual((main["name"], single), ("Straitsmouth", False))
        self.assertEqual([a["name"] for a in F.aliases_of(votes, main)], ["Gap Cove"])

    def test_a_name_in_the_same_years_is_a_slipped_row_not_an_alias(self):
        main = [reading("Willapa Bay", "WA", 46.7167, -124.05, y, f"v{y}") for y in (1893, 1903, 1908)]
        slip = [reading("Neah Bay", "WA", 46.7167, -124.05, y, f"w{y}") for y in (1893, 1896)]
        votes = F.name_votes(main + slip)
        m, _ = F.pick_name(votes)
        self.assertEqual(m["name"], "Willapa Bay")
        self.assertEqual(F.aliases_of(votes, m), [])

    def test_one_letter_slips_are_corrected_only_toward_a_far_commoner_word(self):
        words = Counter({"monomoy": 956, "monomov": 20, "point": 5000, "fishers": 142, "fisher": 90})
        self.assertEqual(F.correct_name("Monomov Point", words), "Monomoy Point")
        self.assertEqual(F.correct_name("Fishers Island", words), "Fishers Island")        # fisher is not 20x commoner
        self.assertEqual(F.correct_name("Unknownest Point", words), "Unknownest Point")

    def test_a_house_of_refuge_is_named_for_what_it_was(self):
        self.assertEqual(F.station_label("Orange Grove", "FL", True), "Orange Grove House of Refuge")
        self.assertEqual(F.station_label("Orange Grove", "FL", False), "Orange Grove Life-Saving Station")


class CheckTest(unittest.TestCase):
    def settle(self, readings, ref=()):
        clusters = F.position_clusters(readings)
        return F.settle(clusters, readings, StubLookup(), list(ref))

    def test_a_position_outside_its_state_is_left_out_with_the_reason(self):
        rs = [reading("Gloucester", "MA", 43.5917, -70.6861, y, f"v{y}") for y in (1902, 1903, 1905)]
        kept, left = self.settle(rs)
        self.assertEqual(kept, [])
        self.assertIn("not MA", left[0]["why"]) if "not MA" in left[0]["why"] else self.assertIn("outside the box", left[0]["why"])

    def test_two_reports_that_agree_need_no_neighbour(self):
        rs = [reading("Coskata", "MA", 41.3667, -70.0208, y, f"v{y}") for y in (1895, 1909)]
        kept, left = self.settle(rs)
        self.assertEqual((len(kept), left), (1, []))

    def test_a_position_read_once_is_kept_only_beside_its_neighbours_in_the_list(self):
        def listing(surfside_lat):
            return [reading("Gay Head", "MA", 41.3511, -70.8356, 1909, "v", district=2, pos=0),
                    reading("Muskeget", "MA", 41.3389, -70.3139, 1909, "v", district=2, pos=1),
                    reading("Surfside", "MA", surfside_lat, -70.1, 1909, "v", district=2, pos=2),
                    reading("Maddequet", "MA", 41.2681, -70.2083, 1909, "v", district=2, pos=3),
                    reading("Coskata", "MA", 41.3667, -70.0208, 1909, "v", district=2, pos=4)]
        kept, left = self.settle(listing(41.2417))
        self.assertEqual(len(kept), 5)
        kept, left = self.settle(listing(42.2417))        # a degree slipped: 100 km from both neighbours
        self.assertEqual(len(kept), 4)
        self.assertEqual(left[0]["cluster"]["lat"], 42.2417)
        self.assertIn("beside it in the list", left[0]["why"])

    def test_another_source_can_vouch_for_a_single_reading_and_can_contradict_it(self):
        ref = [{"source": "nrhp", "key": "nrhp:1", "name": "Coskata Life-Saving Station", "region": "MA", "lat": 41.37, "lon": -70.02}]
        alone = [reading("Coskata", "MA", 41.3667, -70.0208, 1909, "v", district=2, pos=0)]
        kept, left = self.settle(alone, ref)
        self.assertEqual((len(kept), kept[0]["external"]["source"]), (1, "nrhp"))
        far = [reading("Coskata", "MA", 41.9, -70.0208, 1909, "v", district=2, pos=0)]
        kept, left = self.settle(far, ref)
        self.assertEqual(kept, [])
        self.assertIn("nrhp", left[0]["why"])

    def test_a_single_reading_of_a_name_another_position_carries_is_a_slipped_row(self):
        rs = [reading("Chatham", "MA", 41.6528, -69.9528, y, f"v{y}", district=2, pos=0) for y in (1895, 1900, 1909)]
        rs += [reading("Chatham", "MA", 41.7194, -69.9278, 1884, "old", district=2, pos=0),
               reading("Orleans", "MA", 41.7597, -69.9319, 1884, "old", district=2, pos=1)]
        kept, left = self.settle(rs)
        self.assertEqual(len(kept), 2)       # Chatham at its well-supported position (the 1884 row, 7 km away, moved or slipped) and Orleans


class RecordTest(unittest.TestCase):
    def station(self):
        rs = [reading("Orange Grove", "FL", 26.4583, -80.0556, y, f"v{y}", district=8, pos=3,
                      footnote="House of refuge; no crew employed." if y == 1909 else None) for y in (1884, 1895, 1909)]
        (cl,) = F.position_clusters(rs)
        cl["names"] = F.name_votes(cl["members"])
        cl["external"] = None
        return cl

    def test_a_house_of_refuge_record(self):
        vols = {f"v{y}": {"year": y, "identifier": f"v{y}"} for y in (1884, 1895, 1909)}
        rec = F.make_record(self.station(), "fl-orange-grove", vols, {})
        self.assertEqual(rec["key"], "lss_reports:fl-orange-grove")
        self.assertEqual((rec["name"], rec["kind"], rec["region"], rec["precision"]), ("Orange Grove House of Refuge", "life_saving_station", "FL", "approximate"))
        self.assertEqual((rec["lat"], rec["lon"]), (26.4583, -80.0556))
        self.assertIsNone(rec["status"])                                  # the lists never say a station stands or is lost
        self.assertEqual(rec["extra"]["years_listed"], [1884, 1895, 1909])
        self.assertEqual(rec["extra"]["district"], 8)
        self.assertEqual(rec["url"], "https://archive.org/details/v1909")
        self.assertEqual(rec["events"][0]["year"], 1884)

    def test_a_footnote_that_discontinues_a_station_is_a_closed_event(self):
        rs = [reading("Orange Grove", "FL", 26.4583, -80.0556, y, f"v{y}", footnote="Discontinued October 1, 1896.") for y in (1895, 1909)]
        (cl,) = F.position_clusters(rs)
        cl["names"] = F.name_votes(cl["members"])
        cl["external"] = None
        vols = {f"v{y}": {"year": y, "identifier": f"v{y}"} for y in (1895, 1909)}
        rec = F.make_record(cl, "fl-orange-grove", vols, {})
        self.assertIn({"year": 1896, "event": "closed", "note": "Footnote in the list of stations: Discontinued October 1, 1896.", "from": "lss_reports"}, rec["events"])

    def test_a_station_the_list_names_without_a_position(self):
        rs = [reading("Bolinas Bay", "CA", None, None, y, f"v{y}", district=13, clean=False) for y in (1903, 1909)]
        st = {"state": "CA", "members": rs, "names": F.name_votes(rs), "lat": None, "lon": None, "n_readings": 0, "volumes": ["v1903", "v1909"]}
        vols = {f"v{y}": {"year": y, "identifier": f"v{y}"} for y in (1903, 1909)}
        rec = F.make_record(st, "ca-bolinas-bay", vols, {})
        self.assertEqual((rec["lat"], rec["lon"]), (None, None))
        self.assertIn("unplaced_reason", rec["extra"])


if __name__ == "__main__":
    unittest.main()
