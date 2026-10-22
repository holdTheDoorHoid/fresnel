#!/usr/bin/env python3
"""US Life-Saving Service annual reports, the lists of "Life-saving districts and stations" ->
data/sources/lss_reports.json (DESIGN.md 2.5, 3.8).

The Service's annual report has printed, from 1884, a list of its stations by district: name, state,
locality, and (for the Atlantic, Gulf and Pacific coasts) an *approximate position* in degrees, minutes and
seconds. The reports are US federal publications (public domain). This fetcher reads the corpus's OCR text
(`research/corpus.py`, series `lss`, `$FRESNEL_RAW_ROOT/corpus/`; nothing is fetched here) with the table
reader in `lss_table.py` and puts every volume's readings together:

- *A station* is a (state, name) that appears in the tables; spellings that differ by an OCR slip are one
  station when their positions agree; the commonest clean spelling is its name.
- *The years a station appears* are the report years whose table was read and held it (`extra.years_listed`).
  The corpus has no 1883, 1885-87, 1890 or 1910-14 volume and the OCR of some tables cannot be read at all,
  so this is a lower bound, not the dates the station opened or closed.
- *Its position* is the one most readings agree on (within 2 km: the Service refined positions by a few
  seconds from year to year; OCR slips are a digit out, and lose the vote). A position is **kept** only if
  it passes every check: it is a position a block of the table gave with all its counts agreeing; it lies
  in the state the table names (the Census boundary, waters included); it is not far from the
  neighbouring stations of its district; and, where another source (NRHP, Wikidata, the Society) holds a
  station of that name in that state, it is within 15 km of it. A single reading must pass all of them;
  readings that agree in two reports need only the first two.
  A row that cannot be read cleanly, or whose position fails a check, is **left out and listed** in
  `docs/sources/review_2026-10-lss_reports.md`, never guessed. Great Lakes stations have no position in the
  printed list at all.
- *District and list position*: the table prints no station numbers. The record carries the district of the
  newest report that lists the station (`extra.district`; districts were renumbered over the years) and the
  station's place in that district's list (`extra.list_position`), which runs along the coast.

The names of the Florida Houses of Refuge appear in the Eighth District's list with a footnote ("House of
refuge: no crew employed"): they are written as `<name> House of Refuge`. Every other station is
`<name> Life-Saving Station`. Status stays `null`: the lists do not say a station stands or is lost (a
footnote "Discontinued <date>" becomes a `closed` event).

Usage: python3 pipeline/fetch_lss_reports.py [--min-year 1884]
"""
from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402
import lss_table as T  # noqa: E402
import regions  # noqa: E402

SOURCE = "lss_reports"
OUT_PATH = c.REPO / "data" / "sources" / f"{SOURCE}.json"
REVIEW_PATH = c.REPO / "docs" / "sources" / "review_2026-10-lss_reports.md"
LICENSE = ("US federal publications (Annual Reports of the US Life-Saving Service, 1884-1909), public domain; "
           "text read from the Internet Archive's OCR.")
CREDIT = "Annual Reports of the U.S. Life-Saving Service, read from the Internet Archive scans (public domain)"
SAME_STATION_KM = 2.0       # readings this close are one position
NEIGHBOUR_KM = 60.0         # the nearest other station of the same district list is at most this far
EXTERNAL_KM = 15.0          # a station of the same name in another source is at most this far
FIRST_YEAR = 1884           # the first report whose list carries positions
TABLE_WINDOW = 1200         # raw lines after the last district's heading that the table may run
SOURCE_SOURCES = ("nrhp", "wikidata", "osm", "uslhs", "territories")


# ---------------------------------------------------------------------------------------------
# Reading a volume
# ---------------------------------------------------------------------------------------------

def read_volume(lines: list[str]) -> list[dict]:
    """Every row (clean or not) of the district lists in one report's text, as dicts."""
    starts = T.find_tables(lines)
    if not starts:
        return []
    s = starts[0][0]
    heads: list[tuple[int, int]] = []
    for i in range(s, min(len(lines), s + 9000)):
        d = T.district_number(lines[i])
        if d and (not heads or d >= heads[-1][1]):
            heads.append((i, d))
    out: list[dict] = []
    for idx, (i, d) in enumerate(heads):
        j = heads[idx + 1][0] if idx + 1 < len(heads) else min(len(lines), i + TABLE_WINDOW)
        j = end_of_table(lines, i, j) if idx + 1 == len(heads) else j
        rows, notes, _ = T.parse_district(d, lines[i + 1:j])
        foot = {k: v for k, v in notes}
        for pos, r in enumerate(rows):
            name, mark = T.split_mark(r.name)
            if not name or not r.state or r.state == T.DITTO:
                continue
            out.append({"district": d, "pos": pos, "name": name, "mark": mark, "state": r.state, "locality": r.locality,
                        "lat": r.lat, "lon": r.lon, "clean": r.clean, "problem": r.problem,
                        "footnote": foot.get(mark) if mark else None, "footnotes": foot})
    return out


def end_of_table(lines: list[str], start: int, stop: int) -> int:
    """The last district's text runs into the next section ("Instructions to mariners in case of shipwreck")."""
    for k in range(start + 1, stop):
        if re.search(r"INSTRUCTIONS\s+TO\s+MARINERS|PERIODS\s+OF\s+EMPLOYMENT|HOUSES?\s+OF\s+REFUGE\s*\.?\s*$", lines[k]):
            return k
    return stop


def load_volumes(min_year: int = FIRST_YEAR) -> list[dict]:
    root = c.RAW_ROOT / "corpus"
    idx = json.loads((root / "corpus_index.json").read_text(encoding="utf-8"))
    vols = [v for v in idx["volumes"] if v["series"] == "lss" and v["year"] >= min_year]
    vols.sort(key=lambda v: (v["year"], v["identifier"]))
    return vols


def readings_of(vols: list[dict]) -> tuple[list[dict], dict]:
    root = c.RAW_ROOT / "corpus"
    readings: list[dict] = []
    stats: dict = {}
    for v in vols:
        lines = (root / v["path"]).read_text(encoding="utf-8", errors="replace").split("\n")
        rows = read_volume(lines)
        for r in rows:
            r.update(year=v["year"], volume=v["identifier"])
        readings += rows
        stats[v["identifier"]] = {"year": v["year"], "rows": len(rows), "clean": sum(r["clean"] for r in rows)}
    return readings, stats


# ---------------------------------------------------------------------------------------------
# Stations: clusters of readings
# ---------------------------------------------------------------------------------------------

def squash(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def km_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot((a[0] - b[0]) * 111.2, (a[1] - b[1]) * 111.2 * math.cos(math.radians((a[0] + b[0]) / 2)))


def is_name(s: str) -> bool:
    """A reading's name is kept if it looks like a place name and not a locality that slipped into the name column."""
    return T.good_name(s) and len(s.split()) <= 4 and not re.search(
        r"\b(miles?|mile|near|light|inside|north|south|east|west|side|end|abreast|opposite|about|harbor entrance)\b", s, re.I) \
        or bool(re.fullmatch(r"(?:North|South|East|West|Little|Big|Old|Fort|Point|Cape|Port)\s+[A-Z][A-Za-z']+(?:\s+[A-Z][A-Za-z']+)?", s))


def cluster(readings: list[dict]) -> list[dict]:
    """Group readings into stations: by state, then by squashed name, merging names that differ by an OCR slip."""
    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in readings:
        if r["state"] and is_name(r["name"]):
            by_key[(r["state"], squash(r["name"]))].append(r)
    keys = sorted(by_key)
    parent = {k: k for k in keys}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a[0] != b[0] or abs(len(a[1]) - len(b[1])) > 3 or min(len(a[1]), len(b[1])) < 6:
                continue
            if difflib.SequenceMatcher(None, a[1], b[1]).ratio() >= 0.88:
                parent[find(b)] = find(a)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for k in keys:
        groups[find(k)] += by_key[k]
    out = []
    for k in sorted(groups):
        rs = groups[k]
        out.append({"state": k[0], "readings": rs})
    return out


def best_name(readings: list[dict]) -> str:
    """The commonest clean spelling; a name that is wholly damaged never beats one that is not."""
    cnt = Counter(r["name"] for r in readings)
    good = {n: k for n, k in cnt.items() if T.good_name(n)}
    pool = good or cnt
    return sorted(pool.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))[0][0]


def consensus_position(readings: list[dict]) -> dict | None:
    """The position most clean readings agree on (within SAME_STATION_KM), taken from the newest report among
    them; None when no reading is clean."""
    pts = [(r["lat"], r["lon"], r["year"], r["volume"]) for r in readings if r["clean"]]
    if not pts:
        return None
    groups: list[list[tuple]] = []
    for p in sorted(pts, key=lambda p: (-p[2], p[3])):
        for g in groups:
            if km_between(g[0][:2], p[:2]) <= SAME_STATION_KM:
                g.append(p)
                break
        else:
            groups.append([p])
    groups.sort(key=lambda g: (-len({(x[2], x[3]) for x in g}), -g[0][2]))
    top = groups[0]
    tie = len(groups) > 1 and len({(x[2], x[3]) for x in groups[1]}) == len({(x[2], x[3]) for x in top})
    newest = max(p[2] for p in top)
    pick = Counter((p[0], p[1]) for p in top if p[2] == newest).most_common(1)[0][0]
    return {"lat": pick[0], "lon": pick[1], "n_readings": len({(x[2], x[3]) for x in top}),
            "n_years": len({x[2] for x in top}), "years": sorted({x[2] for x in top}), "of": len(pts),
            "tie": tie, "others": [(g[0][0], g[0][1], len({(x[2], x[3]) for x in g})) for g in groups[1:]]}


# ---------------------------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------------------------

def load_reference() -> list[dict]:
    """Life-saving stations other sources hold, with positions: the check on a table position."""
    out = []
    for src in SOURCE_SOURCES:
        path = c.REPO / "data" / "sources" / f"{src}.json"
        if not path.exists():
            continue
        for r in json.loads(path.read_text(encoding="utf-8")).get("records", []):
            if r.get("kind") == "life_saving_station" and isinstance(r.get("lat"), (int, float)) and r.get("country") == "US":
                out.append({"source": src, "key": r["key"], "name": r["name"], "region": r["region"], "lat": r["lat"], "lon": r["lon"]})
    return out


def core(name: str) -> str:
    n = re.sub(r"\b(life|saving|lifesaving|station|coast|guard|house|of|refuge|u\.?s\.?|united|states|no\.?|#\d+|and|lifeboat|boat|light|"
               r"lighthouse|administration|equipment|buildings|old|new|historic|district|site)\b", " ", name.lower())
    return re.sub(r"[^a-z]", "", n)


def reference_match(name: str, state: str, ref: list[dict]) -> list[dict]:
    me = squash(name)
    out = []
    for r in ref:
        if r["region"] != state:
            continue
        rc = core(r["name"])
        if rc and (rc == me or (len(me) >= 5 and (rc.startswith(me) or me.startswith(rc)))
                   or difflib.SequenceMatcher(None, rc, me).ratio() >= 0.88):
            out.append(r)
    return out


def check_position(st: dict, lookup, ref: list[dict], placed: list[tuple[float, float, str]]) -> tuple[bool, list[str]]:
    """(keep, notes). Every position passes every check or is left out."""
    pos = st["position"]
    lat, lon, notes = pos["lat"], pos["lon"], []
    state = st["state"]
    if regions.flag_coordinate(state, lat, lon):
        return False, [f"outside the box of {state} ({regions.flag_coordinate(state, lat, lon)})"]
    where, how, km = lookup.lookup(lat, lon, "US")
    if where != state and not (how == "nearest" and km is not None and km <= 5 and where in (state, None)):
        # points on the line between two states, or in the water between two
        near_state = where is None or km is None or km > 5
        if where != state:
            return False, [f"the position is in {where or 'no state'} ({how}), not {state}"]
    pos["checked_in_state"] = True
    agreed = pos["n_readings"] >= 2
    others = [(a, b) for a, b, s in placed if s != st["id"]]
    nearest = min((km_between((lat, lon), o) for o in others), default=None)
    if nearest is not None and nearest > NEIGHBOUR_KM and not agreed:
        return False, [f"the nearest other listed station is {nearest:.0f} km away and only one reading gives this position"]
    st["nearest_km"] = round(nearest, 1) if nearest is not None else None
    refs = reference_match(st["name"], state, ref)
    if refs:
        d = min(km_between((lat, lon), (r["lat"], r["lon"])) for r in refs)
        st["external"] = {"source": refs[0]["source"], "key": refs[0]["key"], "name": refs[0]["name"], "km": round(d, 1)}
        if d > EXTERNAL_KM and not agreed:
            return False, [f"{refs[0]['name']} ({refs[0]['source']}) is {d:.0f} km from this position and only one reading gives it"]
        if d > EXTERNAL_KM:
            notes.append(f"{refs[0]['source']} puts {refs[0]['name']} {d:.0f} km from the printed position")
    return True, notes
