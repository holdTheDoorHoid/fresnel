#!/usr/bin/env python3
"""Canada's staffed lightstations (the keepers' home and workplace), a small curated source;
writes data/sources/ca_staffed_lightstations.json (DESIGN.md 1 "Access", 2.3, 3.8).

There is no official current list. The table below is built from the newest sources found
(survey_canada.md section 2, then four searches on 2026-10-21):

- **The list**: Appendix 4 (Pacific Region, 27 stations) and Appendix 5 (Newfoundland and Labrador,
  23 stations) of the Senate fisheries committee's report "Seeing the Light" (October 2011), which
  print the Coast Guard's own data of April 2010; the Maritimes' one staffed station, Machias Seal
  Island (New Brunswick), is in its text. The Department of Fisheries and Oceans' page "Lightstations
  of Newfoundland and Labrador" (a 2005 brochure, the page modified 2019-09-24) names the same 23.
- **Newer, general**: the Coast Guard's news release of 31 July 2024 ceasing keeper functions at
  Carmanah Point and Pachena Point ("the twenty-five other staffed light stations on the British
  Columbia coast will continue"), a Question Period note of 17 December 2024 (the two keepers
  "relocated to other lightstations in British Columbia"), and the US Lighthouse Society's January
  2025 count of 49 staffed lighthouses in Canada. The newer sources win where they differ: the two
  stations are `automated`, 2024.
- **Newer, about one station**: Cape Beale (US Lighthouse Society, 5 Jan 2025, a keeper there), Triple
  Island (CTV, 15 May 2025, principal and assistant keepers on a 28-day rotation), Estevan Point
  (a federal impact-assessment page of 2022-23: "staffed by two lightkeepers 24/7"), Long Point,
  Twillingate (a 2023 interview, "one of the 23 ... still staffed"), Machias Seal Island (a March 2025
  article describing summer 2024: two residents, both keepers).

Every station whose staffed status rests only on the April 2010 list (with the 2024 count of 25 for
British Columbia, which names no station) has `extra.check = true`: research agents should confirm it
before a page says "staffed" in the present tense. 44 of the 51 listed stations are in that case.
`staffing.as_of` is the year of the newest evidence for that station.

Each record has no structure facts; it carries the identifiers that join it to the station the
other sources hold (`extra.join_keys`: the Coast Guard list number and Lighthouse Friends' id,
checked against both by position) and the Coast Guard list's position when `ccg_list_of_lights.json`
has one. The merge sets `staffing`, and `access` to `restricted` with the note below.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402

SOURCE = "ca_staffed_lightstations"
OUT_PATH = c.REPO / "data" / "sources" / f"{SOURCE}.json"
CCG_PATH = c.REPO / "data" / "sources" / "ccg_list_of_lights.json"
ACCESS_NOTE = ("Staffed lightstation: the keepers' home and workplace. Visit only where the station welcomes "
               "visitors, and never land uninvited.")
DESTAFFED_NOTE = ("The Canadian Coast Guard ended keeper functions here on 31 July 2024 because the ground under the station is "
                  "unstable and some facilities are no longer safe to use; the light is automated. Check with the Coast Guard "
                  "or Parks Canada (West Coast Trail) before you go.")
LICENSE = ("Facts compiled from Canadian government publications (Senate of Canada, Canadian Coast Guard, Fisheries and Oceans "
           "Canada, Impact Assessment Agency) and news reports, each linked on the record; no text copied.")

SENATE = {"label": "Senate of Canada, 'Seeing the Light' (Oct 2011), Appendix 4 (Pacific) and Appendix 5 (Newfoundland and Labrador): Coast Guard data, April 2010",
          "url": "https://sencanada.ca/content/sen/committee/411/pofo/rep/rep02oct11-e.pdf", "date": "2010-04"}
CCG_2024 = {"label": "Canadian Coast Guard news release, 31 July 2024: keeper functions end at Carmanah Point and Pachena Point; 25 other staffed stations in British Columbia",
            "url": "https://www.canada.ca/en/canadian-coast-guard/news/2024/07/canadian-coast-guard-to-cease-light-keeper-functions-at-carmanah-point-and-pachena-point-light-stations-due-to-safety-concerns.html",
            "date": "2024-07-31"}
QP_NOTE = {"label": "Fisheries and Oceans Canada Question Period note DFO-2024-QP-00038 (received 17 December 2024): keepers relocated to other lightstations",
           "url": "https://search.open.canada.ca/qpnotes/record/dfo-mpo%2CDFO-2024-QP-00038", "date": "2024-12-17"}
DFO_NL = {"label": "Fisheries and Oceans Canada, 'Lightstations of Newfoundland and Labrador' (brochure 2005, page modified 2019-09-24): 23 staffed of 55 major lightstations, named",
          "url": "https://www.dfo-mpo.gc.ca/otw-am/lighthouses-phares/publications/lightstationsnl-lespharestnl-eng.html", "date": "2019-09-24"}
USLHS_2025 = {"label": "US Lighthouse Society, 'Light Hearted' (5 Jan 2025): a keeper at Cape Beale; 49 staffed lighthouses in Canada",
              "url": "https://news.uslhs.org/2025/01/05/light-hearted-lite-12-karen-zacharuk-keeper-at-cape-beale-bc/", "date": "2025-01-05"}
CTV_TRIPLE = {"label": "CTV News (15 May 2025): a keeper dies at Triple Island; the station is staffed by a principal and an assistant lightkeeper",
              "url": "https://www.ctvnews.ca/vancouver/article/lighthouse-keeper-dies-alone-on-northwestern-bc-island", "date": "2025-05-15"}
IAAC_ESTEVAN = {"label": "Impact Assessment Agency of Canada, Estevan Point Lightstation Renewable Power Generation System (project 84166, 2022-23): 'staffed by two lightkeepers 24/7'",
                "url": "https://iaac-aeic.gc.ca/050/evaluations/proj/84166", "date": "2023-11-08"}
USLHS_LONG_POINT = {"label": "US Lighthouse Society, 'Light Hearted' episode 226 (21 May 2023): former keeper's interview; Long Point is one of the 23 staffed stations in Newfoundland",
                    "url": "https://news.uslhs.org/2023/05/21/light-hearted-ep-226-barry-porter-adventures-of-a-lightkeeper-newfoundland-pt-2-of-3/", "date": "2023-05-21"}
PRODUCER_MACHIAS = {"label": "Western Producer (March 2025), on Machias Seal Island in summer 2024: two residents, both lighthouse keepers",
                    "url": "https://www.producer.com/farm-family/canadian-american-disputed-island-where-puffins-rule/", "date": "2025-03"}

# (region, name in the list, other names, CCG list number, Lighthouse Friends id, extra evidence, as_of override)
BC = [
    ("Addenbroke Island", [], "P585", "1428"), ("Boat Bluff", [], "P640", "1432"), ("Bonilla Island", [], "P734", "1434"),
    ("Cape Beale", [], "P176", "1199"), ("Cape Mudge", [], "P511", "1188"), ("Cape Scott", [], "P66", "1194"),
    ("Carmanah Point", [], "P180", "1201"), ("Chatham Point", [], "P518", "1189"), ("Chrome Island", [], "P495", "1187"),
    ("Dryad Point", [], "P611", "1429"), ("Egg Island", [], "P579", "1193"), ("Entrance Island", [], "P435", "1105"),
    ("Estevan Point", [], "P114", "1197"), ("Green Island", ["Green Island (Prince Rupert)"], "P730", "1390"),
    ("Ivory Island", [], "P617", "1430"), ("Langara Island", ["Langara Point"], "P807", "1437"), ("Lennard Island", [], "P134", "1198"),
    ("McInnes Island", [], "P619", "1431"), ("Merry Island", [], "P449", "1184"), ("Nootka", ["Friendly Cove"], "P105", "1196"),
    ("Pachena Point", [], "P178", "1200"), ("Pine Island", [], "P576", "1192"), ("Pulteney Point", [], "P553", "1190"),
    ("Quatsino", ["Kains Island"], "P68", "1195"), ("Scarlett Point", [], "P570", "1191"), ("Trial Island", ["Trial Islands"], "P212", "1181"),
    ("Triple Island", ["Triple Islands"], "P752", "1436"),
]
NL = [
    ("Bell Island", [], "N493", "1292"), ("Cape Anguille", [], "N175", "1257"), ("Cape Bonavista", [], "N449", "1253"),
    ("Cape Norman", [], "N223", "1269"), ("Cape Race", [], "N1", "1308"), ("Cape Ray", [], "N173", "1262"),
    ("Cape St. Mary's", [], "N14", "1301"), ("Fort Amherst", [], "N506", "1312"), ("Fort Point", ["Admiral's Point"], "N462", "1249"),
    ("Fortune Head", [], "N102", "1298"), ("Fox Point", ["Fishing Point"], "N240", "1279"),
    ("Green Island (Fortune Bay)", ["Green Island"], "N100", "1297"), ("Green Island (Trinity Bay)", ["Green Island (Catalina)"], "N453", "1250"),
    ("Lamaline", ["Allan's Island"], "N76", "1375"), ("Long Point (Twillingate)", ["Long Point"], "N358", "1284"),
    ("New Ferolle Peninsula", [], "N220", "1276"), ("Northwest Head", ["Ramea"], "N141", "1270"), ("Pass Island", [], "N129", "1376"),
    ("Powles Head", [], "N5", "1309"), ("Puffin Island", [], "N430", "1290"), ("Red Bay", ["Saddle Island"], "N230", "1264"),
    ("St. Shotts", [], "N7", "2217"), ("Tides Cove Point", [], "N65", "1294"),
]
MACHIAS = ("Machias Seal Island", [], "A6", "1371")

# Stations with a source about that station newer than the 2010 list: name -> (as_of, extra evidence).
NEWER = {
    ("BC", "Cape Beale"): ("2025", [USLHS_2025]),
    ("BC", "Triple Island"): ("2025", [CTV_TRIPLE]),
    ("BC", "Estevan Point"): ("2023", [IAAC_ESTEVAN]),
    ("NL", "Long Point (Twillingate)"): ("2023", [USLHS_LONG_POINT]),
    ("NB", "Machias Seal Island"): ("2024", [PRODUCER_MACHIAS]),
}
DESTAFFED = {"Carmanah Point", "Pachena Point"}


def slug(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", "")).strip("-")


def ccg_positions() -> dict[str, tuple[float, float]]:
    if not CCG_PATH.exists():
        return {}
    data = json.loads(CCG_PATH.read_text(encoding="utf-8"))
    return {r["aton"]["ccg_list_number"]: (r["lat"], r["lon"]) for r in data["records"] if r.get("aton", {}).get("ccg_list_number")}


def build_record(region: str, name: str, others: list[str], ccg: str, lhf: str, positions: dict) -> dict:
    destaffed = region == "BC" and name in DESTAFFED
    newer = NEWER.get((region, name))
    evidence = [SENATE]
    if region == "NL":
        evidence.append(DFO_NL)
    if region == "BC":
        evidence.append(CCG_2024)
    if destaffed:
        evidence.append(QP_NOTE)
    if newer:
        evidence += newer[1]
    if destaffed:
        staffing = {"status": "automated", "as_of": "2024"}
        basis = ("The Senate report's April 2010 list names it staffed; the Coast Guard's release of 31 July 2024 ended keeper functions "
                 "(the newer source wins), and a December 2024 note says the keepers were relocated.")
        check = False
    elif newer:
        staffing = {"status": "staffed", "as_of": newer[0]}
        basis = "Named in the Coast Guard's April 2010 list, and a newer source speaks of this station."
        check = False
    else:
        year = "2024" if region == "BC" else "2010"
        staffing = {"status": "staffed", "as_of": year}
        basis = ("Named only in the Coast Guard's April 2010 list"
                 + ("; the Coast Guard's 31 July 2024 release counts 25 other staffed stations in British Columbia without naming them" if region == "BC"
                    else "; the Fisheries and Oceans Canada page of 23 names has the same list") + ". Check before saying it is staffed today.")
        check = True
    lat, lon = positions.get(ccg, (None, None))
    return {
        "key": f"{SOURCE}:{region.lower()}-{slug(name)}",
        "url": evidence[-1]["url"] if newer else SENATE["url"],
        "name": name,
        "other_names": others,
        "country": "CA",
        "region": region,
        "county": None,
        "lat": lat,
        "lon": lon,
        "precision": "exact",
        "kind": "lighthouse",
        "kind_raw": None,
        "role": None,
        "status": None,
        "status_raw": None,
        "structure": {"type": None, "material": None, "built": None, "height_m": None, "status": None},
        "light": {"first_lit": None, "deactivated": None, "characteristic": None, "focal_height_m": None,
                  "range_nm": None, "fog_signal": None, "lens": None},
        "setting": None,
        "registers": [],
        "aton": {"uscg_llnr": None, "arlhs": None, "ccg_list_number": None, "nga": None},
        "agency": None,
        "ownership": None,
        "events": [{"year": 2024, "event": "other", "note": "Coast Guard ended keeper functions here (31 July 2024); the light is automated",
                    "from": SOURCE}] if destaffed else [],
        "photos": [],
        "links": [{"label": e["label"], "url": e["url"], "kind": "reference"} for e in evidence],
        "relations": {},
        "extra": {
            "station_level": True,
            "staffing": staffing,
            "access": {"level": "restricted", "note": DESTAFFED_NOTE if destaffed else ACCESS_NOTE},
            "evidence": evidence,
            "basis": basis,
            "check": check,
            "join_keys": [f"ccg:{ccg}", f"lhf:{lhf}"],
        },
    }


def build() -> tuple[list[dict], dict]:
    positions = ccg_positions()
    records = []
    for region, table in (("BC", BC), ("NL", NL), ("NB", [MACHIAS])):
        for name, others, ccg, lhf in table:
            records.append(build_record(region, name, others, ccg, lhf, positions))
    notes = {
        "stations": len(records),
        "staffed": sum(1 for r in records if r["extra"]["staffing"]["status"] == "staffed"),
        "destaffed_2024": sorted(r["name"] for r in records if r["extra"]["staffing"]["status"] == "automated"),
        "by_region": {reg: sum(1 for r in records if r["region"] == reg and r["extra"]["staffing"]["status"] == "staffed") for reg in ("BC", "NL", "NB")},
        "rest_only_on_the_2010_list": sorted(r["name"] + f" ({r['region']})" for r in records if r["extra"]["check"]),
        "without_position": sorted(r["name"] for r in records if r["lat"] is None),
        "no_official_current_list": "National total 49 staffed after the 2024 change (US Lighthouse Society, Jan 2025); 51 before it (Fisheries and Oceans, Oct 2017).",
    }
    return records, notes


def main(argv: list[str] | None = None) -> int:
    records, notes = build()
    c.write_source_json(OUT_PATH, source=SOURCE, title="Staffed Canadian lightstations (curated)", url=SENATE["url"],
                        license_text=LICENSE, records=records, notes=notes, retrieved="2026-10-21")
    c.log(f"ca_staffed_lightstations: {notes['staffed']} staffed + {len(notes['destaffed_2024'])} destaffed in 2024; "
          f"{len(notes['rest_only_on_the_2010_list'])} rest only on the 2010 list; {len(notes['without_position'])} without a position")
    return 0


if __name__ == "__main__":
    sys.exit(main())
