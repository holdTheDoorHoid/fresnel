#!/usr/bin/env python3
"""NOAA ENC Direct light points -> data/sources/enc.json (DESIGN.md 2.3). US federal public domain.

NOAA's ENC Direct to GIS ArcGIS REST service serves the lights of the electronic navigational charts
(one `Light_point` layer per chart scale band). A light has no name there and no Light List number; it
has a position, a characteristic (coded), a period and group, a height and a nominal range. So these
records are position-only **enrichment**: they never start a station (`enrich_only`), and the merge
joins each to the station within 150 m (the light as charted: characteristic, focal height, range).

The service is intermittent (some bands answer "Could not find service" on one day and work the
next). The fetcher tries every band, retries, caches every page it gets under `$RAW/enc/`, and records
in the extract's notes which bands were missing; a later run fills the gaps without refetching.

Reading a cluster of ENC records (the same light repeats once per chart cell and band, and once per
sector):

- records within 25 m of each other are one light;
- the main light is the full-circle (no sector limits), non-emergency record with a flashing or fixed
  character, the highest, then the newest (`SORDAT`);
- its characteristic is written in Light List form from `LITCHR` (the S-57 code), `SIGGRP`, `COLOUR`
  and `SIGPER`: `Fl W 4s`, `Fl(2) W 6s`, `Iso W 6s`, `Oc W 4s`, `Q W`, `F R`, `Al Fl W R 20s`;
- `HEIGHT` (metres) is the focal height, `VALNMR` the nominal range in nautical miles;
- a light with only sector records (a sector light's coloured arcs) gets the white sector's character;
- only clusters within 200 m of a record of another source (Wikidata, OpenStreetMap, LighthouseFriends,
  NRHP, USLHS, territories) are kept: thousands of buoys and pile lights have nothing to join.

Usage: python3 pipeline/fetch_enc.py [--refresh]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "sources" / "enc.json"
SOURCE = "enc"
ROOT = "https://encdirect.noaa.gov/arcgis/rest/services/encdirect"
# band -> layer id of its Light_point layer (checked 2026-10-21; the services come and go)
BANDS = {"enc_overview": 8, "enc_general": 10, "enc_coastal": 10, "enc_approach": 13, "enc_harbour": 11, "enc_berthing": 6}
FIELDS = "OBJNAM,CATLIT,COLOUR,LITCHR,SIGPER,SIGGRP,SIGSEQ,HEIGHT,VALNMR,LITVIS,SECTR1,SECTR2,ORIENT,EXCLIT,SORDAT,DSNM,INFORM"
PAGE = 1000
CLUSTER_M = 25.0
NEAR_OTHER_M = 200.0
OTHER_SOURCES = ("wikidata", "osm", "lighthousefriends", "nrhp", "uslhs", "territories")

LITCHR = {
    1: "F", 2: "Fl", 3: "LFl", 4: "Q", 5: "VQ", 6: "UQ", 7: "Iso", 8: "Oc", 9: "IQ", 10: "IVQ", 11: "IUQ",
    12: "Mo", 13: "FFl", 14: "Fl+LFl", 15: "OcFl", 16: "FLFl", 17: "Al Oc", 18: "Al LFl", 19: "Al Fl",
    20: "Al Gr", 25: "Q+LFl", 26: "VQ+LFl", 27: "UQ+LFl", 28: "Al", 29: "F+Al Fl",
}
COLOURS = {"1": "W", "2": "B", "3": "R", "4": "G", "5": "Bu", "6": "Y", "7": "Gy", "8": "Br", "9": "Am",
           "10": "Vi", "11": "Or", "12": "Mg", "13": "Pk"}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371008.8 * math.asin(min(1.0, math.sqrt(h)))


# ---------------------------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------------------------

def fetch_band(band: str, layer: int, refresh: bool) -> tuple[list[dict], str | None]:
    """All features of one band's Light_point layer, paged; (features, problem or None)."""
    out: list[dict] = []
    offset = 0
    while True:
        params = {"where": "1=1", "outFields": FIELDS, "outSR": "4326", "f": "json", "returnGeometry": "true",
                  "resultOffset": offset, "resultRecordCount": PAGE}
        url = f"{ROOT}/{band}/MapServer/{layer}/query?" + urlencode(params)
        path = c.raw_dir(SOURCE) / f"{band}_{layer}_{offset:06d}.json"
        try:
            rx.polite_get(url, path, force=refresh and offset == 0 and not out, retries=2, timeout=180)
            data = json.loads(path.read_text(encoding="utf-8"))
        except (c.FetchError, rx.Blocked, ValueError) as e:
            return out, f"{type(e).__name__}: {str(e)[:120]}"
        if data.get("error"):
            path.unlink(missing_ok=True)   # a service that is down must not be cached as an answer
            return out, f"service error: {str(data['error'].get('message'))[:120]}"
        feats = data.get("features") or []
        out += feats
        if len(feats) < PAGE and not data.get("exceededTransferLimit"):
            return out, None
        offset += PAGE


# ---------------------------------------------------------------------------------------------
# Reading the records
# ---------------------------------------------------------------------------------------------

def _num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def fmt_period(p: float | None) -> str:
    if not p or p <= 0:
        return ""
    return f"{int(p)}s" if float(p).is_integer() else f"{p:g}s"


def characteristic(a: dict) -> str | None:
    """A light's character in Light List form from one record's attributes, else None."""
    code = a.get("LITCHR")
    abbr = LITCHR.get(int(code)) if isinstance(code, (int, float)) else None
    if not abbr:
        return None
    grp = (a.get("SIGGRP") or "").strip()
    if grp in ("(1)", "1", "()", "(0)"):
        grp = ""
    colours = [COLOURS.get(x.strip(), "") for x in str(a.get("COLOUR") or "").split(",") if x.strip()]
    colour = " ".join(x for x in colours if x)
    if abbr == "F":
        return f"F {colour}".strip()
    head = f"{abbr}{grp}" if grp else abbr
    parts = [head]
    if colour:
        parts.append(colour)
    per = fmt_period(_num(a.get("SIGPER")))
    if per and abbr not in ("Q", "VQ", "UQ", "IQ", "IVQ", "IUQ") or (per and grp):
        parts.append(per)
    return " ".join(parts)


def is_main(a: dict) -> bool:
    emergency = "emergency" in str(a.get("CATLIT") or "").lower() or "reduced intensity" in str(a.get("INFORM") or "").lower()
    sector = _num(a.get("SECTR1")) is not None or _num(a.get("SECTR2")) is not None
    return not emergency and not sector


def cluster(features: list[dict]) -> list[list[dict]]:
    """Group features within CLUSTER_M of each other (single linkage on a 0.001 degree grid)."""
    cells: dict[tuple[int, int], list[int]] = defaultdict(list)
    pts = []
    for i, f in enumerate(features):
        g = f.get("geometry") or {}
        if not isinstance(g.get("x"), (int, float)) or not isinstance(g.get("y"), (int, float)):
            continue
        pts.append((i, g["y"], g["x"]))
        cells[(math.floor(g["y"] * 1000), math.floor(g["x"] * 1000))].append(len(pts) - 1)
    parent = list(range(len(pts)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for k, (_i, lat, lon) in enumerate(pts):
        cy, cx = math.floor(lat * 1000), math.floor(lon * 1000)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for j in cells.get((cy + dy, cx + dx), []):
                    if j > k and haversine_m(lat, lon, pts[j][1], pts[j][2]) <= CLUSTER_M:
                        parent[find(j)] = find(k)
    groups: dict[int, list[dict]] = defaultdict(list)
    for k, (i, _la, _lo) in enumerate(pts):
        groups[find(k)].append(features[i])
    return sorted(groups.values(), key=lambda g: (g[0]["geometry"]["y"], g[0]["geometry"]["x"]))


def main_record(group: list[dict]) -> tuple[dict | None, str | None]:
    """(the attributes of the cluster's main light, its characteristic) or (None, None)."""
    def rank(f: dict):
        a = f["attributes"]
        return (-(_num(a.get("HEIGHT")) or 0), "".join(chr(255 - ord(ch)) for ch in str(a.get("SORDAT") or "")))
    mains = [f for f in group if is_main(f["attributes"]) and characteristic(f["attributes"])]
    if mains:
        # the newest chart edition of the highest light
        best_h = max((_num(f["attributes"].get("HEIGHT")) or 0) for f in mains)
        top = [f for f in mains if (_num(f["attributes"].get("HEIGHT")) or 0) == best_h]
        top.sort(key=lambda f: str(f["attributes"].get("SORDAT") or ""), reverse=True)
        a = top[0]["attributes"]
        # a range or ratio: take the range from any record of the same character if the newest lacks one
        if _num(a.get("VALNMR")) is None:
            for f in top[1:]:
                if _num(f["attributes"].get("VALNMR")) is not None and characteristic(f["attributes"]) == characteristic(a):
                    a = {**a, "VALNMR": f["attributes"]["VALNMR"]}
                    break
        return a, characteristic(a)
    whites = [f for f in group if "1" in str(f["attributes"].get("COLOUR") or "").split(",") and characteristic(f["attributes"])]
    if whites:
        whites.sort(key=rank)
        a = whites[0]["attributes"]
        return a, characteristic(a)
    return None, None


def load_other_positions() -> list[tuple[float, float]]:
    pts = []
    for sid in OTHER_SOURCES:
        p = REPO / "data" / "sources" / f"{sid}.json"
        if not p.exists():
            continue
        for rec in json.loads(p.read_text(encoding="utf-8")).get("records", []):
            if isinstance(rec.get("lat"), (int, float)) and isinstance(rec.get("lon"), (int, float)):
                pts.append((rec["lat"], rec["lon"]))
    return pts


def near_any(grid: dict, lat: float, lon: float, radius_m: float) -> bool:
    cy, cx = math.floor(lat * 100), math.floor(lon * 100)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for la, lo in grid.get((cy + dy, cx + dx), []):
                if haversine_m(lat, lon, la, lo) <= radius_m:
                    return True
    return False


def build_records(features: list[dict], others: list[tuple[float, float]] | None) -> tuple[list[dict], dict]:
    grid: dict = defaultdict(list)
    for la, lo in others or []:
        grid[(math.floor(la * 100), math.floor(lo * 100))].append((la, lo))
    records, stats = [], Counter()
    for group in cluster(features):
        a, char = main_record(group)
        if a is None:
            stats["no light character"] += 1
            continue
        lat = sum(f["geometry"]["y"] for f in group) / len(group)
        lon = sum(f["geometry"]["x"] for f in group) / len(group)
        if others is not None and not near_any(grid, lat, lon, NEAR_OTHER_M):
            stats["no station near"] += 1
            continue
        rec = rx.new_record(SOURCE, f"{lat:.5f},{lon:.5f}", None, url="https://encdirect.noaa.gov/", lat=lat, lon=lon,
                            precision="exact", kind="lighthouse",
                            light={"characteristic": char, "focal_height_m": _num(a.get("HEIGHT")),
                                   "range_nm": _num(a.get("VALNMR"))})
        rec["extra"] = {"enrich_only": True, "quiet_unmatched": True, "records": len(group),
                        "chart_cell": a.get("DSNM"), "source_date": a.get("SORDAT"),
                        "sectors": sum(1 for f in group if not is_main(f["attributes"]))}
        records.append(rec)
        stats["kept"] += 1
    return records, dict(stats)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch Fresnel's NOAA ENC light extract")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--no-filter", action="store_true", help="keep lights with no other source's record near")
    args = ap.parse_args(argv)
    features: list[dict] = []
    missing = {}
    per_band = {}
    for band, layer in BANDS.items():
        feats, problem = fetch_band(band, layer, args.refresh)
        per_band[band] = len(feats)
        if problem:
            missing[band] = problem
            c.log(f"enc: {band}: {problem}")
        features += feats
    others = None if args.no_filter else load_other_positions()
    records, stats = build_records(features, others)
    files = sorted(c.raw_dir(SOURCE).glob("*.json"))
    rx.write_extract(
        OUT_PATH, source=SOURCE,
        title="NOAA ENC Direct: charted lights of US waters",
        url="https://encdirect.noaa.gov/",
        license_text="US federal public domain (NOAA). Not for navigation.",
        credit="NOAA Office of Coast Survey, ENC Direct (public domain; not for navigation)",
        records=records,
        notes={"features": len(features), "per_band": per_band, "bands_missing": missing, "clusters": stats},
        retrieved=c.retrieved_date(*files))
    c.log(f"enc: {len(features)} features -> {len(records)} lights kept {stats}; bands {per_band}; missing {list(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
