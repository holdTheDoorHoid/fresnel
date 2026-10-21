"""Tests for research/polite.py: spacing with a fake clock, the per-minute cap, cooldowns, robots.txt rules,
redirects and back-off with a fake transport. Run: python3 research/test_polite.py"""
import io
import os
import sys
import tempfile
import unittest
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import polite  # noqa: E402


class FakeClock:
    def __init__(self, start=1_000_000.0):
        self.now = start
        self.slept = []

    def time(self):
        return self.now

    def sleep(self, s):
        self.slept.append(s)
        self.now += s


class ThrottleTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.c = FakeClock()

    def th(self, **kw):
        kw.setdefault("gap", 2.0)
        return polite.Throttle("web-example.org", clock=self.c.time, sleep=self.c.sleep, lockdir=self.dir, **kw)

    def test_first_request_does_not_wait(self):
        with self.th():
            pass
        self.assertEqual(self.c.slept, [])

    def test_two_second_gap_between_starts(self):
        starts = []
        for _ in range(4):
            with self.th() as t:
                starts.append(t.start)
        gaps = [b - a for a, b in zip(starts, starts[1:])]
        for g in gaps:
            self.assertGreaterEqual(g, 2.0 - 1e-6)
            self.assertLess(g, 2.2)

    def test_slow_request_still_leaves_idle_time(self):
        with self.th() as t:
            self.c.now += 10.0  # the request itself took 10 s
            first_start = t.start
        with self.th() as t2:
            pass
        self.assertGreaterEqual(t2.start - (first_start + 10.0), 0.5 - 1e-6)

    def test_lock_file_is_a_bare_float_like_fetch_text(self):
        with self.th():
            pass
        with open(os.path.join(self.dir, "web-example.org")) as fh:
            float(fh.read().strip())

    def test_reads_a_stamp_written_by_fetch_text(self):
        with open(os.path.join(self.dir, "web-example.org"), "w") as fh:
            fh.write(str(self.c.now))  # fetch_text stamps "now" at the end of its request
        with self.th():
            pass
        self.assertAlmostEqual(sum(self.c.slept), 2.0, places=2)

    def test_per_minute_cap(self):
        starts = []
        for _ in range(8):
            with self.th(gap=1.0, per_minute=5) as t:
                starts.append(t.start)
        # the 6th request may not start until a minute after the 1st
        self.assertGreaterEqual(starts[5] - starts[0], 60.0)
        # and never more than 5 inside any 60 s window
        for i, s in enumerate(starts):
            self.assertLessEqual(sum(1 for x in starts if s <= x < s + 60.0), 5)

    def test_loc_gov_rules(self):
        self.assertEqual(polite.site_gap("www.loc.gov"), 5.0)
        self.assertEqual(polite.site_gap("tile.loc.gov"), 5.0)
        self.assertEqual(polite.site_key("tile.loc.gov"), "loc.gov")
        self.assertEqual(polite.site_key("ia800123.us.archive.org"), "archive.org")
        self.assertEqual(polite.site_gap("archives.uslhs.org"), 2.0)

    def test_cooldown_blocks_everyone_and_long_ones_raise(self):
        t = self.th()
        t.set_cooldown(60.0)
        with self.th():
            pass
        self.assertGreaterEqual(sum(self.c.slept), 60.0)
        t.set_cooldown(3600.0)
        with self.assertRaises(polite.RateLimited):
            with self.th(max_cooldown_wait=180.0):
                pass


class RobotsTests(unittest.TestCase):
    TXT = """User-agent: *
Allow: /core/*.css$
Disallow: /core/
Disallow: /search/
Disallow: /*/media/oembed
User-agent: ClaudeBot
Disallow: /
"""

    def test_rules(self):
        g = polite.parse_robots(self.TXT)
        r = polite.rules_for(g)
        self.assertTrue(polite.path_allowed(r, "/places"))
        self.assertTrue(polite.path_allowed(r, "/places?title=%22Portland+Head%22"))
        self.assertFalse(polite.path_allowed(r, "/search/node"))
        self.assertFalse(polite.path_allowed(r, "/core/x.js"))
        self.assertTrue(polite.path_allowed(r, "/core/x.css"))  # longest match, Allow
        self.assertFalse(polite.path_allowed(r, "/en/media/oembed"))

    def test_ai_crawler_rule_means_skip(self):
        self.assertTrue(polite.ai_blocked(polite.parse_robots(self.TXT)))
        self.assertFalse(polite.ai_blocked(polite.parse_robots("User-agent: *\nDisallow: /x/\n")))
        self.assertTrue(polite.ai_blocked(polite.parse_robots("User-agent: anthropic-ai\nDisallow: /\n")))

    def test_empty_disallow_allows_everything(self):
        g = polite.parse_robots("User-agent: *\nDisallow:\n")
        self.assertTrue(polite.path_allowed(polite.rules_for(g), "/anything"))

    def test_own_group_wins(self):
        g = polite.parse_robots("User-agent: *\nDisallow: /\nUser-agent: FresnelBot\nAllow: /\n")
        self.assertTrue(polite.path_allowed(polite.rules_for(g), "/x"))


class FakeResp:
    def __init__(self, status, body=b"", headers=None):
        self.status = status
        self.headers = headers or {}
        self._b = io.BytesIO(body)

    def read(self, n=-1):
        return self._b.read(n)

    def close(self):
        pass


class FakeOpener:
    def __init__(self, script):
        self.script = list(script)
        self.urls = []

    def open(self, req, timeout=None):
        self.urls.append(req.full_url)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        if item.status >= 300:
            raise urllib.error.HTTPError(req.full_url, item.status, "x", item.headers, io.BytesIO(item._b.getvalue()))
        return item


class GetTests(unittest.TestCase):
    def setUp(self):
        self.raw = tempfile.mkdtemp()
        os.environ["FRESNEL_RAW_ROOT"] = self.raw
        polite._ROBOTS_MEMO.clear()
        self.c = FakeClock()

    def get(self, script, url="https://example.org/a", **kw):
        op = FakeOpener(script)
        kw.setdefault("robots", False)
        r = polite.get(url, opener=op, clock=self.c.time, sleep=self.c.sleep, **kw)
        return r, op

    def test_ok(self):
        r, op = self.get([FakeResp(200, b"hello")])
        self.assertEqual((r.status, r.body), (200, b"hello"))

    def test_404_is_returned_not_raised(self):
        r, _ = self.get([FakeResp(404, b"nope")])
        self.assertEqual(r.status, 404)

    def test_redirects_are_followed_and_each_hop_is_spaced(self):
        r, op = self.get([FakeResp(302, headers={"Location": "https://dn1.us.archive.org/x"}), FakeResp(200, b"data")],
                         url="https://archive.org/download/x/x_djvu.txt")
        self.assertEqual(r.body, b"data")
        self.assertEqual(op.urls, ["https://archive.org/download/x/x_djvu.txt", "https://dn1.us.archive.org/x"])
        self.assertGreaterEqual(sum(self.c.slept), 2.0)  # same site, so the second hop waited

    def test_timeouts_back_off_then_succeed(self):
        r, op = self.get([urllib.error.URLError("timed out"), FakeResp(200, b"ok")], backoff=(7.0,))
        self.assertEqual(r.body, b"ok")
        self.assertIn(7.0, self.c.slept)

    def test_gives_up_after_retries(self):
        with self.assertRaises(polite.NetworkError):
            self.get([urllib.error.URLError("timed out")] * 4, retries=2, backoff=(1.0, 2.0))

    def test_429_sets_a_shared_cooldown(self):
        r, op = self.get([FakeResp(429, headers={"Retry-After": "30"}), FakeResp(200, b"ok")], backoff=(1.0,))
        self.assertEqual(r.body, b"ok")
        self.assertGreaterEqual(sum(self.c.slept), 30.0)

    def test_robots_disallow_blocks_before_any_request(self):
        d = os.path.join(self.raw, "_robots")
        os.makedirs(d)
        with open(os.path.join(d, "example.org.txt"), "w") as fh:
            fh.write("User-agent: *\nDisallow: /private/\n")
        op = FakeOpener([])
        with self.assertRaises(polite.Blocked):
            polite.get("https://example.org/private/x", opener=op, clock=self.c.time, sleep=self.c.sleep)
        self.assertEqual(op.urls, [])

    def test_ai_crawler_rule_records_a_skip(self):
        d = os.path.join(self.raw, "_robots")
        os.makedirs(d)
        with open(os.path.join(d, "blocked.example.txt"), "w") as fh:
            fh.write("User-agent: ClaudeBot\nDisallow: /\n")
        with self.assertRaises(polite.Blocked):
            polite.get("https://blocked.example/x", opener=FakeOpener([]), clock=self.c.time, sleep=self.c.sleep)
        self.assertTrue(os.path.exists(os.path.join(d, "skipped.json")))

    def test_unreadable_robots_is_not_guessed(self):
        op = FakeOpener([urllib.error.URLError("timed out")] * 3)
        with self.assertRaises(polite.Blocked):
            polite.get("https://down.example/x", opener=op, clock=self.c.time, sleep=self.c.sleep)

    def test_stream_to_file(self):
        dest = os.path.join(self.raw, "out", "f.bin")
        r, _ = self.get([FakeResp(200, b"abc" * 100000)], dest=dest)
        self.assertIsNone(r.body)
        with open(dest, "rb") as fh:
            self.assertEqual(len(fh.read()), 300000)
        self.assertFalse(os.path.exists(dest + ".part"))


if __name__ == "__main__":
    unittest.main()
