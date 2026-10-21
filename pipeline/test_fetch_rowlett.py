"""Tests for pipeline/fetch_rowlett.py on a small synthetic page (Rowlett's markup leaves tags open,
puts section headings in <dt> without a <dd>, and marks names with * # [ ] and (n))."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_rowlett as f  # noqa: E402

PAGE = """﻿<html><body><dl>
<dt><font color="#FF0000"><b>Mahone Bay Lighthouses</b></font></dt>
<dt>Mahone Bay is a long bay.</dt>
<dt><strong><a href="https://www.lighthousefriends.com/light.asp?ID=2027">Quaker
  Island (3)</a></strong></dt>
<dd>1981 (station established 1883). Active; focal plane 31 m (102 ft); red flash every 4 s. 6 m (20 ft) round
 fiberglass tower, colored white with a red band at the top. Trabas has a <a href="http://x">photo</a>.
 Located on an island. Accessible only by boat. Site status unknown. Owner/site manager: Canadian Coast Guard.
 ARLHS CAN-422; CCG A-456; Admiralty H3680; NGA 10120.</dd>
<dt><strong><font color="#FF0000">*</font> <a href="http://www.lighthousefriends.com/light.asp?ID=1676">Kaulbach
  Island Range Front</a></strong></dt>
<dd>1914. Active; focal plane 11 m (36 ft); continuous white light.
  6.5 m (22 ft) square pyramidal wood tower covered by siding. Site open, tower closed.
  Owner/site manager: <a href="x">Haldimand County</a> (?). ARLHS CAN-260; CCG A-453; Admiralty
  H3682; NGA 10128.</dd>
<dt><b>#Eddy Point (4)</b></dt>
<dd>1989 (station established 1851). Demolished in 2003. The lighthouse, a 12 m (39 ft) round fiberglass tower, was
 deactivated in 2000 and demolished. ARLHS CAN-100; CCG A-0100.</dd>
<dt><b><br>[Proctor (2)]</b></dt>
<dd>Date unknown (station established 1905?). Active; focal plane 6 m (20 ft); white flash every 4 s. 3 m (10 ft) post.
 Site open, tower closed. CCG P-0010.</dd>
<dt><strong>Red River Mouth (Red River Range Rear (2))</strong></dt>
<dd>Date unknown (station established 1895). Active; focal plane 17 m (56 ft); white flash every 4 s. 17 m (56 ft) square skeletal tower. CCG I-0563.01.</dd>
<dt><strong>Burntcoat Head (2) (replica)</strong></dt>
<dd>1995 replica of 1913 lighthouse. Station established 1859, inactive since the mid 1970s. Octagonal lantern. ARLHS CAN-5.</dd>
<dt><a href="http://www.nslps.com/">Nova Scotia Lighthouse Preservation Society</a></dt>
<dd>This outstanding web site has a wealth of photos.</dd>
</dl></body></html>"""


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.entries = f.read_entries(PAGE)
        seen: dict = {}
        self.recs = {r["name"]: r for r in (f.build_record("nss", e, seen) for e in self.entries) if r}

    def test_pairs_each_dd_with_its_own_dt(self):
        self.assertEqual(len(self.entries), 7)
        self.assertEqual(len(self.recs), 6)  # the society's link is not a light

    def test_name_marks_and_tower_number(self):
        q = self.recs["Quaker Island"]
        self.assertEqual(q["extra"]["tower_number"], 3)
        self.assertEqual(q["extra"]["lhf_ids"], ["2027"])
        self.assertTrue(self.recs["Kaulbach Island Range Front"]["extra"]["notable"])
        self.assertTrue(self.recs["Eddy Point"]["extra"]["gone"])
        self.assertTrue(self.recs["Proctor"]["extra"]["minor_marker"])

    def test_nested_parentheses_give_other_names(self):
        r = self.recs["Red River Mouth"]
        self.assertEqual(r["other_names"], ["Red River Range Rear"])
        self.assertEqual(r["extra"]["tower_number"], 2)

    def test_identifiers(self):
        q = self.recs["Quaker Island"]
        self.assertEqual(q["aton"]["arlhs"], "CAN422")
        self.assertEqual(q["aton"]["ccg_list_number"], "A456")
        self.assertEqual(q["aton"]["admiralty"], "H3680")
        self.assertEqual(q["aton"]["nga"], "10120")
        self.assertEqual(q["extra"]["join_keys"], ["lhf:2027", "arlhs:CAN422", "ccg:A456", "adm:H3680"])
        self.assertEqual(self.recs["Eddy Point"]["aton"]["ccg_list_number"], "A100")        # leading zeros dropped
        self.assertEqual(self.recs["Red River Mouth"]["aton"]["ccg_list_number"], "I563.01")

    def test_years_and_status(self):
        q = self.recs["Quaker Island"]
        self.assertEqual((q["structure"]["built"], q["light"]["first_lit"], q["status"]), (1981, 1883, "active"))
        self.assertEqual(q["structure"]["material"], "fiberglass")
        self.assertEqual(q["structure"]["height_m"], 6.0)
        self.assertEqual(q["light"]["focal_height_m"], 31.0)
        e = self.recs["Eddy Point"]
        self.assertEqual(e["status"], "lost")
        self.assertIn({"year": 2003, "event": "removed", "note": None, "from": "rowlett"}, e["events"])
        p = self.recs["Proctor"]
        self.assertIsNone(p["structure"]["built"])                 # "Date unknown"
        self.assertIsNone(p["light"]["first_lit"])                 # "(station established 1905?)" is uncertain
        self.assertTrue(p["extra"]["established_uncertain"])
        b = self.recs["Burntcoat Head"]
        self.assertEqual((b["status"], b["extra"]["replica_of"]), ("replica", 1913))
        self.assertEqual(b["light"]["first_lit"], 1859)

    def test_lantern_flag_reads_the_structure_sentence_only(self):
        self.assertTrue(f.has_lantern("1900. Active; focal plane 9 m (30 ft); white flash. 9 m (30 ft) octagonal tower with lantern and gallery. Lighthouse painted white.", "1900"))
        self.assertFalse(f.has_lantern("1928. Active; focal plane 7 m (24 ft). 5.5 m (18 ft) square pyramidal concrete tower built on a crib. No lantern. Lighthouse painted white.", "1928"))
        self.assertFalse(f.has_lantern("1900. Active; focal plane 6 m (20 ft). 3 m (10 ft) post colored white. An original lighthouse had a lantern.", "1900"))

    def test_range_roles_and_kind(self):
        k = self.recs["Kaulbach Island Range Front"]
        self.assertEqual((k["kind"], k["role"]), ("range_lights", "front_range"))
        self.assertEqual(self.recs["Quaker Island"]["kind"], "lighthouse")
        self.assertEqual(self.recs["Red River Mouth"]["kind"], "lighthouse")

    def test_access_and_owner(self):
        q = self.recs["Quaker Island"]
        self.assertEqual(q["extra"]["access"], {"boat_only": True, "site": "unknown"})
        self.assertEqual((q["agency"], q["ownership"]), ("Canadian Coast Guard", "federal"))
        k = self.recs["Kaulbach Island Range Front"]
        self.assertEqual(k["extra"]["access"], {"site": "open", "tower": "closed"})
        self.assertEqual(k["agency"], "Haldimand County")
        self.assertEqual(k["ownership"], "local")

    def test_no_position_and_station_level(self):
        q = self.recs["Quaker Island"]
        self.assertIsNone(q["lat"])
        self.assertTrue(q["extra"]["station_level"])
        self.assertEqual(q["country"], "CA")
        self.assertEqual(q["region"], "NS")

    def test_keys_are_stable_and_unique(self):
        seen: dict = {}
        keys = [r["key"] for r in (f.build_record("nss", e, seen) for e in f.read_entries(PAGE)) if r]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertIn("rowlett:nss:quaker-island", keys)


class NormalisationTest(unittest.TestCase):
    def test_ccg_numbers(self):
        self.assertEqual(f.norm_ccg("A-456"), "A456")
        self.assertEqual(f.norm_ccg("I-0563"), "I563")
        self.assertEqual(f.norm_ccg("N-049"), "N49")
        self.assertEqual(f.norm_ccg("I-0114.1"), "I114.1")

    def test_arlhs(self):
        self.assertEqual(f.norm_arlhs("0422"), "CAN422")


class UnionTest(unittest.TestCase):
    def test_keeps_non_canadian_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "rowlett.json"
            out.write_text(json.dumps({"source": "rowlett", "records": [
                {"key": "rowlett:x", "country": "US"}, {"key": "rowlett:old", "country": "CA"}]}))
            old, f.OUT_PATH = f.OUT_PATH, out
            try:
                seen: dict = {}
                recs = [r for r in (f.build_record("nss", e, seen) for e in f.read_entries(PAGE)) if r][:1]
                kept = f.write_union(recs, {}, "2026-10-21")
            finally:
                f.OUT_PATH = old
            self.assertEqual(kept, 1)
            keys = [r["key"] for r in json.loads(out.read_text())["records"]]
            self.assertEqual(keys[0], "rowlett:nss:quaker-island")
            self.assertIn("rowlett:x", keys)
            self.assertNotIn("rowlett:old", keys)


if __name__ == "__main__":
    unittest.main()
