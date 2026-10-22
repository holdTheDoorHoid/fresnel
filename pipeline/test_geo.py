"""Tests for pipeline/geo.py: the sums that place a lightship from "about 4 miles SE. by E. 1/4 E. from Monomoy Point
Light-House", the old compass, and the IGRF-14 declination that turns a magnetic bearing into a true one."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402


def dms(d: int, m: int, s: float) -> float:
    return d + m / 60 + s / 3600


class GreatCircleTest(unittest.TestCase):
    def test_one_degree_of_latitude_is_sixty_nautical_miles(self):
        self.assertAlmostEqual(geo.distance_nm(40.0, -70.0, 41.0, -70.0), 60.04, places=1)

    def test_destination_and_bearing_agree(self):
        lat, lon = geo.destination(41.5, -70.0, 90.0, 10.0)
        self.assertAlmostEqual(lat, 41.5, delta=0.01)
        self.assertAlmostEqual(geo.distance_nm(41.5, -70.0, lat, lon), 10.0, places=4)
        self.assertAlmostEqual(geo.bearing_between(41.5, -70.0, lat, lon), 90.0, delta=0.2)
        # due north, 60 nautical miles: one degree
        lat2, lon2 = geo.destination(41.0, -70.0, 0.0, 60.04)
        self.assertAlmostEqual(lat2, 42.0, places=3)
        self.assertAlmostEqual(lon2, -70.0, places=6)

    def test_the_antimeridian_wraps(self):
        lat, lon = geo.destination(0.0, 179.9, 90.0, 12.0)
        self.assertLess(lon, -179.0)


class CompassTest(unittest.TestCase):
    def test_points(self):
        self.assertEqual(geo.compass_degrees("ESE."), 112.5)
        self.assertEqual(geo.compass_degrees("N"), 0.0)
        self.assertEqual(geo.compass_degrees("due east"), 90.0)

    def test_by(self):
        self.assertEqual(geo.compass_degrees("N. by W."), 348.75)
        self.assertEqual(geo.compass_degrees("E. by S."), 101.25)
        self.assertEqual(geo.compass_degrees("NW. by N."), 326.25)

    def test_fractions_lean_toward_the_named_direction(self):
        self.assertEqual(geo.compass_degrees("SE. 1/2 E."), 129.375)        # half a point from SE toward E
        self.assertEqual(geo.compass_degrees("NW. 3/4 N."), 323.4375)
        self.assertEqual(geo.compass_degrees("S. ¼ E."), 177.1875)
        self.assertAlmostEqual(geo.compass_degrees("WNW. 5/8 W."), 285.46875)
        self.assertAlmostEqual(geo.compass_degrees("SE. ⅜ E."), 130.78125)

    def test_by_and_a_fraction(self):
        # one point and a quarter from SE toward E
        self.assertEqual(geo.compass_degrees("SE. by E. 1/4 E."), 120.9375)

    def test_what_is_not_a_bearing_is_refused(self):
        for bad in ("about 4 miles", "SE. 7/9 E.", "XNE", ""):
            with self.assertRaises(ValueError):
                geo.compass_degrees(bad)


class DeclinationTest(unittest.TestCase):
    """The model's own values: pyIGRF 1.0.0 with the IGRF-14 coefficients file gives the same to three decimals."""

    def test_values(self):
        for lat, lon, year, want in [(42.3, -71.0, 1900.0, -12.67), (35.25, -75.5, 1900.5, -4.112), (24.5, -81.8, 1900.0, 2.926),
                                     (29.3, -94.8, 1900.0, 7.36), (37.8, -122.5, 1900.0, 17.335), (44.0, -82.5, 1925.0, -4.137),
                                     (40.7, -74.0, 2020.0, -12.754), (48.4, -124.8, 1910.0, 24.532)]:
            self.assertAlmostEqual(geo.declination(lat, lon, year), want, delta=0.01, msg=(lat, lon, year))

    def test_the_model_does_not_reach_before_1900(self):
        with self.assertRaises(ValueError):
            geo.declination(42.0, -70.0, 1850.0)


class WorkedExampleTest(unittest.TestCase):
    """Pollock Rip Light-Vessel No. 47, Light List 1900 (page 42, entry 143): "Moored in 36 feet of water ... about 4
    miles SE. by E. 1/4 E. from Monomoy Point Light-House, Mass." The same entry prints her position, 41 32 (17) N,
    69 54 (36) W, and Monomoy Point Light is printed at 41 33 34 N, 69 59 39 W (entry 144). The List says "bearings are
    magnetic" and "distances are in nautical miles". The sum below must land on the printed position."""

    def test_the_description_gives_the_printed_position(self):
        light = (dms(41, 33, 34), -dms(69, 59, 39))
        magnetic = geo.compass_degrees("SE. by E. 1/4 E.")
        self.assertEqual(magnetic, 120.9375)
        declination = geo.declination(*light, 1900.0)
        self.assertAlmostEqual(declination, -12.85, delta=0.05)         # 13 degrees west of north at Cape Cod in 1900
        true = geo.true_bearing(magnetic, *light, 1900.0)
        self.assertAlmostEqual(true, 108.09, delta=0.05)
        lat, lon = geo.destination(*light, true, 4.0)
        printed = (dms(41, 32, 17), -dms(69, 54, 36))
        self.assertLess(geo.distance_nm(lat, lon, *printed), 0.1)         # 0.05 nautical miles, 80 m
        # and left uncorrected the compass bearing would have put her 1 mile out
        lat_u, lon_u = geo.destination(*light, magnetic, 4.0)
        self.assertGreater(geo.distance_nm(lat_u, lon_u, *printed), 0.8)

    def test_diamond_shoal_from_cape_hatteras(self):
        # Light List 1900, entry 654: "14 5/8 miles SE. 1/4 E. from Cape Hatteras Light-House"; printed 35 06 (05) N, 75 16 (44) W
        hat = (dms(35, 15, 17), -dms(75, 31, 16))
        lv = (dms(35, 6, 5), -dms(75, 16, 44))
        magnetic = geo.compass_degrees("SE. 1/4 E.")
        self.assertAlmostEqual(geo.true_bearing(magnetic, *hat, 1900.5), geo.bearing_between(*hat, *lv), delta=0.6)
        self.assertAlmostEqual(geo.distance_nm(*hat, *lv), 15.0, delta=0.2)


if __name__ == "__main__":
    unittest.main()
