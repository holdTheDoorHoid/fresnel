#!/usr/bin/env python3
"""USCG Light List (volumes I-VII, PDF) -> data/sources/uscg_light_list.json (DESIGN.md 2.3). US
federal public domain (a US Coast Guard publication, COMDTPUB P16502).

The Light List is the Coast Guard's list of every federal aid to navigation: lights, buoys,
daybeacons, sound signals. It is published only as PDFs (no CSV or API), one per district group:

    I Northeast (St. Croix River, Maine to Shrewsbury River, NJ)   II East (Shrewsbury River to
    Moriches Inlet... Chesapeake)   III Southeast (Atlantic coast to the Florida Keys, Puerto Rico and the
    Virgin Islands)   IV Gulf   V Mississippi River system   VI Pacific (California to Alaska, Hawaii,
    Guam, American Samoa, Northern Marianas, other Pacific islands)   VII Great Lakes

`pdftotext -layout` gives fixed-width rows: `LLNR  Name  Position  Characteristic  Height  Range
Structure  Remarks`, a name or position continued on the next line. The column offsets are read from the
header row of each volume. The text layer's Height column prints 0 for many lights (Portland Head Light),
so a height counts only when it is above 0; the focal height is otherwise NOAA ENC's (fetch_enc.py).

Kept per light: the Light List number (`aton.uscg_llnr` = "<volume>-<LLNR>", the form Wikidata P3723
uses), name, position to 0.001", the characteristic written in Light List form (`Fl(2) W 6s`), the
nominal range in nautical miles, the structure text, the fog signal from the remarks, and the remarks.
Buoys, daybeacons and virtual aids are dropped. Only lights that can be a station of Fresnel are
kept: the Light List number is one Wikidata carries, or a record of another source lies within
300 m. A record is **enrichment** (`enrich_only`: it never starts a station) joined by the merge by
number, then by name and position. The 2025 edition's server file is dated 2026-10-14; the edition date
is printed on the PDF's first page and is written to the extract's notes.

Usage: python3 pipeline/fetch_uscg_light_list.py [--refresh] [--volumes 1,3]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "sources" / "uscg_light_list.json"
SOURCE = "uscg_light_list"
URL = "https://navcen.uscg.gov/sites/default/files/pdf/lightLists/LightList_V{n}_2025.pdf"
INDEX_URL = "https://www.navcen.uscg.gov/light-list-annual-publication"
# Copies the earlier surveys already downloaded (same files).
OLD_COPIES = {1: ["survey/us/LightList_V1_2025.pdf"], 3: ["survey/territories_lightships_lss/lightlist/V3.pdf"],
              6: ["survey/territories_lightships_lss/lightlist/V6.pdf"]}
NEAR_OTHER_M = 300.0
OTHER_SOURCES = ("wikidata", "osm", "lighthousefriends", "nrhp", "uslhs", "territories")
DEFAULT_COLS = {"name": 9, "pos": 34, "char": 51, "height": 66, "range": 73, "struct": 79, "remarks": 108}

NOT_A_LIGHT_RE = re.compile(r"\b(buoy|bell|gong|whistle|daybeacon|dayboard|day board|virtual|AIS|RACON|mooring|"
                            r"sound signal|marker|pile|dolphin|piling)\b", re.I)
POS_RE = re.compile(r"^\s*(\d{2,3})-(\d{2})-(\d{2}(?:\.\d+)?)([NSEW])\s*$")


def pdf_to_text(pdf: Path, txt: Path) -> Path:
    if not txt.exists() or txt.stat().st_mtime < pdf.stat().st_mtime:
        subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True, timeout=300)
    return txt


def get_volume(n: int, refresh: bool) -> Path:
    cache = c.raw_dir(SOURCE)
    pdf = cache / f"LightList_V{n}_2025.pdf"
    if not pdf.exists() and not refresh:
        for old in OLD_COPIES.get(n, []):
            p = c.RAW_ROOT / old
            if p.exists():
                shutil.copyfile(p, pdf)
                break
    if not pdf.exists() or refresh:
        rx.polite_get(URL.format(n=n), pdf, force=refresh, timeout=300)
    return pdf_to_text(pdf, cache / f"V{n}.txt")


# ---------------------------------------------------------------------------------------------
# Parsing the fixed-width text
# ---------------------------------------------------------------------------------------------

def columns_of(lines: list[str]) -> dict[str, int]:
    for l in lines[:400]:
        if "LLNR" in l and "Characteristic" in l and "Position" in l:
            try:
                return {"name": l.index("Name"), "pos": l.index("Position"), "char": l.index("Characteristic"),
                        "height": l.index("Height"), "range": l.index("Range"), "struct": l.index("Structure"),
                        "remarks": l.index("Remarks")}
            except ValueError:
                break
    return dict(DEFAULT_COLS)


def is_noise(l: str) -> bool:
    return (not l.strip() or "Maritime Safety Information Products" in l or l.strip().startswith("https://")
            or re.fullmatch(r"\s*\d+/\d+\s*", l) is not None or "Light List for Volume" in l)


ENTRY_RE = re.compile(r"^\s{0,2}(?P<llnr>\d+(?:\.\d+)?)\s+(?P<name>\S.*?)\s*(?P<lat>\d{2}-\d{2}-\d{2}(?:\.\d+)?[NS])(?P<rest>.*)$")
LON_RE = re.compile(r"^(?P<pre>.*?)\s*(?P<lon>\d{3}-\d{2}-\d{2}(?:\.\d+)?[EW])\s*(?P<post>.*)$")
TOKEN_RE = re.compile(r"\S+(?: \S+)*")


def parse_text(text: str) -> list[dict]:
    """[{llnr, name, lat_s, lon_s, char, height_ft, range_nm, text}] in order of the printed list.

    An entry starts at a line whose first field is the light number and which carries the latitude; the
    next line with a longitude finishes the position (and any second line of the name before it). The
    cells after the latitude are classified by where they start against the header's column offsets:
    the characteristic, then the height and the range (two numbers: height first; one number: the
    range when it sits at the range column), then the structure and remarks (kept together as `text`)."""
    lines = text.split("\n")
    cols = columns_of(lines)
    out = []
    i = 0
    while i < len(lines):
        l = lines[i]
        m = ENTRY_RE.match(l) if not is_noise(l) else None
        i += 1
        if not m:
            continue
        entry = {"llnr": m.group("llnr"), "name": m.group("name").strip(), "lat_s": m.group("lat"), "lon_s": None,
                 "char": "", "height_ft": None, "range_nm": None, "text": ""}
        base = m.start("rest")
        tokens = [(base + t.start(), t.group(0)) for t in TOKEN_RE.finditer(m.group("rest"))]
        chars, nums, tail = [], [], []
        for start, tok in tokens:
            if start >= cols["struct"] - 4:
                tail.append(tok)
            elif re.fullmatch(r"\d+(?:\.\d+)?", tok) and start >= cols["height"] - 5:
                nums.append((start, float(tok)))
            elif start < cols["height"] - 1:
                chars.append(tok)
            else:
                tail.append(tok)
        entry["char"] = " ".join(chars)
        if len(nums) >= 2:
            entry["height_ft"], entry["range_nm"] = nums[0][1], nums[1][1]
        elif len(nums) == 1:
            entry["range_nm"] = nums[0][1]   # a lit aid always prints its range; the height may be blank
        text_parts = tail
        # continuation lines: up to 6 lines until the next entry; the first with a longitude closes the position
        j = i
        while j < len(lines) and j < i + 8:
            n = lines[j]
            if is_noise(n):
                break
            if ENTRY_RE.match(n) and not n.startswith("        "):
                break
            lm = LON_RE.match(n)
            if lm and entry["lon_s"] is None:
                entry["lon_s"] = lm.group("lon")
                if lm.group("pre").strip() and len(lm.group("pre")) < cols["pos"] + 2:
                    entry["name"] += " " + lm.group("pre").strip()
                if lm.group("post").strip():
                    text_parts.append(lm.group("post").strip())
            elif n.strip() and not re.match(r"^\s{0,2}\d+(?:\.\d+)?\s{2,}\S", n):
                text_parts.append(n.strip())
            elif re.match(r"^\s{0,2}\d+(?:\.\d+)?\s{2,}\S", n):
                break
            j += 1
        i = j if j > i else i
        entry["name"] = re.sub(r"\s+", " ", entry["name"])
        entry["text"] = re.sub(r"\s+", " ", " ".join(text_parts)).strip()
        if entry["lon_s"] is None:
            continue
        out.append(entry)
    return out


def to_deg(s: str) -> float | None:
    m = POS_RE.match(s)
    if not m:
        return None
    return rx.dms(int(m.group(1)), int(m.group(2)), float(m.group(3)), m.group(4))


def rx_ft(feet: float | None) -> float | None:
    """Feet to metres; a 0 in the Height column means 'not printed', not a light at sea level."""
    return round(feet * 0.3048, 1) if feet and feet > 0 else None


def tidy_characteristic(s: str) -> str | None:
    """"Fl (2)W 5s" -> "Fl(2) W 5s"; "FRWG" stays; empty -> None."""
    s = re.sub(r"\s+", " ", s or "").strip()
    if not s:
        return None
    s = re.sub(r"\s*\((\d+(?:\+\d+)?|[A-Z])\)\s*", lambda m: f"({m.group(1)}) ", s).strip()
    s = re.sub(r"\)(?=\S)", ") ", s)
    return s


FOG_RE = re.compile(r"\b(HORN|BELL|SIREN|DIAPHONE|WHISTLE|GONG|REED|NAUTOPHONE|TYFON)\b", re.I)


def fog_signal(remarks: str) -> str | None:
    m = FOG_RE.search(remarks or "")
    return m.group(1).lower() if m else None


# ---------------------------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------------------------

def is_light_entry(e: dict) -> bool:
    """A light that could be a station: characteristic or a lantern-like name, not a buoy or a beacon pole."""
    if NOT_A_LIGHT_RE.search(e["name"]):
        return False
    if not e["char"]:
        return False
    return True


def build_record(volume: int, e: dict) -> dict | None:
    lat, lon = to_deg(e["lat_s"]), to_deg(e["lon_s"])
    if lat is None or lon is None:
        return None
    char = tidy_characteristic(e["char"])
    rng = e["range_nm"]
    focal = rx_ft(e["height_ft"])
    name = re.sub(r"\s*\(AIS\)\s*", " ", e["name"]).strip()
    rec = rx.new_record(SOURCE, f"{volume}-{e['llnr']}", name, url=INDEX_URL, lat=lat, lon=lon, precision="exact",
                        kind="lighthouse",
                        light={"characteristic": char, "range_nm": rng, "focal_height_m": focal, "fog_signal": fog_signal(e["text"])},
                        aton={"uscg_llnr": f"{volume}-{e['llnr']}"})
    sec = bool(re.search(r"\b(directional|sector|auxiliary|emergency|leading|range)\b", name, re.I))
    rec["extra"] = {"enrich_only": True, "quiet_unmatched": True, "volume": volume, "listing": e["text"] or None,
                    "secondary": sec or None,
                    "seasonal": True if re.search(r"\bseasonal\b", e["text"], re.I) else None}
    rec["extra"] = {k: v for k, v in rec["extra"].items() if v is not None}
    return rec


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371008.8 * math.asin(min(1.0, math.sqrt(h)))


def other_positions() -> tuple[list[tuple[float, float]], set[str]]:
    pts, llnrs = [], set()
    for sid in OTHER_SOURCES:
        p = REPO / "data" / "sources" / f"{sid}.json"
        if not p.exists():
            continue
        for rec in json.loads(p.read_text(encoding="utf-8")).get("records", []):
            if isinstance(rec.get("lat"), (int, float)) and isinstance(rec.get("lon"), (int, float)):
                pts.append((rec["lat"], rec["lon"]))
            ll = (rec.get("aton") or {}).get("uscg_llnr")
            if ll:
                llnrs.add(str(ll).split("-")[-1].lstrip("0"))
    return pts, llnrs


def keep_filter(pts: list[tuple[float, float]], llnrs: set[str]):
    grid: dict = defaultdict(list)
    for la, lo in pts:
        grid[(math.floor(la * 100), math.floor(lo * 100))].append((la, lo))

    def keep(rec: dict) -> bool:
        if rec["aton"]["uscg_llnr"].split("-")[-1].lstrip("0") in llnrs:
            return True
        cy, cx = math.floor(rec["lat"] * 100), math.floor(rec["lon"] * 100)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for la, lo in grid.get((cy + dy, cx + dx), []):
                    if haversine_m(rec["lat"], rec["lon"], la, lo) <= NEAR_OTHER_M:
                        return True
        return False
    return keep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch Fresnel's USCG Light List extract")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--volumes", default="1,2,3,4,5,6,7")
    ap.add_argument("--no-filter", action="store_true")
    args = ap.parse_args(argv)
    vols = [int(v) for v in args.volumes.split(",")]
    pts, llnrs = other_positions()
    keep = (lambda r: True) if args.no_filter else keep_filter(pts, llnrs)
    records, stats, editions = [], Counter(), {}
    seen = set()
    for n in vols:
        txt = get_volume(n, args.refresh)
        text = txt.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"Light List for Volume \d+[^\n]*?(\d{2}/\d{2}/\d{4})", text)
        editions[f"V{n}"] = m.group(1) if m else None
        entries = parse_text(text)
        stats[f"V{n} rows"] = len(entries)
        for e in entries:
            if not is_light_entry(e):
                continue
            rec = build_record(n, e)
            if rec is None or rec["key"] in seen:
                continue
            seen.add(rec["key"])
            stats[f"V{n} lights"] += 1
            if keep(rec):
                records.append(rec)
                stats[f"V{n} kept"] += 1
    files = sorted(c.raw_dir(SOURCE).glob("LightList_V*.pdf"))
    rx.write_extract(
        OUT_PATH, source=SOURCE,
        title="USCG Light List (2025 edition)",
        url=INDEX_URL,
        license_text="US federal public domain (US Coast Guard).",
        credit="US Coast Guard Light List (public domain)",
        records=records, notes={"editions": editions, "counts": dict(stats), "volumes": vols,
                                "note": "A height of 0 in the PDF's text layer means 'not printed' and is not taken."},
        retrieved=c.retrieved_date(*files))
    c.log(f"uscg_light_list: wrote {len(records)} records; {dict(stats)}; editions {editions}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
