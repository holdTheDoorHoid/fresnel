#!/usr/bin/env python3
"""Lightship stations -> data/sources/lightship_stations.json (DESIGN.md 2.5, 3.5, 3.8).

**The list** is the US Lighthouse Society's 139 "Lightship Station" places (`uslhs_vessels.py` reads their pages from
the corpus crawl): every one is a record here, with its state, its years, its alternate name and the vessels that served
it. Two of the 139 are depots (Curtis Bay, Staten Island), one was never built (Ohio Ledge), one is a bell boat that was
not a lightship (Humboldt Bay); they are kept and say so, because the Society lists them, and they have no mooring to
place.

**A position** only from a source that gives one (DESIGN section 1: never place a station by a guess):

- *stated*: a latitude and longitude printed in a Light List (`data/lightships/ll_entries.jsonl`: each light-vessel entry
  of the Light Lists of 1893 and 1900 and of the Great Lakes list of 1924-28, read from the page images and OCR, with its
  page, entry number and location text). An entry is tied to a station by the vessel's number and the year (the Society's
  assignment table) and by the name; one that does not agree on both is not used.
- *computed*: an entry's bearing-and-distance text, "about 4 miles SE. by E. 1/4 E. from Monomoy Point Light-House",
  worked from that light's own station position (the light's latitude and longitude in the same list, or in this
  database) with `geo.py`: the compass bearing (magnetic, as the lists say) turned true by the IGRF declination of the
  place and year, then a great-circle sum. `geo.py`'s test works the Pollock Rip example and lands 80 m from the printed
  position. A computed position is `approximate`, `from: "computed"`, and says its source text.

A station with neither is written without a position: it is on the list of stations that cannot be placed yet
(`unplaced.json` on the site), with the reason.

**The survivors**: the sixteen vessels the Society says survive are on the map already (`kind: lightship`, at their
berths, from Wikidata, the National Register and Lighthouse Friends); `build_vessels.py` links them. None is missing from
the map: the one with no berth the sources give (LV-75, "possibly scrapped 2013") cannot be placed.

Usage: python3 pipeline/fetch_lightship_stations.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402
import geo  # noqa: E402
import uslhs_vessels as uv  # noqa: E402

SOURCE = "lightship_stations"
OUT_PATH = c.REPO / "data" / "sources" / f"{SOURCE}.json"
LIGHTSHIPS = c.REPO / "data" / "lightships"
ENTRIES = LIGHTSHIPS / "ll_entries.jsonl"
COMPUTED = LIGHTSHIPS / "computed.json"
LICENSE = ("US Lighthouse Society Digital Archive (c) U.S. Lighthouse Society: the list of stations, their years and vessels, "
           "facts only with a link; positions from US government Light Lists (public domain).")
CREDIT = ("U.S. Lighthouse Society Digital Archive (stations, years, vessels; facts with a link) and the Light Lists of the "
          "Light-House Board and Lighthouse Service (public domain; positions)")

# The Light Lists the positions come from (the Internet Archive identifiers the page images and text were read from)
LISTS = {
    "ll1893": {"title": "Light List: Atlantic and Gulf Coasts of the United States, 1893 (Light-House Board)", "year": 1893,
               "id": "lightlistatlant00servgoog", "url": "https://archive.org/details/lightlistatlant00servgoog", "bearings": "magnetic"},
    "ll1900": {"title": "Light List: Atlantic and Gulf Coasts of the United States, 1900 (Light-House Board)", "year": 1900,
               "id": "lightlistatlant01servgoog", "url": "https://archive.org/details/lightlistatlant01servgoog", "bearings": "magnetic"},
    "gl1925": {"title": "Light List, Great Lakes, United States and Canada, 1925 edition (Lighthouse Service)", "year": 1925,
               "id": "lightlist00unkngoog", "url": "https://archive.org/details/lightlist00unkngoog", "bearings": "true"},
    "gl1928": {"title": "Light List, Great Lakes, United States and Canada, 1928 edition (Lighthouse Service)", "year": 1928,
               "id": "lightlist00unkngoog", "url": "https://archive.org/details/lightlist00unkngoog", "bearings": "true"},
    "ll1934": {"title": "Atlantic Coast of the United States, Local Light and Buoy List, New England Coast, 1934 (Lighthouse Service)", "year": 1934,
               "id": "atlanticcoastofu00unit", "url": "https://archive.org/details/atlanticcoastofu00unit", "bearings": "true"},
    "lhb1895": {"title": "Annual Report of the Light-House Board for the fiscal year 1895", "year": 1895,
                "id": "annualreportlig00boargoog", "url": "https://archive.org/details/annualreportlig00boargoog", "bearings": "true"},
}

# The Society files five stations without a state; each is one of these, by its own description
STATE_FIX = {
    "humboldt-bay-bell-boat-lightship-station": ("CA", "Humboldt Bay entrance (the Society's location)"),
    "saint-helena-bar-lightship-station": ("SC", "the Society gives Combahee Bank, St. Helena Sound, as the same place"),
    "ship-shoal-lightship-station": ("LA", "off Raccoon Point (the Society's location)"),
    "willoughby-split-lightship-station": ("VA", "south side of the entrance to Hampton Roads (the Society's location)"),
}
# An entry that the rules below cannot tie to a station, tied by hand with the reason
ENTRY_STATIONS = {
    "gl1925:362": ("southeast-shoal-lightship-station", "name; the Society's years for the station (1901-1910, the Lake Carriers' Association's vessel) end before "
                                                        "this list, which still prints the lightship at the same shoal"),
}
# A station whose mooring lies in another country than the one the Society files it under
COUNTRY_OF_POSITION = {"southeast-shoal-lightship-station": ("CA", "ON", "Lake Erie off Pelee Island, in Canadian waters")}
# Places the Society lists as lightship stations that are not moorings
NOT_A_MOORING = {
    "curtis-bay-depot-lightship-station": "a depot where lightships were kept and repaired (Curtis Bay, Baltimore), not a mooring",
    "staten-island-depot-lightship-station": "a depot where lightships were kept and repaired (Staten Island), not a mooring",
    "ohio-ledge-lightship-station-never-built": "a station the Light-House Board planned and never established: no vessel was ever moored there",
    "humboldt-bay-bell-boat-lightship-station": "a bell boat, not a lightship: the Society says it had no official lightship designation",
}


def station_name(raw: str) -> tuple[str, list[str], bool]:
    """"Cross Ledge (Upper Middle) (Lightship Station)" -> ("Cross Ledge", ["Upper Middle"], False)."""
    n = re.sub(r"\s*\((?:lightship|light vessel)\s+station[^)]*\)", "", raw, flags=re.I)
    never_built = bool(re.search(r"never built", raw, re.I))
    n = re.sub(r"\s+(?:lightship|light vessel)\s+station\s*$", "", n, flags=re.I)
    alts: list[str] = []
    m = re.search(r"\s*\(([^()]*)\)\s*$", n)
    if m:
        alts.append(m.group(1).strip())
        n = n[:m.start()]
    return re.sub(r"\s+", " ", n).strip(), alts, never_built


def hull_of(label: str) -> tuple[str | None, int | None]:
    """"Lightship: LV-087" -> ("LV", 87); "Lightship: WLV-196" -> ("WLV", 196); a letter ship ("LV- ZZ (Aurora Borealis)") -> ("LV", None)."""
    m = re.search(r"\b(WLV|WAL|LV)\s*-?\s*0*(\d+)\b", label)
    if m:
        return m.group(1), int(m.group(2))
    return ("LV", None) if label else (None, None)


def squash(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


# ---------------------------------------------------------------------------------------------
# Positions
# ---------------------------------------------------------------------------------------------

def dms(t: list[int]) -> float:
    return t[0] + t[1] / 60 + t[2] / 3600


def load_entries() -> list[dict]:
    if not ENTRIES.exists():
        return []
    return [json.loads(line) for line in ENTRIES.read_text(encoding="utf-8").splitlines() if line.strip()]


def entry_station(e: dict, stations: dict[str, dict]) -> tuple[str | None, str]:
    """The slug of the station an entry belongs to, and how that was settled: the vessel's number and the list's year
    against the Society's assignments, and the name; both must agree (a number only when the entry has one)."""
    year = LISTS[e["list"]]["year"]
    manual = ENTRY_STATIONS.get(f"{e['list']}:{e['number']}")
    if manual and manual[0] in stations:
        return manual
    name_key = squash(re.sub(r"\s*\(.*?\)", "", re.sub(r"\s*Light[\s\-]*(?:Vessel|ship).*$", "", e["name"], flags=re.I)))
    by_name, by_hull = [], []
    for slug, st in stations.items():
        sk = squash(st["name"])
        if sk and (name_key in sk or sk in name_key):
            by_name.append(slug)
            for v in st["vessels"]:
                kind, no = hull_of(v["label"])
                if no is not None and no == e.get("vessel_no") and v["start"] is not None and v["start"] - 1 <= year <= (v["end"] or 9999) + 1:
                    by_hull.append(slug)
    def span_end(st: dict) -> int:
        return max([st["discontinued"] or 0] + [v["end"] or 0 for v in st["vessels"]] + [0]) or 9999

    live = [s for s in by_name if stations[s]["established"] is None or stations[s]["established"] - 1 <= year <= span_end(stations[s]) + 1]
    if len(set(by_hull)) == 1:
        return by_hull[0], "vessel number and year agree with the Society's assignment, and the name"
    if e.get("vessel_no") is None and len(live) == 1:
        return live[0], "name and year (the entry carries no vessel number)"
    if len(live) == 1:
        return live[0], f"name and year; the Society numbers the vessel there differently (list: No. {e.get('vessel_no')})"
    return None, f"{len(live)} stations of that name were in service in {year}"


def stated_position(e: dict) -> dict:
    lat, lon = dms(e["lat"]), -dms(e["lon"])
    L = LISTS[e["list"]]
    return {"lat": round(lat, 5), "lon": round(lon, 5), "basis": "stated", "list": e["list"], "page": e["page"], "entry": e["number"],
            "note": (f"Position printed in the {L['title']}, page {e['page']}, entry {e['number']}: {e['name']}, "
                     + (f"{e['lat'][0]} {e['lat'][1]:02d} N, {e['lon'][0]} {e['lon'][1]:02d} W (to the minute)" if e.get("to_minute")
                        else f"{e['lat'][0]} {e['lat'][1]:02d} {e['lat'][2]:02d} N, {e['lon'][0]} {e['lon'][1]:02d} {e['lon'][2]:02d} W"
                        f"{' (the seconds are in brackets: the position varies somewhat)' if any(e.get('approx', [])) else ''}") + ". "
                     
                     f"Location as printed: {e['location']}")}


def computed_position(c_: dict) -> dict:
    """c_ = {"from_light": {"name", "lat", "lon", "source"}, "point": "SE. by E. 1/4 E.", "nm": 4.0, "list": "ll1900", "year": 1900,
    "reference": "magnetic"|"true", "degrees": for a bearing given in degrees, "text": the printed words}."""
    light = c_["from_light"]
    if c_["reference"] == "magnetic":
        mag = c_["degrees"] if "degrees" in c_ else geo.compass_degrees(c_["point"])
        true = geo.true_bearing(mag, light["lat"], light["lon"], float(c_["year"]))
        how = f"compass bearing {c_['point'] if 'point' in c_ else str(mag) + ' degrees'} (magnetic; the list says so) turned true by the IGRF-14 declination of {c_['year']} ({geo.declination(light['lat'], light['lon'], float(c_['year'])):+.1f} degrees)"
    else:
        true = c_["degrees"]
        how = f"true bearing {true:g} degrees as printed"
    lat, lon = geo.destination(light["lat"], light["lon"], true, c_["nm"])
    L = LISTS[c_["list"]]
    return {"lat": round(lat, 5), "lon": round(lon, 5), "basis": "computed", "list": c_["list"],
            "note": (f"Computed: {c_['nm']:g} nautical miles from {light['name']} ({light['lat']:.5f}, {light['lon']:.5f}; {light['source']}), "
                     f"{how}: {true:.1f} degrees true. Source text, {L['title']}: “{c_['text']}”")}


def build_positions(stations: dict[str, dict]) -> tuple[dict[str, dict], list[dict]]:
    """slug -> position (the stated one when the lists give one; else the computed one), and the entries that could not be
    tied to a station (for the review)."""
    out: dict[str, dict] = {}
    unmatched: list[dict] = []
    by_station: dict[str, list[dict]] = {}
    for e in load_entries():
        slug, how = entry_station(e, stations)
        if slug is None:
            unmatched.append({"entry": f"{e['list']}:{e['number']}", "name": e["name"], "why": how})
            continue
        e["_how"] = how
        by_station.setdefault(slug, []).append(e)
    for slug, es in by_station.items():
        if all(e.get("lat") for e in es):
            es.sort(key=lambda e: LISTS[e["list"]]["year"])
            pos = stated_position(es[-1])           # the newest list's reading is the station's position
            pos["also"] = [{"list": e["list"], "lat": round(dms(e["lat"]), 5), "lon": round(-dms(e["lon"]), 5)} for e in es[:-1]]
            pos["tie"] = es[-1]["_how"]
            out[slug] = pos
    if COMPUTED.exists():
        for slug, cs in json.loads(COMPUTED.read_text(encoding="utf-8")).items():
            if slug not in out and slug in stations:
                out[slug] = computed_position(cs)
    return out, unmatched


# ---------------------------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------------------------

def build() -> tuple[list[dict], dict]:
    places = {p["slug"]: p for p in uv.lightship_places()}
    pages = uv.station_pages()
    stations: dict[str, dict] = {}
    for slug, p in places.items():
        name, alts, never_built = station_name(p["name"])
        pg = pages[slug]
        st = {"slug": slug, "name": name, "alts": alts, "never_built": never_built, "nid": p["nid"], "url": p["url"],
              "region": p.get("state"), "established": p.get("established") or pg.get("established"),
              "discontinued": p.get("discontinued") or pg.get("discontinued"), "vessels": pg["vessels"],
              "location": pg.get("location") or p.get("location_desc"), "alternate_name": pg.get("alternate_name") or (p.get("alternate_names") or None),
              "data_source": pg.get("data_source") or p.get("data_source")}
        if not st["region"] and slug in STATE_FIX:
            st["region"] = STATE_FIX[slug][0]
        stations[slug] = st
    positions, unmatched = build_positions(stations)
    records = []
    for slug, st in sorted(stations.items()):
        ident = re.sub(r"-lightship-station.*$", "", slug)
        pos = positions.get(slug)
        reasons = []
        if slug in NOT_A_MOORING:
            reasons.append(NOT_A_MOORING[slug])
        country, region = "US", st["region"]
        if slug in COUNTRY_OF_POSITION and pos:
            country, region = COUNTRY_OF_POSITION[slug][0], COUNTRY_OF_POSITION[slug][1]
        rec = rx.new_record(SOURCE, ident, st["name"], url=st["url"], country=country, region=region,
                            lat=pos["lat"] if pos else None, lon=pos["lon"] if pos else None, precision="approximate",
                            kind="lightship_station", kind_raw="Lightship Station")
        rec["other_names"] = [a for a in ([st["alternate_name"]] if isinstance(st["alternate_name"], str) else []) + st["alts"] if a]
        rec["setting"] = "offshore"
        rec["status"] = "lost" if st["discontinued"] else None
        rec["light"]["first_lit"] = st["established"]
        rec["light"]["deactivated"] = st["discontinued"]
        ev = []
        if st["established"]:
            ev.append({"year": st["established"], "event": "first_lit", "note": "Lightship station established (US Lighthouse Society Digital Archive)", "from": SOURCE})
        if st["discontinued"]:
            ev.append({"year": st["discontinued"], "event": "deactivated", "note": "Station discontinued (US Lighthouse Society Digital Archive)", "from": SOURCE})
        rec["events"] = ev
        rec["links"] = [{"label": f"US Lighthouse Society Digital Archive: {st['name']} (Lightship Station)", "url": st["url"], "kind": "reference"}]
        vessels = []
        for v in st["vessels"]:
            kind, no = hull_of(v["label"])
            vessels.append({"node": v["node"], "label": re.sub(r"^Lightship:\s*", "", re.sub(r"\s+More Information.*$", "", v["label"])), "start": v["start"], "end": v["end"]})
        rec["extra"] = {"slug": slug, "type": "Lightship Station", "vessels": vessels, "location_text": st["location"],
                        "light_list_source": st["data_source"], "region_basis": STATE_FIX[slug][1] if slug in STATE_FIX else None}
        if st["never_built"]:
            rec["extra"]["never_built"] = True
        if slug in NOT_A_MOORING:
            rec["extra"]["not_a_mooring"] = NOT_A_MOORING[slug]
        if pos:
            rec["extra"]["position_from"] = "computed" if pos["basis"] == "computed" else "light_list"
            rec["extra"]["position_note"] = pos["note"]
            rec["extra"]["position"] = {k: v for k, v in pos.items() if k not in ("note", "lat", "lon")}
        else:
            reasons.append("no Light List, Lighthouse Board report or Bulletin entry read gives a position or a bearing and distance for this station")
            rec["extra"]["unplaced_reason"] = "; ".join(reasons)
        if reasons and pos is None and slug in NOT_A_MOORING:
            rec["extra"]["unplaced_reason"] = NOT_A_MOORING[slug]
        if st["region"] is None:
            rec["extra"]["unplaced_reason"] = (rec["extra"].get("unplaced_reason") or "") + "; the Society gives no state"
        records.append(rec)
    notes = {
        "stations": len(records), "placed": sum(1 for r in records if r["lat"] is not None),
        "stated": sum(1 for r in records if r["extra"].get("position_from") == "light_list"),
        "computed": sum(1 for r in records if r["extra"].get("position_from") == "computed"),
        "unplaced": sum(1 for r in records if r["lat"] is None),
        "entries_not_tied_to_a_station": unmatched,
        "lists": LISTS,
    }
    return records, notes


def main() -> int:
    records, notes = build()
    rx.write_extract(OUT_PATH, source=SOURCE, title="Lightship stations (US Lighthouse Society list; positions from Light Lists)",
                     url="https://archives.uslhs.org/type-place/lightship-station", license_text=LICENSE, credit=CREDIT,
                     records=records, notes=notes, retrieved="2026-10-21")
    c.log(f"lightship_stations: {notes['stations']} stations, {notes['placed']} placed ({notes['stated']} stated, {notes['computed']} computed), "
          f"{notes['unplaced']} unplaced; {len(notes['entries_not_tied_to_a_station'])} entries not tied to a station")
    return 0


if __name__ == "__main__":
    sys.exit(main())
