#!/usr/bin/env python3
"""The local text corpus of the official reports, for research agents.

  research/corpus.py grep "<station name>" [--alias "<OCR or old spelling>" ...] [--state XX]
                     [--series lss,lhb,commissioner,bulletin,marine_ca] [--years 1880-1900] [--max 20]
  research/corpus.py page <series> <year> "<phrase>"     the page for a phrase, and the URL to cite
  research/corpus.py cite <identifier | bulletin year>    the URL to cite (so check_quotes.py can find the text)
  research/corpus.py status                               what is in the corpus, what is missing, archive.org state
  research/corpus.py build [--series ...] [--wait]        download / extend the corpus (slow, resumable)
  research/corpus.py discover "<archive.org query>"       list archive.org items (to extend the catalog)

Series: lss = US Life-Saving Service annual reports; lhb = Lighthouse Board annual reports;
commissioner = Commissioner of Lighthouses annual reports; bulletin = Lighthouse Service Bulletin;
marine_ca = Canada, Department of Marine (and Fisheries) annual reports.

Files live under $FRESNEL_RAW_ROOT/corpus/<series>/<year>/ (default <repo>/data/raw/corpus), with
corpus_index.json (series, fiscal year, identifier, source URL, size, sha256). Every volume's year is
read from its own text; the archive's metadata year is only the label (the survey found mislabelled years).

The OCR is poor, so `grep` matches fuzzily: the name's letters may be confused (e/o/c, l/1/i, n/u/h ...),
one letter may be wrong, missing or extra, and the words may be run together. Give aliases for spellings
you have seen. The plain text has no page breaks, except the Bulletin PDFs (form feeds); `page` asks the
Internet Archive's in-item search for the scan page of archive.org volumes.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polite  # noqa: E402

SERIES = {
    "lss": "US Life-Saving Service annual report",
    "lhb": "Lighthouse Board annual report",
    "commissioner": "Commissioner of Lighthouses annual report",
    "bulletin": "Lighthouse Service Bulletin",
    "marine_ca": "Canada, Department of Marine annual report",
}
IA = "https://archive.org"
BULLETIN_YEARS = range(1912, 1940)
PROBE_WAIT = 1800  # seconds between archive.org probes after a failed one
CATALOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus_catalog.json")


def corpus_dir():
    return os.path.join(polite.raw_root(), "corpus")


def index_file():
    return os.path.join(corpus_dir(), "corpus_index.json")


def log(msg):
    print(time.strftime("%H:%M:%S ") + msg, flush=True)


# --------------------------------------------------------------------------------------------------
# Index
# --------------------------------------------------------------------------------------------------

def load_index():
    try:
        return polite.read_json(index_file())
    except (OSError, ValueError):
        return {"volumes": []}


def save_index(idx):
    os.makedirs(corpus_dir(), exist_ok=True)
    idx["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    idx["volumes"].sort(key=lambda v: (v["series"], v["year"], v["identifier"]))
    tmp = index_file() + ".tmp%d" % os.getpid()
    polite.write_json(tmp, idx, indent=1)
    os.replace(tmp, index_file())


def update_index(idx, fn):
    """Apply fn(index) to the index file as it is on disk right now (under a lock, so several processes can
    extend the corpus at once without overwriting each other), then refresh the caller's in-memory copy."""
    import fcntl
    os.makedirs(corpus_dir(), exist_ok=True)
    with open(index_file() + ".lock", "a+") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        disk = load_index()
        fn(disk)
        save_index(disk)
    idx.clear()
    idx.update(disk)


def upsert_volume(idx, rec):
    def fn(d):
        d["volumes"] = [v for v in d["volumes"] if not (v["series"] == rec["series"] and v["identifier"] == rec["identifier"])]
        d["volumes"].append(rec)
        d.get("failed", {}).pop(rec["identifier"], None)
    update_index(idx, fn)


def indexed(idx, series, identifier):
    return any(v["series"] == series and v["identifier"] == identifier for v in idx["volumes"])


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------------------------------
# Reading the year from the text itself
# --------------------------------------------------------------------------------------------------

YEAR_PATTERNS = [
    r"(?:fiscal\s+)?year\s+(?:ending|ended)[^0-9]{0,40}?(1[89]\d\d)",
    r"(?:ending|ended)\s+(?:on\s+)?(?:the\s+)?(?:30(?:th)?\s+)?June[,.\s]{0,5}(?:30[,.\s]{0,4})?(1[89]\d\d)",
    r"June\s+30,?\s*(1[89]\d\d)",
    r"30(?:th)?\s+June,?\s*(1[89]\d\d)",
]


def detect_years(head, lo=1850, hi=1940):
    """Fiscal years named in the front of a report -> Counter({year: mentions})."""
    t = re.sub(r"\s+", " ", head)
    c = Counter()
    for pat in YEAR_PATTERNS:
        for m in re.finditer(pat, t, re.I):
            y = int(m.group(1))
            if lo <= y <= hi:
                c[y] += 1
    return c


def choose_years(counts, label_years):
    """The year(s) a volume covers, from its own text. Falls back to the label when the text is silent.
    -> (years, source) where source is 'text' or 'label'."""
    if not counts:
        return sorted(label_years), "label"
    top = max(counts.values())
    years = sorted(y for y, n in counts.items() if n >= max(2, 0.3 * top) or (top == 1 and n == 1))
    return (years or sorted(label_years)), "text"


TITLE_RX = re.compile(r"(?:annual\s+)?report\s+of\s+the\s+(?:commissioner|light[\s-]*house\s+board|chief|general|"
                      r"superintendent|department|minister|life[\s-]*saving)[^.]{0,200}?(?:fiscal\s+)?year\s+"
                      r"(?:ending|ended)\s+(?:on\s+)?(?:the\s+)?(?:(?:30(?:th)?\s+)?June\s*(?:30(?:th)?)?[,.\s]*|[^0-9]{0,30}?)"
                      r"(1[89]\d\d)", re.I)


def report_starts(text):
    """Where each annual report's title page sits in a (normalised) volume: [[offset, year], ...]. A bound
    volume can hold several reports (the Commissioner volume holds fiscal 1915 to 1922)."""
    first = {}
    for m in TITLE_RX.finditer(text):
        y = int(m.group(1))
        if 1850 <= y <= 1940 and y not in first:
            first[y] = m.start()
    return sorted([off, y] for y, off in first.items())


def attribute_year(v, pos):
    """The fiscal year of the report that holds text offset `pos` in volume v, from the title pages found in it:
    the years the volume covers, minus those that start after `pos`, minus those before the last title page
    before `pos`. None when that leaves more than one year (then the caller shows the volume's whole range)."""
    years = sorted(v["years"])
    if len(years) < 2:
        return years[0] if years else None
    starts = sorted(v.get("report_starts") or [])
    cur = max((y for off, y in starts if off <= pos), default=None)
    nxt = min((y for off, y in starts if off > pos), default=None)
    cand = [y for y in years if (cur is None or y >= cur) and (nxt is None or y < nxt)]
    return cand[0] if len(cand) == 1 else None


def bulletin_year_counts(text):
    return Counter(int(y) for y in re.findall(r"\b(19[1-4]\d)\b", text))


# --------------------------------------------------------------------------------------------------
# Catalog of known volumes
# --------------------------------------------------------------------------------------------------

def load_catalog():
    try:
        return polite.read_json(CATALOG_FILE)["items"]
    except (OSError, ValueError, KeyError):
        return []


def volume_record(series, identifier, years, source_url, path, label_years, counts, source, extra=None):
    rec = {
        "series": series, "year": min(years), "years": years, "identifier": identifier, "source_url": source_url,
        "path": os.path.relpath(path, corpus_dir()), "bytes": os.path.getsize(path), "sha256": sha256_file(path),
        "label_years": sorted(label_years), "year_source": source,
        "year_counts": {str(k): v for k, v in counts.most_common(4)},
        "year_mismatch": bool(label_years) and sorted(label_years) != sorted(years) and source == "text",
        "fetched": time.strftime("%Y-%m-%d"),
    }
    rec.update(extra or {})
    return rec


# --------------------------------------------------------------------------------------------------
# Bulletin PDFs from uslhs.org
# --------------------------------------------------------------------------------------------------

def pdftotext(pdf, out):
    p = subprocess.run(["pdftotext", pdf, out], capture_output=True, timeout=300)  # plain mode, form feeds kept
    if p.returncode != 0:
        raise RuntimeError("pdftotext failed: " + p.stderr.decode("utf-8", "replace")[:200])


def bulletin_files():
    """The Lighthouse Service Bulletin files on https://uslhs.org/resources/bulletins (checked 2026-10-21):
    [(identifier, years, file name, [older names that serve the same file])]."""
    out = []
    odd = {1913: "LighthouseServiceBulletin_1913_0.pdf", 1925: "Lighthouse Service Bulletins 1925.pdf",
           1936: "LighthouseServiceBulletin_1936_0.pdf"}
    for y in BULLETIN_YEARS:
        name = odd.get(y, "LighthouseServiceBulletin_%d.pdf" % y)
        out.append(("LighthouseServiceBulletin_%d" % y, [y], name,
                    ["LighthouseServiceBulletin_%d.pdf" % y] if name != "LighthouseServiceBulletin_%d.pdf" % y else []))
    for a, b, name in ((1912, 1917, "Index to volume 1.pdf"), (1918, 1923, "1918_1923_Index.pdf"),
                       (1924, 1929, "1924_1929_Index.pdf"), (1930, 1935, "1930_1935_Index.pdf"),
                       (1936, 1939, "1936_1939_Index.pdf")):
        out.append(("LighthouseServiceBulletin_Index_%d-%d" % (a, b), list(range(a, b + 1)), name, []))
    return out


def bulletin_url(name):
    return "https://uslhs.org/sites/default/files/bulletins/" + urllib.parse.quote(name)


def build_bulletins(idx, years=BULLETIN_YEARS):
    got = missing = 0
    for ident, yrs, name, aliases in bulletin_files():
        if not (set(yrs) & set(years)) or indexed(idx, "bulletin", ident):
            continue
        is_index = "_Index_" in ident
        url = bulletin_url(name)
        pdf = os.path.join(corpus_dir(), "_pdf", "bulletin", ident.replace("LighthouseServiceBulletin_", "") + ".pdf")
        if not os.path.exists(pdf):
            try:
                r = polite.get(url, dest=pdf, timeout=120, log=log)
            except polite.Blocked as e:
                log("BLOCKED: %s" % e)
                return got, missing
            except polite.PoliteError as e:
                log("%s: %s" % (ident, e))
                missing += 1
                continue
            if r.status != 200:
                log("%s: HTTP %d (%s)" % (ident, r.status, url))
                update_index(idx, lambda d: d.setdefault("not_found", {}).__setitem__(
                    "bulletin/" + ident, {"url": url, "status": r.status, "when": time.strftime("%Y-%m-%d")}))
                missing += 1
                continue
        if polite.read_bytes(pdf, 5) != b"%PDF-":
            log("%s: not a PDF; removing" % ident)
            os.remove(pdf)
            continue
        outdir = os.path.join(corpus_dir(), "bulletin", str(min(yrs)))
        os.makedirs(outdir, exist_ok=True)
        txt = os.path.join(outdir, ident + ".txt")
        pdftotext(pdf, txt)
        text = polite.read_text(txt, errors="replace")
        counts = bulletin_year_counts(text)
        years_found = list(yrs)
        if not is_index and counts:
            top = counts.most_common(1)[0][0]
            if counts[yrs[0]] < 0.5 * counts[top]:
                years_found = [top]  # the volume's own text names a different year than its file name
        rec = volume_record("bulletin", ident, years_found, url, txt, yrs, counts,
                            "text" if counts else "label",
                            {"pages": text.count("\f"), "pdf": os.path.relpath(pdf, corpus_dir()),
                             "pdf_sha256": sha256_file(pdf), "pdf_bytes": os.path.getsize(pdf),
                             "kind": "index" if is_index else "volume",
                             "aliases": [bulletin_url(a) for a in aliases]})
        upsert_volume(idx, rec)
        got += 1
        log("%s: %d pages, %.1f MB pdf" % (ident, rec["pages"], rec["pdf_bytes"] / 1e6))
    return got, missing


# --------------------------------------------------------------------------------------------------
# archive.org
# --------------------------------------------------------------------------------------------------

def probe_file():
    return os.path.join(corpus_dir(), "ia_probe.json")


def read_probe():
    try:
        return polite.read_json(probe_file())
    except (OSError, ValueError):
        return {}


def ia_probe(force=False, now=time.time):
    """One real request to archive.org's search API (timeout 25 s). A failed probe is not repeated for
    30 minutes, by any process. -> (ok, message)."""
    st = read_probe()
    t = now()
    if not force and st and not st.get("ok") and t - st.get("when", 0) < PROBE_WAIT:
        nxt = time.strftime("%H:%M", time.localtime(st["when"] + PROBE_WAIT))
        return False, "archive.org did not answer at %s; next probe allowed after %s" % (
            time.strftime("%H:%M", time.localtime(st["when"])), nxt)
    if not force and st and st.get("ok") and t - st.get("when", 0) < 120:
        return True, "archive.org answered at %s" % time.strftime("%H:%M", time.localtime(st["when"]))
    url = IA + "/advancedsearch.php?q=identifier%3Aannualreportlig00statgoog&fl%5B%5D=identifier&rows=1&output=json"
    try:
        r = polite.get(url, timeout=25, retries=0, log=log)
        ok = r.status == 200 and b"response" in (r.body or b"")
        msg = "archive.org answered (HTTP %d)" % r.status
    except polite.PoliteError as e:
        ok, msg = False, "archive.org did not answer: %s" % e
    os.makedirs(corpus_dir(), exist_ok=True)
    hist = (st.get("history") or [])[-20:] + [{"when": t, "ok": ok}]
    polite.write_json(probe_file(), {"when": t, "ok": ok, "message": msg, "history": hist})
    return ok, msg


def ia_guard(now=time.time):
    """Refuse (without touching the network) while the last archive.org probe failed less than 30 minutes ago."""
    st = read_probe()
    if st and not st.get("ok") and now() - st.get("when", 0) < PROBE_WAIT:
        raise polite.NetworkError("archive.org did not answer at %s; not trying again before %s" % (
            time.strftime("%H:%M", time.localtime(st["when"])), time.strftime("%H:%M", time.localtime(st["when"] + PROBE_WAIT))))


def ia_failed(err):
    """Record that archive.org stopped answering, so every process backs off for 30 minutes."""
    st = read_probe()
    os.makedirs(corpus_dir(), exist_ok=True)
    polite.write_json(probe_file(), {"when": time.time(), "ok": False, "message": str(err),
                                     "history": (st.get("history") or [])[-20:] + [{"when": time.time(), "ok": False}]})


def ia_text_url(identifier):
    q = urllib.parse.quote(identifier)
    return "%s/download/%s/%s_djvu.txt" % (IA, q, q)


def local_seed(identifier):
    """A copy of <id>_djvu.txt already on this machine (the source survey downloaded some), or None."""
    for sub in ("ia_lhb", "ia_or", "ia_lss", "ia_marine"):
        p = os.path.join(polite.raw_root(), "survey", "history", sub, identifier + "_djvu.txt")
        if os.path.exists(p) and os.path.getsize(p) > 100000:
            return p
    return None


def ia_meta(identifier):
    """Item metadata JSON, cached (needed for the in-item search server and dir)."""
    path = os.path.join(corpus_dir(), "_meta", identifier + ".json")
    if not os.path.exists(path):
        ia_guard()
    try:
        body, _ = polite.cached_get("%s/metadata/%s" % (IA, urllib.parse.quote(identifier)), path, timeout=90, log=log)
    except (polite.NetworkError, polite.Blocked) as e:
        ia_failed(e)
        raise
    return json.loads(body)


def download_ia_text(identifier, dest):
    """Stream <id>_djvu.txt to dest. Falls back to the file list in the item metadata when the usual name 404s."""
    url = ia_text_url(identifier)
    ia_guard()
    try:
        r = polite.get(url, dest=dest, timeout=180, log=log)
    except (polite.NetworkError, polite.Blocked) as e:
        ia_failed(e)
        raise
    if r.status == 200:
        return url
    if r.status == 404:
        meta = ia_meta(identifier)
        names = [f["name"] for f in meta.get("files", []) if f["name"].endswith("_djvu.txt")]
        if names:
            url = "%s/download/%s/%s" % (IA, identifier, urllib.parse.quote(names[0]))
            r = polite.get(url, dest=dest, timeout=180, log=log)
            if r.status == 200:
                return url
    raise polite.PoliteError("HTTP %d for %s" % (r.status, url))


def add_ia_volume(idx, item):
    """Download one catalog item, read its year from the text, file it, index it."""
    ident, series = item["identifier"], item["series"]
    tmp = os.path.join(corpus_dir(), "_partial", ident + ".txt")
    seed = local_seed(ident)
    if seed:
        import shutil
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        shutil.copyfile(seed, tmp)
        url = ia_text_url(ident)
    else:
        url = download_ia_text(ident, tmp)
    with open(tmp, "rb") as fh:
        body = fh.read().decode("utf-8", "replace")
    size = os.path.getsize(tmp)
    counts = detect_years(body)  # whole volume: compilations bind two years, and the front matter alone misleads
    label = item.get("years") or []
    years, source = choose_years(counts, label)
    if not years:
        years = [0]
    outdir = os.path.join(corpus_dir(), series, str(min(years)))
    os.makedirs(outdir, exist_ok=True)
    dest = os.path.join(outdir, ident + ".txt")
    os.replace(tmp, dest)
    starts = report_starts(normalise_text(body))
    years = sorted(set(years) | {y for _, y in starts})
    rec = volume_record(series, ident, years, "%s/details/%s" % (IA, ident), dest, label, counts, source,
                        {"text_url": url, "title": item.get("title"), "note": item.get("note"), "report_starts": starts,
                         **({"seeded_from": os.path.relpath(seed, polite.raw_root())} if seed else {})})
    if size < 100000:
        rec["suspect"] = "text under 100 KB"
    upsert_volume(idx, rec)
    flag = " MISMATCH label %s" % label if rec["year_mismatch"] else ""
    log("%s %s: years %s from %s, %.2f MB%s" % (series, ident, years, source, size / 1e6, flag))
    return rec


def build_ia(idx, series_filter, max_items=None):
    n = 0
    for item in load_catalog():  # volumes already on disk need no network
        if series_filter and item["series"] not in series_filter or indexed(idx, item["series"], item["identifier"]):
            continue
        if local_seed(item["identifier"]):
            add_ia_volume(idx, item)
            n += 1
    ok, msg = ia_probe()
    log(msg)
    if not ok:
        return False, n
    for item in load_catalog():
        if series_filter and item["series"] not in series_filter:
            continue
        if indexed(idx, item["series"], item["identifier"]):
            continue
        if max_items and n >= max_items:
            break
        try:
            add_ia_volume(idx, item)
            n += 1
        except polite.NetworkError as e:
            log("archive.org stopped answering (%s); recording and stopping. Probe again in 30 minutes." % e)
            polite.write_json(probe_file(), {"when": time.time(), "ok": False, "message": str(e),
                                             "history": read_probe().get("history", [])})
            return False, n
        except polite.Blocked as e:
            log("BLOCKED: %s" % e)
            return False, n
        except polite.RateLimited as e:
            log("RATE LIMITED: %s" % e)
            return False, n
        except polite.PoliteError as e:
            log("%s: %s (skipped; will retry on the next build)" % (item["identifier"], e))
            update_index(idx, lambda d: d.setdefault("failed", {}).__setitem__(item["identifier"], str(e)))
    return True, n


def cmd_build(a):
    idx = load_index()
    series = set(a.series.split(",")) if a.series else set(SERIES)
    bad = series - set(SERIES)
    if bad:
        sys.exit("unknown series: %s (choose from %s)" % (",".join(sorted(bad)), ",".join(SERIES)))
    if "bulletin" in series:
        got, missing = build_bulletins(idx)
        log("bulletin: %d new, %d unavailable" % (got, missing))
    ia_series = series - {"bulletin"}
    if ia_series and not a.no_ia:
        while True:
            ok, n = build_ia(idx, ia_series, a.max)
            if ok or not a.wait:
                break
            st = read_probe()
            until = st.get("when", time.time()) + PROBE_WAIT
            log("waiting for archive.org; next probe at %s" % time.strftime("%H:%M", time.localtime(until)))
            time.sleep(max(60, until - time.time()))
        if ok:
            log("archive.org: %d new volumes" % n)
    return cmd_status(None)


def cmd_status(a):
    idx = load_index()
    by = {}
    for v in idx["volumes"]:
        by.setdefault(v["series"], []).append(v)
    print("corpus root: %s" % corpus_dir())
    for s, label in SERIES.items():
        vs = by.get(s, [])
        if not vs:
            print("  %-13s none  (%s)" % (s, label))
            continue
        yrs = sorted({y for v in vs for y in v["years"]})
        print("  %-13s %3d volumes, years %d-%d, %.1f MB text  (%s)"
              % (s, len(vs), yrs[0], yrs[-1], sum(v["bytes"] for v in vs) / 1e6, label))
        gaps = [y for y in range(yrs[0], yrs[-1] + 1) if y not in yrs]
        if gaps:
            print("      years with no volume inside that range: " + ", ".join(map(str, gaps)))
        mism = [v for v in vs if v.get("year_mismatch")]
        for v in mism:
            print("      label said %s but the text says %s: %s" % (v["label_years"], v["years"], v["identifier"]))
    st = read_probe()
    if st:
        print("archive.org last probe: %s at %s" % ("ok" if st.get("ok") else "FAILED",
                                                    time.strftime("%H:%M", time.localtime(st["when"]))))
    nf = idx.get("not_found")
    if nf:
        print("not found: " + ", ".join(sorted(nf)))
    pending = [i for i in load_catalog() if not indexed(idx, i["series"], i["identifier"])]
    if pending:
        print("catalog items not yet downloaded: %d" % len(pending))
    return 0


def cmd_cite(a):
    """The URL to cite for a corpus identifier (what research/check_quotes.py can read offline)."""
    vols = [v for v in load_index()["volumes"] if v["identifier"] == a.identifier or
            (a.identifier.isdigit() and v["series"] == "bulletin" and v["year"] == int(a.identifier) and v.get("kind") != "index")]
    if not vols:
        print("No corpus volume %r (`corpus.py status`)." % a.identifier)
        return 1
    for v in vols:
        yrs = ("%d" % v["years"][0]) if len(v["years"]) == 1 else "%d-%d" % (v["years"][0], v["years"][-1])
        print("%s | %s | %s" % (v["series"], yrs, v["source_url"]))
        if v["series"] != "bulletin":
            print("  add /page/n<scan page>/mode/2up for a page (see `corpus.py page`)")
        else:
            print("  add #page=<PDF page> for a page")
    return 0


def cmd_discover(a):
    ok, msg = ia_probe()
    if not ok:
        print(msg)
        return 1
    q = a.query
    url = (IA + "/advancedsearch.php?q=" + urllib.parse.quote(q) + "&rows=%d&output=json&sort%%5B%%5D=date+asc" % a.rows
           + "".join("&fl%5B%5D=" + f for f in ("identifier", "title", "date", "volume", "item_size", "creator")))
    r = polite.get(url, timeout=60, log=log)
    if r.status != 200:
        print("HTTP %d" % r.status)
        return 1
    d = json.loads(r.body)["response"]
    print("numFound", d["numFound"])
    for x in d["docs"]:
        t = x.get("title")
        t = t if isinstance(t, str) else (t[0] if t else "")
        c = x.get("creator")
        c = c if isinstance(c, str) else (c[0] if c else "")
        print("%s | %s | %s | %.1f MB | %s | %s" % (x["identifier"], (x.get("date") or "")[:10], x.get("volume", ""),
                                                   int(x.get("item_size", 0)) / 1e6, t[:90], c[:30]))
    return 0


# --------------------------------------------------------------------------------------------------
# Fuzzy matching
# --------------------------------------------------------------------------------------------------

# Letters OCR confuses with each other (lower case; the regex is case-insensitive).
CONF = {"a": "aoe", "e": "eoca", "o": "oec0a", "c": "ceo", "i": "il1tj!", "l": "li1|!", "n": "nuhr", "u": "unvh",
        "h": "hbn", "b": "bh6", "r": "rnc", "m": "mn", "s": "s5", "t": "tf", "f": "ft", "w": "wv", "v": "vwy",
        "y": "yv", "g": "g9q", "k": "kb", "d": "dcl", "z": "z2"}
ALT_WORDS = {"point": ["point", "pt"], "saint": ["saint", "st"], "st": ["st", "saint"], "pt": ["pt", "point"],
             "fort": ["fort", "ft"], "ft": ["ft", "fort"], "mount": ["mount", "mt"], "mt": ["mt", "mount"],
             "island": ["island", "isl"], "harbor": ["harbor", "harbour"], "harbour": ["harbour", "harbor"]}
STRIP_TAIL = re.compile(r"\s+(?:light\s*house|lighthouse|light\s*station|light|life[\s-]*saving\s+station|"
                        r"life[\s-]*saving|lightship\s+station|lightship|station)\s*$", re.I)
SEP = r"[\s,.;:'\"\-]{0,4}"
WILD = r"[^\W_]"


def _cls(c):
    s = CONF.get(c)
    if not s:
        return re.escape(c)
    return "[" + "".join(re.escape(x) for x in dict.fromkeys(s)) + "]"


def fuzzy_word(tok):
    """Regex for one word as OCR might print it. Short words (under 4 letters) must match exactly; 4 letters
    allow one confusable letter; 5-7 letters allow one deviation (a confusable letter, a wrong, missing or
    extra letter, or a trailing stray letter); 8 or more also accept confusable letters anywhere."""
    tok = tok.lower()
    n = len(tok)
    ex = [re.escape(c) for c in tok]
    cl = [_cls(c) for c in tok]
    alts = ["".join(ex)]
    if n >= 4:
        for i in range(n):
            alts.append("".join(ex[:i]) + cl[i] + "".join(ex[i + 1:]))  # one confusable letter
    if n >= 5:
        for i in range(n):
            alts.append("".join(ex[:i]) + WILD + "".join(ex[i + 1:]))  # one wrong letter
            alts.append("".join(ex[:i]) + "".join(ex[i + 1:]))  # one missing letter
        for i in range(1, n):
            alts.append("".join(ex[:i]) + WILD + "".join(ex[i:]))  # one extra letter
        alts.append("".join(ex) + WILD)  # trailing stray letter
        for i in range(n - 1):
            if tok[i] != tok[i + 1]:
                alts.append("".join(ex[:i]) + ex[i + 1] + ex[i] + "".join(ex[i + 2:]))  # two letters swapped
    if n >= 8:
        alts.append("".join(cl))  # confusable letters anywhere
        for i in range(n):
            alts.append("".join(cl[:i]) + WILD + "".join(cl[i + 1:]))
    return "(?:" + "|".join(dict.fromkeys(alts)) + ")"


def strip_generic(name):
    prev = None
    name = name.strip()
    while prev != name:
        prev = name
        name = STRIP_TAIL.sub("", name)
    return name.strip()


def phrase_regex(name, fuzzy=True):
    """Compiled, case-insensitive pattern for a station name (generic tail words dropped)."""
    core = strip_generic(name) or name
    words = [w for w in re.split(r"[^A-Za-z0-9]+", core) if w]
    if not words:
        raise ValueError("empty name")
    parts = []
    for w in words:
        forms = ALT_WORDS.get(w.lower(), [w.lower()])
        if fuzzy:
            parts.append("(?:" + "|".join(fuzzy_word(f) for f in forms) + ")")
        else:
            parts.append("(?:" + "|".join(re.escape(f) for f in forms) + ")")
    body = SEP.join(parts)
    return re.compile(r"(?<![^\W\d_])" + body + r"(?![^\W\d_])", re.I)


STATE_HINTS = {
    "AL": ["ala", "alabama"], "AK": ["alaska"], "AZ": ["ariz", "arizona"], "AR": ["ark", "arkansas"],
    "CA": ["cal", "calif", "california"], "CO": ["colo", "colorado"], "CT": ["conn", "connecticut"],
    "DE": ["del", "delaware"], "DC": ["d c", "district of columbia"], "FL": ["fla", "florida"], "GA": ["ga", "georgia"],
    "HI": ["hawaii", "hawaiian"], "ID": ["idaho"], "IL": ["ill", "illinois"], "IN": ["ind", "indiana"],
    "IA": ["iowa"], "KS": ["kans", "kansas"], "KY": ["ky", "kentucky"], "LA": ["la", "louisiana"],
    "ME": ["me", "maine"], "MD": ["md", "maryland"], "MA": ["mass", "massachusetts"], "MI": ["mich", "michigan"],
    "MN": ["minn", "minnesota"], "MS": ["miss", "mississippi"], "MO": ["mo", "missouri"], "MT": ["mont", "montana"],
    "NE": ["nebr", "neb", "nebraska"], "NV": ["nev", "nevada"], "NH": ["n h", "new hampshire"],
    "NJ": ["n j", "new jersey"], "NM": ["n mex", "new mexico"], "NY": ["n y", "new york"],
    "NC": ["n c", "north carolina"], "ND": ["n dak", "north dakota"], "OH": ["ohio"], "OK": ["okla", "oklahoma"],
    "OR": ["oreg", "ore", "oregon"], "PA": ["pa", "penn", "pennsylvania"], "RI": ["r i", "rhode island"],
    "SC": ["s c", "south carolina"], "SD": ["s dak", "south dakota"], "TN": ["tenn", "tennessee"],
    "TX": ["tex", "texas"], "UT": ["utah"], "VT": ["vt", "vermont"], "VA": ["va", "virginia"],
    "WA": ["wash", "washington"], "WV": ["w va", "west virginia"], "WI": ["wis", "wisconsin"], "WY": ["wyo", "wyoming"],
    "PR": ["p r", "porto rico", "puerto rico"], "GU": ["guam"], "AS": ["samoa", "tutuila"], "VI": ["virgin islands"],
    "MP": ["marianas", "mariana"],
    "NS": ["n s", "nova scotia"], "NB": ["n b", "new brunswick"], "PE": ["p e i", "prince edward island"],
    "QC": ["que", "quebec"], "ON": ["ont", "ontario"], "BC": ["b c", "british columbia"],
    "MB": ["man", "manitoba"], "NL": ["nfld", "newfoundland"],
}


def _state_rx(code):
    code = code.upper()
    hints = STATE_HINTS.get(code)
    if not hints:
        return None
    return re.compile(r"(?<![a-z])(?:%s)(?![a-z])" % "|".join(re.escape(h).replace(r"\ ", r"\s{0,2}") for h in hints))


_STATE_RX = {}
_SHORT_AMBIGUOUS = {"ME", "LA", "MO", "PA", "IN", "OR", "ID", "AL", "CA", "AS", "MA", "MI", "MS", "ON", "PE", "MB", "WA", "DE",
                    "OH", "IA", "GA", "PR", "VI", "AR", "NE", "HI", "OK", "NL"}


def state_hint(window, center, target, near_chars=120):
    """Classify a hit by the state names around it. `window` is the text around the hit and `center` the hit's
    offset in it. -> 'in' (the target state is named within the window), 'other:XX' (a different state is named
    within `near_chars` of the hit and the target is not named at all), '-' (no state named nearby)."""
    w = re.sub(r"[^a-z]", " ", window.lower())

    def nearest(code):
        rx = _STATE_RX.get(code)
        if rx is None:
            rx = _STATE_RX[code] = _state_rx(code)
        if rx is None:
            return None
        ds = [abs(m.start() - center) for m in rx.finditer(w)]
        return min(ds) if ds else None

    if nearest(target.upper()) is not None:
        return "in"
    best, best_d = None, near_chars + 1
    for code, hints in STATE_HINTS.items():
        if code == target.upper():
            continue
        d = nearest(code)
        if d is None:
            continue
        # abbreviations that are ordinary words (me, la, or, in ...) are ignored; names and unambiguous codes count
        if code in _SHORT_AMBIGUOUS and not re.search(r"(?<![a-z])(?:%s)(?![a-z])" % "|".join(
                re.escape(h) for h in hints if len(h) > 4), w):
            continue
        if d < best_d:
            best, best_d = code, d
    return "other:%s" % best if best else "-"


# --------------------------------------------------------------------------------------------------
# grep
# --------------------------------------------------------------------------------------------------

_HYPHEN_BREAK = re.compile(r"-[ \t]*\r?\n[ \t]*")


def normalise_text(raw):
    """Words hyphenated across lines are rejoined and runs of whitespace become one space (the Commissioner text
    has double spaces). Form feeds (the Bulletin's page breaks) survive."""
    if "-" in raw:
        raw = _HYPHEN_BREAK.sub("", raw)
    if "\f" in raw:
        return "\f".join(" ".join(page.split()) for page in raw.split("\f"))
    return " ".join(raw.split())


def parse_years(s):
    if not s:
        return None
    m = re.match(r"^(\d{4})(?:\s*[-:]\s*(\d{4}))?$", s.strip())
    if not m:
        sys.exit("--years wants 1880 or 1880-1900")
    lo = int(m.group(1))
    return lo, int(m.group(2) or lo)


def select_volumes(idx, series=None, years=None):
    out = []
    for v in idx["volumes"]:
        if series and v["series"] not in series:
            continue
        if years and not any(years[0] <= y <= years[1] for y in v["years"]):
            continue
        out.append(v)
    return sorted(out, key=lambda v: (v["year"], v["series"], v["identifier"]))


def volume_text(v):
    return normalise_text(polite.read_text(os.path.join(corpus_dir(), v["path"]), errors="replace"))


def snippet(text, s, e, before, after):
    a = max(0, s - before)
    b = min(len(text), e + after)
    return text[a:b].replace("\f", " ").strip()


def anchor_fragments(names):
    """A cheap literal gate for the scan. Any fuzzy match of a name with a long word (6+ letters) keeps at
    least one half of that word intact (one deviation touches one half), so searching for the halves finds
    every place worth checking at literal-search speed. None when some name has no long word."""
    frags = set()
    for n in names:
        words = [w for w in re.split(r"[^A-Za-z0-9]+", strip_generic(n) or n) if w and w.lower() not in ALT_WORDS]
        if not words:
            return None
        w = max(words, key=len).lower()
        if len(w) < 6:
            return None
        frags.update((w[: len(w) // 2], w[len(w) // 2:]))
    return sorted(frags)


def scan(text, fuzzy_rxs, gate, pad=80):
    """Spans of fuzzy matches in text, using the gate (literal fragments) to look only near candidate positions."""
    spans = set()
    low = text.lower() if gate else None
    if low is not None and len(low) != len(text):
        low = None
    if low is None:
        for rx in fuzzy_rxs:
            spans.update((m.start(), m.end()) for m in rx.finditer(text))
        return sorted(spans)
    cands = []
    for frag in gate:
        p = low.find(frag)
        while p != -1:
            cands.append(p)
            p = low.find(frag, p + 1)
    cands.sort()
    i = 0
    while i < len(cands):
        j = i
        while j + 1 < len(cands) and cands[j + 1] - cands[j] < 200:
            j += 1
        a, b = max(0, cands[i] - 60 - pad), min(len(text), cands[j] + 60 + pad)
        for rx in fuzzy_rxs:
            spans.update((a + m.start(), a + m.end()) for m in rx.finditer(text[a:b]))
        i = j + 1
    return sorted(spans)


def grep_volume(v, patterns, state, before, after):
    """-> [{pos, end, exact, hint, page, snip}] for one volume, nearby hits merged."""
    text = volume_text(v)
    exact_rx = patterns["exact"]
    hits = scan(text, patterns["fuzzy"], patterns.get("gate"))
    merged = []
    paged = v["series"] == "bulletin"
    for s, e in hits:
        if merged and s - merged[-1][1] < 250 and not (paged and "\f" in text[merged[-1][1]:s]):
            merged[-1][1] = max(merged[-1][1], e)
            merged[-1][2] += 1
        else:
            merged.append([s, e, 1])
    out = []
    for s, e, n in merged:
        matched = text[s:e]
        w0 = max(0, s - 400)
        win = text[w0: e + 400]
        hint = state_hint(win, s - w0, state) if state else None
        page = text.count("\f", 0, s) + 1 if v["series"] == "bulletin" else None
        out.append({"pos": s, "n": n, "exact": any(r.search(matched) for r in exact_rx), "hint": hint,
                    "page": page, "snip": snippet(text, s, e, before, after), "volume": v,
                    "year": attribute_year(v, s)})
    return out


def cmd_grep(a):
    idx = load_index()
    series = set(a.series.split(",")) if a.series else None
    if series and series - set(SERIES):
        sys.exit("unknown series: %s" % ",".join(sorted(series - set(SERIES))))
    vols = select_volumes(idx, series, parse_years(a.years))
    if not vols:
        print("(no volumes in the corpus match that series/years; `corpus.py status` shows what is there)")
        return 1
    names = [a.name] + list(a.alias or [])
    patterns = {"fuzzy": [phrase_regex(n, True) for n in names], "exact": [phrase_regex(n, False) for n in names],
                "gate": None if a.thorough else anchor_fragments(names)}
    state = a.state.upper() if a.state else None
    all_hits = []
    per_vol = []
    for v in vols:
        hs = grep_volume(v, patterns, state, a.before, a.after)
        if hs:
            per_vol.append((v, len(hs)))
        all_hits.extend(hs)
    yrs = parse_years(a.years)
    if yrs:  # inside a bound volume, keep only the reports of the years asked for
        all_hits = [h for h in all_hits if h.get("year") is None or yrs[0] <= h["year"] <= yrs[1]]
    total = len(all_hits)
    dropped = 0
    if state and not a.all_states:
        keep = [h for h in all_hits if not (h["hint"] or "").startswith("other:")]
        dropped = total - len(keep)
        all_hits = keep

    def rank(h):
        return (0 if h["hint"] == "in" else 1, 0 if h["exact"] else 1, h["volume"]["year"], h["pos"])

    chosen = sorted(all_hits, key=rank)[: a.max]
    chosen.sort(key=lambda h: (h["volume"]["year"], h["volume"]["series"], h["pos"]))
    for h in chosen:
        v = h["volume"]
        yr = ("%d" % v["year"]) if len(v["years"]) == 1 else (
            "%d" % h["year"] if h.get("year") else "%d-%d" % (v["years"][0], v["years"][-1]))
        ident = v["identifier"] + (" p.%d" % h["page"] if h["page"] else "")
        tags = ("" if h["exact"] else " ~fuzzy") + (" [%s]" % h["hint"] if h["hint"] and h["hint"] != "-" else "") \
            + (" (+%d nearby)" % (h["n"] - 1) if h["n"] > 1 else "")
        print("%s | %s | %s%s | %s" % (v["series"], yr, ident, tags, h["snip"]))
    vols_hit = len(per_vol)
    note = []
    if dropped:
        note.append("%d hit(s) near a different state's name hidden; --all-states shows them" % dropped)
    if len(all_hits) > len(chosen):
        note.append("showing %d of %d; narrow with --years/--series/--state or raise --max" % (len(chosen), len(all_hits)))
    print("[%d hit(s) in %d of %d volume(s) searched%s]" % (len(all_hits) + dropped, vols_hit, len(vols),
                                                            ("; " + "; ".join(note)) if note else ""))
    if not total:
        print("[nothing found: try --alias with the OCR spelling you expect, drop the state, or widen --years]")
    return 0


# --------------------------------------------------------------------------------------------------
# page
# --------------------------------------------------------------------------------------------------

def inside_search(identifier, phrase):
    """IA's in-item search for the exact phrase -> parsed JSON (cached on disk). Without quotes the search matches
    any of the words."""
    if '"' not in phrase:
        phrase = '"%s"' % phrase.strip()
    key = hashlib.sha1(("%s|%s" % (identifier, phrase)).encode()).hexdigest()
    path = os.path.join(corpus_dir(), "_inside", key + ".json")
    if os.path.exists(path):
        return polite.read_json(path)
    meta = ia_meta(identifier)
    srv, dr = meta.get("server") or meta.get("d1"), meta.get("dir")
    if not srv or not dr:
        raise polite.PoliteError("item metadata for %s has no server/dir" % identifier)
    url = "https://%s/fulltext/inside.php?item_id=%s&doc=%s&path=%s&q=%s" % (
        srv, urllib.parse.quote(identifier), urllib.parse.quote(identifier), urllib.parse.quote(dr),
        urllib.parse.quote(phrase))
    ia_guard()
    try:
        body, _ = polite.cached_get(url, path, timeout=120, log=log)
    except (polite.NetworkError, polite.Blocked) as e:
        ia_failed(e)
        raise
    return json.loads(body)


def parse_inside(d):
    """-> [(leaf, text)] from an inside.php reply."""
    out = []
    for m in d.get("matches", []):
        pars = m.get("par") or []
        leaf = pars[0].get("page") if pars else None
        text = re.sub(r"</?IA_FTS_MATCH>", "", m.get("text", "")).replace("\n", " ")
        out.append((leaf, text))
    return out


def ia_page_url(identifier, leaf, phrase):
    return "%s/details/%s/page/n%s/mode/2up?q=%s" % (IA, identifier, leaf, urllib.parse.quote_plus(phrase.strip('"')))


def cmd_page(a):
    idx = load_index()
    if a.series not in SERIES:
        sys.exit("series must be one of %s" % ",".join(SERIES))
    y = int(a.year)
    vols = [v for v in idx["volumes"] if v["series"] == a.series and y in v["years"]]
    if not vols:
        print("No %s volume for %s in the corpus (`corpus.py status`)." % (a.series, a.year))
        return 1
    for v in vols:
        if v["series"] == "bulletin":
            text = volume_text(v)
            rx = phrase_regex(a.phrase, True)
            seen = 0
            for m in rx.finditer(text):
                page = text.count("\f", 0, m.start()) + 1
                print("bulletin %d: PDF page %d of %d: %s" % (y, page, v["pages"], snippet(text, m.start(), m.end(), 80, 160)))
                what = ("Lighthouse Service Bulletin, index to %d-%d" % (v["years"][0], v["years"][-1])
                        if v.get("kind") == "index" else "Lighthouse Service Bulletin %d" % y)
                print("  cite: %s, PDF page %d, %s#page=%d" % (what, page, v["source_url"], page))
                seen += 1
                if seen >= a.max:
                    break
            if not seen:
                print("bulletin %d: no match for %r" % (y, a.phrase))
            continue
        ident = v["identifier"]
        try:
            d = inside_search(ident, a.phrase)
        except polite.PoliteError as e:
            ok, msg = ia_probe()
            print("%s %d (%s): cannot get the page from archive.org: %s" % (a.series, y, ident, e))
            print("  " + msg)
            print("  Meanwhile cite the volume without a page, and re-run later. Details page: %s/details/%s" % (IA, ident))
            continue
        rows = parse_inside(d)
        print("%s %s  %s  (%s scan pages; %d match(es) for %r)" % (a.series, y, ident, d.get("page_count", "?"), len(rows), a.phrase))
        for leaf, text in rows[: a.max]:
            print("  scan page %s | %s" % (leaf, text[:240]))
            print("    %s" % ia_page_url(ident, leaf, a.phrase))
        if rows:
            print("  (scan page = the image number in the Internet Archive viewer; the printed page number is on the page"
                  " itself: open the URL and read it before citing 'p. N')")
    return 0


_INDEX_MEMO = {}


def _volumes_by_ident():
    p = index_file()
    try:
        m = os.path.getmtime(p)
    except OSError:
        return {}
    memo = _INDEX_MEMO.get(p)
    if memo and memo[0] == m:
        return memo[1]
    by = {v["identifier"]: v for v in load_index()["volumes"]}
    _INDEX_MEMO[p] = (m, by)
    return by


def local_text_for_url(url):
    """If `url` names a corpus volume (an archive.org details / download / stream URL of an indexed item, or a
    Lighthouse Service Bulletin PDF on uslhs.org), the volume's text as bytes; otherwise None. Used by
    research/fetch_text.py so that research/check_quotes.py can verify quotes without the network."""
    u = urllib.parse.urlsplit(url)
    host = u.netloc.lower().removeprefix("www.")
    segs = [urllib.parse.unquote(x) for x in u.path.split("/") if x]
    ident = None
    if host == "archive.org" and len(segs) >= 2 and segs[0] in ("details", "download", "stream"):
        if segs[0] != "details" and not segs[-1].endswith("_djvu.txt"):
            return None
        ident = segs[1]
    elif host == "uslhs.org" and segs[:3] == ["sites", "default", "files"] and len(segs) == 5 and segs[3] == "bulletins":
        want = "/".join(segs)
        for v in _volumes_by_ident().values():
            urls = [v.get("source_url", "")] + list(v.get("aliases") or [])
            if v["series"] == "bulletin" and any(urllib.parse.unquote(urllib.parse.urlsplit(x).path).strip("/") == want
                                                  for x in urls):
                ident = v["identifier"]
                break
    v = _volumes_by_ident().get(ident) if ident else None
    if not v:
        return None
    path = os.path.join(corpus_dir(), v["path"])
    return polite.read_bytes(path) if os.path.exists(path) else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grep", help="fuzzy search of the corpus text")
    g.add_argument("name")
    g.add_argument("--alias", action="append", help="another spelling; repeatable")
    g.add_argument("--state", help="two-letter state or province code; hits near another state's name are hidden")
    g.add_argument("--all-states", action="store_true", help="show hits near another state's name too")
    g.add_argument("--series", help="comma list: " + ",".join(SERIES))
    g.add_argument("--years", help="1880 or 1880-1900 (fiscal years)")
    g.add_argument("--max", type=int, default=20, help="most snippets to print (default 20)")
    g.add_argument("--thorough", action="store_true", help="scan every character with the full fuzzy pattern (slower; "
                   "the default checks only near literal halves of the name's longest word)")
    g.add_argument("--before", type=int, default=90, help="characters before the match")
    g.add_argument("--after", type=int, default=200, help="characters after the match")
    p = sub.add_parser("page", help="page number and citable URL for a phrase")
    p.add_argument("series")
    p.add_argument("year")
    p.add_argument("phrase")
    p.add_argument("--max", type=int, default=5)
    b = sub.add_parser("build", help="download / extend the corpus")
    b.add_argument("--series", help="comma list; default all")
    b.add_argument("--no-ia", action="store_true", help="skip archive.org")
    b.add_argument("--wait", action="store_true", help="if archive.org is down, probe every 30 minutes until it answers")
    b.add_argument("--max", type=int, help="most archive.org volumes to fetch this run")
    sub.add_parser("status", help="what the corpus holds")
    c = sub.add_parser("cite", help="the URL to cite for an identifier (or a Bulletin year)")
    c.add_argument("identifier")
    d = sub.add_parser("discover", help="list archive.org items for a query")
    d.add_argument("query")
    d.add_argument("--rows", type=int, default=100)
    a = ap.parse_args(argv)
    return {"grep": cmd_grep, "page": cmd_page, "build": cmd_build, "status": cmd_status, "cite": cmd_cite, "discover": cmd_discover}[a.cmd](a)


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `| head` must not print a traceback
    sys.exit(main())
