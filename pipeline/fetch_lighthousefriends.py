#!/usr/bin/env python3
"""LighthouseFriends.com state pages -> data/sources/lighthousefriends.json (DESIGN.md 2.4).

Kraig Anderson's LighthouseFriends is the most complete visit-and-keeper site for the United States.
Its text and photographs are copyrighted, so this fetcher takes **facts only** (a light's id, name,
town, 5-decimal position and the icon flags) and links to the light's page; it never reads a
per-light page and never copies prose.

A state page, `pull-state.asp?state=ME`, embeds one Google-Maps script that lists every light's id
and position, and a card per light (name, town; the card is highlighted when the light is
destroyed). The same page takes the legend's icon boxes as filters (`A5=1` lists only the lights
with that icon), which is how a flag is read without opening any light's page:

    A14 destroyed    A6 climbable     A9 overnight lodging     A10 volunteer keeper program
    A5 privately owned, no access without permission           A2 boat required

so each state is fetched once for the list and once per flag (7 requests; the five passes of the
2026-10-21 survey, cached under `survey/us/lhf/`, are reused). Puerto Rico is in LHF's menu and is
fetched too. Canada and Cuba are not this fetcher's.

Readings:

- **destroyed -> status `lost`** (position `approximate`: LHF pins a vanished tower where it believes
  it stood). `(Replica)` -> status `replica`.
- **kind from the name**: "Lightship X LV 87/WAL 512" -> `lightship` (a surviving vessel; the hull
  number goes to `extra.hull`), "... Range", "Front", "Rear" -> `range_lights` with a role,
  "Breakwater", "Pier", "Pierhead" -> `pier_light`, "Minor light of Hawai'i - X" -> `harbor_light`
  flagged `minor_beacon_suspect` (it may join a station, never start one), "Memorial" -> a
  `decorative_hint`.
- **flags -> `visit`, `stay`, `access`** with LHF as the source: climb -> `visit.climbable`; boat ->
  `visit.boat_only`; private -> `access.level` private; lodging -> `stay` (type `rental`, a stand-in:
  LHF does not say B&B, rental or hostel; the Society's accommodations list refines it); volunteer
  keeper program -> `stay` type `keeper_program`. LHF lists only the flags that are true, so a light
  without a flag gets nothing, never a false.

The extract `data/sources/lighthousefriends.json` is shared with the Canadian fetcher
(fetch_lighthousefriends_ca.py): each writes only its own country's records and keeps the other's.

Usage: python3 pipeline/fetch_lighthousefriends.py [--refresh] [--states ME,NH]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "sources" / "lighthousefriends.json"
SOURCE = "lighthousefriends"
BASE = "https://www.lighthousefriends.com"

# The US states and Puerto Rico in LHF's menu (verified 2026-10-21; the menu has no entry for the
# inland states, which have only replicas and river lights).
STATES = ("AL AK CA CT DE FL GA HI IL IN LA ME MD MA MI MN MS NH NJ NY NC OH OR PA PR RI SC TX VT VA WA WI").split()
# pass name -> legend filter (None = the whole list). The survey's cache used the first five names.
PASSES = {"all": None, "destroyed": "A14", "climb": "A6", "lodging": "A9", "keeperprog": "A10",
          "private": "A5", "boat": "A2"}
SURVEY_CACHE = "survey/us/lhf"


def page_url(state: str, flag: str | None) -> str:
    q = f"state={state}" + (f"&{flag}=1&button=Go" if flag else "")
    return f"{BASE}/pull-state.asp?{q}"


def fetch_pages(states: list[str], refresh: bool) -> dict[tuple[str, str], Path]:
    cache = c.raw_dir(SOURCE)
    survey = c.RAW_ROOT / SURVEY_CACHE
    paths: dict[tuple[str, str], Path] = {}
    done = 0
    for st in states:
        for name, flag in PASSES.items():
            p = cache / f"{st}_{name}.html"
            old = survey / f"{st}_{name}.html"
            if not p.exists() and not refresh and old.exists():
                shutil.copyfile(old, p)
            if not p.exists() or refresh:
                rx.polite_get(page_url(st, flag), p, force=refresh)
                done += 1
            paths[(st, name)] = p
    c.log(f"lighthousefriends: {len(paths)} pages ready ({done} fetched)")
    return paths


# ---------------------------------------------------------------------------------------------
# Parsing one state page
# ---------------------------------------------------------------------------------------------

_LATLNG_RE = re.compile(r"var\s+(\w+)\s*=\s*new google\.maps\.LatLng\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
_MARKER_RE = re.compile(r"new google\.maps\.Marker\(\{\s*position:\s*(\w+)")
_OPEN_RE = re.compile(r"window\.open\('https?://www\.lighthousefriends\.com/light\.asp\?ID=(\d+)'\)")
_CARD_RE = re.compile(
    r'<a href="https?://www\.lighthousefriends\.com/light\.asp\?ID=(\d+)"[^>]*class="([^"]*)"[^>]*>(.*?)</a>', re.S)


def parse_state_page(html: str) -> list[dict]:
    """[{id, name, place, lat, lon, destroyed_card}] for every light on the page, in page order."""
    points = {m.group(1): (float(m.group(2)), float(m.group(3))) for m in _LATLNG_RE.finditer(html)}
    positions: dict[str, tuple[float, float]] = {}
    # Each marker is created from a position variable, then given a click handler naming its light.
    markers = [(m.start(), m.group(1)) for m in _MARKER_RE.finditer(html)]
    opens = [(m.start(), m.group(1)) for m in _OPEN_RE.finditer(html)]
    for i, (at, var) in enumerate(markers):
        end = markers[i + 1][0] if i + 1 < len(markers) else len(html)
        ids = [lid for pos, lid in opens if at < pos < end]
        if ids and var in points:
            positions.setdefault(ids[0], points[var])
    out, seen = [], set()
    for m in _CARD_RE.finditer(html):
        lid, cls, inner = m.group(1), m.group(2), m.group(3)
        spans = [rx.clean_text(s) for s in re.findall(r"<span>(.*?)</span>", inner, re.S)]
        if lid in seen or not spans:
            continue
        seen.add(lid)
        pos = positions.get(lid)
        out.append({"id": lid, "name": spans[0], "place": spans[1] if len(spans) > 1 else None,
                    "lat": pos[0] if pos else None, "lon": pos[1] if pos else None,
                    "destroyed_card": "w3-theme" in cls.split()})
    return out


# ---------------------------------------------------------------------------------------------
# Names and kinds
# ---------------------------------------------------------------------------------------------

HULL_RE = re.compile(r"\b(WLV|WAL|LV)[ -]?(\d+)\b", re.I)
SIDE_PAREN_RE = re.compile(r"^(north|south|east|west|upper|lower|front|rear|inner|outer)\b", re.I)


def read_name(raw: str) -> dict:
    """What a LighthouseFriends heading says: the name to match on, other names, the kind and role,
    and flags (replica, minor light, memorial, hull number)."""
    name = re.sub(r"\s+", " ", raw).strip()
    out: dict = {"name": name, "other_names": [], "kind": "lighthouse", "role": None, "replica": False,
                 "minor": False, "memorial": False, "hull": None}
    m = re.match(r"^Minor light of [^-]+ - (.+)$", name)
    if m:
        out.update(name=m.group(1).strip(), kind="harbor_light", minor=True)
        out["other_names"].append(name)
        return out
    if re.match(r"^Lightship\b", name):
        hulls = [f"{h.upper()}-{n}" for h, n in HULL_RE.findall(name)]
        base = HULL_RE.sub("", name[len("Lightship"):])
        base = re.sub(r"[/\s]+$", "", re.sub(r"\s*/\s*", " ", base)).strip(" /-")
        base = re.sub(r"\s+", " ", base)
        out.update(name=base or name, kind="lightship", hull=hulls[0] if hulls else None)
        out["other_names"].append(name)
        return out
    paren = re.search(r"\s*\(([^)]*)\)\s*$", name)
    if paren:
        base, p = name[:paren.start()].strip(), paren.group(1).strip()
        if re.fullmatch(r"replica", p, re.I):
            out.update(name=base, replica=True)
        elif SIDE_PAREN_RE.match(p) and re.search(r"\brange\b", p, re.I):
            out["name"] = f"{base} {p}"
        else:
            out["name"] = base
            if p and p.lower() != base.lower():
                out["other_names"].append(p)
    n = out["name"]
    if re.search(r"\brange\b", n + " " + " ".join(out["other_names"]), re.I):
        out["kind"] = "range_lights"
        side = n + " " + " ".join(out["other_names"])
        if re.search(r"\bfront\b", side, re.I):
            out["role"] = "front_range"
        elif re.search(r"\brear\b", side, re.I):
            out["role"] = "rear_range"
    elif re.search(r"\b(breakwater|pier|pierhead|pier ?head)\b", n, re.I) and not out["replica"]:
        out["kind"] = "pier_light"
    if re.search(r"\bmemorial\b", n, re.I):
        out["memorial"] = True
    return out


# ---------------------------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------------------------

def build_record(state: str, light: dict, flags: set[str], destroyed: bool) -> dict | None:
    if light["lat"] is None or light["lon"] is None:
        return None
    nm = read_name(light["name"])
    lid = light["id"]
    url = f"{BASE}/light.asp?ID={lid}"
    region = rx.state_of(light["place"]) or state
    status = "lost" if destroyed else ("replica" if nm["replica"] else None)
    status_raw = "destroyed" if destroyed else ("replica" if nm["replica"] else None)
    extra: dict = {"lhf_id": lid, "xref": [f"lhf:{lid}"], "place": light["place"], "flags": sorted(flags)}
    if nm["hull"]:
        extra["hull"] = nm["hull"]
    if nm["minor"]:
        extra["minor_beacon_suspect"] = "LighthouseFriends lists it as a minor light"
    if nm["memorial"]:
        extra["decorative_hint"] = "LighthouseFriends lists it as a memorial"
    if nm["replica"] and not destroyed:
        extra["replica_of_name"] = nm["name"]
    shown = f"{nm['name']} (Replica)" if nm["replica"] else nm["name"]   # a copy keeps the word: it is its own station
    rec = rx.new_record(
        SOURCE, lid, shown, url=url, region=region, lat=light["lat"], lon=light["lon"],
        precision="approximate" if destroyed else "exact", kind=nm["kind"], status=status)
    rec["kind_raw"] = light["name"]
    rec["status_raw"] = status_raw
    rec["role"] = nm["role"]
    rec["other_names"] = nm["other_names"]
    rec["links"] = [{"label": f"LighthouseFriends: {light['name']}", "url": url, "kind": "reference"}]
    rec["extra"] = extra
    visit = {}
    if "climb" in flags:
        visit["climbable"] = True
    if "boat" in flags:
        visit["boat_only"] = True
    if visit:
        rec["visit"] = visit
    if "private" in flags:
        rec["access"] = {"level": "private",
                         "note": "LighthouseFriends marks it privately owned, with no access without permission."}
    if "lodging" in flags:
        rec["stay"] = {"type": "rental", "provider": None, "url": None, "season": None, "checked": None,
                       "note": "LighthouseFriends marks overnight lodging here; it does not say whether this is a "
                               "rental, a bed and breakfast or a hostel. Check with the operator."}
        if "keeperprog" in flags:
            rec["stay"]["note"] += " It also lists a volunteer keeper program."
    elif "keeperprog" in flags:
        rec["stay"] = {"type": "keeper_program", "provider": None, "url": None, "season": None, "checked": None,
                       "note": "LighthouseFriends lists a volunteer keeper program here. Check with the host "
                               "organisation for dates and requirements."}
    return rec


def extract(paths: dict[tuple[str, str], Path]) -> tuple[list[dict], dict]:
    records, problems = [], Counter()
    states = sorted({s for s, _ in paths})
    for st in states:
        pages = {name: parse_state_page(paths[(st, name)].read_text(encoding="utf-8", errors="replace"))
                 for name in PASSES}
        by_id = {x["id"]: x for x in pages["all"]}
        flag_sets: dict[str, set[str]] = {lid: set() for lid in by_id}
        for name in PASSES:
            if name == "all":
                continue
            for x in pages[name]:
                if x["id"] in by_id:
                    flag_sets[x["id"]].add(name)
                else:
                    problems[f"{st}: {name} lists a light the full list lacks"] += 1
        for lid, light in by_id.items():
            destroyed = "destroyed" in flag_sets[lid]
            if light["destroyed_card"] != destroyed:
                problems["destroyed filter and highlighted card disagree"] += 1
            rec = build_record(st, light, flag_sets[lid] - {"destroyed"}, destroyed)
            if rec is None:
                problems["no position"] += 1
                continue
            records.append(rec)
    return records, dict(problems)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch Fresnel's LighthouseFriends extract")
    ap.add_argument("--refresh", action="store_true", help="fetch every page again")
    ap.add_argument("--states", help="comma-separated state codes (default all)")
    args = ap.parse_args(argv)
    states = args.states.split(",") if args.states else list(STATES)
    paths = fetch_pages(states, args.refresh)
    records, problems = extract(paths)
    files = sorted(paths.values())
    rx.write_extract(
        OUT_PATH, source=SOURCE,
        title="LighthouseFriends.com: state lists of lighthouses",
        url=f"{BASE}/",
        license_text="Copyright Lighthousefriends.com. Facts only (names, positions, icon flags) with a link to each "
                     "light's page; no text or photographs are copied.",
        credit="LighthouseFriends.com (Kraig Anderson), used for facts with a link",
        records=records, notes={"states": len(states), "passes": list(PASSES), "problems": problems},
        retrieved=c.retrieved_date(*files), country="US")
    cnt = Counter(r["status"] for r in records)
    flg = Counter(f for r in records for f in r["extra"]["flags"])
    c.log(f"lighthousefriends: wrote {len(records)} records; status {dict(cnt)}; flags {dict(flg)}; problems {problems}")
    c.log(f"  kind {dict(Counter(r['kind'] for r in records))}; regions {len({r['region'] for r in records})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
