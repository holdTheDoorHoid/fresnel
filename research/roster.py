#!/usr/bin/env python3
"""Keeper rosters from the USLHS Digital Archive (archives.uslhs.org), for research agents.

  research/roster.py us-me-portland-head          a Fresnel station id (needs data/stations/<dir>/<id>.json)
  research/roster.py --place portland-head        a USLHS place slug or node id
  research/roster.py --name "Split Rock" --state MN [--near 47.2,-91.37]
  research/roster.py crawl | build | stats        maintenance (see below)

The archive is "All Rights Reserved": we keep FACTS ONLY (names, roles, years, salaries, positions,
flags), never its prose, and cite the place page. Rosters come from NARA's Registers of Lighthouse
Keepers via Kraig Anderson's inventory, so every line is a start, not a final word: a story still cites a
primary record for the keepers it names (DESIGN.md 3.6: never join two people by name alone).

Maintenance (all caches live under $FRESNEL_RAW_ROOT/uslhs, default <repo>/data/raw/uslhs):
  crawl   fetch the places index, every place page and every showPeople/<nid> roster (about 2,300 places x 2
          requests, 2 s apart; resumable: anything already cached is skipped; robots.txt honoured)
  build   parse the cache into places.json and rosters.json
  stats   counts by place type, places with rosters, roster lines
"""
import argparse
import html as htmllib
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polite  # noqa: E402

BASE = "https://archives.uslhs.org"
SLUG_RX = re.compile(r"^[A-Za-z0-9._~%\-]+$")


def uslhs_dir():
    return os.path.join(polite.raw_root(), "uslhs")


def clean(s):
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


# --------------------------------------------------------------------------------------------------
# Parsing: places index, place page, roster
# --------------------------------------------------------------------------------------------------

def parse_index(page_html):
    """Rows of the places index: [{slug, name, type, state, existing}]."""
    rows = []
    for chunk in page_html.split('<div class="float views-row">')[1:]:
        m = re.search(r'<a href="/places/([^"?#]+)" rel="bookmark"><span class="field title">(.*?)</span>', chunk, re.S)
        if not m:
            continue
        row = {"slug": urllib.parse.unquote(m.group(1)), "name": clean(m.group(2))}
        for key, label in (("type", "Type"), ("state", "U.S. State"), ("existing", "Existing")):
            f = re.search(r'<div class="field_label">%s: </div>(.*?)(?=<div class="field |<ul class="links|</article>)'
                          % re.escape(label), chunk, re.S)
            row[key] = clean(f.group(1)) if f else None
        rows.append(row)
    return rows


def parse_last_page(page_html):
    m = re.search(r'href="\?page=(\d+)"[^>]*title="Go to last page"', page_html)
    if m:
        return int(m.group(1))
    nums = [int(n) for n in re.findall(r'href="\?page=(\d+)"', page_html)]
    return max(nums) if nums else 0


def parse_total(page_html):
    m = re.search(r"Displaying \d+ - \d+ of (\d+)", page_html)
    return int(m.group(1)) if m else None


def place_nids(page_html):
    """(node id from the shortlink, roster id from the showPeople link or None)."""
    sl = re.search(r'rel="shortlink" href="[^"]*/node/(\d+)"', page_html)
    sp = re.search(r"showPeople/(\d+)", page_html)
    return (int(sl.group(1)) if sl else None, int(sp.group(1)) if sp else None)


# --------------------------------------------------------------------------------------------------
# Cache fetching
# --------------------------------------------------------------------------------------------------

def log(msg):
    print(time.strftime("%H:%M:%S ") + msg, flush=True)


def fetch_cached(url, path, validate=None):
    """-> (text, fetched_now). Caches only responses that validate."""
    if os.path.exists(path):
        return polite.read_text(path), False
    r = polite.get(url, log=log)
    if r.status != 200:
        raise polite.PoliteError("HTTP %d for %s" % (r.status, url))
    text = r.text()
    if validate and not validate(text):
        raise polite.PoliteError("unexpected body for %s" % url)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
    return text, True


def valid_roster(text):
    try:
        j = json.loads(text)
        return isinstance(j, list) and bool(j) and "data" in j[0]
    except ValueError:
        return False


def index_path(n):
    return os.path.join(uslhs_dir(), "index", "page_%03d.html" % n)


def place_path(slug):
    return os.path.join(uslhs_dir(), "place", urllib.parse.quote(slug, safe="") + ".html")


def people_path(nid):
    return os.path.join(uslhs_dir(), "people", "%d.json" % nid)


def cached_index_slugs():
    """Index rows from every cached index page, in order, de-duplicated."""
    rows, seen, n = [], set(), 0
    while os.path.exists(index_path(n)):
        for r in parse_index(polite.read_text(index_path(n))):
            if r["slug"] not in seen:
                seen.add(r["slug"])
                rows.append(r)
        n += 1
    return rows


def cmd_crawl(a):
    os.makedirs(uslhs_dir(), exist_ok=True)
    first, _ = fetch_cached(BASE + "/places?page=0", index_path(0), lambda t: "views-row" in t)
    last = parse_last_page(first)
    total = parse_total(first)
    log("places index: %s places on %d pages" % (total, last + 1))
    for n in range(1, last + 1):
        fetch_cached("%s/places?page=%d" % (BASE, n), index_path(n), lambda t: "views-row" in t)
    rows = cached_index_slugs()
    log("index complete: %d distinct slugs" % len(rows))
    if a.only:
        rows = [r for r in rows if r["slug"] in a.only]
    if a.limit:
        rows = rows[: a.limit]
    failures, consecutive, fetched = [], 0, 0
    t0 = time.time()
    for i, r in enumerate(rows, 1):
        slug = r["slug"]
        if not SLUG_RX.match(urllib.parse.quote(slug, safe="")):
            log("skipping odd slug %r" % slug)
            continue
        try:
            page, new1 = fetch_cached("%s/places/%s" % (BASE, urllib.parse.quote(slug)), place_path(slug),
                                      lambda t: "<h1>" in t)
            node, rid = place_nids(page)
            new2 = False
            if rid:
                _, new2 = fetch_cached("%s/general/showPeople/%d" % (BASE, rid), people_path(rid), valid_roster)
            consecutive = 0
            fetched += new1 + new2
        except polite.Blocked as e:
            log("BLOCKED: %s" % e)
            return 2
        except polite.RateLimited as e:
            log("RATE LIMITED: %s; stopping, re-run later (it resumes)" % e)
            return 3
        except polite.PoliteError as e:
            failures.append((slug, str(e)))
            consecutive += 1
            log("FAILED %s: %s" % (slug, e))
            if consecutive >= 10:
                log("10 failures in a row; the site looks down. Stopping; re-run later (it resumes).")
                return 4
        if i % 25 == 0:
            rate = fetched / max(time.time() - t0, 1)
            left = len(rows) - i
            log("%d/%d places (%d requests this run, %.2f req/s)" % (i, len(rows), fetched, rate))
    polite.write_json(os.path.join(uslhs_dir(), "crawl_failures.json"), failures, indent=1)
    log("crawl finished: %d places, %d requests this run, %d failures" % (len(rows), fetched, len(failures)))
    return 0 if not failures else 1



# --------------------------------------------------------------------------------------------------
# Place pages: facts only. Labels are mapped explicitly; prose fields are never kept.
# --------------------------------------------------------------------------------------------------

FIELD_MAP = {
    "type": "type", "year established": "established", "existing": "existing", "location": "location_desc",
    "latitude": "lat_raw", "longitude": "lon_raw", "city / town": "town", "u.s. state": "state_name",
    "location county": "county", "country": "country", "owner / manager": "owner",
    "open to public": "open_to_public",
    "year tower established": "tower_established", "tower construction material": "tower_material",
    "tower foundation": "tower_foundation", "tower shape": "tower_shape",
    "height of light above mean high water, in feet": "focal_height_ft",
    "height, in feet, from base of structure to center of lantern": "tower_height_ft",
    "active aid to navigation?": "active_aton", "current optic": "current_optic",
    "original optic type": "original_optic", "year original lens installed": "original_lens_year",
    "private aid": "private_aid", "year automated": "automated", "uscg access to optics": "uscg_access_to_optics",
    "fog signal building?": "fog_signal_building", "year fog signal building constructed": "fog_signal_year",
    "keeper's quarters?": "keepers_quarters", "year keeper's quarters": "keepers_quarters_year",
    "keeper's quarters style": "keepers_quarters_style",
    "keeper's quarters construction": "keepers_quarters_construction",
    "other structures": "other_structures", "source": "data_source",
    "alternate name(s)": "alternate_names", "start year": "start_year", "end year": "end_year",
    "disposition": "disposition", "depot type": "depot_type", "tower daymark": "tower_daymark", "vessel": "vessels",
}
# Labels that mean "no longer lit / gone"; the first one present is kept as `discontinued`.
DISCONTINUED_LABELS = ("year discontinued", "year deactivated", "year light discontinued", "year decommissioned",
                       "year deestablished", "year de-established", "year closed", "year abandoned")
DEMOLISHED_LABELS = ("year demolished", "year destroyed", "year tower demolished", "year lost")

STATE_CODES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "district of columbia": "DC", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD", "massachusetts": "MA",
    "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY", "puerto rico": "PR", "guam": "GU",
    "american samoa": "AS", "us virgin islands": "VI", "u.s. virgin islands": "VI", "virgin islands": "VI",
    "united states virgin islands": "VI", "northern mariana islands": "MP", "northern marianas": "MP",
    "commonwealth of the northern mariana islands": "MP", "minor outlying islands": "UM",
    "united states minor outlying islands": "UM",
}
CODE_NAMES = {}
for _n, _c in STATE_CODES.items():
    CODE_NAMES.setdefault(_c, _n.title())


def state_code(s):
    if not s:
        return None
    t = s.strip()
    if len(t) == 2 and t.upper() in CODE_NAMES:
        return t.upper()
    return STATE_CODES.get(t.lower())


def norm_label(label):
    return re.sub(r"\s+", " ", htmllib.unescape(label)).strip().rstrip(":").strip().lower()


def extract_fields(page_html):
    """Label -> text for every `field_label` in the main article of a place page."""
    a0 = page_html.find("<article>")
    a1 = page_html.find("</article>", a0 if a0 >= 0 else 0)
    art = page_html[a0:a1] if a0 >= 0 and a1 > a0 else page_html
    out = {}
    parts = re.split(r'<div class="field_label">', art)[1:]
    for chunk in parts:
        lab, _, rest = chunk.partition("</div>")
        rest = re.split(r'<h3|<h5|<div class="flex-grid"|<div class="row"|<div class="garydata"|'
                        r'<div class="large-6 columns"|<div class="field_label">', rest)[0]
        val = clean(rest)
        key = norm_label(lab)
        if key and val:
            out[key] = out[key] + "; " + val if key in out and val not in out[key] else out.get(key, val)
    return out


def parse_coord(s):
    """'43° 37.4\\'' -> (43.6233, None); a trailing/leading N S E W letter is returned as the hemisphere."""
    if not s:
        return None, None
    t = htmllib.unescape(s).replace("’", "'").replace("′", "'").replace("″", '"')
    nums = re.findall(r"\d+(?:\.\d+)?", t)
    if not nums:
        return None, None
    deg = float(nums[0])
    mins = float(nums[1]) if len(nums) > 1 else 0.0
    secs = float(nums[2]) if len(nums) > 2 else 0.0
    letter = re.search(r"\b([NSEW])\b|([NSEW])\s*$|^\s*([NSEW])", t.upper())
    hemi = next((g for g in (letter.groups() if letter else ()) if g), None)
    if hemi is None and t.strip().startswith("-"):
        hemi = "S/W"
    return round(deg + mins / 60.0 + secs / 3600.0, 5), hemi


def signed_latlon(lat_raw, lon_raw, state):
    """Decimal degrees with signs. The pages print degrees and minutes with no hemisphere, so: north
    everywhere except American Samoa (south); west everywhere except Guam and the Northern Marianas (east)."""
    lat, lat_h = parse_coord(lat_raw)
    lon, lon_h = parse_coord(lon_raw)
    code = state_code(state)
    if lat is not None:
        south = (lat_h in ("S", "S/W")) or (lat_h is None and code == "AS")
        lat = -lat if south else lat
    if lon is not None:
        east = (lon_h == "E") or (lon_h is None and code in ("GU", "MP"))
        lon = lon if east else -lon
    return lat, lon


def to_year(s):
    m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", s or "")
    return int(m.group(1)) if m else None


def to_float(s):
    m = re.search(r"-?\d+(?:\.\d+)?", (s or "").replace(",", ""))
    return float(m.group(0)) if m else None


def yes_no(s):
    t = (s or "").strip().lower()
    return True if t.startswith("y") else False if t.startswith("n") else None


def parse_place(page_html, slug=None):
    """One place page -> a facts-only dict (see FIELD_MAP). Unknown labels are listed in `_unmapped`."""
    f = extract_fields(page_html)
    node, rid = place_nids(page_html)
    title = re.search(r'<h1><span class="field title">(.*?)</span>', page_html, re.S)
    p = {"nid": node or rid, "roster_id": rid, "slug": slug, "name": clean(title.group(1)) if title else None}
    for label, key in FIELD_MAP.items():
        if label in f:
            p[key] = f[label]
    p["state"] = state_code(p.get("state_name"))
    p["lat"], p["lon"] = signed_latlon(p.get("lat_raw"), p.get("lon_raw"), p.get("state_name"))
    p["existing"] = yes_no(p.get("existing"))
    p["open_to_public"] = yes_no(p.get("open_to_public")) if "open_to_public" in p else None
    p["start_year"] = to_year(p.get("start_year")) if "start_year" in p else None
    p["end_year"] = to_year(p.get("end_year")) if "end_year" in p else None
    p["established"] = to_year(p.get("established")) or p["start_year"]
    p["tower_established"] = to_year(p.get("tower_established")) if "tower_established" in p else None
    p["automated"] = to_year(p.get("automated")) if "automated" in p else None
    p["original_lens_year"] = to_year(p.get("original_lens_year")) if "original_lens_year" in p else None
    p["focal_height_ft"] = to_float(p.get("focal_height_ft"))
    p["tower_height_ft"] = to_float(p.get("tower_height_ft"))
    for key in ("active_aton", "private_aid", "fog_signal_building", "keepers_quarters"):
        if key in p:
            p[key] = yes_no(p[key])
    p["discontinued"] = next((to_year(f[l]) for l in DISCONTINUED_LABELS if l in f and to_year(f[l])), None) or p["end_year"]
    p["demolished"] = next((to_year(f[l]) for l in DEMOLISHED_LABELS if l in f and to_year(f[l])), None)
    known = set(FIELD_MAP) | set(DISCONTINUED_LABELS) | set(DEMOLISHED_LABELS)
    p["_unmapped"] = sorted(k for k in f if k not in known and k not in
                            ("download", "file type", "photo date", "photo credit", "photo courtesy of",
                             "entered by", "entered date", "image source", "collection / donor", "comments",
                             "non-existing (more info.)"))
    p["url"] = "%s/places/%s" % (BASE, urllib.parse.quote(slug)) if slug else None
    return {k: v for k, v in p.items() if v is not None}


# --------------------------------------------------------------------------------------------------
# Rosters
# --------------------------------------------------------------------------------------------------

def parse_span(txt):
    """'(at least 1950-1951)' -> (from, to, from_approx, to_approx). Missing ends are None."""
    t = re.sub(r"\s+", " ", txt or "").strip().strip("()").strip()
    halves = t.split("-", 1)
    halves = halves + [""] * (2 - len(halves))
    out = []
    for h in halves:
        approx = bool(re.search(r"at\s+least", h, re.I))
        out.append((to_year(h), approx))
    return out[0][0], out[1][0], out[0][1], out[1][1]


def parse_roster(json_text):
    """showPeople JSON -> [{name, role_raw, from, to, from_approx?, to_approx?, person}] in printed order."""
    try:
        j = json.loads(json_text)
        body = j[0]["data"]
    except (ValueError, KeyError, IndexError, TypeError):
        return []
    lines, role = [], None
    for m in re.finditer(r"<h5>(.*?)</h5>|<li>(.*?)</li>", body, re.S):
        if m.group(1) is not None:
            role = clean(m.group(1))
            continue
        li = m.group(2)
        a = re.search(r'<a href="[^"]*?/people/([^"?#]+)"[^>]*>(.*?)</a>(.*)$', li, re.S)
        if not a:
            continue
        frm, to, fa, ta = parse_span(clean(a.group(3)))
        span = re.sub(r"\s+", " ", clean(a.group(3))).strip()
        rec = {"name": clean(a.group(2)), "role_raw": role or "", "span": span.strip("() "), "from": frm, "to": to,
               "person": urllib.parse.unquote(a.group(1))}
        if fa:
            rec["from_approx"] = True
        if ta:
            rec["to_approx"] = True
        lines.append(rec)
    return lines


def normalise_role(raw, has_assistants=True):
    """USLHS heading -> the STORY_GUIDE role vocabulary (the printed heading is always kept as role_raw)."""
    r = (raw or "").lower().strip()
    if "acting" in r:
        return "acting keeper"
    if "principal" in r:
        return "head keeper" if has_assistants else "keeper"
    for pat, role in ((r"\b(1st|first)\b", "first assistant"), (r"\b(2nd|second)\b", "second assistant"),
                      (r"\b(3rd|third)\b", "third assistant"), (r"\b(4th|fourth)\b", "fourth assistant")):
        if re.search(pat, r) and "assistant" in r:
            return role
    if "assistant" in r:
        return "assistant"
    if "laborer" in r or "labourer" in r:
        return "laborer"
    if "lamplighter" in r or "lamp lighter" in r:
        return "lamplighter"
    if r in ("master", "captain") or r.startswith("master"):
        return "master"
    if r.startswith("mate") or " mate" in r:
        return "mate"
    if "engineer" in r:
        return "engineer"
    if any(w in r for w in ("seaman", "cook", "fireman", "oiler", "deckhand", "steward", "crew", "boatswain",
                            "coxswain", "pilot", "quartermaster")):
        return "crew"
    if "surfman" in r:
        return "surfman"
    if re.search(r"\bkeeper\b", r) and ("station" in r or "life" in r):
        return "station keeper"
    if re.fullmatch(r"(lighthouse )?keeper", r):
        return "keeper"
    if "volunteer" in r:
        return "volunteer keeper"
    if "civilian" in r:
        return "civilian keeper"
    return "other"


def roster_lines(raw_lines):
    has_asst = any("assistant" in (l["role_raw"] or "").lower() for l in raw_lines)
    out = []
    for l in raw_lines:
        l = dict(l)
        l["role"] = normalise_role(l["role_raw"], has_asst)
        if l["role"] == "other" and l["role_raw"]:
            l["role_note"] = ("Coast Guard personnel; position not stated" if l["role_raw"].upper() == "USCG"
                              else "USLHS heading: " + l["role_raw"])
        out.append(l)
    return out


# --------------------------------------------------------------------------------------------------
# build / stats
# --------------------------------------------------------------------------------------------------

def places_file():
    return os.path.join(uslhs_dir(), "places.json")


def rosters_file():
    return os.path.join(uslhs_dir(), "rosters.json")


def cmd_build(a):
    rows = cached_index_slugs()
    places, rosters, missing, unmapped = [], {}, [], {}
    for r in rows:
        path = place_path(r["slug"])
        if not os.path.exists(path):
            missing.append(r["slug"])
            continue
        page = polite.read_text(path)
        p = parse_place(page, r["slug"])
        p.setdefault("name", r["name"])
        if not p.get("type") and r.get("type"):
            p["type"] = r["type"]
        if not p.get("state_name") and r.get("state"):
            p["state_name"], p["state"] = r["state"], state_code(r["state"])
        for u in p.pop("_unmapped", []):
            unmapped[u] = unmapped.get(u, 0) + 1
        rid = p.get("roster_id")
        if rid and os.path.exists(people_path(rid)):
            lines = roster_lines(parse_roster(polite.read_text(people_path(rid))))
            p["roster_lines"] = len(lines)
            rosters[str(rid)] = {"slug": r["slug"], "name": p["name"], "lines": lines}
        else:
            p["roster_lines"] = 0
        places.append(p)
    os.makedirs(uslhs_dir(), exist_ok=True)
    polite.write_json(places_file(), places, indent=0, ensure_ascii=False)
    polite.write_json(rosters_file(), rosters, indent=0, ensure_ascii=False)
    log("built %d places (%d not fetched yet), %d rosters" % (len(places), len(missing), len(rosters)))
    if unmapped:
        log("labels not in FIELD_MAP (review): " + ", ".join("%s x%d" % kv for kv in sorted(unmapped.items())))
    return 0


def load_data():
    try:
        places = polite.read_json(places_file())
        rosters = polite.read_json(rosters_file())
    except OSError:
        sys.exit("No parsed USLHS cache at %s. Run `research/roster.py build` (after `crawl`)." % uslhs_dir())
    return places, rosters


def cmd_stats(a):
    places, rosters = load_data()
    by_type = {}
    for p in places:
        by_type[p.get("type", "?")] = by_type.get(p.get("type", "?"), 0) + 1
    with_roster = sum(1 for p in places if p.get("roster_lines"))
    lines = sum(len(r["lines"]) for r in rosters.values())
    print("places: %d" % len(places))
    for t, n in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print("  %-48s %5d" % (t, n))
    print("places with a roster: %d" % with_roster)
    print("roster lines: %d" % lines)
    print("places with coordinates: %d" % sum(1 for p in places if "lat" in p and "lon" in p))
    return 0


# --------------------------------------------------------------------------------------------------
# Lookup
# --------------------------------------------------------------------------------------------------

GENERIC = {"light", "lights", "lighthouse", "lighthouses", "station", "lightstation", "life", "saving", "lifesaving",
           "the", "of", "light-station", "lss", "uscg", "ls", "lh"}
ABBREV = {"pt": "point", "st": "saint", "ft": "fort", "mt": "mount", "isl": "island", "is": "island", "hbr": "harbor",
          "harbour": "harbor", "pk": "park", "cr": "creek", "&": "and", "ls": "lifesaving"}


def name_tokens(name):
    import unicodedata
    t = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    t = t.replace("&", " and ").replace("-", " ").replace("'", "")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    toks = [ABBREV.get(w, w) for w in t.split()]
    toks = [w for w in toks if w not in GENERIC]
    return toks or [w for w in t.split()]


def name_score(a, b):
    from difflib import SequenceMatcher
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return 0.0
    if ta == tb:
        return 1.0
    sa, sb = set(ta), set(tb)
    contain = len(sa & sb) / min(len(sa), len(sb))
    jacc = len(sa & sb) / len(sa | sb)
    seq = SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()
    return round(max(seq, 0.9 * contain * (0.5 + 0.5 * jacc) + 0.05 * contain), 3)


def haversine_km(lat1, lon1, lat2, lon2):
    from math import asin, cos, radians, sin, sqrt
    p1, p2 = radians(lat1), radians(lat2)
    d = sin((p2 - p1) / 2) ** 2 + cos(p1) * cos(p2) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * asin(sqrt(d))


def rank_candidates(places, names, state=None, near=None, kinds=None):
    """-> [(rank, name_score, dist_km|None, place)] best first."""
    code = state_code(state) if state else None
    prefer_light = not kinds and not any(re.search(r"life|saving|surf|lightship|vessel", n or "", re.I) for n in names)
    out = []
    for p in places:
        if code and p.get("state") and p["state"] != code:
            continue
        if kinds and not any(k in p.get("type", "").lower() for k in kinds):
            continue
        sc = max((name_score(n, p.get("name", "")) for n in names), default=0.0) if names else 0.0
        d = None
        if near and "lat" in p and "lon" in p:
            d = haversine_km(near[0], near[1], p["lat"], p["lon"])
        rank = sc
        if prefer_light and p.get("type") == "Light Station":
            rank += 0.12  # a name shared by a light and its life-saving station means the light, unless asked otherwise
        if d is not None:
            rank += 0.3 if d <= 1 else 0.15 if d <= 5 else 0.05 if d <= 25 else (-0.2 if d > 100 else 0.0)
        if names and sc < 0.55 and (d is None or d > 1):
            continue
        out.append((rank, sc, d, p))
    out.sort(key=lambda x: (-x[0], x[3].get("name", "")))
    return out


def fmt_span(l):
    f = "%d" % l["from"] if l.get("from") else "?"
    t = "%d" % l["to"] if l.get("to") else "?"
    star = "*" if l.get("from_approx") or l.get("to_approx") else ""
    return "%s-%s%s" % (f, t, star)


def place_header(p):
    bits = [p.get("type", "")]
    if p.get("town"):
        bits.append(p["town"].title())
    if p.get("county"):
        bits.append(p["county"].title() + " Co.")
    if p.get("state"):
        bits.append(p["state"])
    s = "%s — %s" % (p.get("name", "?"), ", ".join(b for b in bits if b))
    extra = []
    if p.get("established"):
        extra.append("est. %d" % p["established"])
    if p.get("existing") is not None:
        extra.append("standing/existing" if p["existing"] else "not existing")
    if p.get("discontinued"):
        extra.append("discontinued %d" % p["discontinued"])
    if p.get("automated"):
        extra.append("automated %d" % p["automated"])
    if "lat" in p:
        extra.append("%.4f, %.4f" % (p["lat"], p["lon"]))
    return s + (" (" + "; ".join(extra) + ")" if extra else "")


def print_roster(p, rosters, detail=0, as_json=False, max_lines=500):
    r = rosters.get(str(p.get("roster_id") or p.get("nid")))
    lines = r["lines"] if r else []
    if as_json:
        print(json.dumps({"place": {k: v for k, v in p.items()}, "roster": lines}, ensure_ascii=False, indent=1))
        return
    print(place_header(p))
    print("Cite: USLHS Digital Archive, \"%s\" place record, %s ; roster %s/general/showPeople/%s "
          "(facts only: NARA Registers of Lighthouse Keepers via the Kraig Anderson inventory; confirm each "
          "keeper in a primary record before a story names them)"
          % (p.get("name"), p.get("url"), BASE, p.get("roster_id") or p.get("nid")))
    if not lines:
        print("ROSTER: none listed")
        return
    yrs = [y for l in lines for y in (l.get("from"), l.get("to")) if y]
    print("ROSTER: %d lines, %d-%d  (lines are printed exactly as the archive prints them, so they can be quoted as "
          "evidence; \"at least\" marks a documented span, not necessarily the whole term)"
          % (len(lines), min(yrs) if yrs else 0, max(yrs) if yrs else 0))
    shown, role_raw = 0, None
    details = {}
    if detail:
        details = fetch_details(lines[:detail], p.get("slug"))
    for l in lines:
        if shown >= max_lines:
            print("... %d more lines (use --max-lines or --json)" % (len(lines) - shown))
            break
        if l["role_raw"] != role_raw:
            role_raw = l["role_raw"]
            print("%s  [%s]" % (role_raw or "(no heading)", l["role"]))
        extra = details.get(l["person"], "")
        print("  %s (%s)%s" % (l["name"], l.get("span") or fmt_span(l), ("  " + extra) if extra else ""))
        shown += 1


# -- on-demand person detail (salary, born/died, source): one request per person, cached ----------

def person_path(slug):
    return os.path.join(uslhs_dir(), "person", urllib.parse.quote(slug, safe="") + ".html")


def parse_person(page_html):
    """Facts from a person page: stints [{place, position, from, to, begin_salary, end_salary}], source."""
    out = {"stints": []}
    f = extract_fields(page_html)
    for k, key in (("born", "born"), ("died", "died")):
        if k in f:
            out[key] = to_year(f[k])
    if "source" in f:
        out["source"] = f["source"]
    for blk in page_html.split("paragraph--type--place-years")[1:]:
        blk = blk.split("</article>")[0]
        g = extract_fields("<article>" + blk + "</article>")
        place = re.search(r'href="/places/([^"]+)"', blk)
        out["stints"].append({
            "place": urllib.parse.unquote(place.group(1)) if place else None,
            "position": g.get("title / position"), "from": to_year(g.get("year started")),
            "to": to_year(g.get("year departed")), "begin_salary": to_float(g.get("begin salary")),
            "end_salary": to_float(g.get("end salary"))})
    return out


def fetch_details(lines, place_slug):
    res = {}
    for l in lines:
        slug = l["person"]
        try:
            page, _ = fetch_cached("%s/people/%s" % (BASE, urllib.parse.quote(slug)), person_path(slug),
                                   lambda t: "<h1>" in t)
        except polite.PoliteError as e:
            res[slug] = "(detail unavailable: %s)" % e
            continue
        d = parse_person(page)
        st = next((s for s in d["stints"] if s["place"] == place_slug and s["from"] == l.get("from")), None) \
            or next((s for s in d["stints"] if s["place"] == place_slug), None)
        bits = []
        if st and (st["begin_salary"] or st["end_salary"]):
            bits.append("$%g" % st["begin_salary"] if st["begin_salary"] == st["end_salary"] else
                        "$%s-%s" % (("%g" % st["begin_salary"]) if st["begin_salary"] else "?",
                                    ("%g" % st["end_salary"]) if st["end_salary"] else "?"))
        if d.get("source"):
            bits.append("src: " + d["source"])
        if d.get("died"):
            bits.append("b.%s d.%s" % (d.get("born") or "?", d["died"]))
        res[slug] = "[" + "; ".join(bits) + "]" if bits else ""
    return res


# -- the cached pages as text, for research/fetch_text.py (so check_quotes can verify quotes offline) ----

def place_text(slug=None, rid=None):
    """Plain text of a cached place page (its fact fields) followed by its roster, as the archive prints
    them; None when the page is not cached."""
    if slug and os.path.exists(place_path(slug)):
        page = polite.read_text(place_path(slug))
        _, rid = place_nids(page)
        out = [clean(re.search(r'<h1><span class="field title">(.*?)</span>', page, re.S).group(1)) if "<h1>" in page else slug]
        art = page[page.find("<article>"):page.find("</article>")]
        for chunk in re.split(r'<div class="field_label">', art)[1:]:
            lab, _, rest = chunk.partition("</div>")
            rest = re.split(r'<h3|<h5|<div class="flex-grid"|<div class="row"|<div class="garydata"|'
                            r'<div class="large-6 columns"|<div class="field_label">', rest)[0]
            lab, val = clean(lab), clean(rest)
            if lab and val and norm_label(lab) in set(FIELD_MAP) | set(DISCONTINUED_LABELS) | set(DEMOLISHED_LABELS):
                out.append("%s %s" % (lab if lab.endswith(":") else lab + ":", val))
    else:
        out = []
    if rid and os.path.exists(people_path(rid)):
        raw = parse_roster(polite.read_text(people_path(rid)))
        out.append("")
        out.append("People (%s/general/showPeople/%s)" % (BASE, rid))
        role = None
        for l in raw:
            if l["role_raw"] != role:
                role = l["role_raw"]
                out.append(role)
            out.append("%s (%s)" % (l["name"], l.get("span", "")))
    return "\n".join(out) + "\n" if out else None


def local_text_for_url(url):
    """If `url` is a USLHS place page or roster endpoint we hold in the cache, its text (str), else None."""
    u = urllib.parse.urlsplit(url)
    if u.netloc.lower() != "archives.uslhs.org":
        return None
    m = re.match(r"^/places/([^/?#]+)/?$", u.path)
    if m:
        return place_text(slug=urllib.parse.unquote(m.group(1)))
    m = re.match(r"^/general/showPeople/(\d+)/?$", u.path)
    if m and os.path.exists(people_path(int(m.group(1)))):
        return place_text(rid=int(m.group(1)))
    return None


# -- station-id resolution ------------------------------------------------------------------------

def stations_dir():
    return os.environ.get("FRESNEL_STATIONS_DIR") or os.path.join(polite.REPO, "data", "stations")


def station_record(station_id):
    """(record or None, note). Looks in data/stations/<dir>/<id>.json."""
    m = re.match(r"^([a-z]{2})-([a-z]{2})-(.+)$", station_id)
    if not m:
        return None, "not a station id (expected <country>-<region>-<slug>)"
    country, region, slug = m.groups()
    folder = region if country == "us" else "%s-%s" % (country, region)
    path = os.path.join(stations_dir(), folder, station_id + ".json")
    if os.path.exists(path):
        return polite.read_json(path), None
    return None, "no station record at %s" % path


def resolve_station(station_id, places):
    """-> (place or None, candidates, message). Confident = a name match within ~1 km (or a unique exact
    name match in the state when the station has no position)."""
    m = re.match(r"^([a-z]{2})-([a-z]{2})-(.+)$", station_id)
    if not m:
        return None, [], "'%s' is not a station id; use --place or --name" % station_id
    country, region, slug = m.groups()
    if country != "us":
        return None, [], "USLHS covers the United States only; %s is not a US station" % station_id
    rec, note = station_record(station_id)
    names = [slug.replace("-", " ")]
    near = None
    kinds = None
    if rec:
        names = [rec.get("name", "")] + list(rec.get("other_names") or []) + names
        loc = rec.get("location") or {}
        if loc.get("lat") is not None and loc.get("lon") is not None:
            near = (float(loc["lat"]), float(loc["lon"]))
        if rec.get("kind") == "life_saving_station":
            kinds = ["lifesaving"]
        elif rec.get("kind") in ("lightship_station", "lightship"):
            kinds = ["lightship"]
        region = (rec.get("region") or region).lower()
    cands = rank_candidates(places, names, state=region.upper(), near=near, kinds=kinds)
    if not cands:
        return None, cands, "; ".join(x for x in (note, "no USLHS place matches the name and state") if x)
    top = cands[0]
    rivals = [c for c in cands[1:] if c[1] >= 0.85 and c[0] >= top[0] - 0.1 and (near is None or c[2] is None or c[2] <= 30.0)]
    close = top[2] is not None and top[2] <= 1.0
    # USLHS positions are only to the nearest minute (and sometimes off by more), so an exact, unrivalled name
    # within 30 km is accepted with a warning; a name that merely resembles the station must be within 1 km.
    near_enough = top[2] is not None and top[2] <= 30.0 and top[1] >= 0.95 and not rivals
    by_name_only = near is None and top[1] >= 0.95 and not rivals
    if top[1] >= 0.85 and (close and not [r for r in rivals if r[2] is not None and r[2] <= 1.0] or near_enough or by_name_only):
        if close:
            how = "name and position (%.2f km)" % top[2]
        elif near_enough:
            how = "name; its USLHS position is %.1f km from the station's (USLHS positions are only to the minute)" % top[2]
        else:
            how = "name only (the station has no position)"
        msg = "matched %s by %s" % (top[3]["slug"], how)
        if note:
            msg += "; " + note
        return top[3], cands, msg
    return None, cands, "unsure which USLHS place is %s; candidates below (re-run with --place <slug>)" % station_id


def find_place(key, places):
    k = key.strip()
    for p in places:
        if k.isdigit() and k in (str(p.get("nid")), str(p.get("roster_id"))):
            return p
        if p.get("slug") == k:
            return p
    low = [p for p in places if p.get("slug", "").lower() == k.lower()]
    return low[0] if low else None


def print_candidates(cands, rosters, limit=8):
    for rank, sc, d, p in cands[:limit]:
        print("  %.2f  %-8s %-44s %-24s %-2s  slug=%s nid=%s  roster=%d lines"
              % (sc, ("%.1f km" % d) if d is not None else "-", (p.get("name") or "")[:44], (p.get("type") or "")[:24],
                 p.get("state") or "", p.get("slug"), p.get("nid"), p.get("roster_lines", 0)))


def cmd_lookup(a):
    places, rosters = load_data()
    near = None
    if a.near:
        try:
            near = tuple(float(x) for x in a.near.split(","))
            assert len(near) == 2
        except (ValueError, AssertionError):
            sys.exit("--near wants lat,lon in decimal degrees")
    if a.place:
        p = find_place(a.place, places)
        if not p:
            cands = rank_candidates(places, [a.place.replace("-", " ")], near=near)
            print("No USLHS place with slug or node id '%s'. Closest names:" % a.place)
            print_candidates(cands, rosters)
            return 1
        print_roster(p, rosters, a.detail, a.json, a.max_lines)
        return 0
    if a.name or (near and not a.station):
        cands = rank_candidates(places, [a.name] if a.name else [], state=a.state, near=near)
        if not a.name:
            cands.sort(key=lambda x: x[2] if x[2] is not None else 1e9)
        if not cands:
            print("No USLHS place matches.")
            return 1
        print("Best matches for %r%s:" % (a.name or "(position)", " in " + a.state if a.state else ""))
        print_candidates(cands, rosters, a.top)
        top = cands[0]
        if a.name and not a.no_roster and top[1] >= 0.85 and (len(cands) < 2 or cands[1][0] < top[0] - 0.1
                                                              or cands[1][1] < 0.85):
            print()
            print_roster(top[3], rosters, a.detail, a.json, a.max_lines)
        return 0
    if a.station:
        p, cands, msg = resolve_station(a.station, places)
        print("# " + msg)
        if p:
            print_roster(p, rosters, a.detail, a.json, a.max_lines)
            return 0
        print_candidates(cands, rosters, a.top)
        return 2
    return 1


def build_parser():
    ap = argparse.ArgumentParser(
        description="Keeper rosters from the USLHS Digital Archive cache (facts only). Maintenance commands: "
                    "crawl, build, stats.", usage="roster.py [<station-id> | --place SLUG|NID | --name NAME "
                    "[--state XX] [--near LAT,LON]] [--detail N] [--json] | crawl | build | stats")
    ap.add_argument("station", nargs="?", help="a Fresnel station id such as us-me-portland-head")
    ap.add_argument("--place", help="USLHS place slug (portland-head) or node id (2931)")
    ap.add_argument("--name", help="station name to match (fuzzy)")
    ap.add_argument("--state", help="two-letter state or territory code, to narrow --name")
    ap.add_argument("--near", help="lat,lon in decimal degrees; ranks matches by distance")
    ap.add_argument("--detail", type=int, default=0, metavar="N",
                    help="also fetch the first N people's pages (1 request each, cached) for salaries and the source")
    ap.add_argument("--json", action="store_true", help="print the place and roster as JSON")
    ap.add_argument("--no-roster", action="store_true", help="with --name: candidates only")
    ap.add_argument("--top", type=int, default=6, help="candidates to list (default 6)")
    ap.add_argument("--max-lines", type=int, default=500)
    return ap


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "crawl":
        ap = argparse.ArgumentParser(prog="roster.py crawl")
        ap.add_argument("--limit", type=int)
        ap.add_argument("--only", nargs="*")
        return cmd_crawl(ap.parse_args(argv[1:]))
    if argv and argv[0] == "build":
        return cmd_build(None)
    if argv and argv[0] == "stats":
        return cmd_stats(None)
    a = build_parser().parse_args(argv)
    if not (a.station or a.place or a.name or a.near):
        build_parser().print_help()
        return 1
    return cmd_lookup(a)


if __name__ == "__main__":
    sys.exit(main())
