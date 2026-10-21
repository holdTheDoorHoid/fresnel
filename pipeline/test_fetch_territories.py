"""Tests for pipeline/fetch_territories.py on a few rows shaped like the Wikipedia table and the LoC search."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_territories as ft  # noqa: E402

TABLE = """
<table class="wikitable sortable"><tbody>
<tr><th>Name</th><th>Image</th><th>Location</th><th>Coordinates</th><th>Year built</th><th>Year deactivated</th><th>Focal height</th></tr>
<tr><td><a href="/wiki/Orote">Orote Point Light</a></td><td>N/A</td><td>Guam (Point Udall)</td>
 <td><a href="https://geohack.toolforge.org/geohack.php?pagename=X&amp;params=13_26_45.0_N_144_37_10.3_E_">13&#176;26&#8242;45.0&#8243;N 144&#176;37&#8242;10.3&#8243;E</a></td>
 <td>1929 [ 3 ] (first) N/A (current)</td><td>Active [ 3 ]</td><td>226 ft</td></tr>
<tr><td>Fort Luise Augusta Light</td><td>N/A</td><td>Virgin Islands (Christiansted)</td>
 <td><a href="https://geohack.toolforge.org/geohack.php?params=17_45_17.6_N_64_41_38.7_W_">x</a></td>
 <td>1857 [ 6 ] (first) 1919 [ 6 ] (current)</td><td>1931 [ 6 ] D</td><td>61 ft</td></tr>
<tr><td>Apra Outer Harbor Range Front Light</td><td>N/A</td><td>Guam</td><td>no coordinates</td><td>Unknown</td><td>Unknown</td><td>39 ft</td></tr>
</tbody></table>
"""

LOC = {"results": [
    {"url": "http://www.loc.gov/item/pr0032/", "title": "Faro de Punta Tuna, Punta Tuna, Emajagua, Maunabo Municipio, PR", "latlong": [17.9511, -65.88361]},
    {"url": "http://www.loc.gov/item/pr0033/", "title": "Faro de los Morillos de Cabo Rojo, Cabo Rojo, PR", "latlong": None},
    {"url": "http://www.loc.gov/item/pr0043/", "title": "Superintendent of Lighthouses Dwelling, San Juan", "latlong": None},
    {"url": "http://www.loc.gov/item/pr0076/", "title": "Castillo de San Felipe del Morro, San Juan", "latlong": None},
]}


class TableTest(unittest.TestCase):
    def test_rows_and_coordinates(self):
        t = ft.parse_wikipedia_table(TABLE)
        self.assertEqual(set(t), {"Orote Point Light", "Fort Luise Augusta Light", "Apra Outer Harbor Range Front Light"})
        o = t["Orote Point Light"]
        self.assertAlmostEqual(o["lat"], 13.445833, places=5)
        self.assertAlmostEqual(o["lon"], 144.619528, places=5)
        self.assertIsNone(t["Apra Outer Harbor Range Front Light"]["lat"])

    def test_seed_records(self):
        t = ft.parse_wikipedia_table(TABLE)
        recs = {r["name"]: r for r in ft.seed_records(t, (0.805689, -176.619042))}
        self.assertEqual(set(recs), {"Orote Point Light", "Fort Louise Augusta Light", "Earhart Light"})   # the rest of the seed has no row here
        o = recs["Orote Point Light"]
        self.assertEqual((o["region"], o["status"], o["light"]["first_lit"], o["aton"]["uscg_llnr"]), ("GU", "active", 1929, "6-30685"))
        self.assertIsNone(o["structure"]["built"])
        f = recs["Fort Louise Augusta Light"]
        self.assertEqual((f["region"], f["status"], f["light"]["first_lit"], f["structure"]["built"], f["light"]["deactivated"]),
                         ("VI", "inactive", 1857, 1919, 1931))
        self.assertEqual(f["aton"]["arlhs"], "VIR-006")
        self.assertEqual(recs["Earhart Light"]["region"], "UM")
        self.assertFalse(recs["Orote Point Light"]["extra"].get("enrich_only"))   # a seed light may start a station


class HaerTest(unittest.TestCase):
    def test_haer_records_never_start_a_station(self):
        recs = ft.haer_records(LOC)
        by = {r["registers"][0]["number"]: r for r in recs}
        self.assertEqual(set(by), {"PR-32", "PR-33"})     # not the dwelling, not the castle
        r = by["PR-32"]
        self.assertTrue(r["extra"]["enrich_only"])
        self.assertEqual((r["name"], r["lat"], r["region"]), ("Faro de Punta Tuna", 17.9511, "PR"))
        self.assertEqual(r["registers"][0]["url"], "https://www.loc.gov/item/pr0032/")
        self.assertIsNone(by["PR-33"]["lat"])


if __name__ == "__main__":
    unittest.main()
