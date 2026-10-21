#!/usr/bin/env python3
"""US territories seed: lights Wikidata, OpenStreetMap and the other sources miss, and the Library of
Congress HAER records of Puerto Rico's lights -> data/sources/territories.json (DESIGN.md 2.4).

Two small, hand-curated parts, both facts only:

1. **Seed lights.** Wikidata has no item for any light in Guam, none in American Samoa but one, and
   misses Fort Louise Augusta (US Virgin Islands) and the Earhart Light (Howland Island). The seed names
   the ones that pass DESIGN section 1's test ("a real structure and a history", not a modern post or
   pile beacon with no history): each has a known year its station was established or its tower was
   built. Position, first year, tower year and retirement come from Wikipedia's "List of lighthouses in
   the United States territories" (a /wiki/ article page; facts only, CC BY-SA, linked), the Light List
   number from the USCG Light List (volumes III and VI). Left out on purpose, with their Light List
   numbers, because they are modern posts with no dated history: Apra Outer Harbor ranges (Guam), Glass
   Breakwater (Guam), Ushi Point and Tanapag Harbor ranges (Northern Marianas).
2. **HAER records.** The Library of Congress holds the Historic American Engineering Record's drawings
   and histories of Puerto Rico's Spanish-era lighthouses (HAER PR-32 to PR-47). They are public domain.
   Each is a position-and-name record that never starts a station (`enrich_only`): it adds the HAER
   number and the item's link to the station it joins. Read from the survey's cached LoC search
   (loc.gov asks for 5 s between requests and disallows its picture search; nothing is fetched here).

Usage: python3 pipeline/fetch_territories.py [--refresh]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "sources" / "territories.json"
SOURCE = "territories"
WP_LIST = "https://en.wikipedia.org/wiki/List_of_lighthouses_in_the_United_States_territories"
WP_EARHART = "https://en.wikipedia.org/wiki/Earhart_Light"
SURVEY = "survey/territories_lightships_lss"

# name in Wikipedia's table -> our seed. `llnr` is the Light List number ("<volume>-<number>").
SEED = [
    {"wp": "Orote Point Light", "name": "Orote Point Light", "region": "GU", "kind": "lighthouse", "other": ["Point Udall Light"],
     "llnr": "6-30685", "first_lit": 1929},
    {"wp": "Ritidian Point Light", "name": "Ritidian Point Light", "region": "GU", "kind": "lighthouse", "other": [],
     "llnr": "6-30660", "first_lit": 1932},
    {"wp": "Pago Pago Range Front Lighthbeacon", "name": "Pago Pago Range Front Light", "region": "AS", "kind": "range_lights",
     "role": "front_range", "llnr": "6-30190", "first_lit": 1901},
    {"wp": "Pago Pago Range Rear Lighthbeacon", "name": "Pago Pago Range Rear Light", "region": "AS", "kind": "range_lights",
     "role": "rear_range", "llnr": "6-30195", "first_lit": 1901},
    {"wp": "Aunu'u Lightbeacon A", "name": "Aunu'u Light", "region": "AS", "kind": "lighthouse", "other": [], "llnr": None,
     "first_lit": None, "note": "An older light of the island is described in the 1922 Light List."},
    {"wp": "Fort Luise Augusta Light", "name": "Fort Louise Augusta Light", "region": "VI", "kind": "lighthouse", "other": [],
     "llnr": None, "first_lit": 1857, "arlhs": "VIR-006"},
]


def cells_text(cell: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", cell))).strip()


def years(text: str) -> list[int]:
    return [int(y) for y in re.findall(r"\b(1[5-9]\d\d|20\d\d)\b", text)]


def geohack(cell: str) -> tuple[float, float] | None:
    m = re.search(r"params=(\d+)_(\d+)_([\d.]+)_([NS])_(\d+)_(\d+)_([\d.]+)_([EW])", cell)
    if m:
        lat = rx.dms(int(m.group(1)), int(m.group(2)), float(m.group(3)), m.group(4))
        lon = rx.dms(int(m.group(5)), int(m.group(6)), float(m.group(7)), m.group(8))
        return lat, lon
    m = re.search(r"params=([\d.]+)_([NS])_([\d.]+)_([EW])", cell)
    if m:
        return rx.dms(float(m.group(1)), 0, 0, m.group(2)), rx.dms(float(m.group(3)), 0, 0, m.group(4))
    return None


def parse_wikipedia_table(page_html: str) -> dict[str, dict]:
    """{name: {lat, lon, location, built_text, end_text}} for each row of the list's table."""
    out = {}
    tables = re.findall(r'<table class="wikitable.*?</table>', page_html, re.S)
    if not tables:
        return out
    for row in re.findall(r"<tr.*?</tr>", tables[0], re.S)[1:]:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)
        if len(cells) < 6:
            continue
        name = cells_text(cells[0])
        pos = geohack(cells[3])
        out[name] = {"lat": pos[0] if pos else None, "lon": pos[1] if pos else None, "location": cells_text(cells[2]),
                     "built_text": cells_text(cells[4]), "end_text": cells_text(cells[5])}
    return out


def seed_records(table: dict[str, dict], earhart: tuple[float, float] | None) -> list[dict]:
    recs = []
    for s in SEED:
        row = table.get(s["wp"])
        if not row or row["lat"] is None:
            c.log(f"territories: no row {s['wp']!r} in the Wikipedia list; skipped")
            continue
        built_years = years(row["built_text"])
        end_years = years(row["end_text"])
        first = s.get("first_lit") or (built_years[0] if built_years else None)
        current = built_years[1] if len(built_years) > 1 else None
        active = "active" in row["end_text"].lower()
        status = "active" if active else ("inactive" if end_years else None)
        rec = rx.new_record(SOURCE, s["name"].lower().replace(" ", "-").replace("'", ""), s["name"], url=WP_LIST,
                            region=s["region"], lat=row["lat"], lon=row["lon"], precision="exact", kind=s["kind"], status=status)
        rec["role"] = s.get("role")
        rec["other_names"] = s.get("other", [])
        rec["light"]["first_lit"] = first
        rec["light"]["deactivated"] = end_years[0] if end_years and not active else None
        rec["structure"]["built"] = current
        rec["aton"]["uscg_llnr"] = s.get("llnr")
        rec["aton"]["arlhs"] = s.get("arlhs")
        ev = []
        if first:
            ev.append({"year": first, "event": "first_lit", "note": "Wikipedia: List of lighthouses in the United States territories", "from": SOURCE})
        if current:
            ev.append({"year": current, "event": "built", "note": "The present tower (Wikipedia: List of lighthouses in the United States territories)", "from": SOURCE})
        if rec["light"]["deactivated"]:
            ev.append({"year": rec["light"]["deactivated"], "event": "deactivated", "note": "Wikipedia: List of lighthouses in the United States territories", "from": SOURCE})
        rec["events"] = ev
        rec["links"] = [{"label": "Wikipedia: List of lighthouses in the United States territories", "url": WP_LIST, "kind": "wikipedia"}]
        rec["extra"] = {"seed": True, "location_text": row["location"], "note": s.get("note")}
        rec["extra"] = {k: v for k, v in rec["extra"].items() if v is not None}
        recs.append(rec)
    if earhart:
        rec = rx.new_record(SOURCE, "earhart-light", "Earhart Light", url=WP_EARHART, region="UM", lat=earhart[0], lon=earhart[1],
                            precision="approximate", kind="lighthouse", status="inactive")
        rec["other_names"] = ["Howland Island Day Beacon"]
        rec["light"]["first_lit"] = None
        rec["structure"]["built"] = 1937
        rec["aton"]["arlhs"] = "BAK-002"
        rec["events"] = [{"year": 1937, "event": "built", "note": "Built for Howland Island's colonists (Rowlett's Lighthouse Directory, Wikipedia)", "from": SOURCE}]
        rec["links"] = [{"label": "Wikipedia: Earhart Light", "url": WP_EARHART, "kind": "wikipedia"}]
        rec["extra"] = {"seed": True, "note": "Lighthouse Directory lists it as inactive since 1942."}
        recs.append(rec)
    return recs


def haer_records(search_json: dict) -> list[dict]:
    recs = []
    for item in search_json.get("results") or []:
        url = (item.get("url") or item.get("id") or "").replace("http://", "https://")
        m = re.search(r"/item/pr(\d{4})/", url)
        title = item.get("title") or ""
        ll = item.get("latlong")
        if not m:
            continue
        if not (isinstance(ll, list) and len(ll) == 2):
            ll = [None, None]    # no position in the catalogue: the merge joins it by name within Puerto Rico
        num = int(m.group(1))
        if not 32 <= num <= 47:      # HAER PR-32 to PR-47: the Spanish-era lighthouse system and its dwelling
            continue
        name = re.split(r",\s", title)[0].strip()
        if re.search(r"dwelling", name, re.I):
            continue
        rec = rx.new_record(SOURCE, f"haer-pr-{num}", name, url=url, region="PR", lat=ll[0], lon=ll[1], precision="approximate",
                            kind="lighthouse")
        rec["registers"] = [{"register": "HAER", "number": f"PR-{num}", "url": url}]
        rec["links"] = [{"label": f"Library of Congress: HAER PR-{num}, {name}", "url": url, "kind": "register"}]
        rec["extra"] = {"enrich_only": True, "quiet_unmatched": True, "loc_title": title[:160]}
        recs.append(rec)
    return recs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build Fresnel's territories seed and HAER extract")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    cache = c.raw_dir(SOURCE)
    files = []
    wp = cache / "List_of_lighthouses_in_the_United_States_territories.html"
    old = c.RAW_ROOT / SURVEY / "wp" / "List_of_lighthouses_in_the_United_States_territories.html"
    if not wp.exists() and not args.refresh and old.exists():
        shutil.copyfile(old, wp)
    rx.polite_get(WP_LIST, wp, force=args.refresh)
    ea = cache / "Earhart_Light.html"
    rx.polite_get(WP_EARHART, ea, force=args.refresh)
    haer = cache / "loc_haer_pr.json"
    old_haer = c.RAW_ROOT / SURVEY / "loc_habshaer_pr.json"
    if not haer.exists() and old_haer.exists():
        shutil.copyfile(old_haer, haer)
    files += [wp, ea]
    table = parse_wikipedia_table(wp.read_text(encoding="utf-8", errors="replace"))
    m = re.search(r"params=([\d.]+)_([NS])_([\d.]+)_([EW])_", ea.read_text(encoding="utf-8", errors="replace"))
    earhart = (rx.dms(float(m.group(1)), 0, 0, m.group(2)), rx.dms(float(m.group(3)), 0, 0, m.group(4))) if m else None
    records = seed_records(table, earhart)
    n_haer = 0
    if haer.exists():
        files.append(haer)
        h = haer_records(json.loads(haer.read_text(encoding="utf-8")))
        n_haer = len(h)
        records += h
    rx.write_extract(
        OUT_PATH, source=SOURCE,
        title="US territories: lights the other sources miss, and Library of Congress HAER records of Puerto Rico's lighthouses",
        url=WP_LIST,
        license_text="Facts only. Wikipedia's list (CC BY-SA 4.0) for the seed lights' positions and years; the Library of "
                     "Congress HAER records (US federal public domain) for Puerto Rico.",
        credit="Wikipedia (CC BY-SA 4.0); Library of Congress, Historic American Engineering Record (public domain)",
        records=records, notes={"seed": len(records) - n_haer, "haer": n_haer,
                                "left_out": "Apra Outer Harbor ranges, Glass Breakwater (Guam); Ushi Point, Tanapag Harbor ranges (Northern Marianas): modern posts with no dated history"},
        retrieved=c.retrieved_date(*files))
    c.log(f"territories: wrote {len(records)} records ({len(records) - n_haer} seed, {n_haer} HAER)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
