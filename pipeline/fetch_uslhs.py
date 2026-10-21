#!/usr/bin/env python3
"""US Lighthouse Society Digital Archive ("Lighthouse Research Catalog") places -> data/sources/uslhs.json
(DESIGN.md 2.3).

The archive (archives.uslhs.org) holds ~2,300 places: light stations, lightship stations, lifesaving
stations, minor aids, depots, museums, replicas and faux lighthouses. It is "(c) U.S. Lighthouse
Society, All Rights Reserved", so only **facts** are kept (years, flags, positions, materials), never
the archive's text, and each station links to its place page. Underneath are public-domain federal
records (Light Lists, Record Group 26).

This fetcher does **not crawl**. The research-corpus agent crawls the archive (2 s per request, one
roster per place) into `$RAW/uslhs/` and `research/roster.py build` parses it into `places.json`; this
reads that file (`--places` to name another). Place types read:

- **Light Station** -> lighthouse (range / pier-light / breakwater by name); **Lifesaving Station** and
  **House of refuge** -> life_saving_station; **Lightship Station** -> lightship_station;
  **Replica** -> a lighthouse with status `replica`;
- **Private (Faux) Lighthouse** and **Minor Aid to Navigation**: join an existing station, never start
  one (`enrich_only`); a faux lighthouse carries a `decorative_hint`; a minor aid carries no status;
- Depot, Museum, Fog Signal Station, Non-Government ATON: not stations, skipped.

Readings of a light station's fields: `existing` false -> status `lost` (`demolished` year -> event
`destroyed`); existing and an active aid to navigation (or a private aid) -> `active`; existing and not
-> `inactive` (`discontinued` year); `established` -> `light.first_lit`, `tower_established` ->
`structure.built`; material, shape and foundation -> structure material and type (screwpile, caisson,
crib, skeletal); `current_optic` / `original_optic` "Third Order, Fresnel" -> lens; owner -> agency and a
rough ownership class; `open_to_public` yes -> access public and open grounds (no is kept as a note only: it may mean the tower, the grounds or the interior); `automated` -> an `automated` event. Positions are
degrees and decimal minutes (about 0.1 minute, 185 m) so they are `approximate`. A lightship station
or lifesaving station without a position cannot start a station: the merge joins it to an existing one
by name within its state, else it waits in the extract for a position.

Usage: python3 pipeline/fetch_uslhs.py [--places PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "sources" / "uslhs.json"
SOURCE = "uslhs"
SITE = "https://archives.uslhs.org"

WORD_ORDERS = {"first": "1", "1st": "1", "second": "2", "2nd": "2", "third": "3", "3rd": "3", "fourth": "4", "4th": "4",
               "fifth": "5", "5th": "5", "sixth": "6", "6th": "6", "hyperradiant": "hyperradiant",
               "hyper-radial": "hyperradiant", "hyper radial": "hyperradiant"}
MATERIALS = [(r"cast[- ]iron", "cast_iron"), (r"\bbrick", "brick"), (r"granite|stone|fieldstone|masonry|rubble|marble|limestone|sandstone", "stone"),
             (r"reinforced concrete|concrete", "concrete"), (r"\bwood|timber|frame", "wood"), (r"steel", "steel"),
             (r"aluminum|aluminium", "aluminium"), (r"fiberglass", "fiberglass"), (r"tabby", "tabby"), (r"\biron", "iron")]


def pick_material(text: str | None) -> str | None:
    t = (text or "").lower()
    for pat, val in MATERIALS:
        if re.search(pat, t):
            return val
    return None


def pick_type(shape: str | None, foundation: str | None, name: str) -> str | None:
    f, s = (foundation or "").lower(), (shape or "").lower()
    if "screw" in f:
        return "screwpile"
    if "caisson" in f:
        return "caisson"
    if re.search(r"\bcrib\b", f) or re.search(r"\bcrib\b", name, re.I):
        return "crib"
    if "skelet" in s or "skelet" in f:
        return "skeletal"
    if re.search(r"integral|attached|on (?:keeper|dwelling|house)|dwelling", s):
        return "integral"
    return None


def parse_lens(text: str | None) -> dict | None:
    """"THIRD ORDER, FRESNEL", "Fourth Order" -> {"type": "fresnel", "order": "4"}; anything else None."""
    t = (text or "").lower()
    if "fresnel" not in t and "order" not in t:
        return None
    half = re.search(r"(third|3rd)\s+and\s+(a\s+)?(one[- ])?half", t)
    if half:
        return {"type": "fresnel", "order": "3.5"}
    for w, o in WORD_ORDERS.items():
        if re.search(rf"\b{re.escape(w)}\b(?:\s*(?:and\s+)?(?:order|class|-order))?", t) and (("order" in t) or ("fresnel" in t)):
            return {"type": "fresnel", "order": o}
    m = re.search(r"\b([1-6])\s*(?:st|nd|rd|th)?\s*order\b", t)
    if m:
        return {"type": "fresnel", "order": m.group(1)}
    return None


def ownership_of(owner: str | None) -> str | None:
    t = (owner or "").lower()
    if not t:
        return None
    if re.search(r"coast guard|uscg|national park|nps|fish and wildlife|army|navy|u\.s\. gov|united states|gsa|noaa|federal|bureau of land", t):
        return "federal"
    if re.search(r"private|privately|mr\.|mrs\.|family", t):
        return "private"
    if re.search(r"state of|state park|state parks|department of natural|dnr|\bstate\b|parks and recreation department", t):
        return "state"
    if re.search(r"city of|town of|county|village|municipal|borough|township|port authority|parish", t):
        return "local"
    if re.search(r"association|society|foundation|friends|preservation|historical|museum|trust|conservancy|inc\b|lighthouse committee|club", t):
        return "nonprofit"
    return None


def strip_station_words(name: str) -> str:
    n = re.sub(r"\s*\((?:lightship|light vessel)\s+station\)\s*", " ", name, flags=re.I)
    n = re.sub(r"\s+(?:lightship|light vessel)\s+station\s*$", "", n, flags=re.I)
    n = re.sub(r"\s+life[- ]?saving\s+station\s*$", " Life-Saving Station", n, flags=re.I)
    return re.sub(r"\s+", " ", n).strip()


def read_name(name: str, ptype: str) -> dict:
    n = strip_station_words(name) if ptype in ("Lightship Station", "Lifesaving Station") else name.strip()
    alts = []
    status = None
    m = re.search(r"\s*\(([^()]*)\)\s*$", n)
    if m:
        inner = m.group(1).strip()
        if re.fullmatch(r"replica|faux", inner, re.I):
            status = "replica" if inner.lower() == "replica" else None
        elif re.fullmatch(r"\d+(st|nd|rd|th)?|first|second|third|old|new", inner, re.I):
            pass   # which tower: stays in the name
            return {"name": n, "alts": alts, "status": status, "kind": None, "role": None}
        elif inner:
            alts.append(inner)
        n = n[:m.start()].strip()
    kind, role = None, None
    if re.search(r"\brange\b", n, re.I):
        kind = "range_lights"
        if re.search(r"\bfront\b", n, re.I):
            role = "front_range"
        elif re.search(r"\brear\b", n, re.I):
            role = "rear_range"
    elif re.search(r"\b(breakwater|pier ?head|pier|jetty)\b", n, re.I):
        kind = "pier_light"
    return {"name": n, "alts": alts, "status": status, "kind": kind, "role": role}


def build_record(p: dict) -> dict | None:
    ptype = p.get("type")
    state = p.get("state")
    name = rx.clean_text(p.get("name"))
    if not name or not state:
        return None
    if ptype == "Light Station":
        kind = "lighthouse"
    elif ptype in ("Lifesaving Station", "House of refuge", "House of Refuge"):
        kind = "life_saving_station"
    elif ptype == "Lightship Station":
        kind = "lightship_station"
    elif ptype == "Replica":
        kind = "lighthouse"
    elif ptype in ("Private (Faux) Lighthouse", "Minor Aid to Navigation"):
        kind = "lighthouse"
    else:
        return None
    nm = read_name(name, ptype)
    if nm["kind"] and kind == "lighthouse":
        kind = nm["kind"]
    existing = p.get("existing")
    enrich = ptype in ("Private (Faux) Lighthouse", "Minor Aid to Navigation")
    status = None
    if ptype == "Replica" or nm["status"] == "replica":
        status = "replica"
    elif kind in ("lightship_station",):
        status = None
    elif not enrich:
        if existing is False:
            status = "lost"
        elif existing is True:
            status = "active" if (p.get("active_aton") or p.get("private_aid")) else "inactive"
    lat, lon = p.get("lat"), p.get("lon")
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and abs(lat) < 0.01 and abs(lon) < 0.01:
        lat = lon = None   # "0 0'" placeholders
    shown = f"{nm['name']} (Replica)" if status == "replica" else nm["name"]   # a copy keeps the word: it is its own station
    rec = rx.new_record(SOURCE, str(p.get("nid") or p.get("slug")), shown, url=p.get("url"), region=state,
                        lat=lat, lon=lon, precision="approximate", kind=kind, status=status)
    rec["kind_raw"] = ptype
    rec["role"] = nm["role"]
    rec["other_names"] = nm["alts"]
    if p.get("county"):
        rec["county"] = rx.clean_text(p["county"]).title()
    est, tower, disc, demo = p.get("established"), p.get("tower_established"), p.get("discontinued"), p.get("demolished")
    material = pick_material(p.get("tower_material"))
    stype = pick_type(p.get("tower_shape"), p.get("tower_foundation"), name)
    height = rx_ft(p.get("tower_height_ft"))
    rec["structure"].update({"type": stype, "material": material, "built": tower if isinstance(tower, int) else None,
                             "height_m": height})
    if kind in ("lighthouse", "range_lights", "pier_light") and not enrich:
        lens = parse_lens(p.get("current_optic")) if existing and p.get("active_aton") is not False else None
        if lens:
            lens = {**lens, "status": "in_place", "where": None}
        rec["light"].update({"first_lit": est if isinstance(est, int) else None,
                             "deactivated": disc if isinstance(disc, int) and status in ("inactive", "lost") else None,
                             "focal_height_m": rx_ft(p.get("focal_height_ft")), "lens": lens})
    elif kind == "lightship_station":
        rec["light"].update({"first_lit": est if isinstance(est, int) else None,
                             "deactivated": disc if isinstance(disc, int) else None})
    ev = []
    cite = "US Lighthouse Society Digital Archive"
    if not enrich:
        if isinstance(est, int) and kind != "life_saving_station":
            ev.append({"year": est, "event": "first_lit", "note": f"Station established ({cite})", "from": SOURCE})
        if isinstance(est, int) and kind == "life_saving_station":
            ev.append({"year": est, "event": "built", "note": f"Station established ({cite})", "from": SOURCE})
        if isinstance(tower, int) and tower != est and kind in ("lighthouse", "range_lights", "pier_light"):
            ev.append({"year": tower, "event": "built", "note": f"Present tower ({cite})", "from": SOURCE})
        if isinstance(disc, int):
            ev.append({"year": disc, "event": "deactivated" if kind != "life_saving_station" else "closed",
                       "note": f"Discontinued ({cite})", "from": SOURCE})
        if isinstance(demo, int):
            ev.append({"year": demo, "event": "destroyed", "note": f"Tower gone ({cite})", "from": SOURCE})
        if isinstance(p.get("automated"), int):
            ev.append({"year": p["automated"], "event": "automated", "note": cite, "from": SOURCE})
        if isinstance(p.get("original_lens_year"), int) and parse_lens(p.get("original_optic")):
            o = parse_lens(p["original_optic"])
            ev.append({"year": p["original_lens_year"], "event": "lens_installed",
                       "note": f"Original lens: order {o['order']} Fresnel ({cite})", "from": SOURCE})
    rec["events"] = ev
    owner = rx.clean_text(p.get("owner")) or None
    if owner and not enrich:
        rec["agency"] = owner
        rec["ownership"] = ownership_of(owner)
    op = p.get("open_to_public")
    if op is True and not enrich:
        rec["access"] = {"level": "public", "note": "The US Lighthouse Society's archive lists it as open to the public."}
        rec["visit"] = {"grounds_open": True}
    elif op is False and existing is not False and not enrich and ptype == "Light Station":
        # "Open to public: no" may mean the tower, the grounds or the interior: kept as a note, not as an access level
        rec["access"] = {"level": None, "note": "The US Lighthouse Society's archive lists it as not open to the public."}
    rec["links"] = [{"label": f"US Lighthouse Society Digital Archive: {name}", "url": p.get("url"), "kind": "reference"}] \
        if p.get("url") else []
    extra: dict = {"slug": p.get("slug"), "type": ptype, "town": rx.clean_text(p.get("town")).title() or None,
                   "data_source": p.get("data_source"), "private_aid": p.get("private_aid") or None,
                   "keepers_quarters": p.get("keepers_quarters") or None, "roster_lines": p.get("roster_lines") or None}
    if enrich:
        extra["enrich_only"] = True
        extra["quiet_unmatched"] = True
    if ptype == "Private (Faux) Lighthouse":
        extra["decorative_hint"] = "The US Lighthouse Society's archive lists it as a private (faux) lighthouse"
    if ptype == "Minor Aid to Navigation":
        extra["minor_aid"] = True
    rec["extra"] = {k: v for k, v in extra.items() if v is not None}
    return rec


def rx_ft(feet) -> float | None:
    return c.ft_to_m(feet) if isinstance(feet, (int, float)) and feet > 0 else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build Fresnel's USLHS Digital Archive extract from the corpus agent's places.json")
    ap.add_argument("--places", type=Path, default=c.RAW_ROOT / "uslhs" / "places.json")
    args = ap.parse_args(argv)
    if not args.places.exists():
        c.log(f"uslhs: {args.places} is not there yet (the corpus crawl writes it: research/roster.py build); nothing written")
        return 2
    places = json.loads(args.places.read_text(encoding="utf-8"))
    records, skipped, no_state = [], Counter(), []
    for p in places:
        rec = build_record(p)
        if rec is None:
            skipped[p.get("type") or "no type"] += 1
            if p.get("type") in ("Light Station", "Lightship Station", "Lifesaving Station") and p.get("name") and not p.get("state"):
                no_state.append(f"{p['name']} ({p.get('type')})")   # a station the archive gives no state: it cannot be placed by region
        else:
            records.append(rec)
    seen = set()
    unique = []
    for r in records:
        if r["key"] in seen:
            continue
        seen.add(r["key"])
        unique.append(r)
    rx.write_extract(
        OUT_PATH, source=SOURCE,
        title="US Lighthouse Society Digital Archive (J. Candace Clifford Lighthouse Research Catalog): places",
        url=SITE + "/places",
        license_text="(c) U.S. Lighthouse Society, all rights reserved. Facts only (years, flags, positions, materials) with a "
                     "link to each place's page; no text or images are copied. The underlying records are US federal records.",
        credit="U.S. Lighthouse Society Digital Archive (Lighthouse Research Catalog), used for facts with a link",
        records=unique,
        notes={"places_read": len(places), "skipped_types": dict(skipped), "skipped_no_state": sorted(no_state),
               "by_type": dict(Counter(r["extra"].get("type") for r in unique)),
               "positioned": sum(1 for r in unique if r["lat"] is not None),
               "built_from": "places.json written by research/roster.py build (the corpus crawl)"},
        retrieved=c.retrieved_date(args.places))
    c.log(f"uslhs: wrote {len(unique)} records from {len(places)} places; skipped {dict(skipped)}; "
          f"positioned {sum(1 for r in unique if r['lat'] is not None)}; status {dict(Counter(r['status'] for r in unique))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
