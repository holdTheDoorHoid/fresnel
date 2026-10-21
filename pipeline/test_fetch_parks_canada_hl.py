"""Tests for pipeline/fetch_parks_canada_hl.py on small synthetic copies of the two inputs."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_parks_canada_hl as f  # noqa: E402

CSV = (
    "Directory of Federal Heritage Designations Identifier,Designation name,Other names,Designation type,"
    "Designation date,Local area,Province or territory,Custodian,Construction start date,Construction end date,"
    "Street address,Heritage Lighthouse Number,FHRO Number\n"
    "14432,Fisgard Lighthouse,,Heritage Lighthouse of Canada,2013-05-23,Colwood,British Columbia,Parks Canada,1859,1861,"
    "603 Fort Rodd Hill Road,168,96-096\n"
    "16172,Annandale Rear Range Lighthouse,,Heritage Lighthouse of Canada,2020-03-11,Annandale,Prince Edward Island,,1901,,,502,\n"
    "99,Cape Spear Lighthouse,,National Historic Site of Canada,1962-01-01,St. John's,Newfoundland and Labrador,,,,,,\n"
    "16152,Cape George Lighthouse (Bras d'Or Lake),Cape George Light | Cape George Lighttower,"
    "Heritage Lighthouse of Canada,2022-01-01,Cape George,Nova Scotia,,1968,,,611,\n"
)

PAGE = """
<table><tbody>
<tr data-geometry="POINT (-123.447030 48.430978)" data-type="wkt">
 <td><span class="h4"><a href="https://www.pc.gc.ca/apps/dfhd/page_hl_eng.aspx?id=14432">Fisgard Lighthouse</a></span><br>
   Colwood, British Columbia</td>
 <td class="hidden"><img src="x.jpg"></td>
 <td class="hidden"><strong>Desgination year:</strong> 2013</td>
 <td>Fisgard Lighthouse is a 17.1 metres (56 feet) tall, tapered tower built in 1860 of brick and stone.</td></tr>
<tr data-geometry="POINT (-62.436100 46.266100)" data-type="wkt">
 <td><span class="h4"><a href="https://www.pc.gc.ca/apps/dfhd/page_hl_eng.aspx?id=16172">Annandale Rear Range Lighthouse</a></span><br>
   Annandale, Prince Edward Island</td>
 <td class="hidden"></td><td class="hidden"><strong>Desgination year:</strong> 2020</td>
 <td>The Annandale Rear Range Lighthouse is a 19.8 metre (65 feet) tapered, wooden tower. It was constructed in 1901 to replace the original 1898 lighthouse.</td></tr>
</tbody></table>
"""


class DirectoryTest(unittest.TestCase):
    def test_header_fused_to_title_line(self):
        rows = f.read_directory(CSV)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["Designation name"], "Fisgard Lighthouse")

    def test_only_heritage_lighthouses(self):
        rows = f.heritage_lighthouse_rows(f.read_directory(CSV))
        self.assertEqual([r["Identifier"] for r in rows], ["14432", "16172", "16152"])

    def test_missing_header_is_an_error(self):
        with self.assertRaises(Exception):
            f.read_directory("not,a,directory\n")


class PageTest(unittest.TestCase):
    def test_positions_and_ids(self):
        pages = f.parse_page(PAGE)
        self.assertEqual(sorted(pages), ["14432", "16172"])
        self.assertEqual((pages["14432"]["lat"], pages["14432"]["lon"]), (48.430978, -123.44703))
        self.assertEqual(pages["14432"]["year"], 2013)
        self.assertEqual(pages["14432"]["place"], "Colwood, British Columbia")

    def test_facts(self):
        pages = f.parse_page(PAGE)
        self.assertEqual(f.facts_from_description(pages["14432"]["description"]),
                         {"built": 1860, "height_m": 17.1, "material": "brick", "type": "conical_masonry"})
        a = f.facts_from_description(pages["16172"]["description"])
        self.assertEqual((a["built"], a["height_m"], a["material"], a["type"]), (1901, 19.8, "wood", "wood_frame"))

    def test_elevation_is_not_height(self):
        facts = f.facts_from_description("It sits 28 metres (93 feet) above the Petit Passage, a square wood frame tower.")
        self.assertIsNone(facts["height_m"])


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.rows = {r["Identifier"]: r for r in f.heritage_lighthouse_rows(f.read_directory(CSV))}
        self.pages = f.parse_page(PAGE)

    def test_record_shape(self):
        rec = f.build_record(self.rows["14432"], self.pages["14432"])
        self.assertEqual(rec["key"], "parks_canada_hl:14432")
        self.assertEqual((rec["country"], rec["region"], rec["kind"], rec["role"]), ("CA", "BC", "lighthouse", None))
        self.assertEqual(rec["registers"], [{"register": "Heritage Lighthouse (Canada)", "number": "14432",
                                             "url": "https://www.pc.gc.ca/apps/dfhd/page_hl_eng.aspx?id=14432"}])
        self.assertEqual(rec["events"][0]["year"], 2013)
        self.assertEqual(rec["events"][0]["event"], "heritage_designated")
        self.assertEqual(rec["agency"], "Parks Canada")
        self.assertEqual(rec["ownership"], "federal")
        self.assertTrue(rec["extra"]["standing"])
        self.assertEqual(rec["extra"]["join_keys"], ["hl:14432"])
        self.assertEqual(rec["structure"]["built"], 1860)

    def test_range_light_role(self):
        rec = f.build_record(self.rows["16172"], self.pages["16172"])
        self.assertEqual((rec["kind"], rec["role"]), ("range_lights", "rear_range"))

    def test_no_position_keeps_the_record(self):
        rec = f.build_record(self.rows["16152"], None)
        self.assertIsNone(rec["lat"])
        self.assertEqual(rec["other_names"], ["Cape George Light", "Cape George Lighttower"])
        self.assertFalse(rec["extra"]["has_position"])
        self.assertEqual(rec["structure"]["built"], 1968)  # the Directory's construction year


if __name__ == "__main__":
    unittest.main()
