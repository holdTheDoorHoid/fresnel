"""Tests for pipeline/fetch_uslhs_passport.py on short synthetic inputs shaped like the Society's
passport PDF text (pdftotext without -layout) and its accommodations pages."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_uslhs_passport as up  # noqa: E402

PASSPORT_TEXT = """\
U.S. Lighthouse Society Passport Stamps
Last Updated: July 2026
A passport stamp is available for each of the following Lighthouses, Museums, Lightships (LS), Life Saving Stations (LSS), Coast Guard Stations (CGS) & Boats, Lightship Bells
and Memorials. Stamps for Fresnel lenses not located at the lighthouse are also listed.
Since multiple stamps do exist always ask if additional stamps are available. Remember to donate $2 for each stamp received.
ALABAMA
Fort Morgan Museum
Middle Bay
CALIFORNIA
Pigeon Point
Pigeon Point Lens
Pigeon Point 150th Anniversary
Santa Cruz - Memorial
Santa Cruz Breakwater
Relief LS (LV 605)
Saybrook BW
Point Loma (Old)
Boca Chita (Faux)
Indian River LSS
U.S. Lighthouse Society Passport Stamps
Last Updated: July 2026
A passport stamp is available for each of the following Lighthouses, Museums, Lightships (LS), Life Saving Stations (LSS), Coast Guard Stations (CGS) & Boats, Lightship Bells
CALIFORNIA
Point Montara
St. Joseph Point*
INTERNATIONAL
ARUBA
California Lighthouse
"""


class PassportTest(unittest.TestCase):
    def test_parse_keeps_states_and_drops_headers(self):
        rows = up.parse_passport(PASSPORT_TEXT)
        names = [(r["state"], r["raw"]) for r in rows]
        self.assertEqual(names[0], ("AL", "Fort Morgan Museum"))
        self.assertIn(("CA", "Point Montara"), names)          # the heading repeats on the next page
        self.assertIn(("CA", "St. Joseph Point"), names)       # the asterisk (unavailable) is dropped
        self.assertNotIn("California Lighthouse", [r["raw"] for r in rows])   # international section
        self.assertTrue(all(len(r["raw"]) < 60 for r in rows))   # no header paragraph leaked in

    def test_records_skip_what_is_not_a_station(self):
        recs = up.passport_records(up.parse_passport(PASSPORT_TEXT))
        names = [r["name"] for r in recs]
        for skip in ("Fort Morgan Museum", "Pigeon Point Lens", "Pigeon Point 150th Anniversary", "Santa Cruz - Memorial", "Boca Chita (Faux)"):
            self.assertNotIn(skip, names)
        self.assertIn("Pigeon Point", names)
        by = {r["kind_raw"]: r for r in recs}
        self.assertEqual(by["Saybrook BW"]["name"], "Saybrook Breakwater")
        self.assertEqual((by["Relief LS (LV 605)"]["name"], by["Relief LS (LV 605)"]["kind"]), ("Relief", "lightship"))
        self.assertEqual(by["Indian River LSS"]["kind"], "life_saving_station")
        old = by["Point Loma (Old)"]
        self.assertEqual(old["name"], "Point Loma (Old)")      # which tower stays in the name
        self.assertEqual(old["visit"], {"passport_stamp": True})
        self.assertIsNone(old["lat"])
        self.assertEqual(old["region"], "CA")

    def test_replica_stays_in_the_name(self):
        n = up.clean_stamp_name("Choptank River (Replica)")
        self.assertEqual(n["name"], "Choptank River Replica")
        n = up.clean_stamp_name("Gasparilla Is. (Pt Boca Grande)")
        self.assertEqual((n["name"], n["alts"]), ("Gasparilla Is.", ["Pt Boca Grande"]))
        n = up.clean_stamp_name("Liston Rear Range")
        self.assertEqual((n["kind"], n["role"]), ("range_lights", "rear_range"))


ACC_PAGE = """
<article data-history-node-id="242"><div class="field field--name-body field--type-text-with-summary"><h4>Vacation Rentals</h4>
<h6>Burnt Coat Harbor Light Station (Swan's Island)</h6><p><strong>Location:</strong> Swan's Island, Maine<br>
<strong>Contact 1:</strong> Someone, rental agent. <a href="mailto:x@example.org">Email:</a> x@example.org<br>
<a href="https://www.burntcoatharborlight.com/rent/" target="_blank">Website</a></p>
<h6>Seguin Island Lighthouse Guest Quarters (Also see listing under Volunteer Host)</h6><p><a href="https://seguin.example/stay">Website</a></p>
<h4>Volunteer Host Keeper</h4>
<h6>Raspberry Island &amp; Sand Island Lighthouses</h6><p>No site.</p>
<h6>Seguin Island Lighthouse</h6><p><a href="https://seguin.example/keeper">Website</a></p>
<h4>Something Else</h4>
<h6>An Office</h6>
</div></div></article>
"""


class AccommodationsTest(unittest.TestCase):
    def test_parse_and_records(self):
        entries = up.parse_accommodations(ACC_PAGE, "ME", "https://uslhs.org/travel/lighthouse-accommodations/maine")
        self.assertEqual([e["heading"] for e in entries[:2]], ["Vacation Rentals", "Vacation Rentals"])
        recs = up.accommodation_records(entries, "2026-10-21")
        by = {r["kind_raw"]: r for r in recs}
        b = by["Burnt Coat Harbor Light Station (Swan's Island)"]
        self.assertEqual(b["name"], "Burnt Coat Harbor Light Station")
        self.assertEqual((b["stay"]["type"], b["stay"]["url"], b["region"]), ("rental", "https://www.burntcoatharborlight.com/rent/", "ME"))
        self.assertNotIn("x@example.org", str(b))                # no contact details
        self.assertEqual(by["Seguin Island Lighthouse Guest Quarters (Also see listing under Volunteer Host)"]["name"], "Seguin Island Lighthouse")
        names = sorted(r["name"] for r in recs)
        self.assertIn("Raspberry Island", names)                 # a heading naming two stations becomes two records
        self.assertIn("Sand Island Lighthouses", names)
        self.assertNotIn("An Office", names)                     # not under a stay class
        keeper = [r for r in recs if r["stay"]["type"] == "keeper_program"]
        self.assertTrue(keeper)

    def test_classes(self):
        self.assertEqual(up.stay_class("Bed & Breakfast")[0], "inn")
        self.assertEqual(up.stay_class("Hostels")[0], "hostel")
        self.assertEqual(up.stay_class("Lighthouse Keeper for a Fee")[0], "keeper_program")
        self.assertEqual(up.stay_class("Volunteer Host Keeper")[0], "keeper_program")
        self.assertEqual(up.stay_class("Vacation Rentals")[0], "rental")
        self.assertIsNone(up.stay_class("Contact us"))


if __name__ == "__main__":
    unittest.main()
