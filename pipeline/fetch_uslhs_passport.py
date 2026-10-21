#!/usr/bin/env python3
"""US Lighthouse Society passport-stamp list and accommodations pages -> data/sources/uslhs_passport.json
(DESIGN.md 2.4).

Two pages of the Society's site (uslhs.org; "(c) the Society", so facts only, with a link):

- the free **passport stamp list** (`full_page_mini_list.pdf`, "Last Updated: July 2026"): the places
  that keep a Passport Club stamp, by state. It gives a station name and a state, nothing else, so each
  line is a record with no position that joins a station by name within its state, and sets
  `visit.passport_stamp`. Lines for lenses, anniversary and holiday stamps, museums, memorials, faux
  lights and the "Lost Lights" series (commemorative designs, not places to get a stamp) are not
  stations and are skipped; the Canadian and international sections are not this fetcher's;
- the **accommodations** index and its twelve state pages (`/travel/lighthouse-accommodations/<state>`):
  under headings for vacation rentals, bed and breakfasts, hostels, "keeper for a fee" and volunteer host
  keepers, a block per station with the operator's website. It gives `stay` (type, the operator's site,
  the Society's page as the source). Contact names, telephone numbers and email addresses are not taken.

Passport and accommodation lines for the same place become two records of one name; the merge puts both
on the station. Usage: python3 pipeline/fetch_uslhs_passport.py [--refresh]
"""
from __future__ import annotations

import argparse
import html as htmllib
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "sources" / "uslhs_passport.json"
SOURCE = "uslhs_passport"
SITE = "https://uslhs.org"
PASSPORT_URL = SITE + "/sites/default/files/passport_club/full_page_mini_list.pdf"
PASSPORT_PAGE = SITE + "/travel/passport-club"
ACC_INDEX = SITE + "/travel/accommodations"
ACC_STATE = SITE + "/travel/lighthouse-accommodations/{slug}"
SURVEY_PDF = "survey/us/passport_mini_list.pdf"

STATE_CODES = {
    "ALABAMA": "AL", "ALASKA": "AK", "CALIFORNIA": "CA", "CONNECTICUT": "CT", "DELAWARE": "DE", "FLORIDA": "FL",
    "GEORGIA": "GA", "HAWAII": "HI", "ILLINOIS": "IL", "INDIANA": "IN", "KENTUCKY": "KY", "LOUISIANA": "LA",
    "MAINE": "ME", "MARYLAND": "MD", "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN",
    "MISSISSIPPI": "MS", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW YORK": "NY", "NORTH CAROLINA": "NC",
    "OHIO": "OH", "OREGON": "OR", "PENNSYLVANIA": "PA", "PUERTO RICO": "PR", "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC", "TEXAS": "TX", "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI",
}
ACC_STATES = {"california": "CA", "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
              "minnesota": "MN", "new-york": "NY", "north-carolina": "NC", "oregon": "OR", "rhode-island": "RI",
              "virginia": "VA", "washington": "WA", "wisconsin": "WI"}

# Lines of the stamp list that are not a station.
NOT_STATION_RE = re.compile(r"\b(lens|anniversary|museum|memorial|faux|post|holiday|stamps?|bell|motor ?life ?boat|tender|"
                            r"headquarters|center|hotel|marina|surf & rescue|boathouse|usc?g station|cgs|usc?g \d+)\b|^\s*series\b", re.I)
HEADER_RE = re.compile(r"passport stamps?|last updated|a passport stamp is available|lighthouses, museums|since multiple stamps|"
                       r"and memorials|remember to donate|currently unavailable", re.I)


# ---------------------------------------------------------------------------------------------
# Passport list
# ---------------------------------------------------------------------------------------------

def passport_text(refresh: bool) -> tuple[str, Path]:
    cache = c.raw_dir(SOURCE)
    pdf = cache / "passport_mini_list.pdf"
    old = c.RAW_ROOT / SURVEY_PDF
    if not pdf.exists() and not refresh and old.exists():
        shutil.copyfile(old, pdf)
    if not pdf.exists() or refresh:
        rx.polite_get(PASSPORT_URL, pdf, force=refresh)
    txt = subprocess.run(["pdftotext", str(pdf), "-"], check=True, capture_output=True, timeout=120).stdout.decode("utf-8", "replace")
    return txt, pdf


def parse_passport(text: str) -> list[dict]:
    """[{state, raw}] for the US sections, in order."""
    out, state, skipping = [], None, False
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.upper() in ("INTERNATIONAL", "LOST LIGHTS"):
            break
        if re.search(r"passport stamps\s*$", s, re.I):
            skipping = True
            continue
        if s in STATE_CODES:
            state, skipping = STATE_CODES[s], False
            continue
        if skipping or state is None:
            continue
        if HEADER_RE.search(s):
            continue
        out.append({"state": state, "raw": s.rstrip("*").strip()})
    return out


def clean_stamp_name(raw: str) -> dict:
    """The station name a stamp line names, expanded where the list abbreviates."""
    s = raw.replace("’", "'")
    out = {"name": s, "kind": "lighthouse", "role": None, "alts": []}
    s = re.sub(r"\bBW\b", "Breakwater", s)
    s = re.sub(r"\bLSS\b", "Life-Saving Station", s)
    m = re.match(r"^(.*?)\s+LS\s*\((?:LV|WLV)[ -]?\d+\)$", s)
    if m:
        out.update(name=m.group(1).strip(), kind="lightship")
        return out
    if re.search(r"Life-Saving Station|House of Refuge", s):
        out["kind"] = "life_saving_station"
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", s)
    if m and re.fullmatch(r"replica", m.group(2), re.I):
        s = f"{m.group(1).strip()} Replica"
    elif m and not re.fullmatch(r"(old|new|robot)", m.group(2), re.I):
        out["alts"].append(m.group(2).strip())
        s = m.group(1).strip()
    out["name"] = s
    if re.search(r"\bRange\b", s):
        out["kind"] = "range_lights"
        if re.search(r"\bRear\b", s):
            out["role"] = "rear_range"
        elif re.search(r"\bFront\b", s):
            out["role"] = "front_range"
    return out


def passport_records(entries: list[dict]) -> list[dict]:
    recs, used = [], Counter()
    for e in entries:
        if NOT_STATION_RE.search(e["raw"]):
            continue
        nm = clean_stamp_name(e["raw"])
        base = f"stamp:{e['state'].lower()}:{re.sub(r'[^a-z0-9]+', '-', e['raw'].lower()).strip('-')}"
        used[base] += 1
        ident = base if used[base] == 1 else f"{base}-{used[base]}"
        rec = rx.new_record(SOURCE, ident, nm["name"], url=PASSPORT_PAGE, region=e["state"], kind=nm["kind"])
        rec["other_names"] = nm["alts"]
        rec["role"] = nm["role"]
        rec["kind_raw"] = e["raw"]
        rec["visit"] = {"passport_stamp": True}
        rec["links"] = []
        rec["extra"] = {"list": "passport", "quiet_unmatched": False}
        recs.append(rec)
    return recs


# ---------------------------------------------------------------------------------------------
# Accommodations
# ---------------------------------------------------------------------------------------------

STAY_TYPE_BY_HEADING = [
    (re.compile(r"bed\s*(&|and)\s*breakfast|\binn\b", re.I), "inn", "a bed and breakfast"),
    (re.compile(r"hostel", re.I), "hostel", "a hostel"),
    (re.compile(r"volunteer", re.I), "keeper_program", "a volunteer host keeper program"),
    (re.compile(r"keeper for a fee|keeper.*fee", re.I), "keeper_program", "a stay as a keeper for a fee"),
    (re.compile(r"vacation|rental", re.I), "rental", "a vacation rental"),
]


def stay_class(heading: str) -> tuple[str, str] | None:
    for rx_, typ, words in STAY_TYPE_BY_HEADING:
        if rx_.search(heading):
            return typ, words
    return None


def parse_accommodations(page_html: str, region: str, page_url: str) -> list[dict]:
    """[{heading, name, website, region}] from one state page: <h4> classes, <h6> stations."""
    m = re.search(r'<div class="field field--name-body[^>]*>(.*)</div>\s*</div>\s*</article>', page_html, re.S) or \
        re.search(r"<article.*?</article>", page_html, re.S)
    body = m.group(1) if m else page_html
    out, heading = [], None
    for part in re.split(r"(?=<h[46][ >])", body):
        h = re.match(r"<h([46])[^>]*>(.*?)</h\1>", part, re.S)
        if not h:
            continue
        text = rx.clean_text(h.group(2))
        if h.group(1) == "4":
            heading = text
            continue
        if not text or heading is None:
            continue
        site = None
        for href, label in re.findall(r'<a [^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', part, re.S):
            if re.search(r"website|reserv|book|visit", rx.clean_text(label), re.I):
                site = htmllib.unescape(href)
                break
        out.append({"heading": heading, "name": text, "website": site, "region": region, "page": page_url})
    return out


LIGHT_WORD_RE = re.compile(r"\b(light|lights|lighthouse|lighthouses|light station|station|island|rock|reef|point|head|shoal|ledge)\b", re.I)


def split_names(raw: str) -> list[str]:
    """One heading can name several stations ("Raspberry Island & Sand Island Lighthouses"): split at commas,
    "&" and "and" when every piece still reads as a place."""
    s = re.sub(r"[\u200b\u00a0]+", " ", raw).strip()
    s = re.sub(r"\bPhotos? by\b.*$", "", s, flags=re.I).strip()
    s = re.sub(r"\s+", " ", s).replace("Lighthous e", "Lighthouse")
    parts = [p.strip() for p in re.split(r",\s*(?:and\s+)?|\s+&\s+|\s+and\s+(?=[A-Z])", s) if p.strip()]
    if len(parts) > 1 and all(LIGHT_WORD_RE.search(p) for p in parts) and not re.search(r"\bMuseum$|^Fog Signal", s):
        return parts
    return [s]


def clean_acc_name(raw: str) -> dict:
    raw = re.sub(r"[\u200b\u00a0]+", " ", raw).strip()
    s = re.sub(r"\s*\((?:Also see|see)[^)]*\)\s*", " ", raw, flags=re.I).strip()
    kind = "life_saving_station" if re.search(r"life-?saving", s, re.I) else "lighthouse"
    s = re.sub(r":\s*Former.*$", "", s)
    s = re.sub(r"\b(Guest Quarters|Keeper'?s? (?:House|Quarters|Cottage|Apartment)|Vacation Rentals?|Bed (?:&|and) Breakfast|"
               r"Assistant Keeper'?s?(?: House)?|Light Station Rentals?|Lodging|Hostel)\b", " ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" -:,")
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", s)
    alts = []
    if m:
        alts.append(m.group(2).strip())
        s = m.group(1).strip()
    return {"name": s, "alts": alts, "kind": kind}


def accommodation_records(entries: list[dict], today: str) -> list[dict]:
    recs, used = [], Counter()
    for e in entries:
        cls = stay_class(e["heading"])
        if cls is None:
            continue
        typ, words = cls
        if re.search(r"\bhostel\b", e["name"], re.I):
            typ, words = "hostel", "a hostel"
        for piece in split_names(e["name"]):
            nm = clean_acc_name(piece)
            if not nm["name"]:
                continue
            base = f"stay:{e['region'].lower()}:{re.sub(r'[^a-z0-9]+', '-', piece.lower()).strip('-')[:60]}"
            used[base] += 1
            ident = base if used[base] == 1 else f"{base}-{used[base]}"
            rec = rx.new_record(SOURCE, ident, nm["name"], url=e["page"], region=e["region"], kind=nm["kind"])
            rec["other_names"] = nm["alts"]
            rec["kind_raw"] = e["name"]
            rec["stay"] = {"type": typ, "provider": None, "url": e["website"], "season": None, "checked": today,
                           "note": f"Listed by the US Lighthouse Society as {words}. Confirm availability and rules with the operator."}
            rec["links"] = [{"label": "US Lighthouse Society: lighthouse accommodations", "url": e["page"], "kind": "reference"}]
            rec["extra"] = {"list": "accommodations", "heading": e["heading"]}
            recs.append(rec)
    return recs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch Fresnel's US Lighthouse Society passport and accommodations extract")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    cache = c.raw_dir(SOURCE)
    text, pdf = passport_text(args.refresh)
    stamps = passport_records(parse_passport(text))
    pages = []
    acc_entries = []
    idx = cache / "accommodations.html"
    rx.polite_get(ACC_INDEX, idx, force=args.refresh)
    pages.append(idx)
    for slug, region in ACC_STATES.items():
        p = cache / f"accommodations_{slug}.html"
        url = ACC_STATE.format(slug=slug)
        rx.polite_get(url, p, force=args.refresh)
        pages.append(p)
        acc_entries += parse_accommodations(p.read_text(encoding="utf-8", errors="replace"), region, url)
    stays = accommodation_records(acc_entries, c.retrieved_date(*pages))
    records = stamps + stays
    rx.write_extract(
        OUT_PATH, source=SOURCE,
        title="US Lighthouse Society: passport stamp list and lighthouse accommodations",
        url=SITE + "/travel/",
        license_text="Copyright the United States Lighthouse Society. Facts only (a station's name, whether it keeps a "
                     "passport stamp, the kind of stay and the operator's website) with a link; no text is copied.",
        credit="United States Lighthouse Society, Passport Club list and lighthouse accommodations, used for facts with a link",
        records=records, notes={"passport_lines": len(stamps), "accommodation_blocks": len(stays),
                                "passport_pdf": PASSPORT_URL, "accommodations": ACC_INDEX},
        retrieved=c.retrieved_date(pdf, *pages))
    c.log(f"uslhs_passport: wrote {len(records)} records ({len(stamps)} stamps, {len(stays)} stays); "
          f"stay types {dict(Counter(r['stay']['type'] for r in stays))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
