#!/usr/bin/env python3
"""Chronicling America (Library of Congress) through the loc.gov JSON API, for research agents.

  research/newspapers.py "Point Reyes" ["Joshua Strout" ...] [--with "lighthouse keeper"] [--years 1880-1910]
                         [--state CA] [--max 10] [--results-page 2] [--snippets N]
  research/newspapers.py --page <page URL from a hit> --grep "wreck|keeper" [--context 2] [--max 4000]

Each phrase is searched as an exact quoted phrase and all of them must be on the page; --with adds loose words
(use it to separate a station from a town of the same name: --with lighthouse). --state limits to papers
printed in that state. A hit is a newspaper PAGE: the date, paper, page number and URL. The search reply
carries only the first characters of each page's text, so read a page with `--page URL --grep WORDS`
(that fetches the page's OCR text once and keeps it), or ask for --snippets N to read the first N hits
(one request each).

Rate limits (loc.gov "Working Within Limits"): the JSON API allows 20 requests a minute and blocks a machine
for an hour after a breach. Every process on this machine shares one lock: at least 5 s between requests,
at most 20 a minute, and on HTTP 429/503 a shared cooldown that stops all of them. Every response is cached
under $FRESNEL_RAW_ROOT/newspapers/, so repeating a search costs nothing. Searches take 5 to 60 s: be patient.
Only the JSON API and the OCR text service are used, never the Cloudflare-protected HTML pages.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polite  # noqa: E402

API = "https://www.loc.gov/collections/chronicling-america/"
PER_MINUTE = 20
GAP = 5.0


def cache_dir():
    return os.path.join(polite.raw_root(), "newspapers")


def log(msg):
    print(time.strftime("%H:%M:%S ") + msg, file=sys.stderr, flush=True)


def loc_get(url, **kw):
    """One request to loc.gov under the shared lock (5 s apart, 20 a minute, cooldown on 429/503)."""
    kw.setdefault("timeout", 120)
    kw.setdefault("retries", 2)
    kw.setdefault("backoff", (30.0, 90.0))
    return polite.get(url, gap=GAP, per_minute=PER_MINUTE, log=log, **kw)


def cached(url, path, validate=None):
    """-> (bytes, from_cache). Cache every 200 response that validates."""
    if os.path.exists(path):
        return polite.read_bytes(path), True
    r = loc_get(url)
    if r.status != 200:
        raise polite.PoliteError("HTTP %d for %s" % (r.status, url))
    if validate and not validate(r.body):
        raise polite.PoliteError("unexpected reply from %s" % url)
    if b'"of":0' in r.body.replace(b" ", b"")[:3000]:
        return r.body, False  # an empty result is not cached: the API has answered "0" wrongly under load
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp%d" % os.getpid()
    with open(tmp, "wb") as fh:
        fh.write(r.body)
    os.replace(tmp, path)
    return r.body, False


# --------------------------------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------------------------------

def state_name(code):
    import roster
    if not code:
        return None
    n = roster.CODE_NAMES.get(code.upper())
    return (n or code).lower()


def build_query(phrases, with_words=None):
    parts = ['"%s"' % p.strip().replace('"', "") for p in phrases if p.strip()]
    if with_words:
        parts.append(with_words.strip())
    return " ".join(parts)


def search_url(phrases, with_words=None, years=None, state=None, count=10, page=1):
    p = [("q", build_query(phrases, with_words)), ("fo", "json"), ("c", str(count)), ("at", "results,pagination")]
    if years:
        p.append(("dates", "%d/%d" % years))
    if state:
        p.append(("fa", "location_state:" + state_name(state)))
    if page and page > 1:
        p.append(("sp", str(page)))
    return API + "?" + urllib.parse.urlencode(p)


def parse_years(s):
    if not s:
        return None
    m = re.match(r"^\s*(\d{4})\s*(?:[-/:]\s*(\d{4}))?\s*$", s)
    if not m:
        sys.exit("--years wants 1895 or 1880-1910")
    return int(m.group(1)), int(m.group(2) or m.group(1))


def parse_results(data):
    """loc.gov reply -> (total hits, [hit dicts])."""
    pag = data.get("pagination") or {}
    out = []
    for r in data.get("results", []):
        title = r.get("title") or ""
        m = re.match(r"^Image (\d+) of (.*), ([A-Z][a-z]+ \d{1,2}, \d{4})\s*$", title)
        paper = m.group(2) if m else re.sub(r"^Image \d+ of ", "", title)
        page_no = m.group(1) if m else ((r.get("number_page") or [""])[0].lstrip("0") or None)
        url = r.get("id") or r.get("url") or ""
        url = re.sub(r"^http://", "https://", url.split("&q=")[0])
        alto = r.get("word_coordinates_url")
        iiif = next((u for u in r.get("image_url", []) if "iiif/service:ndnp" in u), None)
        if iiif:
            sid = re.search(r"service:ndnp:([^/]+)/", iiif)
            if sid:
                alto = "https://tile.loc.gov/storage-services/service/ndnp/" + sid.group(1).replace(":", "/") + ".xml"
        desc = r.get("description")
        desc = desc[0] if isinstance(desc, list) and desc else (desc or "")
        out.append({"date": r.get("date"), "paper": paper, "page": page_no, "url": url, "alto": alto,
                    "lccn": ((r.get("number_lccn") or [""])[0]), "state": ", ".join(r.get("location_state") or []),
                    "starts": re.sub(r"\s+", " ", desc)[:140]})
    return pag.get("of"), out


def remember_pages(hits):
    """page URL -> ALTO URL, so --page can find a page's OCR without another lookup."""
    path = os.path.join(cache_dir(), "pages.json")
    try:
        d = polite.read_json(path)
    except (OSError, ValueError):
        d = {}
    for h in hits:
        if h["url"] and h["alto"]:
            d[h["url"]] = {"alto": h["alto"], "paper": h["paper"], "date": h["date"], "page": h["page"]}
    os.makedirs(cache_dir(), exist_ok=True)
    tmp = path + ".tmp%d" % os.getpid()
    polite.write_json(tmp, d)
    os.replace(tmp, path)


def do_search(a):
    phrases = a.phrases
    years = parse_years(a.years)
    url = search_url(phrases, a.with_words, years, a.state, a.fetch, a.results_page)
    path = os.path.join(cache_dir(), "search", hashlib.sha1(url.encode()).hexdigest() + ".json")
    body, hit = cached(url, path, lambda b: b"pagination" in b or b"results" in b)
    data = json.loads(body)
    total, hits = parse_results(data)
    remember_pages(hits)
    q = build_query(phrases, a.with_words)
    print("Chronicling America: %s hit page(s) for %s%s%s%s" % (
        total if total is not None else "?", q, " in %d-%d" % years if years else "",
        " (papers printed in %s)" % a.state.upper() if a.state else "", " [cached]" if hit else ""))
    for i, h in enumerate(hits[: a.max], 1):
        print("[%d] %s | %s | p.%s | %s" % (i, h["date"], h["paper"], h["page"], h["url"]))
        if h["starts"] and not a.snippets:
            print("      page begins: %s" % h["starts"])
    if a.snippets:
        words = [re.escape(p) for p in phrases]
        for i, h in enumerate(hits[: min(a.snippets, a.max)], 1):
            print("--- [%d] %s p.%s: lines mentioning the search" % (i, h["date"], h["page"]))
            try:
                text = page_text(h["url"])
                for ln in grep_lines(text, "|".join(words), 1)[:12]:
                    print("    " + ln)
            except polite.PoliteError as e:
                print("    (could not read this page: %s)" % e)
    if total and total > len(hits):
        print("[%s total; %d fetched this call. More: --results-page %d, or narrow with --years/--state/--with]"
              % (total, len(hits), (a.results_page or 1) + 1))
    return 0


# --------------------------------------------------------------------------------------------------
# Page text
# --------------------------------------------------------------------------------------------------

def alto_to_text(xml_bytes):
    """ALTO XML -> text, one line per text line (hyphenated line ends rejoined)."""
    root = ET.fromstring(xml_bytes)
    lines = []
    for el in root.iter():
        if el.tag.endswith("}TextLine") or el.tag == "TextLine":
            words = []
            for s in el:
                if s.tag.endswith("}String") or s.tag == "String":
                    sub = s.get("SUBS_CONTENT")
                    typ = s.get("SUBS_TYPE")
                    if sub and typ == "HypPart1":
                        words.append(sub)  # the whole word, once
                    elif sub and typ == "HypPart2":
                        continue
                    else:
                        words.append(s.get("CONTENT") or "")
            lines.append(" ".join(w for w in words if w))
    return "\n".join(lines)


def find_alto(url):
    """The ALTO text URL for a loc.gov page URL (from a search we ran, else from the page's JSON record)."""
    url = re.sub(r"^http://", "https://", url.split("&q=")[0].split("#")[0])
    try:
        d = polite.read_json(os.path.join(cache_dir(), "pages.json"))
    except (OSError, ValueError):
        d = {}
    if url in d:
        return d[url]["alto"], d[url]
    if "tile.loc.gov/storage-services" in url and url.endswith(".xml"):
        return url, {}
    m = re.match(r"^https://www\.loc\.gov/resource/([^/]+)/(\d{4}-\d{2}-\d{2})/(ed-\d+)/\?sp=(\d+)", url)
    if not m:
        raise polite.PoliteError("not a Chronicling America page URL (use the URL a search printed): " + url)
    # not seen in a search: ask for the page's record (one request)
    jurl = "https://www.loc.gov/resource/%s/%s/%s/?sp=%s&fo=json&at=page,resources" % m.groups()
    path = os.path.join(cache_dir(), "record", hashlib.sha1(jurl.encode()).hexdigest() + ".json")
    body, _ = cached(jurl, path)
    rec = json.loads(body)
    blob = json.dumps(rec)
    sid = re.search(r"service:ndnp:([^/\"?#]+?)(?:/|\\\\u002f|\"|:\d+/full)", blob)
    mm = re.search(r"/service/ndnp/([A-Za-z0-9_/\-\.]+?\.xml)", blob)
    if mm:
        return "https://tile.loc.gov/storage-services/service/ndnp/" + mm.group(1), {}
    if sid:
        return "https://tile.loc.gov/storage-services/service/ndnp/" + sid.group(1).replace(":", "/") + ".xml", {}
    raise polite.PoliteError("could not find the OCR file for " + url)


def page_text(url):
    alto, meta = find_alto(url)
    path = os.path.join(cache_dir(), "alto", hashlib.sha1(alto.encode()).hexdigest() + ".xml")
    body, _ = cached(alto, path, lambda b: b"<alto" in b[:2000] or b"<?xml" in b[:100])
    return alto_to_text(body)


def grep_lines(text, rx, context):
    """Lines of `text` within `context` lines of a regex match. The match runs over the text with line breaks
    as spaces, so a phrase broken across two lines ("Point / Reyes") still counts."""
    lines = text.splitlines()
    joined, owner = [], []
    for i, l in enumerate(lines):
        joined.append(l + " ")
        owner.extend([i] * (len(l) + 1))
    flat = "".join(joined)
    pat = re.compile(rx, re.I)
    keep = set()
    for m in pat.finditer(flat):
        first = owner[min(m.start(), len(owner) - 1)]
        last = owner[min(max(m.end() - 1, m.start()), len(owner) - 1)]
        keep.update(range(max(0, first - context), min(len(lines), last + context + 1)))
    out, prev = [], None
    for i in sorted(keep):
        if prev is not None and i != prev + 1:
            out.append("...")
        out.append(lines[i])
        prev = i
    return out


def local_text_for_url(url):
    """OCR text of a newspaper page we have already read (so check_quotes can verify quotes cited to its
    loc.gov URL without touching the Cloudflare-protected HTML page), else None."""
    url = re.sub(r"^http://", "https://", url.split("&q=")[0].split("#")[0])
    try:
        d = polite.read_json(os.path.join(cache_dir(), "pages.json"))
    except (OSError, ValueError):
        return None
    rec = d.get(url)
    if not rec:
        return None
    path = os.path.join(cache_dir(), "alto", hashlib.sha1(rec["alto"].encode()).hexdigest() + ".xml")
    if not os.path.exists(path):
        return None
    return alto_to_text(polite.read_bytes(path))


def do_page(a):
    try:
        text = page_text(a.page)
    except polite.PoliteError as e:
        print("ERROR: %s" % e)
        return 1
    _, meta = find_alto(a.page)
    head = "%s | %s | p.%s | %s" % (meta.get("date", ""), meta.get("paper", ""), meta.get("page", ""), a.page) \
        if meta else a.page
    if a.grep:
        out = "\n".join(grep_lines(text, a.grep, a.context)) or "(no matching lines)"
    else:
        out = text
    print("[%s]\n[%d chars of OCR text; showing %d]" % (head, len(text), min(len(out), a.max_chars)))
    print(out[: a.max_chars])
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phrases", nargs="*", help="exact phrases; all must appear on the page")
    ap.add_argument("--with", dest="with_words", help="extra loose words, e.g. lighthouse")
    ap.add_argument("--years", help="1895 or 1880-1910")
    ap.add_argument("--state", help="two-letter code: papers printed in that state")
    ap.add_argument("--max", type=int, default=10, help="hits to print (default 10)")
    ap.add_argument("--fetch", type=int, default=20, help="hits to request from the API per call (default 20)")
    ap.add_argument("--results-page", type=int, default=1, help="page of results")
    ap.add_argument("--snippets", type=int, default=0, metavar="N",
                    help="also read the first N hit pages and print their lines that mention the phrases (1 request each)")
    ap.add_argument("--page", help="a page URL printed by a search: print its OCR text")
    ap.add_argument("--grep", help="with --page: regex; only matching lines")
    ap.add_argument("--context", type=int, default=2, help="with --grep: lines of context")
    ap.add_argument("--max-chars", type=int, default=4000, help="with --page: output cap")
    a = ap.parse_args(argv)
    try:
        if a.page:
            return do_page(a)
        if not a.phrases:
            ap.print_help()
            return 1
        return do_search(a)
    except polite.RateLimited as e:
        print("loc.gov is rate-limiting us: %s. Stop searching and report; nothing was lost (responses are cached)." % e)
        return 3
    except polite.PoliteError as e:
        print("ERROR: %s" % e)
        return 1


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `| head` must not print a traceback
    sys.exit(main())
