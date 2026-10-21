"""Tests for pipeline/regions.py: codes, folders, boxes across 180 degrees, local units, lookup."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regions  # noqa: E402


class CodesTest(unittest.TestCase):
    def test_territories_are_us_regions(self):
        for code in ("PR", "VI", "GU", "MP", "AS", "UM", "DC"):
            self.assertEqual(regions.country_of(code), "US", code)
        self.assertEqual(regions.country_of("NS"), "CA")
        self.assertEqual(regions.country_of("QC"), "CA")
        self.assertIsNone(regions.country_of("XX"))

    def test_every_region_has_a_box_and_a_name(self):
        for code in regions.REGION_COUNTRY:
            self.assertIn(code, regions.REGION_BOXES, code)
            self.assertTrue(regions.region_name(code))

    def test_station_dir_rule(self):
        self.assertEqual(regions.station_dir("us-me-portland-head"), "me")
        self.assertEqual(regions.station_dir("us-pr-punta-higuero"), "pr")
        self.assertEqual(regions.station_dir("ca-ns-sambro-island"), "ca-ns")
        self.assertEqual(regions.id_prefix("US", "ME"), "us-me")
        self.assertEqual(regions.id_prefix(None, "NS"), "ca-ns")

    def test_parse_region(self):
        self.assertEqual(regions.parse_region("Maine"), "ME")
        self.assertEqual(regions.parse_region("US-ME"), "ME")
        self.assertEqual(regions.parse_region("CA-NS"), "NS")
        self.assertEqual(regions.parse_region("Québec"), "QC")
        self.assertEqual(regions.parse_region("Colombie-Britannique"), "BC")
        self.assertEqual(regions.parse_region("Puerto Rico"), "PR")
        self.assertEqual(regions.parse_region("U.S. Virgin Islands"), "VI")
        self.assertEqual(regions.parse_region("Northern Mariana Islands"), "MP")
        self.assertIsNone(regions.parse_region("Ontario", country="US"))
        self.assertIsNone(regions.parse_region("CA-ME"))  # Maine is not in Canada
        self.assertIsNone(regions.parse_region("Atlantis"))

    def test_region_with_country(self):
        self.assertEqual(regions.region_with_country("NS"), "Nova Scotia, Canada")
        self.assertEqual(regions.region_with_country("PR"), "Puerto Rico")


class BoxesTest(unittest.TestCase):
    def test_far_flung_points(self):
        cases = {
            "AK": [(52.94, 172.91), (54.39, -164.74), (71.3, -156.77)],  # Attu, west of 180; Scotch Cap; Barrow
            "GU": [(13.44, 144.62)],                                      # about 145 E
            "MP": [(15.2, 145.75)],
            "AS": [(-14.25, -170.68), (-11.05, -171.08)],                # about 170 W; Swains Island
            "UM": [(18.40, -75.01), (28.21, -177.37), (19.28, 166.65)],   # Navassa, Midway, Wake
            "PR": [(18.08, -67.84)],                                      # Mona Island
            "NS": [(43.93, -60.0), (47.22, -60.15)],                      # Sable Island, St. Paul Island
            "NC": [(33.485, -77.59)],                                     # Frying Pan Shoals
            "HI": [(23.87, -166.28)],                                     # French Frigate Shoals
        }
        for region, pts in cases.items():
            for lat, lon in pts:
                self.assertTrue(regions.in_region_box(region, lat, lon), (region, lat, lon))
                self.assertIsNone(regions.flag_coordinate(region, lat, lon), (region, lat, lon))
        self.assertTrue(regions.in_country("US", -14.25, -170.68))
        self.assertTrue(regions.in_country("US", 52.94, 172.91))
        self.assertFalse(regions.in_country("CA", 13.44, 144.62))

    def test_sign_slips(self):
        self.assertEqual(regions.flag_coordinate("ME", 43.62, 70.2), "lon_positive_sign")
        self.assertEqual(regions.flag_coordinate("ME", -43.62, -70.2), "lat_negative_sign")
        self.assertEqual(regions.flag_coordinate("ME", 30.0, -90.0), "outside_region_bbox")


class LocalUnitTest(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(regions.local_unit_label("US", "ME", "Cumberland"), "Cumberland County")
        self.assertEqual(regions.local_unit_label("US", "LA", "Plaquemines"), "Plaquemines Parish")
        self.assertEqual(regions.local_unit_label("US", "AK", "Nome"), "Nome Census Area")
        self.assertEqual(regions.local_unit_label("US", "AK", "Kodiak Island"), "Kodiak Island")
        self.assertEqual(regions.local_unit_label("US", "AK", "Juneau"), "Juneau Borough")
        self.assertEqual(regions.local_unit_label("US", "PR", "Rincón"), "Rincón")
        self.assertEqual(regions.local_unit_label("US", "CT", "Lower Connecticut River Valley Planning Region"),
                         "Lower Connecticut River Valley Planning Region")
        self.assertEqual(regions.local_unit_label("CA", "NS", "Halifax"), "Halifax")
        self.assertIsNone(regions.local_unit_label("US", "ME", None))


def square(lon0, lat0, lon1, lat1):
    return {"type": "Polygon", "coordinates": [[[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]]]}


class LookupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.census = d / "states.geojson"
        self.census.write_text(json.dumps({"type": "FeatureCollection", "features": [
            {"properties": {"STUSAB": "ME"}, "geometry": square(-71, 43, -67, 47)},
        ]}))
        self.ne = d / "ne.geojson"
        self.ne.write_text(json.dumps({"type": "FeatureCollection", "features": [
            {"properties": {"iso_a2": "CA", "iso_3166_2": "CA-NB"}, "geometry": square(-66.9, 45, -64, 48)},
        ]}))
        self.lookup = regions.RegionLookup(self.census, self.ne)

    def tearDown(self):
        self.tmp.cleanup()

    def test_inside_and_nearest(self):
        self.assertEqual(self.lookup.lookup(44.0, -69.0)[:2], ("ME", "inside"))
        region, how, km = self.lookup.lookup(46.0, -63.9)   # just off the NB square
        self.assertEqual((region, how), ("NB", "nearest"))
        self.assertEqual(self.lookup.lookup(44.0, -69.0, country="CA")[0], None)  # only Canadian polygons
        self.assertEqual(self.lookup.lookup(10.0, -40.0)[1], "none_near")


if __name__ == "__main__":
    unittest.main()
