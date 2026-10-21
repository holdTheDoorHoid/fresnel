"""Tests for research/newspapers.py: query building, result parsing (a trimmed real loc.gov reply shape), ALTO
text, line grep across breaks, the shared 5 s / 20 per minute limiter with a fake clock, and offline serving
of cached pages. Run: python3 research/test_newspapers.py"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ["FRESNEL_RAW_ROOT"] = tempfile.mkdtemp(prefix="fresnel-np-test-")
import newspapers  # noqa: E402
import polite  # noqa: E402
from test_polite import FakeClock, FakeOpener, FakeResp  # noqa: E402

REPLY = {
    "pagination": {"of": 4, "perpage": 5},
    "results": [{
        "date": "1910-09-22",
        "title": "Image 3 of The Calumet news (Calumet, Mich.), September 22, 1910",
        "id": "http://www.loc.gov/resource/sn86086633/1910-09-22/ed-1/?sp=3",
        "url": "https://www.loc.gov/resource/sn86086633/1910-09-22/ed-1/?sp=3&q=%22split+rock%22+lighthouse",
        "number_lccn": ["sn86086633"], "number_page": ["0000000003"], "location_state": ["michigan"],
        "description": ["THURSDAY SEPTEMBER 22 1911 THE CALUMET NEWS  Will the Indoor baseball leaguo be reorganize"],
        "image_url": [
            "https://tile.loc.gov/image-services/iiif/service:ndnp:mimtptc:batch_mimtptc_jackson_ver01:data:sn86086633:00296024521:1910092201:1240/full/pct:3.125/0/default.jpg#h=266&w=199",
            "https://tile.loc.gov/text-services/word-coordinates-service?segment=/service/ndnp/x.xml&format=alto_xml"],
        "word_coordinates_url": "https://tile.loc.gov/text-services/word-coordinates-service?format=alto_xml&segment=%2Fservice%2Fndnp%2Fx.xml"}]}

ALTO = b"""<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v2#"><Layout><Page><PrintSpace>
<TextBlock><TextLine><String CONTENT="the"/><SP/><String CONTENT="tug"/><SP/><String CONTENT="Redwing" /></TextLine>
<TextLine><String CONTENT="used"/><SP/><String CONTENT="at"/><SP/><String CONTENT="Split"/></TextLine>
<TextLine><String CONTENT="Rock"/><SP/><String CONTENT="light-" SUBS_TYPE="HypPart1" SUBS_CONTENT="lighthouse"/></TextLine>
<TextLine><String CONTENT="house" SUBS_TYPE="HypPart2" SUBS_CONTENT="lighthouse"/><SP/><String CONTENT="supplies"/></TextLine>
</TextBlock></PrintSpace></Page></Layout></alto>"""


class Query(unittest.TestCase):
    def test_build_query(self):
        self.assertEqual(newspapers.build_query(["Point Reyes", "Joshua Strout"], "lighthouse"),
                         '"Point Reyes" "Joshua Strout" lighthouse')

    def test_url(self):
        u = newspapers.search_url(["Point Reyes"], "lighthouse", (1890, 1900), "CA", 10, 2)
        self.assertIn("dates=1890%2F1900", u)
        self.assertIn("fa=location_state%3Acalifornia", u)
        self.assertIn("fo=json", u)
        self.assertIn("at=results%2Cpagination", u)  # keeps the reply small
        self.assertIn("sp=2", u)
        self.assertTrue(u.startswith("https://www.loc.gov/collections/chronicling-america/"))

    def test_years(self):
        self.assertEqual(newspapers.parse_years("1880-1910"), (1880, 1910))
        self.assertEqual(newspapers.parse_years("1895"), (1895, 1895))
        self.assertIsNone(newspapers.parse_years(None))


class Results(unittest.TestCase):
    def test_parse(self):
        total, hits = newspapers.parse_results(REPLY)
        self.assertEqual(total, 4)
        h = hits[0]
        self.assertEqual(h["date"], "1910-09-22")
        self.assertEqual(h["paper"], "The Calumet news (Calumet, Mich.)")
        self.assertEqual(h["page"], "3")
        self.assertEqual(h["url"], "https://www.loc.gov/resource/sn86086633/1910-09-22/ed-1/?sp=3")
        self.assertEqual(h["alto"], "https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_jackson_ver01/data/sn86086633/00296024521/1910092201/1240.xml")
        self.assertEqual(h["state"], "michigan")


class PageText(unittest.TestCase):
    def test_alto_text_rejoins_hyphenated_words(self):
        t = newspapers.alto_to_text(ALTO)
        self.assertIn("the tug Redwing", t)
        self.assertIn("lighthouse", t)
        self.assertNotIn("light-", t)

    def test_grep_finds_a_phrase_broken_across_lines(self):
        t = newspapers.alto_to_text(ALTO)
        out = newspapers.grep_lines(t, r"split\s+rock", 0)
        self.assertEqual(out, ["used at Split", "Rock lighthouse"])

    def test_grep_context_and_gaps(self):
        text = "\n".join("line %d" % i for i in range(20))
        out = newspapers.grep_lines(text, r"line 3\b|line 15\b", 1)
        self.assertEqual(out, ["line 2", "line 3", "line 4", "...", "line 14", "line 15", "line 16"])


class OfflineServing(unittest.TestCase):
    def test_pages_read_through_the_tool_are_served_to_fetch_text(self):
        total, hits = newspapers.parse_results(REPLY)
        newspapers.remember_pages(hits)
        path = os.path.join(newspapers.cache_dir(), "alto", __import__("hashlib").sha1(hits[0]["alto"].encode()).hexdigest() + ".xml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(ALTO)
        url = "https://www.loc.gov/resource/sn86086633/1910-09-22/ed-1/?sp=3"
        self.assertIn("Redwing", newspapers.local_text_for_url(url))
        self.assertIn("Redwing", newspapers.local_text_for_url("http://www.loc.gov/resource/sn86086633/1910-09-22/ed-1/?sp=3&q=x"))
        self.assertIsNone(newspapers.local_text_for_url("https://www.loc.gov/resource/sn00000000/1900-01-01/ed-1/?sp=1"))
        import fetch_text
        fetch_text.RAW = polite.raw_root()
        body, ctype = fetch_text.get(url)
        self.assertIn("Redwing", fetch_text.to_text(body, ctype))


class Limiter(unittest.TestCase):
    def setUp(self):
        os.environ["FRESNEL_RAW_ROOT"] = tempfile.mkdtemp(prefix="fresnel-np-limit-")
        polite._ROBOTS_MEMO.clear()

    def test_never_more_than_20_a_minute_and_5_seconds_apart(self):
        c = FakeClock()
        starts = []
        polite._ROBOTS_MEMO.clear()
        raw = os.environ["FRESNEL_RAW_ROOT"]
        for i in range(45):
            op = FakeOpener([FakeResp(200, b"{}")])
            before = c.now
            polite.get("https://www.loc.gov/collections/chronicling-america/?q=x%d" % i, gap=newspapers.GAP,
                       per_minute=newspapers.PER_MINUTE, robots=False, opener=op, clock=c.time, sleep=c.sleep)
            starts.append(c.now)
        for a, b in zip(starts, starts[1:]):
            self.assertGreaterEqual(b - a, 5.0 - 1e-6)
        for s in starts:
            self.assertLessEqual(sum(1 for x in starts if s <= x < s + 60.0), 20)

    def test_loc_gov_hosts_share_one_lock(self):
        self.assertEqual(polite.site_key("www.loc.gov"), polite.site_key("tile.loc.gov"))

    def test_429_stops_everyone(self):
        c = FakeClock()
        op = FakeOpener([FakeResp(429, headers={"Retry-After": "600"})] * 3)
        with self.assertRaises(polite.RateLimited):
            polite.get("https://www.loc.gov/x", gap=5, per_minute=20, robots=False, opener=op, clock=c.time,
                       sleep=c.sleep, retries=2, backoff=(1.0, 1.0), max_cooldown_wait=180.0)


if __name__ == "__main__":
    unittest.main()
