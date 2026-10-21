#!/usr/bin/env python3
"""Canada's designated heritage lighthouses, from the Directory of Federal Heritage Designations
and Parks Canada's heritage-lighthouse page; writes data/sources/parks_canada_hl.json
(DESIGN.md 2.3, 3.8).

Two requests, both cached under RAW_ROOT/parks_canada_hl/ (the survey's copies under
RAW_ROOT/survey/canada/ are used when they are there):

- the Directory's CSV on open.canada.ca ("Dataset of federal heritage designations as of
  March 31, 2026", Open Government Licence - Canada). The rows whose `Heritage Lighthouse Number`
  is filled are the lighthouses the Heritage Lighthouse Protection Act designated: 115, each with
  its designation date, custodian, local area, province and the dates of construction. open.canada.ca
  asks for a 20 s crawl delay (its robots.txt), which `_ca_common` honours.
- Parks Canada's page https://www.pc.gc.ca/en/lhn-nhs/pp-hl, which lists 114 of them with a WKT
  point each (5 decimals) in the markup of its map table. That is the position (the Directory has
  none) and the link to the designation's own page, whose statement of significance is the
  Directory's text.

Licence: the Directory is under the Open Government Licence - Canada (attribution to Parks Canada
required); Parks Canada's page states none, and we take facts from it only (position, year, height,
material), never its sentences. A record is a heritage lighthouse's designation: name, position,
designation date (a `heritage_designated` event), register entry and link to the statement of
significance. `extra.standing` marks it as evidence that the structure stands today (the Act
protects standing lighthouses only), which the merge reads.

Usage: python3 pipeline/fetch_parks_canada_hl.py [--refresh]
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ca_common as cc  # noqa: E402
import _common as c  # noqa: E402
import regions  # noqa: E402
from fetch_wikidata import name_kind, name_role  # noqa: E402

SOURCE = "parks_canada_hl"
OUT_PATH = c.REPO / "data" / "sources" / f"{SOURCE}.json"
CSV_URL = ("https://open.canada.ca/data/dataset/49d5ba7d-d860-40d9-9183-892979e4acbe/resource/"
           "682d1e12-26dd-4d30-bb40-f04658502bcd/download/dataset-of-federal-heritage-designations-as-of-march-31-2026.csv")
PAGE_URL = "https://www.pc.gc.ca/en/lhn-nhs/pp-hl"
DETAIL_URL = "https://www.pc.gc.ca/apps/dfhd/page_hl_eng.aspx?id={id}"
DATASET_URL = "https://open.canada.ca/data/dataset/49d5ba7d-d860-40d9-9183-892979e4acbe"
CSV_DELAY_S = 20.0  # open.canada.ca robots.txt: Crawl-delay 20
LICENSE = ("Directory of Federal Heritage Designations: Open Government Licence - Canada (Parks Canada). "
           "Parks Canada's heritage-lighthouse page: facts only (position, year, height, material), credit and link.")

PROVINCE_CODES = {name: code for code, name in regions.CA_PROVINCES.items()}
OWNERSHIP_BY_CUSTODIAN = [
    (re.compile(r"fisheries and oceans|parks canada|coast guard|environment and climate|transport canada|public works", re.I), "federal"),
    (re.compile(r"province|provincial|government of (ontario|nova scotia|newfoundland|new brunswick|quebec|manitoba|british columbia|prince edward)", re.I), "provincial"),
    (re.compile(r"\b(town|city|village|municipality|county|municipal|township|regional district)\b", re.I), "local"),
]
MATERIALS = [(re.compile(r"\bcast[- ]iron\b", re.I), "cast_iron", "cast_iron"),
             (re.compile(r"\bconcrete\b", re.I), "concrete", "concrete"),
             (re.compile(r"\b(wooden|wood|timber)\b", re.I), "wood", "wood_frame"),
             (re.compile(r"\bbrick\b", re.I), "brick", "conical_masonry"),
             (re.compile(r"\b(stone|granite|sandstone|limestone|masonry)\b", re.I), "stone", "conical_masonry"),
             (re.compile(r"\bsteel\b", re.I), "steel", None)]
BUILT_RE = re.compile(r"\b(?:built|constructed|erected|completed|established)\s+in\s+(1[6-9]\d\d|20[0-2]\d)\b", re.I)
_M = r"(\d+(?:\.\d+)?)[\s-]*(?:metres?|meters?)"
HEIGHT_RES = [re.compile(_M + r"\s*(?:\([^)]*\))?\s*(?:tall|high)\b", re.I),
              re.compile(r"\b(?:measures?|measuring|standing|stands|height of|rises)\s+(?:about\s+)?" + _M, re.I),
              re.compile(r"(?<!above )(?<!from )" + _M + r"\s*(?:\([^)]*\))?(?!\s*(?:above|from|over|away|up\b))[^.;]{0,50}?\b(?:tower|lighthouse|lantern)\b", re.I)]


def read_directory(text: str) -> list[dict]:
    """The Directory's rows. The file starts with a title line fused to the header (`Directory of
    Federal Heritage Designations Identifier,Designation name,...`): parse from `Identifier,`."""
    i = text.find("Identifier,Designation name")
    if i < 0:
        raise c.FetchError("the Directory CSV has no 'Identifier,Designation name' header")
    return list(csv.DictReader(io.StringIO(text[i:])))


def heritage_lighthouse_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if (r.get("Heritage Lighthouse Number") or "").strip()]


def parse_page(html_text: str) -> dict[str, dict]:
    """Parks Canada's table: identifier -> {name, place, lat, lon, year, description}."""
    out: dict[str, dict] = {}
    for geom, body in re.findall(r'<tr data-geometry="([^"]*)" data-type="wkt">(.*?)</tr>', html_text, flags=re.S):
        m_id = re.search(r"page_hl_eng\.aspx\?id=(\d+)", body)
        m_pt = re.match(r"\s*POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)", geom)
        if not m_id:
            continue
        cells = re.findall(r"<td[^>]*>(.*?)</td>", body, flags=re.S)
        place = cc.text_of(cells[0].split("</span>", 1)[1]) if cells and "</span>" in cells[0] else ""
        year = re.search(r"(\d{4})", cc.text_of(cells[2])) if len(cells) > 2 else None
        out[m_id.group(1)] = {
            "name": cc.text_of(cells[0].split("</span>", 1)[0]) if cells else None,
            "place": place,
            "lon": float(m_pt.group(1)) if m_pt else None,
            "lat": float(m_pt.group(2)) if m_pt else None,
            "year": int(year.group(1)) if year else None,
            "description": cc.text_of(cells[3]) if len(cells) > 3 else "",
        }
    return out


def facts_from_description(text: str) -> dict:
    """Year built, height in metres, material and structure type, as Parks Canada's one-paragraph
    description states them. Facts only: nothing of the sentence is kept. The material is the
    first one named (the tower's, before the dwelling's)."""
    built = BUILT_RE.search(text)
    height = next((m for m in (rx.search(text) for rx in HEIGHT_RES) if m), None)
    best = None
    for rx, mat, typ in MATERIALS:
        m = rx.search(text)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), mat, typ)
    material, stype = (best[1], best[2]) if best else (None, None)
    if re.search(r"\bskeleton|skeletal\b", text, re.I):
        stype = "skeletal"
    return {"built": int(built.group(1)) if built else None,
            "height_m": float(height.group(1)) if height else None, "material": material, "type": stype}


def year_of(value: str | None) -> int | None:
    m = re.match(r"\s*(\d{4})", value or "")
    return int(m.group(1)) if m else None


def ownership_of(custodian: str) -> str | None:
    for rx, value in OWNERSHIP_BY_CUSTODIAN:
        if rx.search(custodian or ""):
            return value
    return None


def build_record(row: dict, page: dict | None) -> dict:
    ident = row["Identifier"].strip()
    name = re.sub(r"\s+", " ", row["Designation name"]).strip()
    others = [n.strip() for n in (row.get("Other names") or "").split("|") if n.strip()]
    region = PROVINCE_CODES.get(row.get("Province or territory", "").strip())
    desc_facts = facts_from_description(page["description"]) if page else {}
    built = desc_facts.get("built") or year_of(row.get("Construction end date")) or year_of(row.get("Construction start date"))
    kind = name_kind(name) or "lighthouse"
    designated = (row.get("Designation date") or "").strip()
    d_year = year_of(designated)
    custodian = (row.get("Custodian") or "").strip()
    url = DETAIL_URL.format(id=ident)
    events = []
    if d_year:
        events.append({"year": d_year, "event": "heritage_designated",
                       "note": f"Heritage lighthouse of Canada (Heritage Lighthouse Protection Act), designated {designated}",
                       "from": SOURCE})
    return {
        "key": f"{SOURCE}:{ident}",
        "url": url,
        "name": name,
        "other_names": [n for n in others if n != name],
        "country": "CA",
        "region": region,
        "county": None,
        "lat": page["lat"] if page else None,
        "lon": page["lon"] if page else None,
        "precision": "exact",
        "kind": kind,
        "kind_raw": "heritage lighthouse of Canada",
        "role": name_role(name),
        "status": None,
        "status_raw": None,
        "structure": {"type": desc_facts.get("type"), "material": desc_facts.get("material"), "built": built,
                      "height_m": desc_facts.get("height_m"), "status": None},
        "light": {"first_lit": None, "deactivated": None, "characteristic": None, "focal_height_m": None,
                  "range_nm": None, "fog_signal": None, "lens": None},
        "setting": None,
        "registers": [{"register": "Heritage Lighthouse (Canada)", "number": ident, "url": url}],
        "aton": {"uscg_llnr": None, "arlhs": None, "ccg_list_number": None, "nga": None},
        "agency": custodian or None,
        "ownership": ownership_of(custodian),
        "events": events,
        "photos": [],
        "links": [{"label": "Directory of Federal Heritage Designations: heritage lighthouse and statement of significance",
                   "url": url, "kind": "register"}],
        "relations": {},
        "extra": {
            "standing": True,
            "heritage_lighthouse_number": (row.get("Heritage Lighthouse Number") or "").strip(),
            "designation_date": designated or None,
            "local_area": (row.get("Local area") or "").strip() or None,
            "street_address": (row.get("Street address") or "").strip() or None,
            "construction": [x for x in ((row.get("Construction start date") or "").strip(),
                                         (row.get("Construction end date") or "").strip()) if x],
            "fhro_number": (row.get("FHRO Number") or "").strip() or None,
            "join_keys": [f"hl:{ident}"],
            "has_position": bool(page and page["lat"] is not None),
        },
    }


def fetch(refresh: bool = False) -> tuple[list[dict], dict, list[Path]]:
    cache = c.raw_dir(SOURCE)
    csv_path = cache / "dataset-of-federal-heritage-designations-as-of-march-31-2026.csv"
    page_path = cache / "pp-hl.html"
    csv_body = cc.cached_get(CSV_URL, csv_path, cc.SURVEY / "opencanada" / "dfhd_2026-03-31.csv",
                             interval=CSV_DELAY_S, refresh=refresh, timeout=300)
    page_body = cc.cached_get(PAGE_URL, page_path, cc.SURVEY / "pc_hl.html", refresh=refresh)
    rows = heritage_lighthouse_rows(read_directory(cc.decode(csv_body, "utf-8-sig", "cp1252")))
    pages = parse_page(cc.decode(page_body, "utf-8"))
    records, unplaced = [], []
    for row in rows:
        page = pages.get(row["Identifier"].strip())
        rec = build_record(row, page)
        if rec["lat"] is None:
            unplaced.append({"identifier": row["Identifier"], "name": rec["name"]})
        records.append(rec)
    csv_ids = {r["Identifier"].strip() for r in rows}
    notes = {"in_directory": len(rows), "on_parks_canada_page": len(pages), "with_position": len(records) - len(unplaced),
             "without_position": unplaced, "on_page_not_in_directory": sorted(set(pages) - csv_ids),
             "directory": DATASET_URL, "page": PAGE_URL}
    return records, notes, [csv_path, page_path]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--refresh", action="store_true", help="fetch again instead of using the cache")
    args = ap.parse_args(argv)
    records, notes, paths = fetch(args.refresh)
    c.write_source_json(
        OUT_PATH, source=SOURCE,
        title="Heritage lighthouses of Canada: Directory of Federal Heritage Designations and Parks Canada",
        url=PAGE_URL, license_text=LICENSE, records=records, notes=notes, retrieved=c.retrieved_date(*paths))
    c.log(f"parks_canada_hl: {len(records)} records, {notes['with_position']} with a position")
    return 0


if __name__ == "__main__":
    sys.exit(main())
