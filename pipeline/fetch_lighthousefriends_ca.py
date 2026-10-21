#!/usr/bin/env python3
"""Lighthouse Friends (Kraig Anderson, lighthousefriends.com): the Canadian lights; adds them to
data/sources/lighthousefriends.json (DESIGN.md 2.3, 3.8). The source id is `lighthousefriends`,
shared with the US fetcher (another branch): this module is the Canadian function, `fetch_canada()`,
and its writer keeps whatever non-Canadian records the file already holds, so the two fetchers can
run in either order and give the same union.

Source: the site's own state pages, `https://www.lighthousefriends.com/pull-state.asp?state=<S>` for
S = BC MB NB NF NS ON PE PQ (NF is Newfoundland and Labrador, PQ Quebec). Each page lists every light
of the province as a link (`light.asp?ID=<n>`), its name and community, in a shaded box when the
historic structure is "completely or mostly destroyed", and, in the page's map script, a position
(6 decimals, GPS fixes by the site's author) per light, with a black marker for a destroyed one. That
is the whole record: id, name, community, position, destroyed. The site's own filters add the visit
flags, one request per province and flag, `pull-state.asp?state=<S>&A<k>=1`: A2 boat required, A5
private, A6 open for climbing, A7 interior open or museum on site, A9 overnight lodging, A10 a
volunteer-keeper programme. No station page is read (about 1,150 of them); the per-station keeper
lists, histories and references belong to the research agents, who cite the page by the URL each
record carries.

Licence: all rights reserved, (c) 2001- Kraig Anderson / Lighthousefriends.com, photographs by named
owners. Facts only (names, positions, the flags), credit and a link on every page, never the text.
robots.txt: none (the host answers the IIS 404 page). Pages are windows-1252 with no declared charset.

The survey's cache (RAW_ROOT/survey/canada/lhfriends/) holds all 8 state pages and the filter pages,
and is read in place of fetching again.

Usage: python3 pipeline/fetch_lighthousefriends_ca.py [--refresh]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ca_common as cc  # noqa: E402
import _common as c  # noqa: E402

SOURCE = "lighthousefriends"
OUT_PATH = c.REPO / "data" / "sources" / f"{SOURCE}.json"
STATE_URL = "https://www.lighthousefriends.com/pull-state.asp?state={state}"
FILTER_URL = "https://www.lighthousefriends.com/pull-state.asp?state={state}&{flag}=1"
LIGHT_URL = "https://www.lighthousefriends.com/light.asp?ID={id}"
STATES = {"BC": "BC", "MB": "MB", "NB": "NB", "NF": "NL", "NS": "NS", "ON": "ON", "PE": "PE", "PQ": "QC"}
FLAGS = {"A2": "boat", "A5": "private", "A6": "climb", "A7": "interior_open", "A9": "lodging", "A10": "keeper_program"}
LICENSE = ("All rights reserved, (c) 2001- Kraig Anderson / Lighthousefriends.com. Facts only (names, positions, "
           "access flags), with credit and a link on every page.")
# A light's position must fall in Canada (a loose box): a default or mistyped point is dropped.
CANADA_BOX = (41.5, 84.0, -141.5, -52.0)

CARD_RE = re.compile(r'<a href="https://www\.lighthousefriends\.com/light\.asp\?ID=(\d+)"[^>]*class="([^"]*)"[^>]*>(.*?)</a>', re.S)
SPAN_RE = re.compile(r"<span>(.*?)</span>", re.S)
LATLNG_RE = re.compile(r"var\s+(\w+)\s*=\s*new google\.maps\.LatLng\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
MARKER_RE = re.compile(r"new google\.maps\.Marker\(\{\s*position:\s*(\w+)\b[^}]*?icon:\s*(\w+)\s*\}\)(.*?)(?=new google\.maps\.Marker\(|map\.fitBounds)", re.S)
OPEN_RE = re.compile(r"window\.open\('https://www\.lighthousefriends\.com/light\.asp\?ID=(\d+)'\)")


def parse_state_page(html_text: str) -> dict[str, dict]:
    """id -> {name, community, destroyed (shaded box), lat, lon, marker_destroyed}. A light with no
    marker keeps lat/lon None."""
    lights: dict[str, dict] = {}
    for ident, cls, body in CARD_RE.findall(html_text):
        spans = [cc.text_of(s) for s in SPAN_RE.findall(body)]
        if not spans:
            continue
        lights[ident] = {"name": spans[0], "community": spans[1] if len(spans) > 1 else None,
                         "destroyed": "w3-theme" in cls.split(), "lat": None, "lon": None, "marker_destroyed": None}
    coords = {name: (float(a), float(b)) for name, a, b in LATLNG_RE.findall(html_text)}
    for var, icon, rest in MARKER_RE.findall(html_text):
        m = OPEN_RE.search(rest)
        if not m or var not in coords:
            continue
        light = lights.get(m.group(1))
        if light is not None:
            light["lat"], light["lon"] = coords[var]
            light["marker_destroyed"] = icon == "imageblack"
    return lights


def listed_ids(html_text: str) -> set[str]:
    """The ids a filtered page lists (the filter's matches)."""
    return {ident for ident, _cls, _body in CARD_RE.findall(html_text)}


def in_canada(lat: float | None, lon: float | None) -> bool:
    return lat is not None and lon is not None and CANADA_BOX[0] <= lat <= CANADA_BOX[1] and CANADA_BOX[2] <= lon <= CANADA_BOX[3]


def kind_of(name: str) -> str:
    n = name.lower()
    if re.search(r"\brange\b|\b(front|rear)\b", n):
        return "range_lights"
    if re.search(r"\b(pier ?head|pier|breakwater|jetty|mole)\b", n):
        return "pier_light"
    return "lighthouse"


def role_of(name: str) -> str | None:
    n = name.lower()
    if re.search(r"\bfront\b", n) and not re.search(r"\brear\b", n):
        return "front_range"
    if re.search(r"\brear\b", n) and not re.search(r"\bfront\b", n):
        return "rear_range"
    return None


def build_record(ident: str, state: str, light: dict, flags: list[str]) -> dict:
    name = re.sub(r"\s+", " ", light["name"]).strip()
    lost = bool(light["destroyed"])
    return {
        "key": f"{SOURCE}:{ident}",
        "url": LIGHT_URL.format(id=ident),
        "name": name,
        "other_names": [],
        "country": "CA",
        "region": STATES[state],
        "county": None,
        "lat": light["lat"],
        "lon": light["lon"],
        "precision": "exact",
        "kind": kind_of(name),
        "kind_raw": None,
        "role": role_of(name),
        "status": "lost" if lost else None,
        "status_raw": "destroyed" if lost else None,
        "structure": {"type": None, "material": None, "built": None, "height_m": None, "status": "lost" if lost else None},
        "light": {"first_lit": None, "deactivated": None, "characteristic": None, "focal_height_m": None,
                  "range_nm": None, "fog_signal": None, "lens": None},
        "setting": None,
        "registers": [],
        "aton": {"uscg_llnr": None, "arlhs": None, "ccg_list_number": None, "nga": None},
        "agency": None,
        "ownership": None,
        "events": [],
        "photos": [],
        "links": [{"label": "Lighthouse Friends", "url": LIGHT_URL.format(id=ident), "kind": "reference"}],
        "relations": {},
        "extra": {
            "lhf_id": ident,
            "community": light["community"],
            "destroyed": lost,
            "flags": sorted(flags),
            "join_keys": [f"lhf:{ident}"],
        },
    }


def fetch_canada(refresh: bool = False) -> tuple[list[dict], dict, list[Path]]:
    """(records, notes, cache files) for the eight Canadian state pages and their visit filters."""
    cache = c.raw_dir(SOURCE) / "ca"
    survey = cc.SURVEY / "lhfriends"
    records, notes, paths = [], {"by_state": {}, "no_position": [], "marker_disagrees": [], "flag_counts": {}}, []
    flag_counts = {f: 0 for f in FLAGS.values()}
    for state in STATES:
        sp = cache / f"state_{state}.html"
        page = cc.decode(cc.cached_get(STATE_URL.format(state=state), sp, survey / f"state_{state}.html", refresh=refresh), "cp1252")
        paths.append(sp)
        lights = parse_state_page(page)
        flags_of: dict[str, list[str]] = {i: [] for i in lights}
        for flag, label in FLAGS.items():
            fp = cache / f"filter_{state}_{flag}.html"
            body = cc.cached_get(FILTER_URL.format(state=state, flag=flag), fp, survey / "filters" / f"{state}_{flag}.html", refresh=refresh)
            paths.append(fp)
            for ident in listed_ids(cc.decode(body, "cp1252")):
                if ident in flags_of:
                    flags_of[ident].append(label)
                    flag_counts[label] += 1
        n_placed = 0
        for ident, light in sorted(lights.items(), key=lambda kv: int(kv[0])):
            if not in_canada(light["lat"], light["lon"]):
                notes["no_position"].append({"id": ident, "name": light["name"], "state": state})
                continue
            if light["marker_destroyed"] is not None and light["marker_destroyed"] != light["destroyed"]:
                notes["marker_disagrees"].append({"id": ident, "name": light["name"]})
            records.append(build_record(ident, state, light, flags_of[ident]))
            n_placed += 1
        notes["by_state"][STATES[state]] = {"listed": len(lights), "written": n_placed,
                                            "destroyed": sum(1 for lt in lights.values() if lt["destroyed"])}
    notes["flag_counts"] = flag_counts
    return records, notes, paths


def write_union(records: list[dict], notes: dict, retrieved: str) -> int:
    """Write data/sources/lighthousefriends.json: these Canadian records plus the non-Canadian ones the
    file already holds (the US fetcher's), so either fetcher can run first."""
    kept, header_notes = [], {}
    if OUT_PATH.exists():
        old = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        kept = [r for r in old.get("records", []) if r.get("country") != "CA"]
        header_notes = dict(old.get("notes") or {})
    header_notes["canada"] = notes
    c.write_source_json(OUT_PATH, source=SOURCE, title="Lighthouse Friends (Kraig Anderson): lighthouses",
                        url="https://www.lighthousefriends.com/", license_text=LICENSE, records=kept + records,
                        notes=header_notes, retrieved=retrieved)
    return len(kept)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--refresh", action="store_true", help="fetch again instead of using the cache")
    args = ap.parse_args(argv)
    records, notes, paths = fetch_canada(args.refresh)
    kept = write_union(records, notes, c.retrieved_date(*paths))
    c.log(f"lighthousefriends: {len(records)} Canadian records written, {kept} other records kept; "
          f"{len(notes['no_position'])} without a position")
    return 0


if __name__ == "__main__":
    sys.exit(main())
