"""Tests for pipeline/fetch_lighthousefriends.py on a small synthetic state page that has the real
page's structure: one map script (the first light's position is the map centre variable), the
click handlers that name each light, and the cards (a destroyed light's card is highlighted)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_lighthousefriends as lhf  # noqa: E402


def page(lights: list[tuple[str, str, str, float, float, bool]]) -> str:
    """lights: (id, name, place, lat, lon, destroyed)."""
    first = lights[0]
    js = [f"function initialize() {{ var latlng = new google.maps.LatLng({first[3]},{first[4]}); "
          f"var map = new google.maps.Map(document.getElementById(\"map_canvas\"), {{center: latlng}}); "
          f"var lightMarker = new google.maps.Marker({{ position: latlng, map: map, icon: imageblack}});"
          f"google.maps.event.addListener(lightMarker, 'click', function() {{ window.open('https://www.lighthousefriends.com/light.asp?ID={first[0]}');}});"]
    for i, (lid, _n, _p, lat, lon, _d) in enumerate(lights[1:], start=2):
        js.append(f" var myLatLng{i}= new google.maps.LatLng({lat},{lon}); var lightMarker{i} = new google.maps.Marker({{ position: myLatLng{i}, map: map, icon: image}});"
                  f"google.maps.event.addListener(lightMarker{i}, 'click', function() {{ window.open('https://www.lighthousefriends.com/light.asp?ID={lid}');}});")
    js.append(" }")
    cards = []
    for lid, name, place, _la, _lo, destroyed in lights:
        cls = "w3-theme" if destroyed else "w3-white"
        cards.append(f'<a href="https://www.lighthousefriends.com/light.asp?ID={lid}" target="_blank" '
                     f'class="w3-third w3-button w3-round w3-border  {cls} "> <img src="x.jpg"> '
                     f'<span>{name}</span><br>\n        <span>{place}</span></a>')
    return "<html><script>" + "".join(js) + "</script><body>" + "\n".join(cards) + "</body></html>"


LIGHTS = [
    ("1863", "Avery Rock", "Machias, ME", 44.654275, -67.344127, True),
    ("768", "Cape Neddick (Nubble)", "York, ME", 43.165, -70.595, False),
    ("512", "Burnt Coat Harbor (Hockamock Head)", "Swans Island, ME", 44.1342, -68.4553, False),
]


class ParseTest(unittest.TestCase):
    def test_positions_ids_cards(self):
        out = lhf.parse_state_page(page(LIGHTS))
        self.assertEqual([x["id"] for x in out], ["1863", "768", "512"])
        self.assertEqual((out[0]["lat"], out[0]["lon"]), (44.654275, -67.344127))
        self.assertEqual((out[1]["lat"], out[1]["lon"]), (43.165, -70.595))
        self.assertEqual(out[1]["place"], "York, ME")
        self.assertEqual([x["destroyed_card"] for x in out], [True, False, False])

    def test_ampersand_in_name(self):
        out = lhf.parse_state_page(page([("5", "Ship &amp; Shoal", "X, ME", 44.0, -68.0, False)]))
        self.assertEqual(out[0]["name"], "Ship & Shoal")


class NameTest(unittest.TestCase):
    def test_alias_in_parentheses(self):
        n = lhf.read_name("Cape Neddick (Nubble)")
        self.assertEqual((n["name"], n["other_names"], n["kind"]), ("Cape Neddick", ["Nubble"], "lighthouse"))

    def test_replica(self):
        n = lhf.read_name("Blackistone Island (Replica)")
        self.assertTrue(n["replica"])
        self.assertEqual(n["name"], "Blackistone Island")
        self.assertEqual(n["other_names"], [])

    def test_lightship_hull(self):
        n = lhf.read_name("Lightship Nantucket LV 112/WAL 534")
        self.assertEqual((n["name"], n["kind"], n["hull"]), ("Nantucket", "lightship", "LV-112"))
        n = lhf.read_name("Lightship Umatilla WLV-196")
        self.assertEqual((n["name"], n["hull"]), ("Umatilla", "WLV-196"))
        n = lhf.read_name("Lightship Relief WLV 605")
        self.assertEqual((n["name"], n["hull"]), ("Relief", "WLV-605"))

    def test_minor_light(self):
        n = lhf.read_name("Minor light of Hawai'i - Coconut Point")
        self.assertEqual((n["name"], n["kind"], n["minor"]), ("Coconut Point", "harbor_light", True))

    def test_ranges_and_piers(self):
        n = lhf.read_name("Liston Front Range")
        self.assertEqual((n["kind"], n["role"]), ("range_lights", "front_range"))
        n = lhf.read_name("Chapel Hill Rear Range")
        self.assertEqual((n["kind"], n["role"]), ("range_lights", "rear_range"))
        n = lhf.read_name("Grosse Ile (North Range)")
        self.assertEqual((n["name"], n["kind"], n["role"]), ("Grosse Ile North Range", "range_lights", None))
        n = lhf.read_name("Baileys Harbor Range Lights")
        self.assertEqual((n["kind"], n["role"]), ("range_lights", None))
        n = lhf.read_name("Manistee North Pierhead")
        self.assertEqual(n["kind"], "pier_light")
        n = lhf.read_name("Gasparilla Island (Boca Grande Entrance Rear Range)")
        self.assertEqual(n["name"], "Gasparilla Island")
        self.assertEqual(n["other_names"], ["Boca Grande Entrance Rear Range"])
        self.assertEqual(n["kind"], "range_lights")

    def test_memorial(self):
        self.assertTrue(lhf.read_name("Perry Memorial")["memorial"])


class RecordTest(unittest.TestCase):
    def test_destroyed_is_lost_and_approximate(self):
        out = lhf.parse_state_page(page(LIGHTS))
        rec = lhf.build_record("ME", out[0], set(), True)
        self.assertEqual(rec["key"], "lighthousefriends:1863")
        self.assertEqual((rec["status"], rec["precision"], rec["region"]), ("lost", "approximate", "ME"))
        self.assertEqual(rec["links"][0]["url"], "https://www.lighthousefriends.com/light.asp?ID=1863")

    def test_a_replica_keeps_the_word_in_its_name(self):
        light = {"id": "9", "name": "Blackistone Island (Replica)", "place": "Coltons Point, MD", "lat": 38.2, "lon": -76.7, "destroyed_card": False}
        rec = lhf.build_record("MD", light, set(), False)
        self.assertEqual((rec["name"], rec["status"]), ("Blackistone Island (Replica)", "replica"))

    def test_flags_become_visit_stay_access(self):
        out = lhf.parse_state_page(page(LIGHTS))
        rec = lhf.build_record("ME", out[1], {"climb", "boat", "private", "lodging", "keeperprog"}, False)
        self.assertIsNone(rec["status"])
        self.assertEqual(rec["visit"], {"climbable": True, "boat_only": True})
        self.assertEqual(rec["access"]["level"], "private")
        self.assertEqual(rec["stay"]["type"], "rental")
        self.assertIn("volunteer keeper program", rec["stay"]["note"])
        only_keeper = lhf.build_record("ME", out[2], {"keeperprog"}, False)
        self.assertEqual(only_keeper["stay"]["type"], "keeper_program")
        plain = lhf.build_record("ME", out[2], set(), False)
        for k in ("visit", "stay", "access"):
            self.assertNotIn(k, plain)  # a missing flag says nothing; it is never a false

    def test_no_position_no_record(self):
        light = {"id": "9", "name": "X", "place": "Y, ME", "lat": None, "lon": None, "destroyed_card": False}
        self.assertIsNone(lhf.build_record("ME", light, set(), False))


class ExtractTest(unittest.TestCase):
    def test_passes_become_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            paths = {}
            for name in lhf.PASSES:
                subset = {"all": LIGHTS, "destroyed": LIGHTS[:1], "climb": LIGHTS[1:2], "lodging": [],
                          "keeperprog": [], "private": LIGHTS[2:], "boat": LIGHTS[1:]}[name]
                p = tmp / f"ME_{name}.html"
                p.write_text(page(subset) if subset else "<html></html>", encoding="utf-8")
                paths[("ME", name)] = p
            records, problems = lhf.extract(paths)
            self.assertEqual(problems, {})
            by = {r["extra"]["lhf_id"]: r for r in records}
            self.assertEqual(by["1863"]["status"], "lost")
            self.assertEqual(by["768"]["visit"], {"climbable": True, "boat_only": True})
            self.assertEqual(by["512"]["access"]["level"], "private")


if __name__ == "__main__":
    unittest.main()
