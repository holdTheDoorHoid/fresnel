#!/usr/bin/env python3
"""Canadian lightship stations and life-saving stations that the sources name, a small curated
source; writes data/sources/ca_lightships_lifesaving.json (DESIGN.md 3.5, 2.3, 3.8).

Neither kind has a register or a Wikidata class in Canada (survey_canada.md section 4). What there is:

- **Lightship stations** (a place where lightships were moored): the Coast Guard's own history of the
  floating lights of the St. Lawrence (Jean Cloutier, "Des phares flottants sur le Saint-Laurent",
  Sémaphore, Université du Québec à Rimouski: 1830 to 1964, thirteen or so stations), the Department of
  Marine and Fisheries report for 1900-01 (Internet Archive; the lists of lightships and their
  masters), Lighthouse Friends' pages for the lights that replaced or took over a station, Archives
  Canada's *C.G. Lightship Lurcher* fonds and the Polson Iron Works page for Lurcher Shoal.
- **Life-saving stations**: Parks Canada's national historic event, the Sable Island Humane
  Establishment (1801-1958; Directory of Federal Heritage Designations id 16352, designated 2021-04-28),
  and J. B. Mansfield's *History of the Great Lakes* (1899, public domain), as adapted on the Naval
  Marine Archive's page, which dates the Ontario stations of the federal service (1882-89) and names
  the Nova Scotia places that received lifeboats in 1885.

**Positions only where a source gives one.** Lower Traverse has Lighthouse Friends' own position
(the page is about the lightship station). Lurcher Shoal has none for the vessel's mooring: the
position here is the Coast Guard's Lurcher Shoal light buoy NM (list number A251), which took the
station's place when the last lightship left in 1969, marked `approximate`. The Sable Island Humane
Establishment is placed at the island's coordinates (Wikipedia), `approximate`: its stations lay along
the island. A station with no position in any source (Red Island Reef, Manicouagan Shoal, the lifeboat
stations of Ontario and Nova Scotia) is written without one; the merge lists it as not shown, which makes
the list a set of leads for the research agents and for the owner.

**Lights that were lightship stations first.** White Island Reef and Prince Shoal are stations of a
light that stands there now (or stood): their lightship years are events on those stations, joined by
Lighthouse Friends' id (`join_keys`), with no position of their own.

The merge reads `extra.join_keys` (identifiers that join a record to the station another source holds)
and the entries in `data/curation_ca.json` (which makes Lighthouse Friends' record for Lower Traverse a
lightship station).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402

SOURCE = "ca_lightships_lifesaving"
OUT_PATH = c.REPO / "data" / "sources" / f"{SOURCE}.json"
SOURCES_DIR = c.REPO / "data" / "sources"
LICENSE = ("Facts compiled from Canadian government publications, an open university repository, Lighthouse Friends "
           "(facts only), the Naval Marine Archive's adaptation of a public-domain history and Wikipedia coordinates; "
           "each linked on the record, no text copied.")

EV = {
    "cloutier": {"label": "Jean Cloutier, 'Des phares flottants sur le Saint-Laurent' (Sémaphore, UQAR): the lightships of the St. Lawrence, 1830-1964",
                 "url": "https://semaphore.uqar.ca/2868/1/Des%20phares%20flottants%20sur%20le%20Saint-Laurent.pdf", "date": None},
    "marine1901": {"label": "Report of the Department of Marine and Fisheries (Marine) for 1900-01, Internet Archive: lightships, their repairs and their masters",
                   "url": "https://archive.org/details/1901v35i9p21_0025", "date": "1901"},
    "lhf_lower_traverse": {"label": "Lighthouse Friends: Lower Traverse (the lightship station, the 1904 pier lighthouse and the lightship again)",
                           "url": "https://www.lighthousefriends.com/light.asp?ID=2354", "date": None},
    "lhf_white_island": {"label": "Lighthouse Friends: White Island Reef (the lightship from 1893, the pillar lighthouse from 1956)",
                         "url": "https://www.lighthousefriends.com/light.asp?ID=2365", "date": None},
    "lhf_prince_shoal": {"label": "Lighthouse Friends: Haut-fond Prince / Prince Shoal (Lightship No. 7 from 1905, No. 20 from 1956, the pillar from 1964)",
                         "url": "https://www.lighthousefriends.com/light.asp?ID=1626", "date": None},
    "lhf_red_island": {"label": "Lighthouse Friends: Red Island (the Red Island lightship of 1871)",
                       "url": "https://www.lighthousefriends.com/light.asp?ID=1625", "date": None},
    "lurcher_fonds": {"label": "Archives Canada: C.G. Lightship Lurcher fonds",
                      "url": "https://archivescanada.accesstomemory.org/c-g-lightship-lurcher-ship-fonds", "date": None},
    "lurcher_posterity": {"label": "For Posterity's Sake: Lurcher Lightship (placed on station February 1904; 1944 mooring 2.5 miles SW of the Southwest Shoal patch)",
                          "url": "https://www.forposterityssake.ca/Navy/LURCHER-LIGHTSHIP.htm", "date": None},
    "lurcher_polson": {"label": "Polson Iron Works: Lurcher, Lightship 14 (built 1903)",
                       "url": "https://www.polsonironworks.ca/stories/Lightship-14.html", "date": None},
    "ccg_a251": {"label": "Canadian Coast Guard List of Lights, Atlantic volume: Lurcher Shoal bifurcation light buoy NM (A251), the aid that marks the station today",
                 "url": "https://www.notmar.gc.ca/publications/list-lights/atl/atlvolumee.pdf", "date": "2026"},
    "sable_parks": {"label": "Parks Canada: The Sable Island Humane Establishment (national historic event, 1801-1958)",
                    "url": "https://www.canada.ca/en/parks-canada/news/2021/12/the-sable-island-humane-establishment.html", "date": "2021-12-20"},
    "sable_dfhd": {"label": "Directory of Federal Heritage Designations: Sable Island Humane Establishment (1801-1958), National Historic Event, designated 2021-04-28",
                   "url": "https://www.pc.gc.ca/apps/dfhd/page_nhs_eng.aspx?id=16352", "date": "2021-04-28"},
    "sable_wikipedia": {"label": "Wikipedia: Sable Island (the island's coordinates; the Establishment's central station, two rescue boat stations and lookouts by 1809)",
                        "url": "https://en.wikipedia.org/wiki/Sable_Island", "date": None},
    "mansfield": {"label": "Naval Marine Archive, 'Life saving stations' (adapted from J. B. Mansfield, History of the Great Lakes, 1899): the federal lifeboat stations of Ontario, 1882-89, and the lifeboats of 1885",
                  "url": "https://www.navalmarinearchive.com/research/docs/life_saving_stations.html", "date": "1899"},
}


def record(key: str, name: str, region: str, kind: str, *, lat: float | None = None, lon: float | None = None,
           precision: str | None = "exact", status: str | None = None, events: list | None = None,
           first_lit: int | None = None, deactivated: int | None = None, evidence: list[str] = (), other_names: list | None = None,
           join_keys: list | None = None, note: str | None = None, extra: dict | None = None,
           registers: list | None = None) -> dict:
    ev = [EV[e] for e in evidence]
    return {
        "key": f"{SOURCE}:{key}",
        "url": ev[0]["url"],
        "name": name,
        "other_names": other_names or [],
        "country": "CA",
        "region": region,
        "county": None,
        "lat": lat,
        "lon": lon,
        "precision": precision if lat is not None else None,
        "kind": kind,
        "kind_raw": None,
        "role": None,
        "status": status,
        "status_raw": None,
        "structure": {"type": None, "material": None, "built": None, "height_m": None, "status": None},
        "light": {"first_lit": first_lit, "deactivated": deactivated, "characteristic": None, "focal_height_m": None,
                  "range_nm": None, "fog_signal": None, "lens": None},
        "setting": "offshore" if kind == "lightship_station" else None,
        "registers": registers or [],
        "aton": {"uscg_llnr": None, "arlhs": None, "ccg_list_number": None, "nga": None},
        "agency": None,
        "ownership": None,
        "events": [{**e, "from": SOURCE} for e in (events or [])],
        "photos": [],
        "links": [{"label": e["label"], "url": e["url"], "kind": "reference"} for e in ev],
        "relations": {},
        "extra": {"station_level": bool(join_keys and lat is None), "join_keys": join_keys or [], "evidence": ev,
                  "note": note, **(extra or {})},
    }


def lhf_position(lhf_id: str) -> tuple[float, float] | None:
    path = SOURCES_DIR / "lighthousefriends.json"
    if not path.exists():
        return None
    for r in json.loads(path.read_text(encoding="utf-8")).get("records", []):
        if r.get("extra", {}).get("lhf_id") == lhf_id and r.get("country") == "CA":
            return r["lat"], r["lon"]
    return None


def ccg_position(number: str) -> tuple[float, float] | None:
    """Position of a Coast Guard list entry: from the extract if it has it; the Lurcher buoy is not a
    station and the extract drops it, so its position is the List's own (43 48 57.2 N, 066 29 58.0 W)."""
    return {"A251": (43.815889, -66.499444)}.get(number)


def build() -> tuple[list[dict], dict]:
    lt = lhf_position("2354")
    lurcher = ccg_position("A251")
    recs = [
        record("lower-traverse", "Lower Traverse", "QC", "lightship_station", lat=lt[0] if lt else None, lon=lt[1] if lt else None,
               precision="exact", status="lost", first_lit=1830, deactivated=1940,
               events=[
                   {"year": 1830, "event": "other", "note": "First lightship moored at the lower end of the Saint-Roch traverse (Cloutier gives 1830; Lighthouse Friends says the schooner Brilliant was anchored in 1831)"},
                   {"year": 1875, "event": "other", "note": "An iron lightship, found unsuited to Halifax Harbour, moored here"},
                   {"year": 1887, "event": "damaged", "note": "The lightship was run down and sunk by the ship Loyal on 16 October; raised and back on station 8 July 1888"},
                   {"year": 1904, "event": "other", "note": "A lighthouse on a pier replaced the lightship (the pier failed and the station was abandoned in 1907)"},
                   {"year": 1921, "event": "other", "note": "A new steel, self-propelled lightship placed on the station"},
                   {"year": 1940, "event": "deactivated", "note": "On the Light List for 1939; by the 1940 edition only a buoy marks the place"},
               ],
               evidence=["lhf_lower_traverse", "cloutier", "marine1901"], other_names=["Lower Traverse Lightship", "Traverse Saint-Roch inférieure"],
               join_keys=["lhf:2354"],
               note="Lighthouse Friends lists this lightship station among its lighthouses; the merge treats its record as a lightship station (data/curation_ca.json)."),
        record("lurcher-shoal", "Lurcher Shoal", "NS", "lightship_station", lat=lurcher[0] if lurcher else None,
               lon=lurcher[1] if lurcher else None, precision="approximate", status="lost", first_lit=1904, deactivated=1969,
               events=[
                   {"year": 1904, "event": "other", "note": "Lightship placed on station in February (Archives Canada's record says circa 1906); the vessel built 1903 as Lurcher, later No. 14"},
                   {"year": 1969, "event": "deactivated", "note": "The last lightship of Canada left the station; an automatic buoy replaced her (Cloutier says the last, No. 4, arrived here in 1964)"},
               ],
               evidence=["lurcher_posterity", "lurcher_fonds", "lurcher_polson", "cloutier", "ccg_a251"],
               other_names=["Lurcher Lightship"],
               note=("The position is the Coast Guard's Lurcher Shoal light buoy NM, which marks the shoal today, not the vessel's mooring; "
                     "in 1944 she lay about 2.5 miles southwest of the shoalest patch of the Southwest Shoal."),
               extra={"position_source": "ccg_list_of_lights A251, the buoy that took the lightship's place"}),
        record("red-island-reef", "Red Island Reef", "QC", "lightship_station", status="lost", first_lit=1871,
               events=[
                   {"year": 1871, "event": "other", "note": "Iron lightship moored northeast of Red Island in ten fathoms on 1 July"},
                   {"year": 1923, "event": "other", "note": "Lightship No. 3 replaced the schooner that had marked the station since 1871; she stayed to 1961"},
               ],
               evidence=["lhf_red_island", "cloutier", "marine1901"], other_names=["Red Island Lightship"],
               note="No source found gives the station's position."),
        record("manicouagan-shoal", "Manicouagan Shoal", "QC", "lightship_station", status="lost", first_lit=1871, deactivated=1893,
               events=[{"year": 1893, "event": "other", "note": "The Department of Marine abandoned the lightship here and moved it to White Island Reef"}],
               evidence=["cloutier", "lhf_white_island"], other_names=["Manicouagan Shoal Lightship"],
               note="No source found gives the station's position."),
        record("white-island-reef", "White Island Reef", "QC", "lighthouse", join_keys=["lhf:2365"],
               events=[
                   {"year": 1893, "event": "other", "note": "A lightship (moved from Manicouagan Shoal) was moored at the northeast end of the reef, replacing a gas buoy"},
                   {"year": 1956, "event": "other", "note": "The pillar lighthouse began operating and freed Lightship No. 20 (the last of three vessels, Nos. 5, 23 and 20, to serve here)"},
               ],
               evidence=["lhf_white_island", "cloutier", "marine1901"], note="Lightship years of a station that has a pillar light."),
        record("prince-shoal", "Prince Shoal", "QC", "lighthouse", join_keys=["lhf:1626"],
               events=[
                   {"year": 1905, "event": "other", "note": "Iron Lightship No. 7 replaced a gas buoy at the opening of navigation (Cloutier says 1906)"},
                   {"year": 1956, "event": "other", "note": "Lightship No. 20 came from White Island Reef and No. 7 was withdrawn"},
                   {"year": 1964, "event": "other", "note": "The pillar lighthouse replaced the last lightship of the St. Lawrence at this station"},
               ],
               evidence=["lhf_prince_shoal", "cloutier"], note="Lightship years of a station that has a pillar light."),
    ]
    sable = record("sable-island-humane-establishment", "Sable Island Humane Establishment", "NS", "life_saving_station",
                   lat=43.930833, lon=-59.917778, precision="approximate", status="lost",
                   events=[
                       {"year": 1801, "event": "other", "note": "Founded under Governor Wentworth with James Morris as first superintendent: the first permanent, government-sponsored coastal rescue organisation in the northwest Atlantic"},
                       {"year": 1958, "event": "closed", "note": "Operations ceased"},
                       {"year": 2021, "event": "heritage_designated", "note": "National Historic Event of Canada, designated 2021-04-28"},
                   ],
                   evidence=["sable_dfhd", "sable_parks", "sable_wikipedia"], other_names=["Sable Island Humane Establishment (1801-1958)"],
                   note=("Placed at the island's coordinates: its stations (a central station, two rescue boat stations and lookouts by 1809) lay "
                         "along the island, and no source gives each one's position."),
                   extra={"position_source": "Wikipedia, Sable Island (43 55 51 N, 59 55 04 W)"},
                   registers=[{"register": "National Historic Event (Canada)", "number": "16352", "url": EV["sable_dfhd"]["url"]}])
    recs.append(sable)

    # The federal lifeboat service: stations by place and year (Mansfield, 1899); no positions.
    ontario = [("cobourg", "Cobourg", "ON", 1882, "Established 7 November 1882: the first station equipped; coxswain Daniel Rooney"),
               ("toronto", "Toronto (Island)", "ON", 1883, "Established 1 March 1883, after a voluntary life-saving crew on the island"),
               ("wellington", "Wellington", "ON", 1883, "Established in 1883"),
               ("point-traverse", "Point Traverse (Poplar Point)", "ON", 1883, "Established in 1883, Prince Edward County"),
               ("port-rowan", "Port Rowan", "ON", 1883, "Established 19 October 1883"),
               ("port-stanley", "Port Stanley", "ON", 1885, "Established 25 June 1885, the first of the twelve lifeboats of 1885"),
               ("collingwood", "Collingwood", "ON", 1885, "Established 2 September 1885"),
               ("goderich", "Goderich", "ON", 1886, "Established 21 October 1886"),
               ("port-hope", "Port Hope", "ON", 1889, "Established 6 November 1889")]
    for slug, name, region, year, note in ontario:
        recs.append(record(f"{slug}-life-saving-station", f"{name} Life-Saving Station", region, "life_saving_station", status="unknown",
                           events=[{"year": year, "event": "other", "note": note}], evidence=["mansfield"],
                           note="Federal lifeboat station of the Department of Marine and Fisheries; no source found gives its position."))
    maritime = [("devils-island", "Devil's Island", "NS"), ("duncans-cove", "Duncan's Cove", "NS"), ("yarmouth", "Yarmouth", "NS"),
                ("scatarie", "Scatarie", "NS"), ("pelee-island", "Pelee Island", "ON")]
    for slug, name, region in maritime:
        recs.append(record(f"{slug}-life-saving-station", f"{name} Life-Saving Station", region, "life_saving_station", status="unknown",
                           events=[{"year": 1885, "event": "other", "note": "One of the twelve lifeboats ordered in 1885 was allotted here"}],
                           evidence=["mansfield"],
                           note="The Naval Marine Archive page names the place only; whether a station was built, and its position, are not given."))
    unplaced = sorted(r["name"] for r in recs if r["lat"] is None and not r["extra"]["join_keys"])
    notes = {
        "records": len(recs),
        "placed": sorted(r["name"] for r in recs if r["lat"] is not None),
        "joined_to_a_light_by_identifier": sorted(r["name"] for r in recs if r["extra"]["join_keys"]),
        "unplaced_leads": unplaced,
        "not_a_lightship_station": "Sambro Island is a lighthouse (1758); no source found a Sambro lightship.",
        "leads_not_in_this_file": ["Sandheads (BC): a lightship 1865-79 and again from 1913, per Lighthouse Friends and Wikipedia; not confirmed from a page read this session",
                                   "Anticosti East Point, Île aux Coudres, Sandy Beach (Gaspé Bay), Upper Saint-Roch Traverse (Cloutier)",
                                   "Lake St. Louis (3 vessels), Lake St. Peter (3), Lachine, Chateauguay, Miramichi Bay, Zephyr Rock, Barrington (Marine report 1900-01)"],
    }
    return recs, notes


def main(argv: list[str] | None = None) -> int:
    recs, notes = build()
    c.write_source_json(OUT_PATH, source=SOURCE, title="Canadian lightship stations and life-saving stations (curated)",
                        url=EV["cloutier"]["url"], license_text=LICENSE, records=recs, notes=notes, retrieved="2026-10-21")
    c.log(f"ca_lightships_lifesaving: {len(recs)} records, {len(notes['placed'])} placed, {len(notes['unplaced_leads'])} unplaced leads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
