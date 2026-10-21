#!/usr/bin/env python3
"""Canadian Coast Guard List of Lights, Buoys and Fog Signals (2026 edition): the lit fixed aids
that are lighthouses or sit where a station is; writes data/sources/ccg_list_of_lights.json
(DESIGN.md 2.3, 3.8).

Source: https://www.notmar.gc.ca/list-livre-en.php (Notices to Mariners, Canadian Coast Guard),
which links five volumes (Newfoundland and Labrador, Atlantic, Inland Waters, Pacific, Arctic) of
numbered sections, each an HTML table (`<table class="wb-tables ...">`, one `<tr>` per aid). A
section is `.../publications/list-lights/<volume>/<code>-en.php`. About 130 sections; the fetcher
reads the index, then each section once (2 s apart, robots.txt honoured: only /zip-publication-*
and /tmp/ are disallowed), caching every page under RAW_ROOT/ccg_list_of_lights/.

Licence: (c) His Majesty the King in Right of Canada, as represented by the Canadian Coast Guard,
2026. No open licence is stated, so only facts are taken (position, characteristic, focal height,
range, the kind of structure and its height, the list and Admiralty numbers), with credit and a
link to the volume.

What a row gives (its cells): list number (+ the international Admiralty number `H####` in italics
under it), name (bold in Newfoundland and Labrador for a major light station), location text and the
position to 0.1 arc-second, characteristic (`Fl`), colour (`W`), period (`4s`), focal height above
water (m), nominal range (nm), a description of the structure with its height above ground (m), and
remarks (seasonal or year round, fog signal). Buoys are rows in italics (`<em>`): never taken.

**Which rows are kept** (`classify`, `keep_record`): fixed lit aids only, and of those:

- every one that is *clearly a lighthouse*: its name says light station / lighthouse, or (Newfoundland
  and Labrador, where the List prints major lights in bold) it is a major light, or its description
  names a lighthouse, dwelling, keeper or lantern, or a tower attached to a building;
- every other lit fixed aid within MATCH_M of a Canadian station record in the other extracts
  (Wikidata, OpenStreetMap lights that may start a station, the heritage lighthouses, Lighthouse
  Friends): those add the charted light (characteristic, heights, range, fog signal, list number) to
  a station the other sources already hold;
- nothing else. The thousands of small modern beacons (skeleton towers, poles, piles, dolphins,
  small prefabricated towers on a rock) are counted in the header and not written: DESIGN section 1
  leaves modern automated beacons out. `extra.aid_class` (`lighthouse`, `tower`, `beacon`, `other`) and
  `extra.clear_lighthouse` carry the reading, and the merge starts a station from a record only when
  `clear_lighthouse` is set.

Usage: python3 pipeline/fetch_ccg_list_of_lights.py [--refresh] [--no-match]
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

SOURCE = "ccg_list_of_lights"
OUT_PATH = c.REPO / "data" / "sources" / f"{SOURCE}.json"
HOST = "https://www.notmar.gc.ca"
INDEX_URL = f"{HOST}/list-livre-en.php"
VOLUME_URL = HOST + "/publications/list-lights/{vol}/{vol_code}volumee.pdf"
SECTION_RE = re.compile(r'href="(/publications/list-lights/([a-z\-]+)/([a-z]+)(\d+)-en\.php)"')
# volume directory -> (code in file names, list-number prefix used by Wikidata P3920 and the Directory, title)
VOLUMES = {
    "newfoundland": ("nl", "N", "Newfoundland and Labrador"),
    "atl": ("atl", "A", "Atlantic Coast and the St. Lawrence to Montreal"),
    "inland-waters": ("iw", "I", "Inland Waters"),
    "pac": ("pac", "P", "Pacific Coast"),
    "arc": ("arc", "T", "Arctic Coast"),
}
LICENSE = ("(c) His Majesty the King in Right of Canada, as represented by the Canadian Coast Guard, 2026. "
           "No open licence stated: facts only (position, characteristic, height, range, structure), with credit and link.")
MATCH_M = 150.0


def section_links(index_html: str) -> list[tuple[str, str, str]]:
    """(path, volume directory, section code) for every numbered section the index links (front
    matter, index pages and annexes have no digits in their code and are not aids)."""
    seen, out = set(), []
    for path, vol, code, num in SECTION_RE.findall(index_html):
        if vol in VOLUMES and path not in seen:
            seen.add(path)
            out.append((path, vol, f"{code}{num}"))
    return out


def cache_name(path: str) -> str:
    return path.removeprefix("/publications/list-lights/").replace("/", "__")


def fetch_pages(refresh: bool = False) -> tuple[str, list[tuple[str, str, str, Path]]]:
    """The index and every section, cached. Returns (index html, [(path, volume, code, cache path)])."""
    cache = c.raw_dir(SOURCE)
    index_path = cache / "list-livre-en.php"
    index_html = cc.decode(cc.cached_get(INDEX_URL, index_path, cc.SURVEY / "ccg" / "list-livre-en.php", refresh=refresh))
    sections = section_links(index_html)
    out = []
    for n, (path, vol, code) in enumerate(sections, 1):
        p = cache / cache_name(path)
        legacy = cc.SURVEY / "ccg" / Path(path).name
        if not p.exists() or refresh:
            c.log(f"ccg_list_of_lights: section {n}/{len(sections)} {path}")
        cc.cached_get(HOST + path, p, legacy, refresh=refresh)
        out.append((path, vol, code, p))
    return index_html, out


# ---------------------------------------------------------------------------------------------
# Reading a section
# ---------------------------------------------------------------------------------------------

ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL_RE = re.compile(r"<td\b([^>]*?)(?:/>|>(.*?)</td>)", re.S)
POS_RE = re.compile(r"(\d{2,3})\s+(\d{2})\s+(\d{2}(?:\.\d+)?)")
NUM_RE = re.compile(r"^\d+(?:\.\d+)?$")
FOG_WORDS = [(re.compile(r"diaphone", re.I), "diaphone"), (re.compile(r"\bhorn\b", re.I), "horn"),
             (re.compile(r"\bsiren\b", re.I), "siren"), (re.compile(r"whistle", re.I), "whistle"),
             (re.compile(r"\bbell\b", re.I), "bell"), (re.compile(r"\bgong\b", re.I), "gong"),
             (re.compile(r"\breed\b", re.I), "reed"), (re.compile(r"\bbuoy\b", re.I), None)]
NOT_LIGHTHOUSE = re.compile(r"skelet|tripod|lattice|pole\b|\bpost\b|\bpile|dolphin|\bpipe\b|\bmast\b|stake|pillar|spar\b|"
                            r"daymark|day mark|\bcairn\b|pedestal|stanchion|\bpylon\b|\bcolumn\b|buoy|\bbeacon\b|\bcribwork\b|"
                            r"\bdyke\b|\bwharf\b|\bpier\b|\bbreakwater\b|floating|\bbarge\b|\bplatform\b|\bgantry\b", re.I)
TOWER_WORDS = re.compile(r"\btower\b|\bcylinder\b|\bcylindrical\b|\boctagon|\bhexagon|\bpyramid|\bconical\b|\bcircular\b", re.I)
NAME_TAIL_RE = re.compile(r"(?:\s*(?:,|-)?\s*(?:&|and)\s+(?:fog|siren|horn|bell|whistle|diaphone|radio)\b.*)$", re.I)
RANGE_RE = re.compile(r"\brange\b|\b(front|rear)\b", re.I)


def norm_admiralty(value: str) -> str:
    """"H0443.4" -> "H443.4" (leading zeros dropped, the join key's form)."""
    return re.sub(r"^([A-Z])0+(?=\d)", r"\1", value.strip())


def cells_of(row_html: str) -> list[tuple[str, str]]:
    return [(attrs, body or "") for attrs, body in CELL_RE.findall(row_html)]


def parse_position(cell: str) -> tuple[float, float] | None:
    m = POS_RE.findall(cell)
    if len(m) < 2:
        return None
    lat = cc.dms_to_deg(*m[0], hemisphere="N")
    lon = cc.dms_to_deg(*m[1], hemisphere="W")
    return lat, lon


def number_or_none(text: str) -> float | None:
    t = text.strip()
    return float(t) if NUM_RE.match(t) else None


def characteristic_of(char: str, colour: str, period: str) -> str | None:
    char, colour, period = (re.sub(r"\s+", " ", x).strip() for x in (char, colour, period))
    if not char or char.startswith("."):
        return None
    out = [char]
    if colour and not colour.startswith("."):
        out.append(colour)
    if period and not period.startswith("."):
        out.append(period)
    return " ".join(out)


def fog_signal_of(remarks_html: str) -> str | None:
    for m in re.finditer(r"<b>\s*(?:Audible signal:\s*)?([^<]*)</b>(?:\s*([^<]{0,40}))?", remarks_html):
        text = f"{m.group(1)} {m.group(2) or ''}"
        for rx, word in FOG_WORDS:
            if rx.search(text):
                return word
    return None


def classify(name: str, bold_major: bool, desc: str) -> tuple[str, bool]:
    """(aid class, clearly a lighthouse). The List never calls a structure a lighthouse; it describes
    it ("White square tower with red top, connected to white building"). Clear lighthouses: the name
    says light station or lighthouse; a major light (bold, Newfoundland and Labrador only); a
    description naming a lighthouse, dwelling, keeper or lantern, or a tower attached to a building.
    Other towers are class `tower` (a small modern tower; kept only where a station is), skeleton
    towers, poles, piles, dolphins, masts, posts and anything with a daymark are `beacon`."""
    if re.search(r"light ?house|light ?station|lightstation|fog signal station", name, re.I) and not (
            re.match(r"lighthouse (?:point|beach|island|shoal|rock|road|park|bay|cove)\b", name, re.I)
            and NOT_LIGHTHOUSE.search(desc)):
        return "lighthouse", True
    if re.search(r"\bracon\b|\bbridge\b|\bsector\b", name, re.I):
        return ("beacon" if NOT_LIGHTHOUSE.search(desc) else "other"), False
    if re.search(r"light ?house|keeper|dwelling|lantern", desc, re.I):
        return "lighthouse", True
    if NOT_LIGHTHOUSE.search(desc):
        return "beacon", False
    if bold_major:
        return "lighthouse", True
    if re.search(r"\b(?:connected|attached) to\b|\brising from\b|\bon (?:a )?(?:dwelling|house)\b|\bbuilding with\b|\bwith (?:attached )?building\b", desc, re.I):
        return "lighthouse", True
    if TOWER_WORDS.search(f"{name} {desc}"):
        return "tower", False
    return "other", False


def clean_list_name(raw: str) -> str:
    """"Cape Race Light Station & Fog Signal" -> "Cape Race Light Station"; the 'Light' stays."""
    s = re.sub(r"\s+", " ", raw).strip()
    s = NAME_TAIL_RE.sub("", s).strip(" ,-")
    return s


def kind_of(name: str) -> str:
    if RANGE_RE.search(name):
        return "range_lights"
    if re.search(r"\b(pier ?head|pier|breakwater|jetty|mole|wharf)\b", name, re.I):
        return "pier_light"
    if re.search(r"light ?house|light ?station|lightstation", name, re.I):
        return "lighthouse"
    return "harbor_light"


def role_of(name: str) -> str | None:
    if re.search(r"\bfront\b", name, re.I) and not re.search(r"\brear\b", name, re.I):
        return "front_range"
    if re.search(r"\brear\b", name, re.I) and not re.search(r"\bfront\b", name, re.I):
        return "rear_range"
    return None


def parse_section(html_text: str, vol: str, code: str, path: str) -> tuple[str, list[dict]]:
    """(the section's title, its fixed-aid rows as records; buoys are skipped and counted by the caller)."""
    title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, re.S)
    title = cc.text_of(title_m.group(1)) if title_m else code
    prefix = VOLUMES[vol][1]
    body = html_text[html_text.find("<tbody>"):]
    area = None
    records: list[dict] = []
    for row in ROW_RE.findall(body):
        cells = cells_of(row)
        if len(cells) == 0:
            continue
        if len(cells) < 11:
            # a sub-heading row: <td colspan=2 ...><strong>Minas Basin</strong></td>
            m = re.search(r"<strong>(.*?)</strong>", row, re.S)
            if m:
                area = cc.text_of(m.group(1)) or area
            continue
        c0, c1, _c2, c3, c4, c5, c6, c7, c8, c9, c10 = (b for _a, b in cells[:11])
        if "<em" in c0 or "<em" in c1:
            continue  # a buoy
        num_html = c0
        num = cc.text_of(re.sub(r"<i>.*?</i>", "", num_html, flags=re.S))
        adm_m = re.search(r"<i>\s*([A-Z]?\d+(?:\.\d+)?)\s*</i>", num_html)
        if not num or not re.match(r"^\d", num):
            continue
        if re.search(r"light and \w+ buoy|light buoy|\bbuoy\b", c1, re.I):
            continue
        pos = parse_position(c3)
        if pos is None:
            continue
        bold = "<b>" in c1 and vol == "newfoundland"
        raw_name = cc.text_of(c1)
        name = clean_list_name(raw_name)
        desc_html = c9.split("<center>")[0]
        desc = cc.text_of(desc_html)
        height_m = None
        mh = re.search(r"<center>\s*([\d.]+)\s*</center>", c9)
        if mh and NUM_RE.match(mh.group(1)):
            height_m = float(mh.group(1))
        location_text = cc.text_of(re.sub(r"\d{2,3}\s+\d{2}\s+\d{2}(?:\.\d+)?", "", c3.split("<br")[0])) if "<br" in c3 else ""
        remarks = cc.text_of(c10)
        adm = norm_admiralty(adm_m.group(1)) if adm_m else None
        aid_class, clear = classify(raw_name, bold, desc)
        list_no = f"{prefix}{num}"
        rec = {
            "key": f"{SOURCE}:{list_no}",
            "url": HOST + path,
            "name": name,
            "other_names": [],
            "country": "CA",
            "region": None,
            "county": None,
            "lat": pos[0],
            "lon": pos[1],
            "precision": "exact",
            "kind": kind_of(name),
            "kind_raw": aid_class,
            "role": role_of(name),
            "status": "active",
            "status_raw": "listed in the current List of Lights",
            "structure": {"type": None, "material": None, "built": None, "height_m": height_m, "status": None},
            "light": {"first_lit": None, "deactivated": None,
                      "characteristic": characteristic_of(cc.text_of(c4), cc.text_of(c5), cc.text_of(c6)),
                      "focal_height_m": number_or_none(cc.text_of(c7)), "range_nm": number_or_none(cc.text_of(c8)),
                      "fog_signal": fog_signal_of(c10), "lens": None},
            "setting": None,
            "registers": [],
            "aton": {"uscg_llnr": None, "arlhs": None, "ccg_list_number": list_no, "nga": None, "admiralty": adm},
            "agency": "Canadian Coast Guard",
            "ownership": "federal",
            "events": [],
            "photos": [],
            "links": [{"label": f"Canadian Coast Guard List of Lights, {VOLUMES[vol][2]}: {title}",
                       "url": HOST + path, "kind": "reference"}],
            "relations": {},
            "extra": {
                "ccg_volume": vol,
                "section": title,
                "area": area,
                "list_name": raw_name,
                "location_text": location_text or None,
                "structure_text": desc,
                "major_light": bold,
                "aid_class": aid_class,
                "clear_lighthouse": clear,
                "season": "seasonal" if re.search(r"\bseasonal\b", remarks, re.I) else "year round" if re.search(r"year round", remarks, re.I) else None,
                "join_keys": [f"ccg:{list_no}"] + ([f"adm:{adm}"] if adm else []),
            },
        }
        records.append(rec)
    return title, records


# ---------------------------------------------------------------------------------------------
# Which records to keep
# ---------------------------------------------------------------------------------------------

REFERENCE_SOURCES = ("wikidata", "osm", "parks_canada_hl", "lighthousefriends")
CELL = 0.01  # degrees, for the reference grid


def reference_points(sources_dir: Path | None = None) -> dict[tuple[int, int], list[tuple[float, float, str]]]:
    """Canadian station records in the other extracts that already have a position, on a grid:
    Wikidata items (not out of scope), OpenStreetMap lights that may start a station (not a seamark
    light without a lighthouse tag, not a suspected minor beacon, named), the heritage lighthouses
    and Lighthouse Friends' lights. An extract that is not there is skipped."""
    sources_dir = sources_dir or (c.REPO / "data" / "sources")
    grid: dict[tuple[int, int], list[tuple[float, float, str]]] = {}
    for sid in REFERENCE_SOURCES:
        path = sources_dir / f"{sid}.json"
        if not path.exists():
            continue
        for r in json.loads(path.read_text(encoding="utf-8")).get("records", []):
            if r.get("country") != "CA" or not isinstance(r.get("lat"), (int, float)) or not isinstance(r.get("lon"), (int, float)):
                continue
            ex = r.get("extra") or {}
            if ex.get("out_of_scope") or ex.get("enrich_only") or ex.get("minor_beacon_suspect") or not r.get("name"):
                continue
            grid.setdefault((int(r["lat"] // CELL), int(r["lon"] // CELL)), []).append((r["lat"], r["lon"], sid))
    return grid


def near_reference(grid: dict, lat: float, lon: float, radius_m: float = MATCH_M) -> list[str]:
    """The sources that have a station record within radius_m of the point."""
    import math
    cy, cx = int(lat // CELL), int(lon // CELL)
    span = 1 + int(radius_m / 111_000 / CELL)
    found: set[str] = set()
    for dy in range(-span, span + 1):
        for dx in range(-span * 2, span * 2 + 1):
            for la, lo, sid in grid.get((cy + dy, cx + dx), []):
                d = 111_195 * math.hypot(la - lat, (lo - lon) * math.cos(math.radians(lat)))
                if d <= radius_m:
                    found.add(sid)
    return sorted(found)


def keep_record(rec: dict, grid: dict | None) -> bool:
    """Clear lighthouses always; any other fixed lit aid only where another source has a station."""
    if rec["extra"]["clear_lighthouse"]:
        return True
    if grid is None:
        return True
    near = near_reference(grid, rec["lat"], rec["lon"])
    rec["extra"]["near"] = near
    return bool(near)


def fetch(refresh: bool = False, match: bool = True) -> tuple[list[dict], dict, list[Path]]:
    _index, sections = fetch_pages(refresh)
    lookup = None
    try:
        import regions
        lookup = regions.region_lookup(c.RAW_ROOT)
    except Exception as e:  # noqa: BLE001 - the boundary files are cached; say so if they are not
        c.log(f"ccg_list_of_lights: no region lookup ({e})")
    grid = reference_points() if match else None
    kept, counts = [], {"fixed_aids": 0, "clear_lighthouses": 0, "kept_near_a_station": 0, "dropped": 0, "no_region": 0}
    by_class: dict[str, int] = {}
    for path, vol, code, p in sections:
        _title, recs = parse_section(cc.decode(p.read_bytes()), vol, code, path)
        for rec in recs:
            counts["fixed_aids"] += 1
            by_class[rec["extra"]["aid_class"]] = by_class.get(rec["extra"]["aid_class"], 0) + 1
            if not keep_record(rec, grid):
                counts["dropped"] += 1
                continue
            region = lookup.lookup(rec["lat"], rec["lon"], "CA")[0] if lookup else None
            if region is None:
                counts["no_region"] += 1
            rec["region"] = region
            if rec["extra"]["clear_lighthouse"]:
                counts["clear_lighthouses"] += 1
            else:
                counts["kept_near_a_station"] += 1
            kept.append(rec)
    notes = {"sections": len(sections), **counts, "fixed_aids_by_class": dict(sorted(by_class.items())),
             "match_radius_m": MATCH_M, "matched_against": [s for s in REFERENCE_SOURCES if (c.REPO / "data" / "sources" / f"{s}.json").exists()] if match else [],
             "buoys": "skipped (rows in italics)", "volumes": {v: t for v, (_c, _p, t) in VOLUMES.items()}}
    return kept, notes, [p for _a, _b, _c, p in sections]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--refresh", action="store_true", help="fetch again instead of using the cache")
    ap.add_argument("--no-match", action="store_true", help="keep every fixed aid, not only clear lighthouses and those near a station")
    args = ap.parse_args(argv)
    records, notes, paths = fetch(args.refresh, match=not args.no_match)
    c.write_source_json(
        OUT_PATH, source=SOURCE,
        title="Canadian Coast Guard: List of Lights, Buoys and Fog Signals (lighthouses and lit fixed aids at stations)",
        url=INDEX_URL, license_text=LICENSE, records=records, notes=notes, retrieved=c.retrieved_date(*paths))
    c.log(f"ccg_list_of_lights: {len(records)} records kept of {notes['fixed_aids']} fixed aids "
          f"({notes['clear_lighthouses']} clear lighthouses, {notes['kept_near_a_station']} near a station)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
