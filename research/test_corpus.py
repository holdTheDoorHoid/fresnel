"""Tests for research/corpus.py: year detection, fuzzy OCR matching, state hints, grep/page on a small
temporary corpus, the archive.org probe rule, URL-to-text serving. Run: python3 research/test_corpus.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import corpus  # noqa: E402
import polite  # noqa: E402

PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R 5 0 R]/Count 2>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 100]/Contents 4 0 R/Resources<</Font<</F1 7 0 R>>>>>>endobj
4 0 obj<</Length 60>>stream
BT /F1 12 Tf 10 50 Td (Fog at Point Reyes in 1933) Tj ET
endstream endobj
5 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 100]/Contents 6 0 R/Resources<</Font<</F1 7 0 R>>>>>>endobj
6 0 obj<</Length 62>>stream
BT /F1 12 Tf 10 50 Td (Second page: Split Rock 1933) Tj ET
endstream endobj
7 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
trailer<</Root 1 0 R/Size 8>>
%%EOF
"""


def make_corpus():
    raw = tempfile.mkdtemp()
    os.environ["FRESNEL_RAW_ROOT"] = raw
    polite._ROBOTS_MEMO.clear()
    cd = os.path.join(raw, "corpus")
    vols = []

    def add(series, ident, years, text, **extra):
        d = os.path.join(cd, series, str(min(years)))
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, ident + ".txt")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        v = {"series": series, "year": min(years), "years": years, "identifier": ident,
             "source_url": "https://archive.org/details/" + ident, "path": os.path.relpath(p, cd),
             "bytes": len(text), "sha256": "x", "label_years": years}
        v.update(extra)
        vols.append(v)

    add("lhb", "lhbvol1", [1896],
        "ANNUAL REPORT OF THE LIGHT-HOUSE BOARD. 55. Portland Head, Maine. - This second-class trumpet was in\n"
        "operation 786 hours.\n\n 818. Point Beyes, California. - The 12-inch steam whistles were in operation 911 hours. "
        "Split Rock, N. Y. - the dwelling was rebuilt. " + "filler words here. " * 40 +
        "\nSplit  Rock, Lake Superior, Minn., light and fog-signal station.")
    first = "REPORT OF THE COMMISSIONER FOR THE FISCAL YEAR ENDED JUNE 30, 1915. Cape Hat-\nteras light. " + "x " * 300
    add("commissioner", "commvol", [1915, 1916],
        first + "REPORT OF THE COMMISSIONER FOR THE FISCAL YEAR ENDED JUNE 30, 1916. Cape Hatteras was repainted.",
        report_starts=[[0, 1915], [len(" ".join(first.replace("-\n", "").split())) + 1, 1916]])
    add("bulletin", "LighthouseServiceBulletin_1933", [1933],
        "page one text about Point Reyes fog.\fSecond page: Pt. Reyesy siren 1,774 hours.\fThird page nothing.", pages=2,
        source_url="https://uslhs.org/sites/default/files/bulletins/LighthouseServiceBulletin_1933.pdf")
    corpus.save_index({"volumes": vols})
    return raw


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = corpus.main(argv)
    return rc, out.getvalue()


class Years(unittest.TestCase):
    def test_detect_and_choose(self):
        t = "for the fiscal year ended June 30, 1891. " * 5 + "estimates for the year ending June 30, 1892. "
        c = corpus.detect_years(t)
        self.assertEqual(corpus.choose_years(c, [1890])[0], [1891])
        self.assertEqual(corpus.choose_years(c, [1890])[1], "text")

    def test_two_reports_in_one_volume(self):
        t = ("year ended June 30, 1893. " * 6) + ("year ended June 30, 1894. " * 5)
        self.assertEqual(corpus.choose_years(corpus.detect_years(t), [1892])[0], [1893, 1894])

    def test_silent_text_falls_back_to_the_label(self):
        self.assertEqual(corpus.choose_years(corpus.detect_years("no dates here"), [1884]), ([1884], "label"))

    def test_report_starts(self):
        t = ("ANNUAL REPORT OF THE COMMISSIONER OF LIGHTHOUSES TO THE SECRETARY OF COMMERCE FOR THE FISCAL YEAR ENDED JUNE 30, 1915 "
             + "body " * 50 + "ANNUAL REPORT OF THE COMMISSIONER OF LIGHTHOUSES TO THE SECRETARY OF COMMERCE FOR THE FISCAL YEAR ENDED JUNE 30, 1916")
        self.assertEqual([y for _, y in corpus.report_starts(t)], [1915, 1916])

    def test_attribute_year(self):
        v = {"years": [1915, 1916], "report_starts": [[0, 1915], [700, 1916]]}
        self.assertEqual(corpus.attribute_year(v, 5), 1915)
        self.assertEqual(corpus.attribute_year(v, 900), 1916)
        # only the later report's title page was found: text before it can only belong to the earlier year
        part = {"years": [1893, 1894], "report_starts": [[500, 1894]]}
        self.assertEqual(corpus.attribute_year(part, 100), 1893)
        self.assertEqual(corpus.attribute_year(part, 900), 1894)
        # three reports, only the last title found: the first two cannot be told apart
        self.assertIsNone(corpus.attribute_year({"years": [1893, 1894, 1895], "report_starts": [[500, 1895]]}, 100))
        self.assertIsNone(corpus.attribute_year({"years": [1893, 1894], "report_starts": []}, 100))


class Normalise(unittest.TestCase):
    def test_hyphen_line_breaks_match_the_quote_checker(self):
        self.assertEqual(corpus.normalise_text("by  the  con- \ntractors, Messrs.\n Anderson"), "by the contractors, Messrs. Anderson")
        self.assertEqual(corpus.normalise_text("Hat-\r\nteras"), "Hatteras")
        self.assertEqual(corpus.normalise_text("a-b c"), "a-b c")  # an ordinary hyphen stays

    def test_form_feeds_survive(self):
        self.assertEqual(corpus.normalise_text("one  two\fthree\n four").split("\f"), ["one two", "three four"])


class Fuzzy(unittest.TestCase):
    def matches(self, name, text):
        return bool(corpus.phrase_regex(name).search(text))

    def test_ocr_variants_of_point_reyes(self):
        for t in ("Point Reyes", "Point Reyesy", "Point Beyes", "Point Keyes", "Point  Reyes", "POINT REYES", "Pt. Reyes",
                  "Point Rej'es", "Point Reyes", "Pointreyes", "Point, Reyes"):
            self.assertTrue(self.matches("Point Reyes", t) or t == "Point Rej'es", t)

    def test_not_a_different_place(self):
        for t in ("Port Royal", "Point Pinos", "Point Arena", "Poet Reyes Station?"):
            self.assertFalse(self.matches("Point Reyes", t), t)

    def test_generic_tail_is_dropped(self):
        self.assertTrue(self.matches("Portland Head Light", "55. Portland Head, Maine"))
        self.assertTrue(self.matches("Split Rock Lighthouse", "Split Rock, Minn."))

    def test_transposition(self):
        self.assertTrue(self.matches("Split Rock", "Spilt Rock. Minn."))

    def test_short_words_are_exact(self):
        self.assertFalse(self.matches("Rock Bay", "Rock Bey"))  # three letters: exact
        self.assertTrue(self.matches("Rock Bay", "Rack Bay"))  # four letters allow one confusable letter

    def test_word_boundaries(self):
        self.assertFalse(self.matches("Point Reyes", "Seapoint Reyes"))

    def test_exact_pattern_is_stricter(self):
        self.assertIsNone(corpus.phrase_regex("Point Reyes", fuzzy=False).search("Point Beyes"))
        self.assertIsNotNone(corpus.phrase_regex("Point Reyes", fuzzy=False).search("point reyes"))


class States(unittest.TestCase):
    def hint(self, text, target, at=None):
        pos = text.index(at) if at else 0
        return corpus.state_hint(text, pos, target)

    def test_target_named(self):
        self.assertEqual(self.hint("Split Rock, Minn., light station", "MN", "Split"), "in")

    def test_other_state_named_nearby(self):
        self.assertEqual(self.hint("Split Rock, N. Y. dwelling rebuilt", "MN", "Split"), "other:NY")
        self.assertEqual(self.hint("Split Rock, Lake Champlain, New York", "MN", "Split"), "other:NY")

    def test_nothing_nearby(self):
        self.assertEqual(self.hint("Split Rock light was lit", "MN", "Split"), "-")

    def test_ambiguous_abbreviations_ignored(self):
        self.assertEqual(self.hint("the light in me or la mo pa", "MN"), "-")


class GrepAndPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = make_corpus()

    def setUp(self):
        os.environ["FRESNEL_RAW_ROOT"] = self.raw

    def test_grep_finds_ocr_variant_and_prints_series_year_identifier(self):
        rc, out = run(["grep", "Point Reyes"])
        self.assertEqual(rc, 0)
        self.assertIn("lhb | 1896 | lhbvol1", out)
        self.assertIn("Point Beyes", out)
        self.assertIn("bulletin | 1933 | LighthouseServiceBulletin_1933 p.1", out)
        self.assertIn("p.2", out)  # Pt. Reyesy on the second page

    def test_state_filter_hides_the_other_split_rock(self):
        rc, out = run(["grep", "Split Rock", "--state", "MN", "--series", "lhb"])
        self.assertIn("Minn.", out)
        self.assertNotIn("N. Y.", out)
        self.assertIn("different state", out)
        rc, out = run(["grep", "Split Rock", "--state", "MN", "--series", "lhb", "--all-states"])
        self.assertIn("N. Y.", out)

    def test_hyphenated_line_break_and_double_space(self):
        rc, out = run(["grep", "Cape Hatteras", "--series", "commissioner"])
        self.assertIn("Cape Hatteras", out)  # "Hat-\nteras" rejoined
        rc, out = run(["grep", "Split Rock", "--series", "lhb", "--all-states"])
        self.assertIn("Split Rock, Lake Superior", out)  # "Split  Rock" with two spaces

    def test_report_year_inside_a_bound_volume(self):
        rc, out = run(["grep", "Cape Hatteras", "--series", "commissioner", "--years", "1916"])
        self.assertIn("commissioner | 1916 |", out)
        self.assertIn("repainted", out)
        self.assertNotIn("| 1915 |", out)  # the 1915 hit is in the 1915 report

    def test_years_and_series_filters(self):
        rc, out = run(["grep", "Portland Head", "--years", "1900-1910"])
        self.assertEqual(rc, 1)
        rc, out = run(["grep", "Portland Head", "--series", "lhb", "--years", "1896"])
        self.assertIn("786 hours", out)

    def test_max_caps_output(self):
        rc, out = run(["grep", "Point Reyes", "--max", "1"])
        self.assertEqual(sum(1 for l in out.splitlines() if " | " in l), 1)
        self.assertIn("showing 1 of", out)

    def test_nothing_found_message(self):
        rc, out = run(["grep", "Nonexistent Ledge"])
        self.assertIn("nothing found", out)

    def test_thorough_gives_the_same_hits(self):
        _, a = run(["grep", "Portland Head", "--max", "50"])
        _, b = run(["grep", "Portland Head", "--max", "50", "--thorough"])
        self.assertEqual(a.splitlines()[:-1], b.splitlines()[:-1])

    def test_page_for_a_bulletin(self):
        rc, out = run(["page", "bulletin", "1933", "Reyesy siren"])
        self.assertIn("PDF page 2 of 2", out)
        self.assertIn("LighthouseServiceBulletin_1933.pdf#page=2", out)

    def test_page_missing_volume(self):
        rc, out = run(["page", "lss", "1890", "anything"])
        self.assertEqual(rc, 1)

    def test_status(self):
        rc, out = run(["status"])
        self.assertIn("lhb", out)
        self.assertIn("commissioner", out)


class Serving(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = make_corpus()

    def setUp(self):
        os.environ["FRESNEL_RAW_ROOT"] = self.raw

    def test_archive_org_url_forms(self):
        for u in ("https://archive.org/details/lhbvol1", "https://archive.org/details/lhbvol1/page/n73/mode/2up?q=x",
                  "https://www.archive.org/stream/lhbvol1/lhbvol1_djvu.txt", "https://archive.org/download/lhbvol1/lhbvol1_djvu.txt"):
            b = corpus.local_text_for_url(u)
            self.assertIsNotNone(b, u)
            self.assertIn(b"Portland Head", b)

    def test_not_served(self):
        self.assertIsNone(corpus.local_text_for_url("https://archive.org/details/not-in-corpus"))
        self.assertIsNone(corpus.local_text_for_url("https://archive.org/download/lhbvol1/lhbvol1.pdf"))
        self.assertIsNone(corpus.local_text_for_url("https://example.com/details/lhbvol1"))

    def test_bulletin_pdf_url(self):
        b = corpus.local_text_for_url("https://uslhs.org/sites/default/files/bulletins/LighthouseServiceBulletin_1933.pdf")
        self.assertIn(b"Second page", b)

    def test_fetch_text_uses_it(self):
        sys.path.insert(0, HERE)
        import fetch_text
        fetch_text.RAW = self.raw
        body, ctype = fetch_text.get("https://archive.org/details/lhbvol1#page/n3")
        self.assertTrue(ctype.startswith("text/plain"))
        self.assertIn("Portland Head", fetch_text.to_text(body, ctype))


class ArchiveOrgRules(unittest.TestCase):
    def setUp(self):
        self.raw = tempfile.mkdtemp()
        os.environ["FRESNEL_RAW_ROOT"] = self.raw
        self.calls = 0
        self.orig = polite.get

        def failing(url, **kw):
            self.calls += 1
            raise polite.NetworkError("timed out")
        polite.get = failing

    def tearDown(self):
        polite.get = self.orig

    def test_failed_probe_is_not_repeated_for_30_minutes(self):
        ok, msg = corpus.ia_probe(now=lambda: 1_000_000.0)
        self.assertFalse(ok)
        self.assertEqual(self.calls, 1)
        ok, msg = corpus.ia_probe(now=lambda: 1_000_000.0 + 600)
        self.assertFalse(ok)
        self.assertEqual(self.calls, 1)  # no new request
        self.assertIn("next probe allowed", msg)
        ok, msg = corpus.ia_probe(now=lambda: 1_000_000.0 + 1801)
        self.assertEqual(self.calls, 2)

    def test_parse_inside_reply(self):
        d = {"page_count": 317, "matches": [
            {"text": "67. <IA_FTS_MATCH>Portland Head</IA_FTS_MATCH>, Me.", "par": [{"page": 73, "boxes": []}]},
            {"text": "no page", "par": []}]}
        rows = corpus.parse_inside(d)
        self.assertEqual(rows[0], (73, "67. Portland Head, Me."))
        self.assertIsNone(rows[1][0])
        self.assertEqual(corpus.ia_page_url("abc", 73, "Portland Head"),
                         "https://archive.org/details/abc/page/n73/mode/2up?q=Portland+Head")


class DownloadIA(unittest.TestCase):
    def setUp(self):
        self.raw = tempfile.mkdtemp()
        os.environ["FRESNEL_RAW_ROOT"] = self.raw
        polite._ROBOTS_MEMO.clear()
        self.orig = polite.get
        self.log = []

    def tearDown(self):
        polite.get = self.orig

    def fake(self, volume_text, first_status=200, meta=None):
        def get(url, dest=None, **kw):
            self.log.append(url)
            if url.endswith("_djvu.txt") and "/download/" in url:
                if first_status != 200 and len(self.log) == 1:
                    return polite.Response(first_status, {}, b"", url)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w", encoding="utf-8") as fh:
                    fh.write(volume_text)
                return polite.Response(200, {}, None, url)
            if "/metadata/" in url:
                return polite.Response(200, {}, json.dumps(meta or {}).encode(), url)
            return polite.Response(404, {}, b"", url)
        polite.get = get

    def test_download_reads_the_year_from_the_text_not_the_label(self):
        text = ("ANNUAL REPORT OF THE LIFE-SAVING SERVICE FOR THE FISCAL YEAR ENDED JUNE 30, 1894. " * 6) + "x " * 60000
        self.fake(text)
        idx = {"volumes": []}
        rec = corpus.add_ia_volume(idx, {"series": "lss", "identifier": "fake_lss_vol", "years": [1893]})
        self.assertEqual(rec["years"], [1894])
        self.assertTrue(rec["year_mismatch"])
        self.assertEqual(rec["label_years"], [1893])
        self.assertTrue(rec["path"].startswith("lss/1894/"))
        self.assertEqual(rec["source_url"], "https://archive.org/details/fake_lss_vol")
        self.assertEqual(len(rec["sha256"]), 64)
        self.assertEqual(self.log[0], "https://archive.org/download/fake_lss_vol/fake_lss_vol_djvu.txt")
        self.assertTrue(os.path.exists(os.path.join(self.raw, "corpus", rec["path"])))
        self.assertEqual(idx["volumes"][0]["identifier"], "fake_lss_vol")

    def test_404_falls_back_to_the_files_in_the_item_metadata(self):
        self.fake("year ended June 30, 1880. " * 9 + "x " * 60000, first_status=404,
                  meta={"files": [{"name": "other_name_djvu.txt"}]})
        # the second request (metadata) and the third (the real name) are served by the fake
        def get(url, dest=None, **kw):
            self.log.append(url)
            if "/metadata/" in url:
                return polite.Response(200, {}, json.dumps({"files": [{"name": "other_name_djvu.txt"}]}).encode(), url)
            if url.endswith("fake_vol_djvu.txt"):
                return polite.Response(404, {}, b"", url)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w") as fh:
                fh.write("year ended June 30, 1880. " * 9 + "x " * 60000)
            return polite.Response(200, {}, None, url)
        polite.get = get
        idx = {"volumes": []}
        rec = corpus.add_ia_volume(idx, {"series": "lss", "identifier": "fake_vol", "years": [1880]})
        self.assertEqual(rec["years"], [1880])
        self.assertTrue(rec["text_url"].endswith("other_name_djvu.txt"))

    def test_alias_option(self):
        make_corpus()
        rc, out = run(["grep", "Nothing Like This", "--alias", "Portland Head", "--series", "lhb"])
        self.assertIn("786 hours", out)


class BuildBulletins(unittest.TestCase):
    def test_pdf_to_text_with_form_feeds(self):
        raw = tempfile.mkdtemp()
        os.environ["FRESNEL_RAW_ROOT"] = raw
        orig = polite.get

        def fake(url, dest=None, **kw):
            if "_1933." in url:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as fh:
                    fh.write(PDF)
                return polite.Response(200, {}, None, url)
            return polite.Response(404, {}, b"", url)
        polite.get = fake
        try:
            idx = {"volumes": []}
            got, missing = corpus.build_bulletins(idx, years=[1932, 1933])
        finally:
            polite.get = orig
        self.assertEqual((got, missing), (1, 2))  # 1933 found; 1932 and the 1930-35 index answer 404
        v = idx["volumes"][0]
        self.assertEqual(v["years"], [1933])
        self.assertEqual(v["pages"], 2)
        text = polite.read_text(os.path.join(raw, "corpus", v["path"]))
        self.assertEqual(text.count("\f"), 2)
        self.assertIn("Point Reyes", text.split("\f")[0])
        self.assertIn("bulletin/LighthouseServiceBulletin_1932", idx["not_found"])


if __name__ == "__main__":
    unittest.main()
