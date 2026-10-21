"""Tests for pipeline/fetch_lighthousefriends_ca.py on a small synthetic state page."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_lighthousefriends_ca as f  # noqa: E402

PAGE = """
<div id="Light List"><center><div class="w3-row">
<a href="https://www.lighthousefriends.com/light.asp?ID=2162" target="_blank" class="w3-third w3-button w3-round w3-border  w3-theme ">
  <img src="x.jpg"><span>Berens Island (Swampy Island)</span><br><span>Berens River, MB</span></a>
<a href="https://www.lighthousefriends.com/light.asp?ID=1710" target="_blank" class="w3-third w3-button w3-round w3-border  w3-white ">
  <img src="y.jpg"><span>Black Bear Island</span><br><span>Selkirk, MB</span></a>
<a href="https://www.lighthousefriends.com/light.asp?ID=2160" target="_blank" class="w3-third w3-button w3-round w3-border  w3-white ">
  <img src="z.jpg"><span>Warren Landing Lower Range</span><br><span>Warren Landing, MB</span></a>
</div></center></div>
<script type="text/javascript"> function initialize() { var latlng = new google.maps.LatLng(52.366576,-97.25861);
var myOptions = {}; var lightMarker = new google.maps.Marker({ position: latlng, map: map, shadow: shadow, icon: imageblack});loc = 1;
google.maps.event.addListener(lightMarker, 'click', function() { window.open('https://www.lighthousefriends.com/light.asp?ID=2162');});
var myLatLng2= new google.maps.LatLng(50.146875,-96.865503); var lightMarker2 = new google.maps.Marker({ position: myLatLng2, map: map, shadow: shadow, icon: image});loc = 2;
google.maps.event.addListener(lightMarker2, 'click', function() { window.open('https://www.lighthousefriends.com/light.asp?ID=1710');});
var myLatLng3= new google.maps.LatLng(53.700249,-97.849883); var lightMarker3 = new google.maps.Marker({ position: myLatLng3, map: map, shadow: shadow, icon: image});loc = 3;
google.maps.event.addListener(lightMarker3, 'click', function() { window.open('https://www.lighthousefriends.com/light.asp?ID=2160');});
map.fitBounds(bounds); }
</script>
"""


class ParseTest(unittest.TestCase):
    def test_cards_and_markers(self):
        lights = f.parse_state_page(PAGE)
        self.assertEqual(sorted(lights), ["1710", "2160", "2162"])
        self.assertEqual(lights["2162"]["name"], "Berens Island (Swampy Island)")
        self.assertEqual(lights["2162"]["community"], "Berens River, MB")
        self.assertTrue(lights["2162"]["destroyed"])
        self.assertTrue(lights["2162"]["marker_destroyed"])      # black marker, shaded box: they agree
        self.assertEqual((lights["2162"]["lat"], lights["2162"]["lon"]), (52.366576, -97.25861))
        self.assertFalse(lights["1710"]["destroyed"])
        self.assertEqual((lights["1710"]["lat"], lights["1710"]["lon"]), (50.146875, -96.865503))

    def test_filtered_page_lists_ids(self):
        self.assertEqual(f.listed_ids(PAGE), {"2162", "1710", "2160"})

    def test_position_must_be_in_canada(self):
        self.assertTrue(f.in_canada(50.1, -96.8))
        self.assertFalse(f.in_canada(0.0, 0.0))
        self.assertFalse(f.in_canada(None, -96.8))
        self.assertFalse(f.in_canada(44.0, -70.0 + 20))  # Atlantic far east of Newfoundland


class RecordTest(unittest.TestCase):
    def test_destroyed_range_and_flags(self):
        lights = f.parse_state_page(PAGE)
        rec = f.build_record("2162", "MB", lights["2162"], ["boat", "climb"])
        self.assertEqual(rec["key"], "lighthousefriends:2162")
        self.assertEqual((rec["country"], rec["region"], rec["status"]), ("CA", "MB", "lost"))
        self.assertEqual(rec["extra"]["flags"], ["boat", "climb"])
        self.assertEqual(rec["links"][0]["url"], "https://www.lighthousefriends.com/light.asp?ID=2162")
        rng = f.build_record("2160", "MB", lights["2160"], [])
        self.assertEqual((rng["kind"], rng["role"], rng["status"]), ("range_lights", None, None))

    def test_state_codes(self):
        self.assertEqual(f.STATES["NF"], "NL")
        self.assertEqual(f.STATES["PQ"], "QC")

    def test_front_rear_roles(self):
        self.assertEqual(f.role_of("Mullins Point Range Rear"), "rear_range")
        self.assertEqual(f.role_of("Mullins Point Range Front"), "front_range")
        self.assertIsNone(f.role_of("Mullins Point Range"))


class UnionTest(unittest.TestCase):
    def test_keeps_other_records_and_replaces_canadian_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "lighthousefriends.json"
            out.write_text(json.dumps({"source": "lighthousefriends", "notes": {"us": {"x": 1}}, "records": [
                {"key": "lighthousefriends:1", "country": "US"}, {"key": "lighthousefriends:2", "country": "CA", "name": "old"}]}))
            old = f.OUT_PATH
            f.OUT_PATH = out
            try:
                lights = f.parse_state_page(PAGE)
                recs = [f.build_record("1710", "MB", lights["1710"], [])]
                kept = f.write_union(recs, {"by_state": {}}, "2026-10-21")
            finally:
                f.OUT_PATH = old
            data = json.loads(out.read_text())
            self.assertEqual(kept, 1)
            self.assertEqual([r["key"] for r in data["records"]], ["lighthousefriends:1", "lighthousefriends:1710"])
            self.assertEqual(data["notes"]["us"], {"x": 1})
            self.assertIn("canada", data["notes"])


if __name__ == "__main__":
    unittest.main()
