#!/usr/bin/env python3
"""Read a web page or PDF as plain text, cheaply, for research agents.

  research/fetch_text.py URL [--grep REGEX] [--context 1] [--max 6000]

- nhlr.org / firetower.org pages are read from the crawl cache (data/raw/nhlr, data/raw/fflos);
  archive.org details/download/stream URLs of volumes in the local report corpus, the uslhs.org Lighthouse
  Service Bulletin PDFs, the archives.uslhs.org place / showPeople pages we crawled and the Chronicling
  America pages research/newspapers.py has read are read from the caches of corpus.py, roster.py and
  newspapers.py (no network; this is how check_quotes.py verifies
  quotes cited to them); everything else is fetched once and cached under data/raw/web/ (polite: 2 s per
  host, 5 s and 20 a minute for loc.gov, honest UA). The cache root is $FRESNEL_RAW_ROOT, default data/raw.
- HTML is reduced to text (scripts, styles and navigation dropped); PDFs go through pdftotext.
- --grep prints only the lines matching REGEX (case-insensitive) with --context lines around them,
  so a 40-page NRHP nomination costs a few hundred words instead of thousands.
- Output is capped at --max characters; the first line says how long the full text was."""
import argparse, fcntl, hashlib, html, os, re, subprocess, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.environ.get("FRESNEL_RAW_ROOT") or os.path.join(ROOT, "data", "raw")
if HERE not in sys.path:
    sys.path.insert(0, HERE)
UA = "FresnelBot/0.1 (+https://github.com/holdTheDoorHoid/fresnel)"
LOCKDIR = os.path.join(RAW, "_locks")


def cached_register(url):
    u = urllib.parse.urlsplit(url)
    host = u.netloc.lower().removeprefix("www.")
    src = {"nhlr.org": "nhlr", "firetower.org": "fflos"}.get(host)
    if not src:
        return None
    path = os.path.join(RAW, src, host, u.path.strip("/"), "index.html")
    return path if os.path.exists(path) else None


def polite_get(url):
    host = urllib.parse.urlsplit(url).netloc.lower()
    import polite  # the shared throttle: one lock file per site, also used by roster.py / corpus.py / newspapers.py
    site = polite.site_key(host)
    th = polite.Throttle("web-" + re.sub(r"[^a-z0-9.]", "_", site), gap=polite.site_gap(host),
                         per_minute=20 if site == "loc.gov" else None, lockdir=LOCKDIR)
    with th:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/pdf,*/*"})
        with urllib.request.urlopen(req, timeout=40) as r:
            body, ctype = r.read(), r.headers.get("Content-Type", "")
    return body, ctype


def local_source(url):
    """(body, content-type) for URLs whose text we already hold locally, else None."""
    host = urllib.parse.urlsplit(url).netloc.lower().removeprefix("www.")
    try:
        if host == "archives.uslhs.org":
            import roster
            t = roster.local_text_for_url(url)
            return (t.encode("utf-8"), "text/plain; charset=utf-8") if t else None
        if host == "loc.gov":
            import newspapers
            t = newspapers.local_text_for_url(url)
            return (t.encode("utf-8"), "text/plain; charset=utf-8") if t else None
        if host in ("archive.org", "uslhs.org"):
            import corpus
            b = corpus.local_text_for_url(url)
            return (b, "text/plain; charset=utf-8") if b else None
    except Exception:  # a broken cache must not break ordinary fetching
        return None
    return None


def get(url):
    url = url.split("#", 1)[0]  # fragments (#page=7) never reach the server and must not split the cache
    reg = cached_register(url)
    if reg:
        return open(reg, "rb").read(), "text/html"
    local = local_source(url)
    if local:
        return local
    os.makedirs(os.path.join(RAW, "web"), exist_ok=True)
    key = os.path.join(RAW, "web", hashlib.sha1(url.encode()).hexdigest())
    if os.path.exists(key + ".bin"):
        return open(key + ".bin", "rb").read(), open(key + ".type").read()
    body, ctype = polite_get(url)
    open(key + ".bin", "wb").write(body)
    open(key + ".type", "w").write(ctype)
    return body, ctype


def to_text(body, ctype):
    if ctype.lower().startswith("text/plain"):
        return body.decode("utf-8", "replace")
    if body[:5] == b"%PDF-" or "pdf" in ctype:
        p = subprocess.run(["pdftotext", "-layout", "-", "-"], input=body, capture_output=True, timeout=120)
        return p.stdout.decode("utf-8", "replace")
    s = body.decode("utf-8", "replace")
    s = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer|header|form)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h[1-6]|table|section|article)>", "\n", s)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    lines = [re.sub(r"[ \t ]+", " ", l).strip() for l in s.splitlines()]
    return "\n".join(l for l in lines if l)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--grep")
    ap.add_argument("--context", type=int, default=1)
    ap.add_argument("--max", type=int, default=6000)
    a = ap.parse_args()
    try:
        text = to_text(*get(a.url))
    except Exception as e:
        print(f"ERROR fetching {a.url}: {e}")
        sys.exit(1)
    out = text
    if a.grep:
        lines = text.splitlines()
        rx = re.compile(a.grep, re.I)
        keep = set()
        for i, l in enumerate(lines):
            if rx.search(l):
                keep.update(range(max(0, i - a.context), min(len(lines), i + a.context + 1)))
        out = "\n".join(("..." if i - 1 not in keep and i else "") + lines[i] for i in sorted(keep)) or "(no matching lines)"
    print(f"[{len(text)} chars of text; showing {min(len(out), a.max)}]")
    print(out[: a.max])


if __name__ == "__main__":
    main()
