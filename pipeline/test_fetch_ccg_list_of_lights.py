"""Tests for pipeline/fetch_ccg_list_of_lights.py on a small synthetic section of the List of Lights."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_ccg_list_of_lights as f  # noqa: E402

SECTION = """<html><body><main><h1 id="wb-cont" property="name">Atlantic Coast - Bay of Fundy, N.S.</h1>
<section><table class="wb-tables"><thead><tr><th>No.</th></tr></thead><tbody>
<tr><td>163<br /><i>H4032</i></td>
<td>Apple River</td>
<td />
<td>On Cape Capstan, N. entrance.<br />   &nbsp; 45   28   24.0<br /> 064   51   22.9<span><br /><br /></span></td>
<td>LFl</td><td>W</td><td>12s</td><td>20.8</td><td>9</td>
<td>White square tower.<br /><center>11.2</center></td>
<td>Year round.<br />Flash 2 s; eclipse 10 s.<br /></td>
</tr>
<tr><td><em>165</em></td><td><em>Advocate Harbour light and bell buoy MM</em></td><td><em /></td>
<td><em>At entrance to harbour.<br />   &nbsp; 45   19   10.3<br /> 064   48   00.8</em></td>
<td><em>Mo(A)</em></td><td><em>W</em></td><td><em>6s</em></td><td><em>.....</em></td><td><em>.....</em></td>
<td><em>Red-white, pillar, marked "MM".</em></td><td><em>Year round.</em></td></tr>
<tr><td>166<br /><i>H3934</i></td><td>Advocate Harbour</td><td />
<td>On S. side of entrance.<br />   &nbsp; 45   19   07.1<br /> 064   46   59.9<span><br /><br /></span></td>
<td>Fl</td><td>R</td><td>4s</td><td>.....</td><td>5</td>
<td>Square skeleton tower, red and white rectangular daymark.</td><td>Year round.<br /></td></tr>
<tr><td>167<br /><i>H3938</i></td><td>Cape d'Or</td><td />
<td>On extreme point.<br />   &nbsp; 45   17   27.0<br /> 064   46   27.5</td>
<td>LFl</td><td>W</td><td>6s</td><td>20.3</td><td>8</td>
<td>White square tower with red top, connected to white building.<br /><center>10.7</center><br /></td>
<td>Year round.<br />Operates 24 h.<br /><br /><b>Fog Horn</b><br />Blast 3 s; sil. 27 s.<br /></td></tr>
<tr><td style="display: none">???</td><td colspan="2" style="padding: 10px;border-top: 1px solid black;"><strong>Minas Basin</strong></td><td colspan="9" /></tr>
<tr><td>171<br /><i>H3950</i></td><td>Cape Sharp</td><td />
<td>On S. extremity of cape.<br />   &nbsp; 45   21   52.2<br /> 064   23   31.5</td>
<td>Oc</td><td>W</td><td>10s</td><td>17.4</td><td>11</td>
<td>White square tower with red upper portion.<br /><center>11.7</center></td><td>Seasonal.<br /></td></tr>
<tr><td>189.5<br /><i>H0957</i></td><td>Caraquet front range light</td><td />
<td>   &nbsp; 47   47   00.0<br /> 064   57   00.0</td>
<td>F</td><td>G</td><td>.....</td><td>7.1</td><td>.....</td><td>White pyramid tower with red vertical stripe.</td><td>Year round.</td></tr>
</tbody></table></section></main></body></html>"""

NL_SECTION = SECTION.replace("<td>Apple River</td>", "<td><b>Cape Race Light Station &amp; Fog Signal</b></td>").replace(
    "White square tower.", "White cylindrical tower, red upper portion.")


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.title, self.recs = f.parse_section(SECTION, "atl", "atl163", "/publications/list-lights/atl/atl163-en.php")
        self.by_key = {r["key"]: r for r in self.recs}

    def test_title_buoys_and_headings(self):
        self.assertEqual(self.title, "Atlantic Coast - Bay of Fundy, N.S.")
        self.assertEqual(len(self.recs), 5)  # the buoy and the sub-heading row are not records
        self.assertEqual(self.by_key["ccg_list_of_lights:A171"]["extra"]["area"], "Minas Basin")

    def test_position_in_decimal_degrees(self):
        r = self.by_key["ccg_list_of_lights:A163"]
        self.assertAlmostEqual(r["lat"], 45.473333, places=6)
        self.assertAlmostEqual(r["lon"], -64.856361, places=6)

    def test_light_fields(self):
        r = self.by_key["ccg_list_of_lights:A163"]
        self.assertEqual(r["light"]["characteristic"], "LFl W 12s")
        self.assertEqual((r["light"]["focal_height_m"], r["light"]["range_nm"], r["structure"]["height_m"]), (20.8, 9.0, 11.2))
        self.assertEqual((r["aton"]["ccg_list_number"], r["aton"]["admiralty"]), ("A163", "H4032"))
        self.assertEqual(r["extra"]["join_keys"], ["ccg:A163", "adm:H4032"])
        self.assertEqual(r["status"], "active")
        self.assertEqual(r["extra"]["season"], "year round")
        self.assertEqual(self.by_key["ccg_list_of_lights:A171"]["extra"]["season"], "seasonal")

    def test_fixed_light_without_period_or_height(self):
        r = self.by_key["ccg_list_of_lights:A189.5"]
        self.assertEqual(r["light"]["characteristic"], "F G")
        self.assertEqual(r["aton"]["admiralty"], "H957")      # leading zero dropped
        self.assertIsNone(r["light"]["range_nm"])
        self.assertEqual((r["kind"], r["role"]), ("range_lights", "front_range"))

    def test_fog_signal(self):
        self.assertEqual(self.by_key["ccg_list_of_lights:A167"]["light"]["fog_signal"], "horn")
        self.assertIsNone(self.by_key["ccg_list_of_lights:A163"]["light"]["fog_signal"])

    def test_classes(self):
        cls = {k.split(":")[1]: (r["extra"]["aid_class"], r["extra"]["clear_lighthouse"]) for k, r in self.by_key.items()}
        self.assertEqual(cls["A163"], ("tower", False))          # a plain small tower
        self.assertEqual(cls["A166"], ("beacon", False))         # skeleton tower with a daymark
        self.assertEqual(cls["A167"], ("lighthouse", True))      # tower connected to a building
        self.assertEqual(cls["A171"], ("tower", False))

    def test_major_light_is_bold_in_newfoundland_only(self):
        _t, nl = f.parse_section(NL_SECTION, "newfoundland", "nl1", "/publications/list-lights/newfoundland/nl1-en.php")
        cape_race = next(r for r in nl if r["key"] == "ccg_list_of_lights:N163")
        self.assertEqual(cape_race["name"], "Cape Race Light Station")
        self.assertTrue(cape_race["extra"]["clear_lighthouse"])
        _t, atl = f.parse_section(NL_SECTION, "atl", "atl163", "/publications/list-lights/atl/atl163-en.php")
        self.assertFalse(next(r for r in atl if r["key"] == "ccg_list_of_lights:A163")["extra"]["major_light"])


class NameTest(unittest.TestCase):
    def test_fog_signal_tail_dropped(self):
        self.assertEqual(f.clean_list_name("Cape Race Light Station & Fog Signal"), "Cape Race Light Station")
        self.assertEqual(f.clean_list_name("Portugal Cove South Light and Fog Signal"), "Portugal Cove South Light")
        self.assertEqual(f.clean_list_name("Parrsboro Wharf"), "Parrsboro Wharf")
        self.assertEqual(f.clean_list_name("St. Shotts Fog Signal Station"), "St. Shotts")
        self.assertEqual(f.clean_list_name("Butterworth Rocks Racon X (- . . -) X & S Bands"), "Butterworth Rocks")

    def test_place_called_lighthouse_point_with_a_skeleton_tower(self):
        self.assertEqual(f.classify("Lighthouse Beach", False, "Square skeleton tower, red and white rectangular daymark."), ("beacon", False))
        self.assertEqual(f.classify("Mimico Lighthouse", False, "White pyramid tower with red top."), ("lighthouse", True))

    def test_norm_admiralty(self):
        self.assertEqual(f.norm_admiralty("H0443.4"), "H443.4")
        self.assertEqual(f.norm_admiralty("H444"), "H444")


class SectionLinksTest(unittest.TestCase):
    def test_links(self):
        html = ('<a href="/publications/list-lights/atl/atl163-en.php">x</a> <a href="/publications/list-lights/atl/atlfront-en.php">f</a> '
                '<a href="/publications/list-lights/atl/ATL163e.pdf">p</a> <a href="/publications/list-lights/pac/pac1-en.php">1</a> '
                '<a href="/publications/list-lights/other/zz9-en.php">z</a>')
        self.assertEqual([t[0] for t in f.section_links(html)],
                         ["/publications/list-lights/atl/atl163-en.php", "/publications/list-lights/pac/pac1-en.php"])


class KeepTest(unittest.TestCase):
    def test_keep_rule(self):
        grid = {(int(45.0 // f.CELL), int(-64.0 // f.CELL)): [(45.0, -64.0, "wikidata")]}
        mk = lambda clear, lat: {"lat": lat, "lon": -64.0, "extra": {"clear_lighthouse": clear}}  # noqa: E731
        self.assertTrue(f.keep_record(mk(True, 50.0), grid))      # a clear lighthouse is kept anywhere
        self.assertTrue(f.keep_record(mk(False, 45.001), grid))   # ~110 m from a station
        self.assertFalse(f.keep_record(mk(False, 45.01), grid))   # a small beacon far from any
        self.assertTrue(f.keep_record(mk(False, 50.0), None))     # --no-match keeps everything
        far = {"name": "Dalhousie Wharf", "lat": 50.0, "lon": -64.0, "extra": {"clear_lighthouse": False, "join_keys": ["ccg:A5", "adm:H1"]}}
        self.assertFalse(f.keep_record(far, grid, set()))
        self.assertTrue(f.keep_record(far, grid, {"adm:H1"}))     # the Directory lists it with a lantern
        self.assertEqual((far["extra"]["clear_lighthouse"], far["extra"]["corroborated_by"]), (True, "rowlett"))


if __name__ == "__main__":
    unittest.main()
