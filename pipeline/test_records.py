"""Tests for pipeline/_records.py: the extract writer shared with the Canadian fetchers, and the small parsers."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _records as rx  # noqa: E402


class UnionWriterTest(unittest.TestCase):
    def test_each_country_replaces_only_its_own_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lighthousefriends.json"
            ca = [rx.new_record("lighthousefriends", "2027", "Pointe X", region="NS", country="CA", lat=44.0, lon=-63.0)]
            us = [rx.new_record("lighthousefriends", "547", "Cape Elizabeth", region="ME", lat=43.5, lon=-70.2)]
            # the Canadian fetcher ran first and wrote its extract (its writer keeps non-Canadian records)
            path.write_text(json.dumps({"source": "lighthousefriends", "title": "Canada's title", "url": "u", "retrieved": "2026-10-21",
                                        "license": "Canada's licence", "notes": {"canada": {"n": 1}}, "records": ca}))
            rx.write_extract(path, source="lighthousefriends", title="US title", url="u2", license_text="US licence", credit="Credit",
                             records=us, notes={"states": 31}, country="US")
            data = json.loads(path.read_text())
            self.assertEqual(sorted(r["key"] for r in data["records"]), ["lighthousefriends:2027", "lighthousefriends:547"])
            self.assertEqual(data["title"], "Canada's title")           # the shared header stays as the first writer wrote it
            self.assertEqual(data["notes"], {"canada": {"n": 1}, "us": {"states": 31}})
            # the US fetcher again, with one light fewer: the Canadian record is still there, the old US one is gone
            us2 = [rx.new_record("lighthousefriends", "999", "Other", region="ME", lat=44.0, lon=-69.0)]
            rx.write_extract(path, source="lighthousefriends", title="t", url="u", license_text="l", credit="c", records=us2,
                             notes={"states": 30}, country="US")
            data = json.loads(path.read_text())
            self.assertEqual(sorted(r["key"] for r in data["records"]), ["lighthousefriends:2027", "lighthousefriends:999"])

    def test_a_first_write_carries_the_credit_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nrhp.json"
            rx.write_extract(path, source="nrhp", title="T", url="u", license_text="L", credit="NPS", records=[], notes=None)
            data = json.loads(path.read_text())
            self.assertEqual(data["credit"], "NPS")
            self.assertEqual(list(data)[:6], ["source", "title", "url", "retrieved", "license", "credit"])

    def test_parsers(self):
        self.assertEqual(rx.year_in("built about 1873, rebuilt 1902"), 1873)
        self.assertIsNone(rx.year_in("no year"))
        self.assertAlmostEqual(rx.dms(43, 37, 23.209, "N"), 43.623114, places=5)
        self.assertAlmostEqual(rx.dms(70, 12, 28.323, "W"), -70.207868, places=5)
        self.assertEqual(rx.state_of("Port Alexander, AK"), "AK")
        self.assertEqual(rx.excel_date("26778"), "1973-04-24")
        self.assertEqual(rx.clean_text("<b>A&nbsp;  &amp; B</b>\n"), "A & B")


if __name__ == "__main__":
    unittest.main()
