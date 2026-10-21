"""Tests for pipeline/fetch_nrhp.py and the .xlsx reader it uses, on a tiny workbook built in memory."""
from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _records as rx  # noqa: E402
import fetch_nrhp as nrhp  # noqa: E402

HEADER = ["Ref#", "Prefix", "Property Name", "State", "County", "City ", "Category of Property", "External Link",
          "Listed Date", "NHL Designated Date", "Other Names", "Status"]


def make_xlsx(path: Path, rows: list[list[str]]) -> None:
    """A workbook with shared strings (as NPS's is): numbers stay numbers, everything else is a string."""
    strings: list[str] = []

    def sst(s: str) -> int:
        if s not in strings:
            strings.append(s)
        return strings.index(s)

    xml_rows = []
    for ri, row in enumerate([HEADER] + rows, start=1):
        cells = []
        for ci, val in enumerate(row):
            if val == "":
                continue
            ref = f"{chr(65 + ci)}{ri}"
            if re_number(val):
                cells.append(f'<c r="{ref}"><v>{val}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="s"><v>{sst(val)}</v></c>')
        xml_rows.append(f'<row r="{ri}">{"".join(cells)}</row>')
    sheet = ('<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             f'<sheetData>{"".join(xml_rows)}</sheetData></worksheet>')
    sst_xml = ('<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
               + "".join(f"<si><t>{s.replace('&', '&amp;')}</t></si>" for s in strings) + "</sst>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        z.writestr("xl/sharedStrings.xml", sst_xml)


def re_number(s: str) -> bool:
    return s.isdigit() and len(s) <= 6


ROWS = [
    ["73000121", "", "Portland Headlight", "MAINE", "Cumberland", "Cape Elizabeth", "BUILDING",
     "https://catalog.archives.gov/id/88685813", "26778", "", "Portland Head Light; Portland Head Lighthouse", "Listed"],
    ["03000529", "", "Point Retreat Light Station", "ALASKA", "Juneau", "Juneau", "DISTRICT",
     "https://catalog.archives.gov/id/75325043", "37750", "40000", "", "Listed"],
    ["90001315", "", "Dothan Municipal Light and Water Plant", "ALABAMA", "Houston", "Dothan", "BUILDING", "", "33000", "", "", "Listed"],
    ["05000300", "", "First Baptist Church, Kingston", "ALABAMA", "Jefferson", "Birmingham", "BUILDING", "", "38462", "", "Lighthouse Church Ministries", "Listed"],
    ["79000477", "", "Humboldt Bay Life-Saving Station", "CALIFORNIA", "Humboldt", "Eureka", "BUILDING", "", "29000", "", "", "Listed"],
    ["09001288", "", "Fire Island Light Station Historic District (Boundary Increase)", "NEW YORK", "Suffolk", "Fire Island", "DISTRICT", "", "40000", "", "", "Listed"],
    ["83004523", "", "Japanese Lighthouse", "FEDERATED STATES OF MICRONESIA", "Yap", "Puluwat", "STRUCTURE", "", "30000", "", "", "Listed"],
    ["100004382", "", "Hams Bluff Light", "VIRGIN ISLANDS", "St. Croix", "Frederiksted", "STRUCTURE", "", "43700", "", "", "Listed"],
]


class WorkbookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "wb.xlsx"
        make_xlsx(self.path, ROWS)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reader_pads_short_rows(self):
        rows = list(rx.read_xlsx_rows(self.path))
        self.assertEqual(rows[0][:3], ["Ref#", "Prefix", "Property Name"])
        self.assertEqual(len(rows), len(ROWS) + 1)
        wb = nrhp.read_workbook(self.path)
        self.assertEqual(wb["73000121"]["Property Name"], "Portland Headlight")
        self.assertEqual(wb["09001288"]["Other Names"], "")

    def test_excel_dates(self):
        self.assertEqual(rx.excel_date("26778"), "1973-04-24")
        self.assertIsNone(rx.excel_date(""))
        self.assertIsNone(rx.excel_date("x"))

    def test_selection(self):
        wb = nrhp.read_workbook(self.path)
        chosen = nrhp.select(wb, {"73000121"}, set())
        self.assertEqual(chosen["73000121"], "wikidata")
        self.assertEqual(chosen["03000529"], "name")
        self.assertEqual(chosen["79000477"], "name")
        self.assertIn("100004382", chosen)
        for no in ("90001315", "05000300", "83004523"):   # a water plant, a church, a lighthouse in Micronesia
            self.assertNotIn(no, chosen)
        self.assertEqual(nrhp.select(wb, set(), {"90001315"})["90001315"], "mps")  # a listing's own MPS wins


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = Path(self.tmp.name) / "wb.xlsx"
        make_xlsx(path, ROWS)
        self.wb = nrhp.read_workbook(path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_structure_with_point(self):
        feature = {"geometry": {"x": -70.20768, "y": 43.62313}}
        rec = nrhp.build_record("73000121", self.wb["73000121"], feature, None)
        self.assertEqual(rec["key"], "nrhp:73000121")
        self.assertEqual((rec["region"], rec["county"], rec["kind"]), ("ME", "Cumberland", "lighthouse"))
        self.assertEqual((rec["lat"], rec["lon"], rec["precision"]), (43.62313, -70.20768, "approximate"))
        reg = rec["registers"][0]
        self.assertEqual((reg["register"], reg["number"], reg["listed"]), ("NRHP", "73000121", "1973-04-24"))
        self.assertIsNone(reg["nhl"])
        self.assertEqual(reg["nomination"], "https://catalog.archives.gov/id/88685813")
        self.assertEqual(rec["events"][0]["event"], "nrhp_listed")
        self.assertEqual(rec["events"][0]["year"], 1973)
        self.assertIn("Portland Head Light", rec["other_names"])
        self.assertNotIn("station_level", rec["extra"])

    def test_district_is_station_level_and_nhl_dated(self):
        rec = nrhp.build_record("03000529", self.wb["03000529"], None, None, centre=(58.41, -134.95))
        self.assertTrue(rec["extra"]["station_level"])
        self.assertEqual((rec["lat"], rec["lon"]), (58.41, -134.95))
        self.assertIn("polygon", rec["extra"]["position_from"])
        self.assertIsNotNone(rec["registers"][0]["nhl"])
        self.assertEqual([e["event"] for e in rec["events"]], ["nrhp_listed", "heritage_designated"])

    def test_boundary_increase_never_starts_a_station(self):
        rec = nrhp.build_record("09001288", self.wb["09001288"], None, None)
        self.assertTrue(rec["extra"]["enrich_only"])
        self.assertIsNone(rec["lat"])

    def test_life_saving_station_kind(self):
        rec = nrhp.build_record("79000477", self.wb["79000477"], {"geometry": {"x": -124.2, "y": 40.77}}, None)
        self.assertEqual(rec["kind"], "life_saving_station")

    def test_new_style_number_has_no_gallery_page(self):
        rec = nrhp.build_record("100004382", self.wb["100004382"], {"geometry": {"x": -64.87, "y": 17.77}}, "Light Stations of the United States MPS")
        self.assertEqual((rec["region"], rec["extra"]["mps"]), ("VI", "Light Stations of the United States MPS"))
        self.assertIsNone(rec["url"])

    def test_outside_the_us_has_no_record(self):
        self.assertIsNone(nrhp.build_record("83004523", self.wb["83004523"], None, None))

    def test_ring_centre(self):
        self.assertEqual(nrhp.ring_centre({"rings": [[[-75.52, 35.25], [-75.54, 35.27], [-75.52, 35.27]]]}), (35.26, -75.53))
        self.assertIsNone(nrhp.ring_centre({}))


if __name__ == "__main__":
    unittest.main()
