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
MOVED_KM = 8.0              # the same name this far apart, in different years, is one station that moved
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
                        "state_inferred": r.state_inferred, "footnote": footnote_for(foot, mark)})
    return out


def footnote_for(foot: dict, mark: str | None) -> str | None:
    """The footnote a name's mark points to; a symbol the OCR made of the first mark (®, ©, «) is the first footnote."""
    if not mark:
        return None
    return foot.get("a" if mark == "*" else mark.lower())


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
    return T.good_name(s) and T.looks_like_name(s)


def same_name(a: str, b: str) -> bool:
    """Two squashed names that differ by an OCR slip or a spelling (Hunniwell's / Hunniwells) are one."""
    if a == b:
        return True
    if min(len(a), len(b)) < 6 or abs(len(a) - len(b)) > 3:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.88


def volumes_of(rs: list[dict]) -> set[tuple[int, str]]:
    return {(r["year"], r["volume"]) for r in rs}


def position_clusters(readings: list[dict]) -> list[dict]:
    """Clean readings that lie within SAME_STATION_KM of each other (same state) are one station: names change and
    are sometimes used again for another station (Plum Island), but a station stays where it is."""
    clean = [r for r in readings if r["clean"] and r["state"] and is_name(r["name"])]
    clusters: list[dict] = []
    for r in sorted(clean, key=lambda r: (r["state"], r["lat"], r["lon"], r["year"], r["volume"])):
        for cl in clusters:
            if cl["state"] == r["state"] and any(km_between((m["lat"], m["lon"]), (r["lat"], r["lon"])) <= SAME_STATION_KM for m in cl["members"]):
                cl["members"].append(r)
                break
        else:
            clusters.append({"state": r["state"], "members": [r]})
    # single linkage in one pass can leave two clusters that a later reading joins: merge them
    merged = True
    while merged:
        merged = False
        for i, a in enumerate(clusters):
            for b in clusters[i + 1:]:
                if a["state"] == b["state"] and any(km_between((m["lat"], m["lon"]), (n["lat"], n["lon"])) <= SAME_STATION_KM
                                                    for m in a["members"] for n in b["members"]):
                    a["members"] += b["members"]
                    clusters.remove(b)
                    merged = True
                    break
            if merged:
                break
    for cl in clusters:
        ms = cl["members"]
        newest = max(m["year"] for m in ms)
        lat, lon = Counter((m["lat"], m["lon"]) for m in ms if m["year"] == newest).most_common(1)[0][0]
        vols = volumes_of(ms)
        cl.update(lat=lat, lon=lon, n_readings=len(vols), newest=newest, years=sorted({m["year"] for m in ms}),
                  volumes=sorted(v[1] for v in vols))
    clusters.sort(key=lambda c: (c["state"], -c["lat"], c["lon"]))
    return clusters


VOCAB: set[str] = set()


def spelling_rank(name: str) -> tuple:
    """Of several spellings of one name, the one made of the most known words, in the fewest pieces."""
    words = re.findall(r"[a-z]+", ascii_fold(name))
    known = sum(w in VOCAB for w in words) / max(len(words), 1)
    return (round(known, 2), -len(words))


def name_votes(rs: list[dict]) -> list[dict]:
    """The names a station is called in its readings: [{name, key, volumes, years, newest}], newest-used first."""
    by_key: dict[str, list[dict]] = defaultdict(list)
    for r in rs:
        if is_name(r["name"]):
            by_key[squash(r["name"])].append(r)
    keys = sorted(by_key, key=lambda k: -len(volumes_of(by_key[k])))
    groups: list[list[str]] = []
    for k in keys:
        for g in groups:
            if same_name(g[0], k):
                g.append(k)
                break
        else:
            groups.append([k])
    out = []
    for g in groups:
        members = [r for k in g for r in by_key[k]]
        spell = Counter(r["name"] for r in members)
        name = sorted(spell.items(), key=lambda kv: (tuple(-x for x in spelling_rank(kv[0])), -kv[1], -len(kv[0]), kv[0]))[0][0]
        vols = volumes_of(members)
        out.append({"name": name, "key": squash(name), "volumes": len(vols), "years": sorted({v[0] for v in vols}),
                    "newest": max(v[0] for v in vols), "spellings": sorted(spell)})
    out.sort(key=lambda n: (-n["newest"], -n["volumes"], n["name"]))
    return out


def check_cluster(cl: dict, lookup, ref: list[dict]) -> tuple[bool, str | None]:
    """The checks that need no neighbours: the box of the state, the state's boundary, a station of that name that
    another source holds."""
    lat, lon, state = cl["lat"], cl["lon"], cl["state"]
    flag = regions.flag_coordinate(state, lat, lon)
    if flag:
        return False, f"{lat:.4f}, {lon:.4f} is outside the box of {state} ({flag})"
    if not near_state(lookup, lat, lon, state):
        where = lookup.lookup(lat, lon, "US")[0]
        return False, f"{lat:.4f}, {lon:.4f} lies in {where or 'no state'}, not {state}"
    cl["external"] = None
    best_d = None
    for nv in cl["names"]:
        for r in reference_match(nv["name"], state, ref):
            d = km_between((lat, lon), (r["lat"], r["lon"]))
            if best_d is None or d < best_d:
                best_d = d
                cl["external"] = {"source": r["source"], "key": r["key"], "name": r["name"], "km": round(d, 1)}
    if cl["external"] and cl["external"]["km"] > EXTERNAL_KM and cl["n_readings"] < 2:
        e = cl["external"]
        return False, f"{e['name']} ({e['source']}) is {e['km']:.0f} km from {lat:.4f}, {lon:.4f} and only one reading gives that position"
    return True, None


def near_state(lookup, lat: float, lon: float, state: str, km: float = 8.0) -> bool:
    """The point is in `state`'s boundary (waters drawn out) or within `km` of it (the printed position is
    approximate and a station on a state line, Sabine Pass, can fall on the other side)."""
    where, _how, _ = lookup.lookup(lat, lon, "US")
    if where == state:
        return True
    coslat = max(math.cos(math.radians(lat)), 0.05)
    for r in (km / 2, km):
        for i in range(16):
            a = 2 * math.pi * i / 16
            if state in lookup._hits(lat + r / 111.2 * math.cos(a), lon + r / (111.2 * coslat) * math.sin(a), "US"):
                return True
    return False


GENERIC = re.compile(r"\b(life|saving|lifesaving|station|coast|guard|house|of|refuge|u\.?s\.?|united|states|no\.?|#\d+|and|lifeboat|boat|"
                     r"light|lighthouse|administration|equipment|buildings|old|new|historic|district|site)\b", re.I)


def core(name: str) -> str:
    return re.sub(r"[^a-z]", "", GENERIC.sub(" ", name).lower())


def reference_match(name: str, state: str, ref: list[dict]) -> list[dict]:
    me = squash(name)
    out = []
    for r in ref:
        if r["region"] != state:
            continue
        rc = core(r["name"])
        if rc and (rc == me or (len(me) >= 5 and len(rc) >= 5 and (rc.startswith(me) or me.startswith(rc)))
                   or (len(rc) >= 5 and difflib.SequenceMatcher(None, rc, me).ratio() >= 0.88)):
            out.append(r)
    return out


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


def list_neighbours_ok(member: dict, by_list: dict[tuple[str, int], list[dict]]) -> tuple[bool, str]:
    """A position read once is believed only if the stations printed on either side of it in the same list (the
    list runs along the coast) are near it: a digit slipped in a degree puts a station 100 km from both."""
    rows = by_list.get((member["volume"], member["district"]), [])
    before = [r for r in rows if r["pos"] < member["pos"] and r["clean"]]
    after = [r for r in rows if r["pos"] > member["pos"] and r["clean"]]
    near = []
    for r in ([before[-1]] if before else []) + ([after[0]] if after else []):
        near.append(km_between((member["lat"], member["lon"]), (r["lat"], r["lon"])))
    if not near:
        return False, "it is the only position read in its district's list"
    if max(near) > NEIGHBOUR_KM:
        return False, f"the stations beside it in the list are {max(near):.0f} km away"
    return True, ""


def settle(clusters: list[dict], readings: list[dict], lookup, ref: list[dict]) -> tuple[list[dict], list[dict]]:
    """Run the checks. Returns (kept clusters, left-out positions with the reason)."""
    by_list: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for r in readings:
        by_list[(r["volume"], r["district"])].append(r)
    for rows in by_list.values():
        rows.sort(key=lambda r: r["pos"])
    left: list[dict] = []
    ok_ = []
    for cl in clusters:
        cl["names"] = name_votes(cl["members"])
        good, why = check_cluster(cl, lookup, ref)
        if good and cl["n_readings"] < 2 and not (cl["external"] and cl["external"]["km"] <= EXTERNAL_KM):
            good, why = list_neighbours_ok(cl["members"][0], by_list)
            if not good:
                why = "read once, no other source holds a station of that name, and " + why
        if good:
            ok_.append(cl)
        else:
            left.append({"cluster": cl, "why": why})
    # a position read once for a name that another, better supported position carries is a slipped row
    final = []
    for cl in ok_:
        if cl["n_readings"] < 2:
            rival = next((o for o in ok_ if o is not cl and o["state"] == cl["state"] and o["n_readings"] >= 2
                          and any(same_name(a["key"], b["key"]) for a in cl["names"][:1] for b in o["names"] if b["volumes"] >= 2)), None)
            if rival is not None:
                d = km_between((cl["lat"], cl["lon"]), (rival["lat"], rival["lon"]))
                if d > SAME_STATION_KM:
                    left.append({"cluster": cl, "why": f"read once, and its name belongs to a position {d:.1f} km away that {rival['n_readings']} readings give"})
                    continue
        final.append(cl)
    return merge_moved(final), left


def merge_moved(clusters: list[dict]) -> list[dict]:
    """The same name at two places a few km apart, listed in different years, is a station that was moved or
    rebuilt: one station, at its newest position."""
    out: list[dict] = []
    for cl in sorted(clusters, key=lambda c: (c["state"], -c["newest"], c["lat"], c["lon"])):
        for o in out:
            if (o["state"] == cl["state"] and km_between((o["lat"], o["lon"]), (cl["lat"], cl["lon"])) <= MOVED_KM
                    and any(same_name(a["key"], b["key"]) for a in o["names"] for b in cl["names"] if a["volumes"] >= 2 and b["volumes"] >= 2)
                    and not (set(o["years"]) & set(cl["years"]))):
                o["members"] += cl["members"]
                o["moved_from"] = o.get("moved_from", []) + [{"lat": cl["lat"], "lon": cl["lon"], "years": cl["years"]}]
                o["names"] = name_votes(o["members"])
                vols = volumes_of(o["members"])
                o.update(n_readings=len(vols), years=sorted({m["year"] for m in o["members"]}), volumes=sorted(v[1] for v in vols))
                break
        else:
            out.append(cl)
    out.sort(key=lambda c: (c["state"], -c["lat"], c["lon"]))
    return out


def attach_unplaced(final: list[dict], readings: list[dict], used: set[int]) -> tuple[list[dict], list[dict]]:
    """Readings with no position (the block would not read, or the Great Lakes, which print none): added to the
    years of the station whose name they carry; the rest are stations listed without a position."""
    loose = [r for r in readings if (not r["clean"] or r.get("position_rejected")) and r["state"] and is_name(r["name"])]
    name_only: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in loose:
        key = squash(r["name"])
        hits = []
        for cl in final:
            if cl["state"] != r["state"]:
                continue
            for nv in cl["names"]:
                if same_name(nv["key"], key):
                    gap = min(abs(r["year"] - y) for y in nv["years"])
                    hits.append((gap, cl))
                    break
        if hits:
            hits.sort(key=lambda h: h[0])
            if len(hits) == 1 or hits[0][0] < hits[1][0]:
                hits[0][1].setdefault("loose", []).append(r)
                continue
        name_only[(r["state"], key)].append(r)
    # merge near-identical spellings of name-only stations
    keys = sorted(name_only)
    groups: list[list[tuple[str, str]]] = []
    for k in keys:
        for g in groups:
            if g[0][0] == k[0] and same_name(g[0][1], k[1]):
                g.append(k)
                break
        else:
            groups.append([k])
    stations = []
    for g in groups:
        rs = [r for k in g for r in name_only[k]]
        stations.append({"state": g[0][0], "readings": rs})
    return final, stations


# ---------------------------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------------------------

DISCONTINUED = re.compile(r"discontinued\s+([A-Za-z]+\.?\s+\d{1,2},?\s+)?(\d{4})", re.I)


def slug_of(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def pick_name(votes: list[dict]) -> tuple[dict, bool]:
    """The station's name: the one used in the newest report among those read in two or more volumes; failing
    that, the newest. The flag is True when the name rests on one volume."""
    multi = [n for n in votes if n["volumes"] >= 2]
    if multi:
        return multi[0], False
    return votes[0], True


def aliases_of(votes: list[dict], main: dict) -> list[dict]:
    """The station's other names: used in other years than the main name (a rename is one name after another; a second
    name in the same years is a row the OCR put beside the wrong coordinates), and either read in three or more
    volumes or directly before or after the main name."""
    out = []
    for n in votes:
        if n is main or n["volumes"] < 2:
            continue
        overlap = set(n["years"]) & set(main["years"])
        adjacent = (n["years"][-1] <= main["years"][0] + 1) or (n["years"][0] >= main["years"][-1] - 1)
        gap = min(abs(main["years"][0] - n["years"][-1]), abs(n["years"][0] - main["years"][-1]))
        if len(overlap) <= 1 and (n["volumes"] >= 3 or (adjacent and gap <= 2)):
            out.append(n)
    return out


def station_label(name: str, state: str, house_of_refuge: bool) -> str:
    return f"{name} House of Refuge" if house_of_refuge else f"{name} Life-Saving Station"


def make_record(st: dict, ident: str, volumes_by_id: dict[str, dict]) -> dict:
    name_vote, single = pick_name(st["names"])
    rs = st["members"] + st.get("loose", [])
    foot = " ".join(r["footnote"] or "" for r in rs if r.get("footnote"))
    hor = bool(re.search(r"house of refuge", foot, re.I))
    label = station_label(name_vote["name"], st["state"], hor)
    years = sorted({r["year"] for r in rs})
    newest = max(rs, key=lambda r: (r["year"], r["volume"]))
    pos = st.get("lat") is not None
    vol_ids = st["volumes"] if pos else sorted({r["volume"] for r in rs})
    src_vol = max(vol_ids, key=lambda v: (volumes_by_id[v]["year"], v)) if vol_ids else newest["volume"]
    rec = rx.new_record(SOURCE, ident, label, url=f"https://archive.org/details/{src_vol}", country="US", region=st["state"],
                        lat=st.get("lat"), lon=st.get("lon"), precision="approximate", kind="life_saving_station",
                        kind_raw="life-saving station" if not hor else "house of refuge")
    rec["other_names"] = [station_label(n["name"], st["state"], hor) for n in aliases_of(st["names"], name_vote)]
    ev = []
    first, last = years[0], years[-1]
    ev.append({"year": first, "event": "other",
               "note": f"First listed among the Life-Saving Service's stations in the report for {first}"
                       f"{'' if first > FIRST_YEAR else ' (the earliest report read with a station list)'}",
               "from": SOURCE})
    for r in rs:
        m = DISCONTINUED.search(r.get("footnote") or "")
        if m:
            ev.append({"year": int(m.group(2)), "event": "closed", "note": f"Footnote in the list of stations: {r['footnote'].strip()}", "from": SOURCE})
            break
    rec["events"] = ev
    district_year = max(r["year"] for r in rs if r.get("district"))
    districts = Counter(r["district"] for r in rs if r["year"] == district_year and r.get("district"))
    locs = Counter((r.get("locality") or "").strip() for r in rs if r.get("locality"))
    rec["links"] = [{"label": f"Annual Report of the U.S. Life-Saving Service for {volumes_by_id[src_vol]['year']}: list of life-saving districts and stations",
                     "url": f"https://archive.org/details/{src_vol}", "kind": "reference"}]
    rec["extra"] = {
        "district": districts.most_common(1)[0][0] if districts else None,
        "district_year": district_year,
        "years_listed": years,
        "locality": locs.most_common(1)[0][0] if locs else None,
        "readings": st.get("n_readings", 0),
        "volumes": vol_ids,
        "name_read_once": single or None,
        "footnotes": sorted({r["footnote"].strip() for r in rs if r.get("footnote")}) or None,
        "house_of_refuge": hor or None,
        "table_note": ("the printed list gives no latitude or longitude for this station (the Great Lakes stations have none)" if not pos else None),
    }
    if pos:
        rec["extra"]["position_text"] = "Approximate position as printed in the Life-Saving Service's list of stations, in degrees, minutes and seconds"
        if st.get("external"):
            rec["extra"]["other_source_km"] = st["external"]["km"]
    rec["extra"] = {k: v for k, v in rec["extra"].items() if v is not None}
    return rec


# ---------------------------------------------------------------------------------------------
# Vocabulary: a name read in one volume must be made of words other sources use
# ---------------------------------------------------------------------------------------------

GREAT_LAKES_STATES = {"MI", "WI", "IL", "IN", "OH", "MN", "PA", "KY", "NY"}   # NY: only the lake stations lack a position


def corpus_word_counts() -> Counter:
    """Capitalised words of every Life-Saving Service report in the corpus: a real place name occurs hundreds of times
    in the wreck tables; an OCR slip occurs a few times. Read once per run."""
    global _WORDS
    if _WORDS is None:
        cnt: Counter = Counter()
        root = c.RAW_ROOT / "corpus" / "lss"
        for path in sorted(root.glob("*/*.txt")):
            cnt.update(w.lower() for w in re.findall(r"\b[A-Z][a-z]{3,}\b", path.read_text(encoding="utf-8", errors="replace")))
        _WORDS = cnt
    return _WORDS


_WORDS: Counter | None = None
MIN_WORD_COUNT = 8          # a word in a station name read in one volume occurs at least this often in the reports
CORRECT_RATIO = 20          # ... and a one-letter variant is not this many times commoner


def load_vocabulary(readings: list[dict]) -> set[str]:
    """Words (lower case) of every station name in the other extracts, and of names read in three or more volumes."""
    vocab: set[str] = set()
    for path in sorted((c.REPO / "data" / "sources").glob("*.json")):
        if path.name == f"{SOURCE}.json":
            continue
        try:
            recs = json.loads(path.read_text(encoding="utf-8")).get("records", [])
        except ValueError:
            continue
        for r in recs:
            if r.get("country") == "US":
                vocab.update(re.findall(r"[a-z]{3,}", ascii_fold(r.get("name") or "")))
    seen: dict[str, set[str]] = defaultdict(set)
    for r in readings:
        seen[r["name"]].add(r["volume"])
    for name, vols in seen.items():
        if len(vols) >= 3 and T.good_name(name):
            vocab.update(re.findall(r"[a-z]{3,}", ascii_fold(name)))
    return vocab


def edits1(w: str) -> set[str]:
    letters = "abcdefghijklmnopqrstuvwxyz"
    splits = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    out = {a + b[1:] for a, b in splits if b} | {a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1}
    out |= {a + ch + b[1:] for a, b in splits if b for ch in letters} | {a + ch + b for a, b in splits for ch in letters}
    out.discard(w)
    return out


def correct_name(name: str, words: Counter) -> str:
    """OCR slips in a name read in one volume: a word that occurs rarely in the reports and has a one-letter variant that
    is CORRECT_RATIO times commoner (Monomov -> Monomoy) is written as the variant."""
    out = []
    for tok in name.split(" "):
        m = re.fullmatch(r"([A-Za-z]+)(.*)", tok)
        if not m:
            out.append(tok)
            continue
        w, rest = m.group(1).lower(), m.group(2)
        cw = words.get(w, 0)
        best = max(((words.get(v, 0), v) for v in edits1(w)), default=(0, None))
        if len(w) >= 5 and cw < 40 and best[1] and best[0] >= CORRECT_RATIO * max(cw, 1):
            fixed = best[1].capitalize() if tok[:1].isupper() else best[1]
            out.append(fixed + rest)
        else:
            out.append(tok)
    return " ".join(out)


def ascii_fold(s: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().replace("'", "")


def words_known(name: str, vocab: set[str]) -> bool:
    """Every word is one other sources use or one the reports print often (MIN_WORD_COUNT times)."""
    words = re.findall(r"[a-z]+", ascii_fold(name))
    counts = corpus_word_counts()
    return bool(words) and all(w in vocab or len(w) <= 2 or counts.get(w, 0) >= MIN_WORD_COUNT for w in words)


# ---------------------------------------------------------------------------------------------
# The whole run
# ---------------------------------------------------------------------------------------------

def stations_from(readings: list[dict], lookup, ref: list[dict]):
    clusters = position_clusters(readings)
    kept, left = settle(clusters, readings, lookup, ref)
    for l in left:
        for m in l["cluster"]["members"]:
            m["position_rejected"] = True
    vocab = load_vocabulary(readings)
    VOCAB.clear()
    VOCAB.update(vocab)
    for cl in kept:
        cl["names"] = name_votes(cl["members"])
    final = []
    for cl in kept:
        name_vote, single = pick_name(cl["names"])
        if single:
            fixed = correct_name(name_vote["name"], corpus_word_counts())
            if fixed != name_vote["name"]:
                cl["name_corrected"] = {"from": name_vote["name"], "to": fixed}
                name_vote["name"], name_vote["key"] = fixed, squash(fixed)
        if single and not words_known(name_vote["name"], vocab) and not (cl["external"] and cl["external"]["km"] <= EXTERNAL_KM):
            left.append({"cluster": cl, "why": f"the name \u201c{name_vote['name']}\u201d is read in one report only and is not made of words other sources use "
                                              f"(an OCR slip, probably); the position is left out with it"})
            continue
        final.append(cl)
    final, name_only = attach_unplaced(final, readings, set())
    return final, left, name_only, vocab


def name_only_stations(name_only: list[dict], vocab: set[str]) -> list[dict]:
    """Stations the lists name but whose position could not be read, kept when the name is sound: not a Great
    Lakes state (those lists print no position and their OCR is too broken to read), made of known words, and
    read in two volumes or in the 1909 list; a state the OCR had to infer does not count."""
    out = []
    for g in name_only:
        if g["state"] in GREAT_LAKES_STATES:
            continue
        rs = [r for r in g["readings"] if not r.get("state_inferred")]
        if not rs:
            continue
        names = name_votes(rs)
        if not names:
            continue
        nv, _single = pick_name(names)
        vols = volumes_of(rs)
        if not (len(vols) >= 2 or any(v[0] == 1909 for v in vols)) or not words_known(nv["name"], vocab):
            continue
        out.append({"state": g["state"], "members": rs, "names": names, "lat": None, "lon": None, "n_readings": 0,
                    "volumes": sorted({v[1] for v in vols})})
    out.sort(key=lambda s: (s["state"], pick_name(s["names"])[0]["name"]))
    return out


def build(min_year: int = FIRST_YEAR) -> tuple[list[dict], dict]:
    vols = load_volumes(min_year)
    volumes_by_id = {v["identifier"]: v for v in vols}
    readings, vstats = readings_of(vols)
    lookup = regions.region_lookup(c.RAW_ROOT)
    ref = load_reference()
    placed, left, name_only, vocab = stations_from(readings, lookup, ref)
    unplaced = name_only_stations(name_only, vocab)
    # a station keeps one record key for good: <state>-<slug of its name>, numbered when two share a name
    records, seen = [], Counter()
    for st in sorted(placed + unplaced, key=lambda s: (s["state"], pick_name(s["names"])[0]["name"], -(s.get("lat") or 0), s.get("lon") or 0)):
        label_name = pick_name(st["names"])[0]["name"]
        base = f"{st['state'].lower()}-{slug_of(label_name)}"
        seen[base] += 1
        ident = base if seen[base] == 1 else f"{base}-{seen[base]}"
        st["ident"] = ident
        records.append(make_record(st, ident, volumes_by_id))
    notes = {
        "volumes_read": {v["identifier"]: {**vstats[v["identifier"]], "table_found": vstats[v["identifier"]]["rows"] > 0} for v in vols},
        "stations_with_position": sum(1 for r in records if r["lat"] is not None),
        "stations_without_position": sum(1 for r in records if r["lat"] is None),
        "positions_left_out": len(left),
        "station_numbers": "The lists print no station numbers; the record carries the district of the newest report that lists the station (districts were renumbered), not a number.",
        "great_lakes": "The Great Lakes stations (districts 10-12 in 1909) have no latitude or longitude in the printed lists, and their pages are too broken in the OCR to read reliably: not included.",
        "review": "docs/sources/review_2026-10-lss_reports.md",
    }
    return records, {"notes": notes, "placed": placed, "left": left, "unplaced": unplaced, "readings": readings, "volumes_by_id": volumes_by_id}


def review_markdown(info: dict) -> str:
    placed, left, unplaced = info["placed"], info["left"], info["unplaced"]
    readings = info["readings"]
    out = ["# Review: Life-Saving Service station lists (`lss_reports`)", "",
           "Generated by `pipeline/fetch_lss_reports.py`; do not edit by hand. Everything here was **left out** of the extract or is "
           "**kept on thin evidence**; a human can settle it from the scans (each volume's Internet Archive page is linked). Rows the OCR could not "
           "read cleanly are listed, never guessed.", ""]
    stations_ = {"with a position": sum(1 for s in placed), "with no position (named in the lists)": len(unplaced)}
    out += ["## Counts", ""] + [f"- {k}: {v}" for k, v in stations_.items()]
    out += [f"- positions left out: {len(left)}", f"- volumes read: {len(info['volumes_by_id'])} "
            f"({', '.join(sorted({str(v['year']) for v in info['volumes_by_id'].values()}))})", ""]
    out += ["## Positions left out", "", "| State | Name as read | Position | Reports | Years | Why |", "|---|---|---|---|---|---|"]
    for l in sorted(left, key=lambda l: (l["cluster"]["state"], l["cluster"]["names"][0]["name"] if l["cluster"]["names"] else "")):
        cl = l["cluster"]
        nm = cl["names"][0]["name"] if cl.get("names") else "?"
        out.append(f"| {cl['state']} | {nm} | {cl['lat']:.4f}, {cl['lon']:.4f} | {cl['n_readings']} | {', '.join(map(str, cl['years']))} | {l['why']} |")
    out += ["", "## Kept, but read in one report only", "",
            "These positions passed every check (state boundary, the stations beside them in the list, or another source holding a station of the "
            "same name) but only one report gives them.", "", "| State | Name | Position | Report | Other source |", "|---|---|---|---|---|"]
    for s in placed:
        if s["n_readings"] < 2:
            e = s.get("external")
            out.append(f"| {s['state']} | {pick_name(s['names'])[0]['name']} | {s['lat']:.4f}, {s['lon']:.4f} | {s['years'][0]} | "
                       f"{e['name'] + ' (' + e['source'] + '), ' + str(e['km']) + ' km' if e else 'none'} |")
    out += ["", "## Stations that changed name or place", "", "| State | Newest name | Other names read in two or more volumes | Years | Moved |", "|---|---|---|---|---|"]
    for s in placed:
        main_, _ = pick_name(s["names"])
        al = aliases_of(s["names"], main_)
        mv = s.get("moved_from")
        if al or mv:
            out.append(f"| {s['state']} | {main_['name']} | {', '.join(a['name'] + ' ' + str(a['years'][0]) + '-' + str(a['years'][-1]) for a in al) or '-'} | "
                       f"{s['years'][0]}-{s['years'][-1]} | {'; '.join(f'{m_['lat']:.3f},{m_['lon']:.3f} in ' + str(m_['years']) for m_ in mv) if mv else '-'} |")
    out += ["", "## Listed without a position", "",
            "The lists name these stations (in the 1909 list or in two or more reports) but the position could not be read, or the printed list gives none.", "",
            "| State | Name | Reports | Years |", "|---|---|---|---|"]
    for s in unplaced:
        ys = sorted({m["year"] for m in s["members"]})
        out.append(f"| {s['state']} | {pick_name(s['names'])[0]['name']} | {len(s['volumes'])} | {ys[0]}-{ys[-1]} |")
    newest = max(v["year"] for v in info["volumes_by_id"].values())
    nv = [v["identifier"] for v in info["volumes_by_id"].values() if v["year"] == newest]
    bad = [r for r in readings if r["volume"] in nv and not r["clean"]]
    out += ["", f"## Rows of the {newest} list that could not be read cleanly ({len(bad)})", "",
            "| District | Name as read | State | Problem |", "|---|---|---|---|"]
    for r in sorted(bad, key=lambda r: (r["district"], r["pos"])):
        out.append(f"| {r['district']} | {r['name']} | {r['state']} | {r['problem'] or ''} |")
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-year", type=int, default=FIRST_YEAR)
    args = ap.parse_args(argv)
    records, info = build(args.min_year)
    rx.write_extract(OUT_PATH, source=SOURCE, title="US Life-Saving Service annual reports: lists of life-saving districts and stations (1884-1909)",
                     url="https://archive.org/search?query=annual+report+life-saving+service", license_text=LICENSE, credit=CREDIT,
                     records=records, notes=info["notes"], retrieved="2026-10-21")
    REVIEW_PATH.write_text(review_markdown(info), encoding="utf-8")
    n = info["notes"]
    c.log(f"lss_reports: {len(records)} records ({n['stations_with_position']} with a position, {n['stations_without_position']} without); "
          f"{n['positions_left_out']} positions left out; review: {REVIEW_PATH.relative_to(c.REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
