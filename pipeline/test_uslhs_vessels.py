"""Tests for pipeline/uslhs_vessels.py: reading the Society's station and vessel pages (small snippets in the pages' own markup)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import uslhs_vessels as U  # noqa: E402


def field(label: str, value: str) -> str:
    return f'<div class="field inline"><div class="field_label">{label}: </div><div>{value}</div></div>\n'


STATION_PAGE = (
    field("Year Established", "1839") + field("Year Discontinued", "1972") + field("Source", "1850 LL")
    + field("U.S. State", "New Jersey") + field("Location", "Off Cape May near Entrance to Delaware Bay")
    + field("Vessel", '<a href="/node/4061">Lightship: LV-018</a>') + field("Start Year", "1839") + field("End Year", "1869")
    + field("Vessel", '<a href="/node/4152">Lightship: LV-108</a>') + field("Start Year", "1924") + field("End Year", "1942")
    + field("Vessel", '<a href="/node/4152">Lightship: LV-108</a>') + field("Start Year", "1945") + field("End Year", "")
    + '<div class="field comments"><div class="field_label">Comments</div><div><p>Alternate name: Cape May</p></div></div>\n</article>'
)

VESSEL_PAGE = (
    "<html><head><title>Lightship: LV-075 | USLHS Digital Archive</title></head><body>"
    + field("Type of Vessel", '<a href="/type-vessel/lightship">Lightship</a>') + field("LV Name/Number", "LV-75")
    + field("WAL Number", "") + field("Year Built", "1902") + field("Year Retired", "1940") + field("Existing", "Yes")
    + field("LV Station Name", "Grosse Point") + field("Year Started", "1902") + field("Year Ended", "1911")
    + field("LV Station Name", "Lake St. Clair") + field("Year Started", "1912") + field("Year Ended", "1940")
    + '<div class="field remarks"><div class="field_label">Remarks</div><div><p>Privately Owned Cadiz&#039;s Shipyard, Possibly Scrapped 2013</p></div></div>\n'
    + '<div class="field inline"><div class="field_label">Entered by:</div><div>someone</div></div></body></html>'
)


class StationPageTest(unittest.TestCase):
    def test_years_source_and_state(self):
        rec = U.parse_station_page(STATION_PAGE)
        self.assertEqual((rec["established"], rec["discontinued"]), (1839, 1972))
        self.assertEqual(rec["data_source"], "1850 LL")
        self.assertEqual(rec["state_name"], "New Jersey")
        self.assertEqual(rec["alternate_name"], "Cape May")

    def test_each_vessel_assignment_keeps_its_node_hull_and_years(self):
        rec = U.parse_station_page(STATION_PAGE)
        self.assertEqual([(v["node"], v["label"], v["start"], v["end"]) for v in rec["vessels"]],
                         [(4061, "Lightship: LV-018", 1839, 1869), (4152, "Lightship: LV-108", 1924, 1942), (4152, "Lightship: LV-108", 1945, None)])

    def test_a_page_with_no_assignments_has_none(self):
        self.assertEqual(U.parse_station_page(field("Year Established", "1850"))["vessels"], [])


class VesselPageTest(unittest.TestCase):
    def test_hull_years_and_existence(self):
        rec = U.parse_vessel_page(VESSEL_PAGE)
        self.assertEqual(rec["title"], "Lightship: LV-075")
        self.assertEqual((rec["hull"], rec["built"], rec["retired"], rec["existing"]), ("LV-75", 1902, 1940, True))
        self.assertIsNone(rec["wal"])

    def test_station_assignments_in_page_order(self):
        rec = U.parse_vessel_page(VESSEL_PAGE)
        self.assertEqual(rec["stations"], [{"station": "Grosse Point", "start": 1902, "end": 1911}, {"station": "Lake St. Clair", "start": 1912, "end": 1940}])

    def test_remarks_are_read_unescaped_and_stop_before_the_entry_credit(self):
        rec = U.parse_vessel_page(VESSEL_PAGE)
        self.assertEqual(rec["remarks"], "Privately Owned Cadiz's Shipyard, Possibly Scrapped 2013")


class SmallHelpersTest(unittest.TestCase):
    def test_years_are_read_from_text_and_nonsense_is_none(self):
        self.assertEqual(U.int_or_none("1902"), 1902)
        self.assertEqual(U.int_or_none("c. 1850"), 1850)
        self.assertIsNone(U.int_or_none(""))
        self.assertIsNone(U.int_or_none("none"))
        self.assertIsNone(U.int_or_none("0000"))


if __name__ == "__main__":
    unittest.main()
