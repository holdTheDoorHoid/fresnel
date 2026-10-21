"""Tests for pipeline/fetch_rowlett.py on a small page with the directory's markup: <dt> names (bold,
with red section headings and marks), <dd> paragraphs. Only facts are read from the paragraphs."""
from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_rowlett_us as rl  # noqa: E402

PAGE = """
<html><body><table><tr><td><dl>
<dt><strong>Goat Island (3)</strong></dt>
<dd>1859 (station established 1834). Active; focal plane 38 ft (11.5 m); white flash every 6 s. A round brick tower.
 Anderson has a <a href="http://lighthousefriends.com/light.asp?ID=765">page</a>. ARLHS USA-366; Admiralty J0034; USCG 1-1390.</dd>
<dt><br><b><font color="#FF0000">Narraguagus Bay Lighthouses </font></b></dt>
<DT><A HREF="http://www.newenglandlighthouses.net/nash-island.html"><B>Nash Island
 (2) </B></A></DT>
<DD>1873 (station established 1838). Inactive since 1982; charted as a landmark. ARLHS USA-527. Whistle buoy: USCG 1-1510.</DD>
<dt><strong>#Southwest Pass Entrance (1)</strong></dt>
<dd>1962. Demolished by the Coast Guard in 2007. The lighthouse was an 85 ft steel tower. ARLHS USA-790.</dd>
<dt><strong>[Manana Island Fog Signal]</strong></dt>
<dd>1889. Inactive since 2014.</dd>
<dt><strong>* Cape Mendocino (1) (relocated to Shelter Cove)</strong></dt>
<dd>Date unknown. Inactive since the 1950s. Original tower.</dd>
<dt><strong>Statue of Liberty</strong></dt>
<dd>1886 (Auguste Bartholdi). Inactive as a lighthouse since 1902; charted as a daybeacon.</dd>
<dt><strong>Google Maps</strong></dt>
<dd>Satellite view of Kansas City, Kansas.</dd>
<dt><strong>Lake Havasu Copy</strong></dt>
<dd>1985 replica of 1850 lighthouse. Active (privately maintained); a decorative light.</dd>
</dl></td></tr></table></body></html>
"""


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.entries = rl.parse_page(PAGE)

    def test_names_are_the_last_bold_text_outside_red_headings(self):
        names = [e["name"] for e in self.entries]
        self.assertEqual(names[0], "Goat Island (3)")
        self.assertIn("Nash Island (2)", names)
        self.assertNotIn("Narraguagus Bay Lighthouses", names)
        self.assertEqual(self.entries[0]["links"], ["http://lighthousefriends.com/light.asp?ID=765"])

    def test_name_markers(self):
        n = rl.read_name("#Southwest Pass Entrance (1)")
        self.assertEqual((n["name"], n["tower"], n["lost_mark"]), ("Southwest Pass Entrance", 1, True))
        n = rl.read_name("* Cape Mendocino (1) (relocated to Shelter Cove)")
        self.assertEqual((n["name"], n["tower"], n["alts"]), ("Cape Mendocino", 1, []))
        n = rl.read_name("Palmer (Palmers) Island")
        self.assertEqual((n["name"], n["alts"]), ("Palmer (Palmers) Island", []))   # the merge reads a middle parenthesis itself
        self.assertTrue(rl.read_name("[Manana Island Fog Signal]")["bracket"])

    def test_facts_of_an_active_tower(self):
        f = rl.read_text(self.entries[0]["text"])
        self.assertEqual((f["built"], f["established"], f["status"]), (1859, 1834, "active"))
        self.assertEqual((f["arlhs"], f["uscg"], f["admiralty"]), ("USA-366", "1-1390", "J0034"))

    def test_inactive_year_and_a_buoys_number_is_not_the_lights(self):
        nash = next(e for e in self.entries if e["name"].startswith("Nash"))
        f = rl.read_text(nash["text"])
        self.assertEqual((f["built"], f["established"], f["status"], f["deactivated"]), (1873, 1838, "inactive", 1982))
        self.assertIsNone(f["uscg"])

    def test_lost(self):
        sw = next(e for e in self.entries if e["name"].startswith("#Southwest"))
        f = rl.read_text(sw["text"])
        self.assertEqual((f["status"], f["lost_year"]), ("lost", 2007))

    def test_replica_and_decorative(self):
        e = next(e for e in self.entries if e["name"] == "Lake Havasu Copy")
        f = rl.read_text(e["text"])
        self.assertTrue(f["replica"] and f["decorative"])


class RecordTest(unittest.TestCase):
    def test_records(self):
        used: Counter = Counter()
        recs = {}
        for e in rl.parse_page(PAGE):
            r = rl.build_record("me2.htm", "ME", "Maine: South", e, used)
            if r:
                recs[e["name"]] = r
        self.assertTrue(recs["[Manana Island Fog Signal]"]["extra"]["enrich_only"])   # a building: it may join, never start a station
        self.assertNotIn("Google Maps", recs)                  # not a light's entry
        goat = recs["Goat Island (3)"]
        self.assertEqual(goat["key"], "rowlett:me2:goat-island-3")
        self.assertEqual((goat["lat"], goat["lon"], goat["name"]), (None, None, "Goat Island"))
        self.assertEqual(goat["aton"]["arlhs"], "USA-366")
        self.assertEqual(goat["extra"]["xref"], ["lhf:765"])
        self.assertEqual([e["event"] for e in goat["events"]], ["built", "first_lit"])
        self.assertEqual(goat["light"]["first_lit"], 1834)
        self.assertEqual(goat["links"][0]["url"], "https://www.ibiblio.org/lighthouse/me2.htm")
        nash = recs["Nash Island (2)"]
        self.assertEqual((nash["status"], nash["light"]["deactivated"]), ("inactive", 1982))
        sw = recs["#Southwest Pass Entrance (1)"]
        self.assertEqual(sw["status"], "lost")
        self.assertIn("removed", [e["event"] for e in sw["events"]])
        self.assertNotIn("quiet_unmatched", sw["extra"])       # a lost light stays on the report's list
        self.assertTrue(goat["extra"]["quiet_unmatched"])      # an active one does not
        self.assertEqual(recs["Lake Havasu Copy"]["status"], "replica")

    def test_same_name_twice_gets_distinct_keys(self):
        used: Counter = Counter()
        e = {"name": "Fort Point", "text": "1900. Active.", "links": []}
        a = rl.build_record("ca.htm", "CA", "California", e, used)
        b = rl.build_record("ca.htm", "CA", "California", e, used)
        self.assertNotEqual(a["key"], b["key"])


if __name__ == "__main__":
    unittest.main()
