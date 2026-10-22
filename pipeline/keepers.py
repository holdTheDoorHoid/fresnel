#!/usr/bin/env python3
"""The keepers index (DESIGN.md 3.6): people records, archive rosters for stations, and the data the
website loads for /keepers/ and /k/<person-id>/.

This module is the rules; `pipeline/build_people.py` is the command that reads the USLHS cache and
writes the committed files, and `pipeline/build_site_data.py` calls `KeeperData` and `write_site`.

THE RULES (each has a test in pipeline/test_keepers.py)

1. One person = one record in the U.S. Lighthouse Society's Digital Archive (its `/people/<slug>`
   page; the slug is the person id here). Roster lines that name the same archive record are the
   stints of one person. **Two records are never joined because their names match.** Where two
   records share a name and their years and region fit, each page may say "possibly the same person
   as ..." and nothing more (`add_possible`).
2. **Living people.** A person with any recorded stint that begins in 1950 or later, or ends after
   1960, or whose stints carry no year at all, gets no person page and no index entry. A stint with
   no end year is read as lasting OPEN_END_YEARS (so one that began in 1931 or later might have
   ended after 1960). The person stays only as a line in the roster tables of the stations, exactly
   as the archive prints it (`withhold_reason`). The archive's race and sex fields are never read.
3. **Research rosters** (data/research/<station>.json `keepers`) join a person only where the line
   names the archive record (`person`) or carries `other_stations`, each with a `cite`
   (`KeeperData._layer_research`). A research line with neither stays a roster-table row.
4. Facts only from the archive ("All Rights Reserved"): names, roles, years, places. No prose.

Python 3.12, standard library only.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Iterable

# ---------------------------------------------------------------------------------------------
# The living-people rule (DESIGN.md 3.6)
# ---------------------------------------------------------------------------------------------

CUTOFF_BEGIN = 1950   # service that begins in this year or later is withheld ...
CUTOFF_END = 1960     # ... and so is service that ends after this year
OPEN_END_YEARS = 30   # a stint with no end year is read as running this long (a long career)
MIN_YEAR, MAX_YEAR = 1700, 2030  # a year outside this is a typing slip in the archive ("1560-1943")

ARCHIVE = "https://archives.uslhs.org"
PERSON_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# A research-only person: <station id>--<name slug>. The double hyphen cannot occur in an archive slug.
RESEARCH_ID_RE = re.compile(r"^[a-z]{2}-[a-z0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*--[a-z0-9]+(?:-[a-z0-9]+)*$")
YEAR_RX = re.compile(r"(1[5-9]\d\d|20\d\d)")

# The archive's section headings that map to a fixed role; any other heading is shown as printed.
STANDARD_HEADINGS = {
    "Principal Lighthouse Keeper", "Acting Principal Lighthouse Keeper", "1st Assistant Lighthouse Keeper",
    "2nd Assistant Lighthouse Keeper", "3rd Assistant Lighthouse Keeper", "4th Assistant Lighthouse Keeper",
    "Laborer",
}


def _year(text: str) -> int | None:
    m = YEAR_RX.search(text or "")
    if not m:
        return None
    y = int(m.group(1))
    return y if MIN_YEAR <= y <= MAX_YEAR else None


def parse_span(span: str | None) -> tuple[int | None, int | None, bool, bool]:
    """'at least 1950-1951' -> (1950, 1951, True, False). Years are read from the span as printed:
    '1950s-' gives 1950 (approximate), '1912.10.01-1913' gives 1912 and 1913, '-' gives None, None."""
    s = re.sub(r"\s+", " ", span or "").strip()
    a, _, b = s.partition("-")
    b = b.split("-")[0]

    def half(t: str) -> tuple[int | None, bool]:
        y = _year(t)
        approx = bool(re.search(r"at\s+least", t, re.I)) or bool(re.search(r"\d{4}s\b", t))
        return y, approx and y is not None

    fa, fa_ap = half(a)
    ta, ta_ap = half(b)
    return fa, ta, fa_ap, ta_ap


def withhold_reason(stints: Iterable[dict]) -> str | None:
    """Why a person gets no page, or None when they may have one (the module docstring, rule 2).
    Reasons: 'begins' (a stint begins in CUTOFF_BEGIN or later), 'ends' (a stint ends after
    CUTOFF_END), 'open' (a stint with no end year began so late it may have ended after CUTOFF_END),
    'undated' (no stint has a year)."""
    stints = list(stints)
    if not any(s.get("from") is not None or s.get("to") is not None for s in stints):
        return "undated"
    for s in stints:
        f, t = s.get("from"), s.get("to")
        if f is not None and f >= CUTOFF_BEGIN:
            return "begins"
        if t is not None and t > CUTOFF_END:
            return "ends"
        if t is None and f is not None and f + OPEN_END_YEARS > CUTOFF_END:
            return "open"
    return None


# ---------------------------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------------------------

_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "2nd", "3rd"}


def norm_name(name: str) -> str:
    """The name folded for comparison: ASCII, lower case, punctuation gone, single spaces.
    'Jr.' and 'Sr.' are kept, so a father and a son never compare equal."""
    t = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())


def surname_and_given(name: str) -> tuple[str, str]:
    """('strout', 'joshua f') for 'Joshua F. Strout'; nicknames in quotes or brackets and a trailing
    Jr. / Sr. / III are not part of the surname."""
    t = re.sub(r'\([^)]*\)|"[^"]*"', " ", name or "")
    toks = [w for w in norm_name(t).split() if w]
    while len(toks) > 1 and toks[-1] in _SUFFIXES:
        toks.pop()
    if not toks:
        return "", ""
    return toks[-1], " ".join(toks[:-1])


def sort_key(name: str) -> tuple[str, str]:
    return surname_and_given(name)


def letter_of(name: str) -> str:
    """The index chunk a name belongs to: the first letter of the surname, or '#'."""
    sur, _ = surname_and_given(name)
    c = sur[:1]
    return c.upper() if c.isalpha() and c.isascii() else "#"


def research_person_id(station_id: str, name: str, taken: set[str]) -> str:
    slug = "-".join(norm_name(name).split()) or "unnamed"
    base = f"{station_id}--{slug}"
    pid, n = base, 1
    while pid in taken:
        n += 1
        pid = f"{base}-{n}"
    return pid


# ---------------------------------------------------------------------------------------------
# Stints and people from the archive's roster lines
# ---------------------------------------------------------------------------------------------


# research/roster.py maps every heading with "acting" to "acting keeper"; two of the archive's are not that.
ROLE_FIXES = {
    "Acting Assistant": "assistant",
    "Temporary / Relief / Substitute Keeper (who is not Acting for Principal Keeper)": "other",
}


def make_line(raw: dict) -> dict:
    """An archive roster line (research/roster.py's rosters.json) in the shape the data files keep:
    name, role (normalised), role_raw only when the heading is not one of the standard seven, span as
    printed, years read from the span, and the archive's person slug."""
    f, t, fa, ta = parse_span(raw.get("span"))
    heading = raw.get("role_raw") or ""
    line: dict = {"name": raw["name"], "role": ROLE_FIXES.get(heading) or raw.get("role") or "other"}
    if heading and heading not in STANDARD_HEADINGS:
        line["role_raw"] = heading
    line["span"] = re.sub(r"\s+", " ", raw.get("span") or "").strip()
    if f is not None:
        line["from"] = f
    if t is not None:
        line["to"] = t
    if fa:
        line["from_approx"] = True
    if ta:
        line["to_approx"] = True
    line["person"] = raw["person"]
    return line


def _stint_of(line: dict, place_slug: str, place_name: str, state: str | None) -> dict:
    s: dict = {"place": place_slug, "place_name": place_name}
    if state:
        s["state"] = state
    for k in ("role", "role_raw", "span", "from", "to", "from_approx", "to_approx"):
        if k in line:
            s[k] = line[k]
    return s


def _stint_order(s: dict) -> tuple:
    y = s.get("from") if s.get("from") is not None else s.get("to")
    return (y if y is not None else 9999, s.get("to") if s.get("to") is not None else 9999, s.get("place", s.get("station", "")))


def group_people(rosters: dict, places_by_slug: dict[str, dict]) -> dict[str, dict]:
    """Every person the archive's rosters name, keyed by the archive person slug: lines that name the
    same archive record are one person's stints. Nothing here looks at a name to join two records."""
    people: dict[str, dict] = {}
    for rid in sorted(rosters, key=lambda k: (rosters[k]["slug"], k)):
        ro = rosters[rid]
        place = places_by_slug.get(ro["slug"], {})
        for raw in ro["lines"]:
            pid = raw["person"]
            p = people.setdefault(pid, {"id": pid, "name": raw["name"], "stints": []})
            p["stints"].append(_stint_of(make_line(raw), ro["slug"], ro.get("name") or place.get("name") or ro["slug"],
                                         place.get("state")))
    for p in people.values():
        p["stints"].sort(key=_stint_order)
    return people


# ---------------------------------------------------------------------------------------------
# "Possibly the same person as ..."
# ---------------------------------------------------------------------------------------------

MAX_GAP_YEARS = 6      # years between one career ending and the other beginning
MAX_NEAR_KM = 150.0    # when the states differ: stations this close count as one region
MAX_HINTS = 3          # more candidates than this and the name is too common to say anything


def _span_of(p: dict) -> tuple[int, int] | None:
    ys = [y for s in p["stints"] for y in (s.get("from"), s.get("to")) if y is not None]
    return (min(ys), max(ys)) if ys else None


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    (la1, lo1), (la2, lo2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    d = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(d))


def _regions_fit(a: dict, b: dict, coords: dict[str, tuple[float, float]]) -> bool:
    sa = {s.get("state") for s in a["stints"]} - {None}
    sb = {s.get("state") for s in b["stints"]} - {None}
    if sa & sb:
        return True
    for x in a["stints"]:
        for y in b["stints"]:
            cx, cy = coords.get(x.get("place", "")), coords.get(y.get("place", ""))
            if cx and cy and _km(cx, cy) <= MAX_NEAR_KM:
                return True
    return False


def fits(a: dict, b: dict, coords: dict[str, tuple[float, float]]) -> bool:
    """Two different archive records with one name: do their years and regions fit one person's
    career? One career ends within MAX_GAP_YEARS of the other beginning (or just before it ends: a
    year's overlap is a transfer), in the same state or within MAX_NEAR_KM. Careers that overlap
    more than that are two people."""
    sa, sb = _span_of(a), _span_of(b)
    if not sa or not sb:
        return False
    first, second = (sa, sb) if sa[0] <= sb[0] else (sb, sa)
    gap = second[0] - first[1]
    if gap < -1 or gap > MAX_GAP_YEARS:
        return False
    return _regions_fit(a, b, coords)


def add_possible(people: dict[str, dict], coords: dict[str, tuple[float, float]]) -> int:
    """Set `possibly` (a sorted list of person ids) on people whose name another record shares and
    whose years and region fit. A pair is listed only when each side lists the other and neither has
    more than MAX_HINTS candidates. Returns the number of people with a hint."""
    for p in people.values():
        p.pop("possibly", None)
    by_name: dict[str, list[dict]] = defaultdict(list)
    for p in people.values():
        by_name[norm_name(p["name"])].append(p)
    cands: dict[str, set[str]] = {}
    for group in by_name.values():
        if len(group) < 2:
            continue
        for a in group:
            cands[a["id"]] = {b["id"] for b in group if b is not a and fits(a, b, coords)}
    n = 0
    for pid, c in cands.items():
        if not c or len(c) > MAX_HINTS:
            continue
        keep = sorted(o for o in c if cands.get(o) and len(cands[o]) <= MAX_HINTS and pid in cands[o])
        if keep:
            people[pid]["possibly"] = keep
            n += 1
    return n


def far_overlaps(p: dict, coords: dict[str, tuple[float, float]], km: float = 100.0, years: int = 2) -> bool:
    """True when the archive files two stints under one record that overlap in time by `years` or more
    at places `km` or more apart: a sign the record may hold two people (or a wrong place)."""
    st = [s for s in p["stints"] if s.get("from") is not None]
    for i, a in enumerate(st):
        for b in st[i + 1:]:
            if a.get("place") == b.get("place"):
                continue
            ea = a.get("to") if a.get("to") is not None else a["from"]
            eb = b.get("to") if b.get("to") is not None else b["from"]
            if min(ea, eb) - max(a["from"], b["from"]) < years:
                continue
            ca, cb = coords.get(a.get("place", "")), coords.get(b.get("place", ""))
            if ca and cb and _km(ca, cb) >= km:
                return True
    return False


# ---------------------------------------------------------------------------------------------
# Which archive place is which station
# ---------------------------------------------------------------------------------------------


def match_places(stations: Iterable[dict], places: list[dict], rosters: dict,
                 resolve: Callable[[str, list[dict]], tuple[dict | None, list, str]] | None = None) -> dict[str, list[dict]]:
    """station id -> [{slug, nid, how}] for every visible US station and the archive places whose
    rosters it shows.

    1. The merge's own join first: a station whose `sources` hold `uslhs:<nid>` shows that place's
       roster (the merge matched name and position and a person reviewed the doubtful ones,
       docs/sources/review_2026-10-us.md). A station may hold several places (a range's front and rear).
    2. A station with no archive record at all is matched as `research/roster.py` does (`resolve`), and
       accepted only when the match is by name AND position within 1 km, the place is claimed by no
       station's merge key, and no other station is matched to the same place.
    """
    by_nid = {str(p["nid"]): p for p in places if p.get("nid") is not None}
    has_roster = {str(rid) for rid, ro in rosters.items() if ro.get("lines")}
    stations = [s for s in stations if isinstance(s, dict)]
    claimed: set[str] = set()
    out: dict[str, list[dict]] = {}
    keyless: list[dict] = []
    for s in sorted(stations, key=lambda s: s.get("id", "")):
        keys = []
        for src in s.get("sources") or []:
            if isinstance(src, dict) and src.get("source") == "uslhs" and ":" in str(src.get("key")):
                nid = str(src["key"]).split(":", 1)[1]
                if nid not in keys:
                    keys.append(nid)
        claimed.update(keys)
        if s.get("hidden") or s.get("merged_into") or s.get("country") != "US":
            continue
        if not keys:
            keyless.append(s)
            continue
        found = [{"slug": by_nid[k]["slug"], "nid": int(k), "how": f"merge (uslhs:{k})"}
                 for k in keys if k in by_nid and k in has_roster]
        if found:
            out[s["id"]] = sorted(found, key=lambda m: (by_nid[str(m["nid"])].get("name", ""), m["slug"]))
    if resolve:
        proposals: dict[str, list[tuple[dict, str]]] = defaultdict(list)
        for s in keyless:
            place, _cands, msg = resolve(s["id"], places)
            if (place and "by name and position" in msg and str(place.get("nid")) in has_roster
                    and str(place.get("nid")) not in claimed
                    and (not place.get("state") or place["state"] == s.get("region"))):
                proposals[str(place["nid"])].append((s, msg))
        for nid, props in sorted(proposals.items()):
            if len(props) == 1:
                s, msg = props[0]
                out[s["id"]] = [{"slug": by_nid[nid]["slug"], "nid": int(nid), "how": "name and position (" + msg.split("(")[-1].rstrip(")") + ")"}]
    return out


# ---------------------------------------------------------------------------------------------
# Building the committed files from the archive cache
# ---------------------------------------------------------------------------------------------


def build(places: list[dict], rosters: dict, stations: Iterable[dict],
          resolve: Callable[[str, list[dict]], tuple[dict | None, list, str]] | None = None) -> dict:
    """People records, station rosters and a report from the archive cache. Returns
    {'people': {id: record}, 'station_rosters': {station id: record}, 'report': {...}}.
    The report holds counts only: it never names a withheld person."""
    places_by_slug = {p["slug"]: p for p in places}
    coords = {p["slug"]: (p["lat"], p["lon"]) for p in places
              if p.get("lat") is not None and p.get("lon") is not None and not p.get("coord_suspect")}
    everyone = group_people(rosters, places_by_slug)
    reasons: Counter[str] = Counter()
    people: dict[str, dict] = {}
    for pid, p in everyone.items():
        why = withhold_reason(p["stints"])
        if why:
            reasons[why] += 1
        else:
            people[pid] = {"id": pid, "name": p["name"], "source": "uslhs", "archive": f"{ARCHIVE}/people/{pid}",
                           "stints": p["stints"]}
    hinted = add_possible(people, coords)
    for p in people.values():
        if far_overlaps(p, coords):
            p["check"] = "far_overlap"

    matches = match_places(stations, places, rosters, resolve)
    station_rosters: dict[str, dict] = {}
    by_nid = {str(p["nid"]): p for p in places if p.get("nid") is not None}
    for sid, ms in sorted(matches.items()):
        entry = {"station": sid, "source": "uslhs", "places": []}
        for m in ms:
            place = by_nid[str(m["nid"])]
            ro = rosters[str(m["nid"])]
            entry["places"].append({"slug": m["slug"], "nid": m["nid"], "name": place.get("name") or ro.get("name"),
                                    "url": f"{ARCHIVE}/places/{m['slug']}", "match": m["how"],
                                    "lines": [make_line(l) for l in ro["lines"]]})
        station_rosters[sid] = entry

    lines_all = sum(len(r["lines"]) for r in rosters.values())
    place_station = {m["slug"]: sid for sid, ms in matches.items() for m in ms}
    multi = sum(1 for p in people.values() if len({place_station.get(s["place"], s["place"]) for s in p["stints"]}) > 1)
    report = {
        "source": "uslhs", "rule": {"withheld_if_any_stint_begins_in_or_after": CUTOFF_BEGIN,
                                    "or_ends_after": CUTOFF_END, "or_has_no_year_at_all": True,
                                    "stint_without_end_read_as_lasting_years": OPEN_END_YEARS},
        "archive_people": len(everyone), "archive_roster_lines": lines_all, "archive_rosters": len(rosters),
        "people_published": len(people), "people_with_stints_at_several_places": multi,
        "people_withheld": sum(reasons.values()), "withheld_by_reason": dict(sorted(reasons.items())),
        "people_with_possible_matches": hinted,
        "people_flagged_far_overlap": sum(1 for p in people.values() if p.get("check")),
        "stations_with_archive_roster": len(station_rosters),
        "station_roster_lines": sum(len(pl["lines"]) for r in station_rosters.values() for pl in r["places"]),
        "stations_matched_by_merge": sum(1 for ms in matches.values() if ms[0]["how"].startswith("merge")),
        "stations_matched_by_name_and_position": sum(1 for ms in matches.values() if not ms[0]["how"].startswith("merge")),
    }
    return {"people": people, "station_rosters": station_rosters, "report": report}


# ---------------------------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------------------------


def _fmt(o: object, depth: int) -> str:
    """JSON with one short object per line (a stint, a roster line), so the files stay small and a
    change shows in a diff as the lines that changed."""
    if isinstance(o, dict):
        flat = json.dumps(o, ensure_ascii=False, separators=(", ", ": "))
        if len(flat) <= 200:
            return flat
        pad = " " * (depth + 1)
        return "{\n" + ",\n".join(f"{pad}{json.dumps(k, ensure_ascii=False)}: {_fmt(v, depth + 1)}" for k, v in o.items()) + "\n" + " " * depth + "}"
    if isinstance(o, list):
        flat = json.dumps(o, ensure_ascii=False, separators=(", ", ": "))
        if not any(isinstance(x, (dict, list)) for x in o) and len(flat) <= 200:
            return flat
        pad = " " * (depth + 1)
        return "[\n" + ",\n".join(pad + _fmt(x, depth + 1) for x in o) + "\n" + " " * depth + "]"
    return json.dumps(o, ensure_ascii=False)


def dump(obj: object) -> str:
    return _fmt(obj, 0) + "\n"


def write_tree(directory: Path, files: dict[str, object]) -> tuple[int, int]:
    """Write {relative path: object} under `directory` as JSON, and remove .json files there that the
    set no longer holds (a person who has become withheld must disappear). Returns (written, removed)."""
    written = removed = 0
    directory.mkdir(parents=True, exist_ok=True)
    for rel, obj in files.items():
        path = directory / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        text = dump(obj)
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            written += 1
    keep = {directory / rel for rel in files}
    for path in sorted(directory.rglob("*.json")):
        if path not in keep:
            path.unlink()
            removed += 1
    for sub in sorted((d for d in directory.rglob("*") if d.is_dir()), reverse=True):
        if not any(sub.iterdir()):
            sub.rmdir()
    return written, removed


def _read_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_people(directory: Path | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(directory.glob("*.json")) if directory and directory.is_dir() else []:
        rec = _read_json(path)
        if isinstance(rec, dict) and rec.get("id") == path.stem and isinstance(rec.get("stints"), list):
            out[rec["id"]] = rec
    return out


def load_station_rosters(directory: Path | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(directory.rglob("*.json")) if directory and directory.is_dir() else []:
        rec = _read_json(path)
        if isinstance(rec, dict) and rec.get("station") == path.stem and isinstance(rec.get("places"), list):
            out[rec["station"]] = rec
    return out


# ---------------------------------------------------------------------------------------------
# The site: committed files + research rosters -> what the pages load
# ---------------------------------------------------------------------------------------------

ROLE_ORDER = ["keeper", "head keeper", "first assistant", "second assistant", "third assistant", "fourth assistant",
              "assistant", "acting keeper", "station keeper", "surfman", "master", "mate", "engineer", "crew",
              "lamplighter", "laborer", "officer in charge", "civilian keeper", "volunteer keeper", "other"]
LETTERS = [chr(c) for c in range(ord("A"), ord("Z") + 1)] + ["#"]


def chunk_name(letter: str) -> str:
    """File name (without .json) of a surname-initial chunk: the letter, or `other` for '#'."""
    return "other" if letter == "#" else letter


def yr(v: object) -> int | None:
    """The year of a year number or a 'YYYY' / 'YYYY-MM-DD' string."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        m = re.match(r"^\s*(\d{4})", v)
        return int(m.group(1)) if m else None
    return None


def role_code(role: object) -> str:
    r = " ".join(str(role or "").lower().replace("-", " ").split())
    if r in ROLE_ORDER:
        return r
    if r in ("principal keeper", "principal lighthouse keeper", "head lighthouse keeper"):
        return "head keeper"
    return "other"


def _usable_line(k: object) -> bool:
    return isinstance(k, dict) and isinstance(k.get("name"), str) and bool(k["name"].strip())


def _overlaps(a: dict, b: dict) -> bool:
    fa, ta, fb, tb = yr(a.get("from")), yr(a.get("to")), yr(b.get("from")), yr(b.get("to"))
    if fa is None and ta is None or fb is None and tb is None:
        return False
    fa, fb = (fa if fa is not None else ta), (fb if fb is not None else tb)
    ta, tb = (ta if ta is not None else fa), (tb if tb is not None else fb)
    return max(fa, fb) <= min(ta, tb) + 1


class KeeperData:
    """People and archive rosters as the site uses them: the committed archive files, with the research
    rosters layered on, the living-people rule applied to the result, and station pages and person
    pages produced from it.

    people: published people (archive stints carry `place`; research stints carry `station`)
    rosters: station id -> the archive roster record (data/rosters)
    """

    def __init__(self, people: dict[str, dict], rosters: dict[str, dict], research: dict[str, dict] | None = None,
                 report: dict | None = None) -> None:
        self.people = json.loads(json.dumps(people))
        self.rosters = rosters
        self.report = report or {}
        self.warnings: list[str] = []
        self.place_station: dict[str, str] = {}
        for sid, r in rosters.items():
            for pl in r.get("places") or []:
                self.place_station.setdefault(pl["slug"], sid)
        # every archive person slug on a station roster: published, or withheld by the rule
        self.known_archive = {l["person"] for r in rosters.values() for pl in r.get("places") or [] for l in pl.get("lines") or []
                              if isinstance(l.get("person"), str)} | set(self.people)
        self.checked: set[str] = set()
        self.line_person: dict[tuple[str, int], str] = {}
        self.withheld_by_research = 0
        self.research_people = 0
        self._layer_research(research or {})

    # -- research rosters ---------------------------------------------------------------------

    def _layer_research(self, research: dict[str, dict]) -> None:
        archive_ids = set(self.people)
        for sid in sorted(research):
            lines = [k for k in (research[sid].get("keepers") or []) if _usable_line(k)]
            if lines:
                self.checked.add(sid)
            for i, k in enumerate(lines):
                where = f"{sid} keepers[{i}] ({k['name']})"
                stint = self._research_stint(k, sid)
                pid = k.get("person") if isinstance(k.get("person"), str) else None
                others = []
                for o in k.get("other_stations") or []:
                    if not (isinstance(o, dict) and isinstance(o.get("name"), str) and o["name"].strip()):
                        continue
                    if not (isinstance(o.get("cite"), list) and o["cite"] and all(isinstance(c, int) for c in o["cite"])):
                        self.warnings.append(f"{where}: other_stations entry {o.get('name')!r} has no cite, so it is not added to a person")
                        continue
                    others.append(o)
                person = None
                if pid and pid in archive_ids:
                    person = self.people[pid]
                    mine = [s for s in person["stints"] if s.get("place") and self.place_station.get(s["place"]) == sid]
                    old = next((s for s in mine if _overlaps(s, stint)), None)
                    if old is not None:
                        person["stints"].remove(old)
                    person["stints"].append(stint)
                elif pid and pid in self.known_archive:
                    continue  # withheld by the living-people rule: the line stays a table row, with no person
                elif pid:
                    self.warnings.append(f"{where}: person {pid!r} is no record the archive rosters name; line left unlinked")
                if person is None and others:
                    new_id = research_person_id(sid, k["name"], set(self.people))
                    person = self.people[new_id] = {"id": new_id, "name": k["name"].strip(), "source": "research", "stints": [stint]}
                    self.research_people += 1
                if person is not None:
                    for o in others:
                        person["stints"].append(self._other_stint(o, sid))
                    self.line_person[(sid, i)] = person["id"]
        # the rule again, over everything the person now has
        for pid in sorted(self.people):
            p = self.people[pid]
            years = [{"from": yr(s.get("from")), "to": yr(s.get("to"))} for s in p["stints"]]
            if withhold_reason(years):
                del self.people[pid]
                self.withheld_by_research += 1
        for p in self.people.values():
            p["stints"].sort(key=lambda s: _stint_order({**s, "from": yr(s.get("from")), "to": yr(s.get("to"))}))
            if p.get("possibly"):
                keep = [o for o in p["possibly"] if o in self.people]
                if keep:
                    p["possibly"] = keep
                else:
                    del p["possibly"]
        self.line_person = {k: v for k, v in self.line_person.items() if v in self.people}

    @staticmethod
    def _research_stint(k: dict, sid: str) -> dict:
        s: dict = {"station": sid, "src": "research", "checked": True, "role": k.get("role") or "other"}
        for key in ("from", "to", "from_approx", "to_approx", "note", "cite"):
            if k.get(key) is not None:
                s[key] = k[key]
        return s

    @staticmethod
    def _other_stint(o: dict, home: str) -> dict:
        s: dict = {"src": "research", "via": home, "station_name": o["name"].strip(), "cite": o["cite"]}
        if isinstance(o.get("id"), str):
            s["station"] = o["id"]
        for key in ("role", "from", "to", "from_approx", "to_approx", "note"):
            if o.get(key) is not None:
                s[key] = o[key]
        return s

    # -- station pages ------------------------------------------------------------------------

    def station_extras(self, station_id: str, rec: dict) -> None:
        """Put the archive roster on a station record, and keep `person` on a research roster line only
        when that person has a page."""
        for i, k in enumerate(rec.get("keepers") or []):
            pid = self.line_person.get((station_id, i))
            if pid:
                k["person"] = pid
            else:
                k.pop("person", None)
        roster = self.rosters.get(station_id)
        if not roster:
            return
        places = []
        count = 0
        for pl in roster.get("places") or []:
            lines = pl.get("lines") or []
            count += len(lines)
            place: dict = {"name": pl.get("name"), "url": pl.get("url"), "count": len(lines)}
            if station_id not in self.checked:
                place["lines"] = [{**{k: v for k, v in l.items() if k != "person"},
                                   **({"person": l["person"]} if l.get("person") in self.people else {})} for l in lines]
            places.append(place)
        rec["archive_roster"] = {"count": count, "places": places}

    # -- the files the pages load -------------------------------------------------------------

    def write_site(self, out: Path, stations: dict[str, dict], merged: dict[str, str] | None = None,
                   stories: dict[str, str] | None = None, built: str = "") -> dict:
        """Write out/k/: index.json (counts), stations.json (the station filter), i/<L>.json (the index
        rows by surname initial, loaded on demand) and p/<L>.json (the person pages' data, read by the
        prerender and then deleted). `stations` maps a visible station id to {name, region}. Returns
        the counts the site's meta.json reports."""
        import shutil
        import regions
        merged, stories = merged or {}, stories or {}
        base = out / "k"
        if base.exists():
            shutil.rmtree(base)
        (base / "i").mkdir(parents=True)
        (base / "p").mkdir()

        def resolve(sid: str | None) -> str | None:
            sid = merged.get(sid, sid) if sid else sid
            return sid if sid in stations else None

        norm_story = {sid: " " + norm_name(text) + " " for sid, text in stories.items() if sid in stations}
        site_people: dict[str, dict] = {}
        for pid, p in self.people.items():
            stints = []
            for s in p["stints"]:
                if s.get("src") == "research":
                    sid = resolve(s.get("station"))
                    out_s = {k: v for k, v in s.items() if k not in ("station", "src", "via")}
                    out_s["src"] = "research"
                    if sid:
                        out_s["station"] = sid
                        out_s["station_name"] = stations[sid]["name"]
                        out_s["region"] = stations[sid]["region"]
                    if s.get("via") and resolve(s["via"]):
                        out_s["via"] = resolve(s["via"])
                    if not (out_s.get("station_name")):
                        out_s["station_name"] = s.get("station_name") or "an unnamed station"
                else:
                    sid = resolve(self.place_station.get(s["place"]))
                    out_s = {k: v for k, v in s.items() if k != "state"}
                    out_s["src"] = "uslhs"
                    out_s["place_url"] = f"{ARCHIVE}/places/{s['place']}"
                    if sid:
                        out_s["station"] = sid
                        out_s["station_name"] = stations[sid]["name"]
                        out_s["region"] = stations[sid]["region"]
                    elif s.get("state"):
                        out_s["region"] = s["state"]
                if out_s.get("station") in norm_story:
                    out_s["story"] = True
                    nm = " " + norm_name(p["name"]) + " "
                    if nm.strip() and nm in norm_story[out_s["station"]]:
                        out_s["mentioned"] = True
                stints.append(out_s)
            site_people[pid] = {**{k: v for k, v in p.items() if k not in ("stints", "possibly")}, "stints": stints}
            if p.get("source") == "research" and any(stations.get(s.get("station"), {}).get("fixture") for s in stints):
                site_people[pid]["fixture"] = True

        # hints, with enough to read without opening the other page
        def brief(oid: str) -> dict:
            o = site_people[oid]
            ys = [y for s in o["stints"] for y in (yr(s.get("from")), yr(s.get("to"))) if y is not None]
            names = []
            for s in o["stints"]:
                n = s.get("station_name") or s.get("place_name")
                if n and n not in names:
                    names.append(n)
            return {"id": oid, "name": o["name"], "from": min(ys) if ys else None, "to": max(ys) if ys else None, "places": names[:3]}

        for pid, p in self.people.items():
            if p.get("possibly"):
                site_people[pid]["possibly"] = [brief(o) for o in p["possibly"] if o in site_people]

        # the station filter's list: every station a published person has a stint at, by name
        used = sorted({s["station"] for sp in site_people.values() for s in sp["stints"] if s.get("station")},
                      key=lambda sid: (stations[sid]["name"].lower(), sid))
        station_idx = {sid: i for i, sid in enumerate(used)}
        station_list = [[sid, stations[sid]["name"], stations[sid]["region"]] for sid in used]

        # index rows, by surname initial
        role_count: Counter[str] = Counter()
        region_count: Counter[str] = Counter()
        multi = 0
        rows_by_letter: dict[str, list[tuple]] = defaultdict(list)
        pages_by_letter: dict[str, dict] = defaultdict(dict)
        for pid, sp in site_people.items():
            ys = [y for s in sp["stints"] for y in (yr(s.get("from")), yr(s.get("to"))) if y is not None]
            codes = sorted({role_code(s.get("role")) for s in sp["stints"]}, key=ROLE_ORDER.index)
            regs = sorted({s["region"] for s in sp["stints"] if s.get("region")})
            sids = sorted({station_idx[s["station"]] for s in sp["stints"] if s.get("station")})
            places = {s.get("station") or s.get("place") or s.get("station_name") for s in sp["stints"]}
            multi += len(places) > 1
            for c in codes:
                role_count[c] += 1
            for r in regs:
                region_count[r] += 1
            letter = letter_of(sp["name"])
            rows_by_letter[letter].append((sort_key(sp["name"]), pid, sp["name"], min(ys) if ys else None,
                                           max(ys) if ys else None, " ".join(regs), codes, sids))
            pages_by_letter[letter][pid] = sp
        roles = [r for r in ROLE_ORDER if role_count[r]]
        letters = {}
        for letter in LETTERS:
            rows = sorted(rows_by_letter.get(letter, []))
            if not rows:
                continue
            letters[letter] = len(rows)
            chunk = [[r[1], r[2], r[3], r[4], r[5], [roles.index(c) for c in r[6]], r[7]] for r in rows]
            _write_compact(base / "i" / f"{chunk_name(letter)}.json", {"letter": letter, "rows": chunk})
            _write_compact(base / "p" / f"{chunk_name(letter)}.json", dict(sorted(pages_by_letter[letter].items())))
        _write_compact(base / "stations.json", {"stations": station_list})
        reg_rows = [{"code": c, "name": regions.region_name(c), "n": n} for c, n in
                    sorted(region_count.items(), key=lambda kv: regions.region_name(kv[0]))]
        withheld = int(self.report.get("people_withheld", 0)) + self.withheld_by_research
        manifest = {
            "built": built, "total": len(site_people), "multi": multi, "withheld": withheld,
            "letters": letters, "regions": reg_rows,
            "roles": [{"id": r, "n": role_count[r]} for r in roles],
            "stations": len(station_list), "chunks": {"index": "i/", "stations": "stations.json"},
            "format": {"rows": "[id, name, first year, last year, regions (space-separated), role numbers (index into roles), station numbers (index into stations.json)]"},
        }
        _write_compact(base / "index.json", manifest)
        archive_rosters = sum(1 for sid in self.rosters if sid in stations and sid not in self.checked)
        return {"people": len(site_people), "multi": multi, "withheld": withheld, "letters": len(letters),
                "archive_rosters": archive_rosters, "research_people": self.research_people,
                "withheld_by_research": self.withheld_by_research}


def _write_compact(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def load_report(path: Path | None) -> dict:
    rec = _read_json(path) if path and path.is_file() else None
    return rec if isinstance(rec, dict) else {}


def load_research_dir(directory: Path | None) -> dict[str, dict]:
    """data/research/<station id>.json files that parse, keyed by station id."""
    out: dict[str, dict] = {}
    for path in sorted(directory.glob("*.json")) if directory and directory.is_dir() else []:
        rec = _read_json(path)
        if isinstance(rec, dict):
            out[path.stem] = rec
    return out
