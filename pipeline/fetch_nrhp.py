#!/usr/bin/env python3
"""National Register of Historic Places -> data/sources/nrhp.json (DESIGN.md 2.4). Public domain
(a federal work of the National Park Service).

Two NPS files, joined by the NRHP reference number:

- the **workbook** `national-register-listed_<date>.xlsx` (nps.gov data downloads; 100,866 rows, no
  coordinates): reference number, property name and other names, state, county, city, category,
  listed date, National Historic Landmark designation date, and the National Archives link to the
  nomination form;
- the **NPS point service** `mapservices.nps.gov/.../nrhp_locations/MapServer/0`: one point per
  property (`NRIS_Refnum`), and the multiple-property listing it belongs to (`MultiName`).

Which properties are Fresnel's: (1) every reference number Wikidata carries on a station
(`data/sources/wikidata.json`, P649: the hub the merge joins on first, so run fetch_wikidata.py
first); (2) every property in a lighthouse or life-saving multiple-property listing ("Light
Stations of Maine MPS", "Lighthouses of Massachusetts TR", "Lifesaving Stations of Maine MPS"...);
(3) a property whose name or other names say lighthouse, light station, lightship, range light, life-
saving station, lifeboat station, house of refuge or Coast Guard station, minus the electric-light
companies, churches and carousels that share the words (DENY_RE and DENY_REFS).

What a record carries: the NRHP reference number, listed date and National Historic Landmark date
(`registers[]` with `listed`, `nhl`, `nomination` beside `number` and `url`), an `nrhp_listed` event,
the register's name for the property (the old form, "Portland Headlight", is kept as a name to match
on), and the point. A district (a whole light station) is station-level; a building or structure is
one part. A boundary increase or an additional documentation never starts a station (it joins its
station by number or place).
A point outside the bounding box of the state the listing is filed under (the service puts Great Beds, NJ,
in New York) is dropped, with `extra.position_dropped`; the listing still joins by its number.

Usage: python3 pipeline/fetch_nrhp.py [--refresh]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote, urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402
import regions  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "sources" / "nrhp.json"
SOURCE = "nrhp"
DOWNLOADS_PAGE = "https://www.nps.gov/subjects/nationalregister/data-downloads.htm"
WORKBOOK_URL = "https://www.nps.gov/subjects/nationalregister/upload/national-register-listed_20260522.xlsx"
POINTS_URL = "https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/0/query"
POLYGONS_URL = "https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/1/query"
SURVEY_WORKBOOK = "survey/us/nrhp_listed.xlsx"
NPGALLERY = "https://npgallery.nps.gov/AssetDetail/NRIS/"

STATE_CODES = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR", "CALIFORNIA": "CA", "COLORADO": "CO",
    "CONNECTICUT": "CT", "DELAWARE": "DE", "DISTRICT OF COLUMBIA": "DC", "FLORIDA": "FL", "GEORGIA": "GA",
    "HAWAII": "HI", "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD", "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO", "MONTANA": "MT",
    "NEBRASKA": "NE", "NEVADA": "NV", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM",
    "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
    "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY", "PUERTO RICO": "PR", "VIRGIN ISLANDS": "VI",
    "GUAM": "GU", "NORTHERN MARIANA ISLANDS": "MP", "AMERICAN SAMOA": "AS",
}

LIGHT_RE = re.compile(
    r"light ?houses?\b|light ?stations?\b|lightstation|lightship|light vessel|range lights?\b|"
    r"\blight$|\bheadlight\b|\blight house\b|\bpierhead light|\bbreakwater light", re.I)
LSS_RE = re.compile(
    r"life[- ]?saving|lifesaving|lifeboat station|life boat station|house of refuge|"
    r"coast guard (?:station|boathouse|lifeboat)|u\.?s\.? coast guard (?:station|boathouse)|boathouse.*coast guard", re.I)
# Words that share the spelling: power companies, churches, carousels, archeological sites...
DENY_RE = re.compile(
    r"\b(power|electric|gas|gasholder|church|ministries|armory|plant|company|railway|water|carousel|temple|school|"
    r"hall|archeological|archaeological|shell ring|tender|motor lifeboat|hotel|lodge|missionary|hospital|"
    r"theater|theatre|cemetery|substation|ice|dairy|laundry|inn|train|car|tank)\b", re.I)
# By reference number: kept although DENY_RE trips on a word of the name, or dropped although the name passes.
KEEP_REFS: set[str] = {"89001466"}   # "Baileys Harbor Range Light"
DENY_REFS: set[str] = {
    "73001954",   # Fort Taber District (a fort that mentions the lighthouses of Massachusetts)
    "66000048",   # Salem Maritime National Historic Site
    "82002815",   # Havre de Grace Historic District
    "85001948",   # Watch Hill Historic District
    "90001465",   # Ocracoke Historic District
    "75001148",   # Navesink Historic District
    "93000339",   # Lake Park (Milwaukee)
    "16000190",   # Fort Sumter National Monument
    "83004523",   # Japanese Lighthouse, Puluwat (Federated States of Micronesia)
    "91001823",   # LIGHT VESSEL No. 57 (Shipwreck): a wreck site, not a station
    "81000694",   # Superintendent of Lighthouses' Dwelling (San Juan): the dwelling of the district, not a station
}
MPS_WHERE = ("UPPER(MultiName) LIKE '%LIGHTHOUSE%' OR UPPER(MultiName) LIKE '%LIGHT STATION%' OR "
             "UPPER(MultiName) LIKE '%LIFESAV%' OR UPPER(MultiName) LIKE '%LIFE-SAV%' OR UPPER(MultiName) LIKE '%LIFE SAV%' OR "
             "UPPER(MultiName) LIKE '%HOUSES OF REFUGE%'")
POINT_FIELDS = "NRIS_Refnum,RESNAME,ResType,City,County,State,STATUS,CertDate,NARA_URL,MultiName,Is_NHL,SRC_ACCU"
BATCH = 40


# ---------------------------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------------------------

def get_workbook(refresh: bool) -> Path:
    """The workbook in this fetcher's cache; the survey's copy (2026-05-22 snapshot) is reused."""
    dest = c.raw_dir(SOURCE) / "national-register-listed.xlsx"
    old = c.RAW_ROOT / SURVEY_WORKBOOK
    if not dest.exists() and not refresh and old.exists():
        shutil.copyfile(old, dest)
    if not dest.exists() or refresh:
        rx.polite_get(WORKBOOK_URL, dest, force=refresh, timeout=300)
    return dest


def read_workbook(path: Path) -> dict[str, dict]:
    """{reference number: row as a dict keyed by the header} for every listed property."""
    rows = rx.read_xlsx_rows(path)
    header = [h.strip() for h in next(rows)]
    out = {}
    for r in rows:
        r = r + [""] * (len(header) - len(r))
        d = dict(zip(header, r))
        ref = d.get("Ref#", "").strip()
        if ref:
            out[ref] = d
    return out


def wikidata_refs() -> set[str]:
    p = REPO / "data" / "sources" / "wikidata.json"
    if not p.exists():
        return set()
    out = set()
    for rec in json.loads(p.read_text(encoding="utf-8")).get("records", []):
        for g in rec.get("registers") or []:
            if g.get("register") == "NRHP" and g.get("number"):
                out.add(str(g["number"]))
    return out


def point_query(where: str, name: str, refresh: bool, layer_url: str = POINTS_URL) -> list[dict]:
    """Features (attributes + geometry) of one query on the point (or polygon) layer, cached by the query's text."""
    fields = POINT_FIELDS if layer_url == POINTS_URL else "NRIS_Refnum,RESNAME"
    params = {"where": where, "outFields": fields, "outSR": "4326", "f": "json", "returnGeometry": "true"}
    url = layer_url + "?" + urlencode(params, quote_via=quote)
    path = c.raw_dir(SOURCE) / f"points_{name}_{c.cache_key(url)}.json"
    rx.polite_get(url, path, force=refresh)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error"):
        raise c.FetchError(f"NPS point service: {data['error']}")
    if data.get("exceededTransferLimit"):
        c.log("  nrhp: a point query hit the transfer limit; narrow it")
    return data.get("features") or []


def fetch_points(refs: list[str], refresh: bool) -> tuple[dict[str, dict], dict[str, str]]:
    """({ref: point feature}, {ref: multiple-property listing}) for the MPS properties and the given refs."""
    points: dict[str, dict] = {}
    mps: dict[str, str] = {}
    for f in point_query(MPS_WHERE, "mps", refresh):
        a = f["attributes"]
        points[a["NRIS_Refnum"]] = f
        mps[a["NRIS_Refnum"]] = a.get("MultiName") or ""
    todo = sorted(r for r in refs if r not in points)
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        where = "NRIS_Refnum IN (" + ",".join(f"'{r}'" for r in batch) + ")"
        for f in point_query(where, f"refs{i // BATCH:03d}", refresh):
            a = f["attributes"]
            points.setdefault(a["NRIS_Refnum"], f)
            if a.get("MultiName"):
                mps.setdefault(a["NRIS_Refnum"], a["MultiName"])
    return points, mps


def ring_centre(geometry: dict) -> tuple[float, float] | None:
    """The centre of the bounding box of a polygon's rings: (lat, lon)."""
    xs, ys = [], []
    for ring in (geometry or {}).get("rings") or []:
        for x, y in ring:
            xs.append(x)
            ys.append(y)
    if not xs:
        return None
    return round((min(ys) + max(ys)) / 2, 6), round((min(xs) + max(xs)) / 2, 6)


def fetch_polygon_centres(refs: list[str], refresh: bool) -> dict[str, tuple[float, float]]:
    """For properties the point layer has no point for (many districts): the centre of the boundary polygon."""
    out: dict[str, tuple[float, float]] = {}
    todo = sorted(refs)
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        where = "NRIS_Refnum IN (" + ",".join(f"'{r}'" for r in batch) + ")"
        for f in point_query(where, f"poly{i // BATCH:03d}", refresh, POLYGONS_URL):
            centre = ring_centre(f.get("geometry") or {})
            if centre:
                out.setdefault(f["attributes"]["NRIS_Refnum"], centre)
    return out


# ---------------------------------------------------------------------------------------------
# Selection and records
# ---------------------------------------------------------------------------------------------

def looks_in_scope(name: str, others: str) -> bool:
    names = [name] + [n.strip() for n in re.split(r"[;|]", others or "") if n.strip()]
    if not any(LIGHT_RE.search(n) or LSS_RE.search(n) for n in names):
        return False
    return not DENY_RE.search(name)


def kind_of(name: str, others: str) -> str:
    text = f"{name}; {others}"
    if LSS_RE.search(name) or (LSS_RE.search(text) and not LIGHT_RE.search(name)):
        return "life_saving_station"
    if re.search(r"lightship|light vessel", name, re.I):
        return "lightship"
    if re.search(r"\brange\b", name, re.I):
        return "range_lights"
    return "lighthouse"


def other_names_of(raw: str) -> list[str]:
    out = []
    for part in re.split(r"[;]", rx.clean_text(raw)):
        part = re.sub(r"^(see also|see|formerly|also known as|aka)\s*:?\s*", "", part.strip(), flags=re.I).strip()
        if part and len(part) <= 80 and not re.fullmatch(r"[A-Z0-9 .\-/]{2,12}", part) and part.lower() not in ("armory",):
            out.append(part)
    return out


def build_record(ref: str, row: dict, feature: dict | None, mps: str | None,
                 centre: tuple[float, float] | None = None) -> dict | None:
    name = rx.clean_text(row.get("Property Name"))
    if not name:
        return None
    state = (row.get("State") or "").strip().upper()
    region = STATE_CODES.get(state)
    if region is None:
        return None
    others = row.get("Other Names") or ""
    kind = kind_of(name, others)
    cat = (row.get("Category of Property") or "").strip().upper()
    geom = (feature or {}).get("geometry") or {}
    lat, lon = geom.get("y"), geom.get("x")
    from_polygon = False
    if lat is None and centre:
        lat, lon, from_polygon = centre[0], centre[1], True
    dropped = None
    if lat is not None and lon is not None:
        flag = regions.flag_coordinate(region, lat, lon)
        if flag:   # the service's point is outside the state it is filed under (Great Beds, NJ, at 44.09 N): joins by number or name only
            dropped = f"{lat}, {lon}: outside {region}'s bounding box ({flag})"
            lat = lon = None
            from_polygon = False
    listed = rx.excel_date(row.get("Listed Date"))
    nhl = rx.excel_date(row.get("NHL Designated Date"))
    nara = (row.get("External Link") or "").strip() or None
    boundary = bool(re.search(r"boundary (increase|decrease)|additional documentation", name, re.I))
    rec = rx.new_record(SOURCE, ref, name, url=NPGALLERY + ref if re.fullmatch(r"\d{8}", ref) else None, region=region,
                        lat=lat, lon=lon, precision="approximate", kind=kind)
    rec["county"] = (row.get("County") or "").strip() or None
    rec["other_names"] = [n for n in other_names_of(others) if n != name]
    reg = {"register": "NRHP", "number": ref, "url": NPGALLERY + ref if re.fullmatch(r"\d{8}", ref) else nara,
           "listed": listed, "nhl": nhl, "nomination": nara}
    rec["registers"] = [reg]
    if listed:
        rec["events"] = [{"year": int(listed[:4]), "event": "nrhp_listed",
                          "note": "National Register of Historic Places" + (" and National Historic Landmark" if nhl else ""),
                          "from": SOURCE}]
        if nhl:
            rec["events"].append({"year": int(nhl[:4]), "event": "heritage_designated",
                                  "note": "National Historic Landmark", "from": SOURCE})
    if nara:
        rec["links"] = [{"label": "NRHP nomination (National Archives)", "url": nara, "kind": "register"}]
    extra: dict = {"nrhp_category": cat or None, "city": (row.get("City") or "").strip() or None, "mps": mps or None}
    if cat == "DISTRICT" or re.search(r"light station|lightstation|life[- ]saving station|lighthouses? complex", name, re.I):
        extra["station_level"] = True
    if boundary:
        extra["enrich_only"] = True
        extra["boundary_increase"] = True
    elif not (LIGHT_RE.search(name) or LSS_RE.search(name)):
        extra["weak_name"] = True
        extra["enrich_only"] = True   # a listing named for something else: it may join a station, never start one
    if lat is None:
        extra["no_point"] = True
    if dropped:
        extra["position_dropped"] = dropped
    if from_polygon:
        extra["position_from"] = "the centre of the register's boundary polygon"
    rec["extra"] = {k: v for k, v in extra.items() if v is not None}
    return rec


def select(workbook: dict[str, dict], wd_refs: set[str], mps_refs: set[str]) -> dict[str, str]:
    """{ref: why} for every property that is Fresnel's."""
    chosen: dict[str, str] = {}
    for ref, row in workbook.items():
        if ref in DENY_REFS:
            continue
        name, others = row.get("Property Name", ""), row.get("Other Names", "")
        if ref in wd_refs:
            chosen[ref] = "wikidata"
        elif ref in mps_refs:
            chosen[ref] = "mps"
        elif ref in KEEP_REFS or looks_in_scope(name, others):
            chosen[ref] = "name"
    return chosen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch Fresnel's NRHP extract")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    wb_path = get_workbook(args.refresh)
    workbook = read_workbook(wb_path)
    c.log(f"nrhp: {len(workbook)} listed properties in the workbook")
    wd_refs = wikidata_refs()
    # Properties of the lighthouse and life-saving listings, then everything else chosen.
    mps_features = point_query(MPS_WHERE, "mps", args.refresh)
    mps_refs = {f["attributes"]["NRIS_Refnum"] for f in mps_features}
    chosen = select(workbook, wd_refs, mps_refs)
    points, mps = fetch_points(sorted(chosen), args.refresh)
    centres = fetch_polygon_centres([r for r in chosen if r not in points], args.refresh)
    records, skipped = [], Counter()
    for ref in sorted(chosen):
        rec = build_record(ref, workbook[ref], points.get(ref), mps.get(ref), centres.get(ref))
        if rec is None:
            skipped["no usable name or state"] += 1
        else:
            records.append(rec)
    rx.write_extract(
        OUT_PATH, source=SOURCE,
        title="National Register of Historic Places: lighthouses, light stations, lightships and life-saving stations",
        url=DOWNLOADS_PAGE,
        license_text="US federal public domain (National Park Service). Reference numbers, dates and the nomination "
                     "links of the National Register of Historic Places; positions from the NPS point service.",
        credit="National Register of Historic Places, National Park Service (public domain)",
        records=records,
        notes={"selected": len(chosen), "by_reason": dict(Counter(chosen.values())), "skipped": dict(skipped),
               "workbook_rows": len(workbook), "workbook": WORKBOOK_URL, "points": POINTS_URL},
        retrieved=c.retrieved_date(wb_path))
    c.log(f"nrhp: wrote {len(records)} records ({dict(Counter(chosen.values()))}); "
          f"kind {dict(Counter(r['kind'] for r in records))}; no point {sum(1 for r in records if r['lat'] is None)}; "
          f"NHL {sum(1 for r in records if r['registers'][0]['nhl'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
