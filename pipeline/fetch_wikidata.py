#!/usr/bin/env python3
"""Fetch the light stations, lightships and life-saving stations of the United States (its
territories included) and Canada from Wikidata, and write data/sources/wikidata.json
(DESIGN.md 3.1/3.2).

Wikidata is CC0. We read it through QLever's Wikidata SPARQL endpoint
(https://qlever.dev/api/wikidata, University of Freiburg), not the Wikidata Query Service:
query.wikidata.org's robots.txt disallows /sparql for every agent and Fresnel honours robots.txt
(DESIGN.md section 2, "Endpoint rulings"); qlever.dev has no robots.txt. QLever needs explicit
PREFIX lines and has no label SERVICE, so labels are read with rdfs:label. Every request uses our
User-Agent, at most one every 2 s, with backoff on 429/5xx, and every answer is cached under
RAW_ROOT/wikidata/ so a re-run asks nothing again.

Selection (each a small query; every class and property id below was checked against the live
service on 2026-10-21, and again on QLever):

- lighthouses: instance of lighthouse (Q39715) or any subclass (P31/P279*): leading lights
  Q1930418, Integral Lighthouse Q3278565, screw-pile Q7439086, caisson Q5017835, sparkplug
  Q7573695, crib Q55608558, Texas Tower Q7708181, skeletal tower Q7534372, wooden lighthouse
  Q66088335, inactive lighthouse Q111363199, lower/upper light Q33129345/Q33129347, faux
  lighthouse Q33185258, aerial lighthouse Q4688013 ...; and light station Q27193297, which is not
  a subclass of lighthouse.
- lightships: lightvessel Q831515 (the surviving vessels, at their berths) and lightvessel
  station Q109662605 (a place where lightships were moored).
- life-saving stations: lifeboat station Q11997323 (Wikidata's class for the US Life-Saving
  Service stations), coast guard station Q31407679 only when the item is on a heritage register
  (P649 or P1435: the historic Coast Guard stations that inherited the Life-Saving Service's;
  never air stations), and any NRHP-listed item (P649) whose English label says Life-Saving /
  Lifesaving / Life Saving Station, Lifeboat Station, House of Refuge or Coast Guard Station /
  Boathouse.
- countries: country (P17) the United States Q30, Canada Q16, or one of the territories' own
  items (Puerto Rico Q1183, US Virgin Islands Q11703, Guam Q16635, Northern Mariana Islands
  Q16644, American Samoa Q16641, US Minor Outlying Islands Q16645), or located (P131*) in a
  territory.

Fields (one small query per property over all the selected items, so no query multiplies
rows; QLever times out on one query with many OPTIONAL value-node patterns): English label (French label too, the name for a Quebec item that has no
English one), aliases, coordinates (P625, with their precision), instance-of classes (P31),
located in (P131, followed up to four levels for the region code P300 and the county),
inception (P571), service entry (P729, first lit), service retirement (P730, deactivated),
dissolved/abolished/demolished (P576), state of use (P5817), height (P2048), focal height
(P2923), elevation (P2044), light characteristic (P1030), lighthouse range (P2929, with its
colour qualifier P462), NRHP reference number (P649), ARLHS lighthouse ID (P2980), USCG
lighthouse ID (P3723: the Light List number, "volume-number"), Canadian Coastguard Lighthouse ID
(P3920: the List of Lights number), NGA lighthouse ID (P3563), Canadian Register of Historic
Places ID (P477), Heritage Lighthouse of Canada ID (P3211), Federal Heritage Buildings ID
(P3197), Nova Scotia (P909) and PEI (P763) registers, heritage designation (P1435, with start
time P580), Lighthouse Directory page (P11627), image (P18), Commons category (P373), official
website (P856), made from material (P186), operator (P137), owned by (P127), architectural
style (P149), replaces / replaced by (P1365 / P1366), significant event (P793: automatization,
relocation, demolition..., with point in time P585), and the English and French Wikipedia
articles.

Quantities go through p:/psv: to read the unit: on 2026-10-21 height was in metres on 750
lighthouse items and in feet on 78, focal height in metres on 806 and feet on 60, range in
nautical miles on 696, statute miles on 9 and kilometres on 1. wdt: would silently drop the
unit. Anything in a unit not listed in UNIT_* is left unconverted (kept in extra).

Usage: python3 pipeline/fetch_wikidata.py [--refresh]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import regions  # noqa: E402

SPARQL_URL = "https://qlever.dev/api/wikidata"
OUT_PATH = c.REPO / "data" / "sources" / "wikidata.json"
WD = "http://www.wikidata.org/entity/"

COUNTRY_VALUES = "wd:Q30 wd:Q16 wd:Q1183 wd:Q11703 wd:Q16635 wd:Q16644 wd:Q16641 wd:Q16645"
TERRITORY_VALUES = "wd:Q1183 wd:Q11703 wd:Q16635 wd:Q16644 wd:Q16641 wd:Q16645"

# ---------------------------------------------------------------------------------------------
# Classes (Q ids) and what they mean for Fresnel
# ---------------------------------------------------------------------------------------------

Q_LIGHTHOUSE = "Q39715"
Q_LIGHT_STATION = "Q27193297"
Q_LIGHTVESSEL = "Q831515"
Q_LIGHTVESSEL_STATION = "Q109662605"
Q_LIFEBOAT_STATION = "Q11997323"
Q_COAST_GUARD_STATION = "Q31407679"

# Classes that are out of scope: the record is kept in the extract with the reason, and the
# merge hides any station that only such records describe (DESIGN.md section 1, Scope).
OUT_OF_SCOPE_CLASSES = {
    "Q33185258": "Decorative: Wikidata classes it as a faux lighthouse, never an aid to navigation",
    "Q4688013": "An aviation beacon (aerial lighthouse), not a marine light",
    "Q109851549": "A firing-range warning beacon, not a light station",
    "Q22681801": "A beacon, not a light station",
}
# Classes that say what the structure is (DESIGN.md 3.4 structures[].type).
STRUCTURE_TYPE_CLASSES = {
    "Q7439086": "screwpile", "Q7193855": "screwpile", "Q5017835": "caisson", "Q7573695": "caisson",
    "Q55608558": "crib", "Q7708181": "texas_tower", "Q7534372": "skeletal", "Q3278565": "integral",
    "Q66088335": "wood_frame",
}
OFFSHORE_TYPES = {"screwpile", "caisson", "crib", "texas_tower"}
# Classes that say the item is a whole station (several buildings), not one structure.
STATION_LEVEL_CLASSES = {
    Q_LIGHT_STATION, "Q15243209", "Q20856087", "Q1081138", "Q358", "Q1497375", "Q18247357",
}
# Multiple Property Submissions and Thematic Resources: NRHP covers for a group of listings
# ("Light Stations of Maine MPS"), not places.
MPS_COVER_RE = re.compile(r"\b(MPS|MPDF|MRA|TR)$")
RANGE_CLASSES = {"Q1930418", "Q43266387", "Q33129345", "Q33129347", "Q66350506"}
FRONT_CLASSES = {"Q33129345"}   # lower light: the front of a range
REAR_CLASSES = {"Q33129347"}    # upper light: the rear
LOST_CLASSES = {
    "Q19860854": "Wikidata classes it as a destroyed building or structure",
    "Q15893266": "Wikidata classes it as a former entity",
    "Q24410914": "Wikidata classes it as a demolished building or structure",
}
RUINS_CLASSES = {"Q109607": "Wikidata classes it as ruins"}
REPLICA_CLASSES = {"Q1232589": "Wikidata classes it as a replica"}
INACTIVE_CLASSES = {"Q111363199": "Wikidata classes it as an inactive lighthouse"}
DWELLING_CLASSES = {"Q108840273"}  # lighthouse keeper's house
# P5817 state of use
STATE_OF_USE = {
    "Q63065035": ("inactive", "Wikidata state of use: abandoned"),
    "Q55654238": ("active", "Wikidata state of use: in use"),
    "Q55653430": ("inactive", "Wikidata state of use: out of use"),
    "Q56556915": ("lost", "Wikidata state of use: demolished or destroyed"),
    "Q30108381": ("ruins", "Wikidata state of use: ruins"),
}
# P793 significant events
EVENT_ITEMS = {
    "Q24410992": "automated", "Q30184664": "automated", "Q2918584": "relocated", "Q826949": "relocated",
    "Q331483": "removed", "Q19828398": "deactivated", "Q29933838": "deactivated", "Q19828403": "first_lit",
    "Q29933828": "first_lit", "Q385378": "built", "Q3875186": "built", "Q52385658": "rebuilt",
    "Q106334491": "modified", "Q105979665": "restored", "Q111422874": "damaged", "Q168983": "burned",
    "Q1076056": "modified",
}
EVENT_NOTES = {"Q1076056": "Electrified.", "Q105979665": "Repainted.", "Q30184664": "Keepers withdrawn."}
# P186 material
MATERIALS = {
    "Q1370714": "wood", "Q287": "wood", "Q40089": "brick", "Q22657": "concrete", "Q184190": "concrete",
    "Q22731": "stone", "Q3115353": "stone", "Q41177": "stone", "Q23757": "stone", "Q665231": "stone",
    "Q1402843": "stone", "Q272999": "stone", "Q1225329": "stone", "Q43338": "stone", "Q13085": "stone",
    "Q483269": "cast_iron", "Q677": "iron", "Q860451": "iron", "Q11427": "steel", "Q172587": "steel",
    "Q11426": "steel", "Q17310244": "aluminium", "Q663": "aluminium", "Q5861": "fiberglass",
    "Q7224880": "fiberglass", "Q7672986": "tabby",
}
# Units
UNIT_M = {WD + "Q11573": 1.0, WD + "Q3710": 0.3048, WD + "Q828224": 1000.0, WD + "Q174728": 0.01}
UNIT_NM = {WD + "Q93318": 1.0, WD + "Q253276": 1609.344 / 1852.0, WD + "Q828224": 1000.0 / 1852.0}
COLOURS = {"Q23444": "W", "Q3142": "R", "Q3133": "G", "Q943": "Y", "Q1088": "B"}
# P1435 designations already given as a register number elsewhere (the number wins).
DESIGNATION_COVERED = {
    "Q19558910": "P649", "Q1129142": "P649",            # NRHP listed / contributing
    "Q15641550": "P3211",                                # heritage lighthouse (Canada)
    "Q14451490": "P3197", "Q14480054": "P3197",          # recognized / classified federal heritage building
}
CA_DESIGNATIONS = {"Q15641550", "Q14451490", "Q14480054", "Q1568567", "Q14500239", "Q13790797",
                   "Q14897292", "Q15080599", "Q14916934", "Q22871013", "Q14916935", "Q13789518",
                   "Q57584209", "Q57584014", "Q14452577", "Q14331266", "Q22955890", "Q60042864",
                   "Q14943752", "Q26989049"}
NRHP_DESIGNATIONS = {"Q19558910", "Q1129142"}

# Operators/owners that settle `ownership` (DESIGN.md 3.4), by label words.
OWNERSHIP_WORDS = [
    (re.compile(r"\b(United States Coast Guard|US Coast Guard|U\.S\. Coast Guard|National Park Service|"
                r"Bureau of Land Management|Fish and Wildlife Service|United States Navy|U\.S\. Navy|"
                r"General Services Administration|Canadian Coast Guard|Fisheries and Oceans|Parks Canada|"
                r"Transport Canada|Department of National Defence|Government of Canada|United States Army)\b", re.I), "federal"),
    (re.compile(r"\b(State Park|Department of Natural Resources|State of \w+|Commonwealth of)\b", re.I), "state"),
    (re.compile(r"\b(Provincial|Province of)\b", re.I), "provincial"),
    (re.compile(r"\b(Town of|City of|County of|Village of|Township|Municipality|Borough of|Port Authority)\b", re.I), "local"),
    (re.compile(r"\b(Society|Association|Friends of|Preservation|Foundation|Trust|Conservancy|Keepers|Museum|Historical)\b", re.I), "nonprofit"),
]

# County-level units, by the class labels of a P131 place.
US_COUNTY_CLASS_RE = re.compile(
    r"county of |\bcounty of the United States|parish of Louisiana|borough of Alaska|census area|"
    r"municipality of Puerto Rico|municipio|district of the United States Virgin Islands|"
    r"district of American Samoa|municipality of the Northern Mariana Islands|village of Guam|"
    r"independent city|consolidated city-county|unified municipality|city and borough", re.I)
CA_UNIT_CLASS_RE = re.compile(
    r"census division|regional county municipality|regional district|county of (Nova Scotia|New Brunswick|"
    r"Prince Edward Island|Ontario)|district of Ontario|regional municipality|united counties|"
    r"county municipality|municipal district|territorial equivalent|equivalent territory", re.I)
COUNTY_SUFFIX_RE = re.compile(r"\s+(County|Parish|Borough|Census Area)$")

LSS_LABEL_RE = re.compile(r"life[- ]?saving|lifeboat station|house of refuge|coast guard (station|boathouse)", re.I)

# ---------------------------------------------------------------------------------------------
# SPARQL (QLever's Wikidata endpoint; DESIGN.md section 2, "Endpoint rulings")
# ---------------------------------------------------------------------------------------------

PREFIXES = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX psv: <http://www.wikidata.org/prop/statement/value/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
"""


def run_query(name: str, query: str, refresh: bool = False) -> list[dict]:
    """One SPARQL query, cached by its text under RAW_ROOT/wikidata/."""
    query = PREFIXES + query
    path = c.raw_dir("wikidata") / f"{name}_{c.cache_key(query)}.json"
    if not path.exists() or refresh:
        c.log(f"wikidata: query {name}")
        body = urllib.parse.urlencode({"query": query}).encode()
        c.fetch_cached(SPARQL_URL, path, data=body, timeout=300, force=refresh, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        })
    return read_sparql_json(path)


def read_sparql_json(path: Path) -> list[dict]:
    """The bindings of a cached SPARQL JSON answer. QLever sometimes sends its whole answer a
    second time, headers and all, after the first (seen 2026-10-21 on large results): the
    first complete JSON document is the answer, and the cache file is trimmed to it."""
    text = path.read_text(encoding="utf-8")
    data, end = json.JSONDecoder().raw_decode(text.lstrip())
    if text.lstrip()[end:].strip():
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    if "results" not in data:
        raise c.FetchError(f"not a SPARQL answer: {path}")
    return data["results"]["bindings"]


def v(row: dict, key: str) -> str | None:
    x = row.get(key, {}).get("value")
    return x if x not in (None, "") else None


def qid(uri: str | None) -> str | None:
    if not uri:
        return None
    return uri.rsplit("/", 1)[-1] if uri.startswith(WD) else None


SELECTIONS = {
    "sel_lighthouse_country": """
SELECT DISTINCT ?item WHERE {
  VALUES ?country { %s }
  ?item wdt:P31/wdt:P279* wd:Q39715 .
  ?item wdt:P17 ?country .
}""" % COUNTRY_VALUES,
    "sel_lighthouse_territory": """
SELECT DISTINCT ?item WHERE {
  VALUES ?t { %s }
  ?item wdt:P31/wdt:P279* wd:Q39715 .
  ?item wdt:P131+ ?t .
}""" % TERRITORY_VALUES,
    **{name: """
SELECT DISTINCT ?item WHERE {
  VALUES ?country { %s }
  ?item wdt:P31/wdt:P279* wd:%s .
  ?item wdt:P17 ?country .
}""" % (COUNTRY_VALUES, cls) for name, cls in (
        ("sel_light_station", Q_LIGHT_STATION), ("sel_lightvessel", Q_LIGHTVESSEL),
        ("sel_lightvessel_station", Q_LIGHTVESSEL_STATION), ("sel_lifeboat_station", Q_LIFEBOAT_STATION))},
    "sel_coast_guard_station": """
SELECT DISTINCT ?item WHERE {
  VALUES ?country { %s }
  ?item wdt:P31/wdt:P279* wd:Q31407679 .
  ?item wdt:P17 ?country .
  ?item wdt:P649 ?nrhp .
}""" % COUNTRY_VALUES,
    "sel_coast_guard_station_designated": """
SELECT DISTINCT ?item WHERE {
  VALUES ?country { %s }
  ?item wdt:P31/wdt:P279* wd:Q31407679 .
  ?item wdt:P17 ?country .
  ?item wdt:P1435 ?designation .
}""" % COUNTRY_VALUES,
    "sel_lss_label": """
SELECT DISTINCT ?item WHERE {
  ?item wdt:P649 ?n .
  ?item rdfs:label ?l . FILTER(LANG(?l)="en")
  FILTER(REGEX(?l, "life.?saving|lifeboat station|house of refuge|coast guard (station|boathouse)", "i"))
}""",
}

# One small query per property over every selected item (VALUES), each a plain required
# pattern: QLever answers these in a second or two, where one query with many OPTIONALs times
# out. name -> (pattern binding ?item and ?val, extra variables).
PROPERTY_QUERIES: dict[str, str] = {
    "en": '?item rdfs:label ?val . FILTER(LANG(?val)="en")',
    "fr": '?item rdfs:label ?val . FILTER(LANG(?val)="fr")',
    "es": '?item rdfs:label ?val . FILTER(LANG(?val)="es")',
    "aliases": '?item skos:altLabel ?val . FILTER(LANG(?val)="en")',
    "coords": "?item wdt:P625 ?val .",
    "countries": "?item wdt:P17 ?val .",
    "classes": "?item wdt:P31 ?val .",
    "inceptions": "?item wdt:P571 ?val .",
    "entries": "?item wdt:P729 ?val .",
    "retirements": "?item wdt:P730 ?val .",
    "dissolved": "?item wdt:P576 ?val .",
    "uses": "?item wdt:P5817 ?val .",
    "chars": "?item wdt:P1030 ?val .",
    "arlhs": "?item wdt:P2980 ?val .",
    "uscg": "?item wdt:P3723 ?val .",
    "ccg": "?item wdt:P3920 ?val .",
    "nga": "?item wdt:P3563 ?val .",
    "crhp": "?item wdt:P477 ?val .",
    "hl": "?item wdt:P3211 ?val .",
    "fhbro": "?item wdt:P3197 ?val .",
    "nsr": "?item wdt:P909 ?val .",
    "pei": "?item wdt:P763 ?val .",
    "ld": "?item wdt:P11627 ?val .",
    "nrhp": "?item wdt:P649 ?val .",
    "images": "?item wdt:P18 ?val .",
    "commonscat": "?item wdt:P373 ?val .",
    "website": "?item wdt:P856 ?val .",
    "replaces": "?item wdt:P1365 ?val .",
    "replacedBy": "?item wdt:P1366 ?val .",
    "materials": "?item wdt:P186 ?val .",
    "operator_items": "?item wdt:P137 ?val .",
    "owner_items": "?item wdt:P127 ?val .",
    "enwiki": "?val schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> .",
    "frwiki": "?val schema:about ?item ; schema:isPartOf <https://fr.wikipedia.org/> .",
    "eswiki": "?val schema:about ?item ; schema:isPartOf <https://es.wikipedia.org/> .",
    "admin1": "?item wdt:P131 ?val .",
}
# Statements with a qualifier: name -> pattern binding ?item, ?val and ?q.
QUALIFIED_QUERIES: dict[str, str] = {
    "designation_stmts": "?item p:P1435 ?s . ?s ps:P1435 ?val . OPTIONAL { ?s pq:P580 ?q . }",
    "event_stmts": "?item p:P793 ?s . ?s ps:P793 ?val . OPTIONAL { ?s pq:P585 ?q . }",
}
QUANTITY_PROPS = {"height": "P2048", "focal": "P2923", "range": "P2929", "elevation": "P2044"}


def values_clause(var: str, qids: list[str]) -> str:
    return "VALUES ?%s { %s }" % (var, " ".join(f"wd:{q}" for q in qids))


def select_items(refresh: bool) -> dict[str, set[str]]:
    """QID -> the selection groups that found it."""
    found: dict[str, set[str]] = {}
    for name, query in SELECTIONS.items():
        group = "lighthouse" if name.startswith("sel_lighthouse") else (
            "coast_guard_station" if name.startswith("sel_coast_guard") else name[4:])
        for row in run_query(name, query, refresh):
            q = qid(v(row, "item"))
            if q:
                found.setdefault(q, set()).add(group)
    return found


def labels_for(qids: set[str], refresh: bool, name: str) -> dict[str, str]:
    out: dict[str, str] = {}
    ordered = sorted(qids, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
    for i in range(0, len(ordered), 2000):
        part = ordered[i:i + 2000]
        query = "SELECT ?x ?l WHERE { %s ?x rdfs:label ?l . FILTER(LANG(?l)=\"en\") }" % values_clause("x", part)
        for row in run_query(f"{name}_{i // 2000:02d}", query, refresh):
            x = qid(v(row, "x"))
            if x and v(row, "l"):
                out[x] = v(row, "l")
    return out


def _b(value) -> dict:
    """A SPARQL-result-like binding, so the record builder reads every row one way."""
    return {"value": str(value)}


def fetch_details(qids: list[str], refresh: bool) -> dict[str, dict]:
    """QID -> {"vals": {name: [strings]}, "quantities": [rows], "admin": [rows]} (see build_record)."""
    out: dict[str, dict] = {q: {"vals": {}, "quantities": [], "admin": []} for q in qids}
    items = values_clause("item", qids)
    for name, pattern in PROPERTY_QUERIES.items():
        for row in run_query(f"p_{name}", "SELECT ?item ?val WHERE { %s %s }" % (items, pattern), refresh):
            q = qid(v(row, "item"))
            val = v(row, "val")
            if q in out and val is not None:
                out[q]["vals"].setdefault(name, []).append(val)
    qualified: dict[str, dict[str, list[tuple[str, str]]]] = {}
    for name, pattern in QUALIFIED_QUERIES.items():
        for row in run_query(f"q_{name}", "SELECT ?item ?val ?q WHERE { %s %s }" % (items, pattern), refresh):
            q = qid(v(row, "item"))
            if q in out and v(row, "val"):
                qualified.setdefault(q, {}).setdefault(name, []).append((v(row, "val"), v(row, "q") or ""))
    for prop, pid in QUANTITY_PROPS.items():
        query = ("SELECT ?item ?amount ?unit ?colour WHERE { %s ?item p:%s ?st . ?st psv:%s ?qv . "
                 "?qv wikibase:quantityAmount ?amount . ?qv wikibase:quantityUnit ?unit . "
                 "OPTIONAL { ?st pq:P462 ?colour . } }") % (items, pid, pid)
        for row in run_query(f"qty_{prop}", query, refresh):
            q = qid(v(row, "item"))
            if q in out:
                row = dict(row)
                row["prop"] = _b(prop)
                out[q]["quantities"].append(row)

    # The P131 chain, level by level (QLever has no trouble with it, but walking it here keeps
    # the depth, so the county is the nearest county-level place).
    parents: dict[str, set[str]] = {}
    level = {q: set(out[q]["vals"].get("admin1", [])) for q in qids}
    frontier = {qid(a) for s in level.values() for a in s} - {None}
    seen: set[str] = set()
    for depth in range(1, 5):
        frontier -= seen
        if not frontier:
            break
        seen |= frontier
        if depth < 4:
            query = "SELECT ?a ?p WHERE { %s ?a wdt:P131 ?p . }" % values_clause("a", sorted(frontier))
            nxt: set[str] = set()
            for row in run_query(f"admin_parents_{depth}", query, refresh):
                a, p_ = qid(v(row, "a")), qid(v(row, "p"))
                if a and p_:
                    parents.setdefault(a, set()).add(p_)
                    nxt.add(p_)
            frontier = nxt
    admin_items = sorted(seen)
    iso: dict[str, str] = {}
    classes: dict[str, set[str]] = {}
    for i in range(0, len(admin_items), 2000):
        part = admin_items[i:i + 2000]
        for row in run_query(f"admin_iso_{i // 2000:02d}", "SELECT ?a ?iso WHERE { %s ?a wdt:P300 ?iso . }" % values_clause("a", part), refresh):
            if qid(v(row, "a")) and v(row, "iso"):
                iso.setdefault(qid(v(row, "a")), v(row, "iso"))
        for row in run_query(f"admin_class_{i // 2000:02d}", "SELECT ?a ?cls WHERE { %s ?a wdt:P31 ?cls . }" % values_clause("a", part), refresh):
            if qid(v(row, "a")) and qid(v(row, "cls")):
                classes.setdefault(qid(v(row, "a")), set()).add(qid(v(row, "cls")))

    # English labels for every item the records name: classes, designations, events, operators,
    # owners, states of use, admin places and their classes.
    wanted: set[str] = set(admin_items) | {x for s in classes.values() for x in s}
    for q in qids:
        for name in ("classes", "uses", "operator_items", "owner_items"):
            wanted |= {qid(x) for x in out[q]["vals"].get(name, []) if qid(x)}
        for stmts in qualified.get(q, {}).values():
            wanted |= {qid(x) for x, _ in stmts if qid(x)}
    labels = labels_for(wanted, refresh, "labels")

    for q in qids:
        vals = out[q]["vals"]
        vals["classes"] = [f"{x}={labels.get(qid(x) or '', '')}" for x in vals.get("classes", [])]
        vals["operators"] = [labels[qid(x)] for x in vals.get("operator_items", []) if qid(x) in labels]
        vals["owners"] = [labels[qid(x)] for x in vals.get("owner_items", []) if qid(x) in labels]
        vals["coords"] = [s for s in (wkt_to_coord(x) for x in vals.get("coords", [])) if s]
        vals["dissolved"] = [x if parse_year(x) else "somevalue" for x in vals.get("dissolved", [])]
        vals["designations"] = [f"{x}={labels.get(qid(x) or '', '')}={t}" for x, t in qualified.get(q, {}).get("designation_stmts", [])]
        vals["events"] = [f"{x}={labels.get(qid(x) or '', '')}={t}" for x, t in qualified.get(q, {}).get("event_stmts", [])]
        # The chain, nearest first, as rows the region and county reader takes.
        rows = []
        frontier_q = {qid(x) for x in vals.get("admin1", []) if qid(x)}
        visited: set[str] = set()
        for depth in range(1, 5):
            for a in sorted(frontier_q - visited):
                rows.append({"depth": _b(depth), "a": _b(WD + a),
                             "aLabel": _b(labels.get(a, "")) if labels.get(a) else {},
                             "iso": _b(iso[a]) if a in iso else {},
                             "cls": _b("|".join(sorted(labels.get(x, "") for x in classes.get(a, set()))))})
            visited |= frontier_q
            frontier_q = {p_ for a in frontier_q for p_ in parents.get(a, set())}
        out[q]["admin"] = rows
    return out


def wkt_to_coord(wkt: str) -> str | None:
    """"POINT(-70.207778 43.623056)" -> "43.623056 -70.207778 - NormalRank -" (parse_coords)."""
    m = re.match(r"^\s*point\s*\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\)\s*$", wkt, re.I)
    if not m:
        return None
    return f"{m.group(2)} {m.group(1)} - NormalRank -"

# ---------------------------------------------------------------------------------------------
# Parsing helpers (unit-tested in test_fetchers.py)
# ---------------------------------------------------------------------------------------------


def parse_year(dt: str | None) -> int | None:
    """"1872-01-01T00:00:00Z" -> 1872. Years before 1500 or unknown values -> None."""
    if not dt:
        return None
    m = re.match(r"^\+?(-?)(\d{1,4})-", dt)
    if not m or m.group(1):
        return None
    y = int(m.group(2))
    return y if 1500 <= y <= 2100 else None


def min_year(values: list[str]) -> int | None:
    years = [y for y in (parse_year(x) for x in values) if y]
    return min(years) if years else None


def max_year(values: list[str]) -> int | None:
    years = [y for y in (parse_year(x) for x in values) if y]
    return max(years) if years else None


def parse_coords(values: list[str]) -> list[dict]:
    """Each "lat lon precision rank part" string -> {lat, lon, prec, rank, part}; preferred first."""
    out = []
    for s in values:
        parts = s.split(" ")
        if len(parts) < 5:
            continue
        try:
            lat, lon = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        prec = None if parts[2] == "-" else float(parts[2])
        out.append({"lat": lat, "lon": lon, "prec": prec, "rank": parts[3],
                    "part": None if parts[4] == "-" else parts[4]})
    out.sort(key=lambda x: (x["rank"] != "PreferredRank", x["lat"], x["lon"]))
    return out


def quantity(rows: list[dict], prop: str, units: dict[str, float]) -> tuple[float | None, list[dict]]:
    """(the converted value, every value seen with its unit and colour). The value is the
    largest converted amount (a light's white range is its longest)."""
    seen = []
    best = None
    for row in rows:
        if v(row, "prop") != prop:
            continue
        try:
            amount = float(v(row, "amount") or "")
        except ValueError:
            continue
        unit = v(row, "unit")
        colour = COLOURS.get(qid(v(row, "colour")) or "", None)
        factor = units.get(unit or "")
        conv = round(amount * factor, 2) if factor is not None else None
        seen.append({"amount": amount, "unit": qid(unit) if unit else None, "colour": colour, "value": conv})
        if conv is not None and (best is None or conv > best):
            best = conv
    seen.sort(key=lambda x: (x["value"] is None, -(x["value"] or 0), x["colour"] or ""))
    return best, seen


def name_role(name: str) -> str | None:
    """"Grosse Ile Range Front Light" -> "front_range"; "... Rear Range Light" -> "rear_range"."""
    n = name.lower()
    if re.search(r"\brange\b", n) or re.search(r"\b(front|rear)\s+(range\s+)?light", n):
        if re.search(r"\bfront\b", n) and not re.search(r"\brear\b", n):
            return "front_range"
        if re.search(r"\brear\b", n) and not re.search(r"\bfront\b", n):
            return "rear_range"
    return None


def name_kind(name: str) -> str | None:
    """The kind a name alone says, or None: range, pier/breakwater, lightship, life-saving."""
    n = name.lower()
    if LSS_LABEL_RE.search(n):
        return "life_saving_station"
    if re.search(r"\blight ?(ship|vessel)\b|\blv[- ]?\d+\b|\bwal[- ]?\d+\b", n):
        return "lightship"
    if re.search(r"\brange\b", n) and re.search(r"\blights?\b|\bfront\b|\brear\b|\bbeacon\b", n):
        return "range_lights"
    if re.search(r"\b(pier ?head|pier|breakwater|jetty|mole)\b", n):
        return "pier_light"
    return None


def ownership_of(labels: list[str]) -> str | None:
    for label in labels:
        for rx, value in OWNERSHIP_WORDS:
            if rx.search(label):
                return value
    return None


def commons_photo(image_uri: str) -> dict | None:
    if "Special:FilePath/" not in image_uri:
        return None
    fname = urllib.parse.unquote(image_uri.split("Special:FilePath/", 1)[1])
    quoted = urllib.parse.quote(fname.replace(" ", "_"))
    return {
        "url": f"https://commons.wikimedia.org/wiki/Special:FilePath/{quoted}",
        "thumb_url": f"https://commons.wikimedia.org/wiki/Special:FilePath/{quoted}?width=640",
        "source_url": f"https://commons.wikimedia.org/wiki/File:{quoted}",
        "credit": "Wikimedia Commons",
        "license": None,
        "caption": None,
        "year": None,
    }


def region_and_county(admin_rows: list[dict], country: str) -> tuple[str | None, str | None, list[str]]:
    """(region code from a P300 ISO 3166-2 code or a territory item up the P131 chain, the
    nearest county-level place's label, the P131 labels seen)."""
    region = None
    best_depth = 99
    county = None
    county_depth = 99
    labels = []
    for row in sorted(admin_rows, key=lambda r: (int(v(r, "depth") or 9), v(r, "a") or "")):
        depth = int(v(row, "depth") or 9)
        a = qid(v(row, "a"))
        label = v(row, "aLabel")
        if label and depth == 1:
            labels.append(label)
        iso = v(row, "iso")
        code = None
        if a in regions.WIKIDATA_REGION_ITEMS:
            code = regions.WIKIDATA_REGION_ITEMS[a]
        elif iso and re.fullmatch(r"(US|CA)-[A-Z]{2}", iso):
            code = regions.parse_region(iso)
        if code and regions.country_of(code) == country and depth < best_depth:
            region, best_depth = code, depth
        cls = v(row, "cls") or ""
        rx = US_COUNTY_CLASS_RE if country == "US" else CA_UNIT_CLASS_RE
        if label and depth < county_depth and rx.search(cls) and not code:
            county, county_depth = label, depth
    if county and country == "US":
        county = COUNTY_SUFFIX_RE.sub("", county)
        county = re.sub(r",\s*(Puerto Rico|U\.S\. Virgin Islands|Guam)$", "", county)
        county = re.sub(r"^Municipality of\s+", "", county)
    return region, county, labels


# ---------------------------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------------------------

def build_record(q: str, groups: set[str], d: dict, lookup) -> tuple[dict | None, str | None]:
    """(source record, None) or (None, the reason it was skipped)."""
    vals_ = d["vals"]

    def vals(name: str) -> list[str]:
        return list(vals_.get(name, []))

    def first(name: str) -> str | None:
        x = sorted(vals_.get(name, []))
        return x[0] if x else None

    coords = parse_coords(vals("coords"))
    if not coords:
        return None, "no_coordinates"
    countries = {regions.WIKIDATA_COUNTRY_ITEMS.get(qid(x) or "") for x in vals("countries")} - {None}
    classes: dict[str, str] = {}
    for item in vals("classes"):
        uri, _, label = item.partition("=")
        if qid(uri):
            classes[qid(uri)] = label
    admin_country = None
    for row in d["admin"]:
        iso = v(row, "iso") or ""
        a = qid(v(row, "a"))
        if a in regions.WIKIDATA_REGION_ITEMS or iso.startswith("US-"):
            admin_country = admin_country or "US"
        elif iso.startswith("CA-"):
            admin_country = admin_country or "CA"
    if len(countries) == 1:
        country = countries.pop()
    elif admin_country:
        country = admin_country
    else:
        return None, "no_country"

    if MPS_COVER_RE.search(first("en") or ""):
        return None, "nrhp_cover_document"
    pos = coords[0]
    lat, lon = pos["lat"], pos["lon"]
    region, county, p131_labels = region_and_county(d["admin"], country)
    region_from = "wikidata_p131"
    if not region:
        region, how, _km = lookup.lookup(lat, lon, country)
        region_from = f"boundaries_{how}" if region else None
    if not region:
        return None, "no_region"
    if not regions.in_region_box(region, lat, lon):
        # A P131 region whose box does not hold the point: trust the point's region instead.
        alt, how, _km = lookup.lookup(lat, lon, country)
        if alt and alt != region:
            region, region_from = alt, f"boundaries_{how}_over_p131"

    en, fr, es = first("en"), first("fr"), first("es")
    name = en or fr or es or q
    other_names = []
    for alt in [fr if en else None, es if (en or fr) else None, *vals("aliases")]:
        if alt and alt != name and alt not in other_names:
            other_names.append(alt)

    # What kind of station, and what part of one.
    kind = "lighthouse"
    if "lightvessel" in groups or Q_LIGHTVESSEL in classes:
        kind = "lightship"
    elif "lightvessel_station" in groups or Q_LIGHTVESSEL_STATION in classes:
        kind = "lightship_station"
    elif groups & {"lifeboat_station", "coast_guard_station", "lss_label"} and "lighthouse" not in groups:
        kind = "life_saving_station"
    elif RANGE_CLASSES & set(classes):
        kind = "range_lights"
    by_name = name_kind(name)
    if kind == "lighthouse" and by_name in ("range_lights", "pier_light", "life_saving_station", "lightship"):
        if by_name in ("range_lights", "pier_light"):
            kind = by_name
        elif by_name == "life_saving_station" and "lighthouse" not in groups:
            kind = by_name
    role = None
    if FRONT_CLASSES & set(classes):
        role = "front_range"
    elif REAR_CLASSES & set(classes):
        role = "rear_range"
    elif kind == "range_lights":
        role = name_role(name)
    elif DWELLING_CLASSES & set(classes) and not (set(classes) - DWELLING_CLASSES - {"Q3947"}):
        role = "dwelling"
    station_level = bool(STATION_LEVEL_CLASSES & set(classes)) or bool(
        re.search(r"\blight ?station\b|\blights\b|\blighthouses\b", name, re.I) and kind != "range_lights")

    # Dates
    built = min_year(vals("inceptions"))
    first_lit = min_year(vals("entries"))
    retired = max_year(vals("retirements"))
    dissolved_vals = vals("dissolved")
    dissolved = max_year(dissolved_vals)

    # Status claim (station status vocabulary), with the words that support it.
    status, status_raw = None, None
    for cq, why in LOST_CLASSES.items():
        if cq in classes:
            status, status_raw = "lost", why
    for cq, why in RUINS_CLASSES.items():
        if cq in classes and not status:
            status, status_raw = "ruins", why
    for cq, why in REPLICA_CLASSES.items():
        if cq in classes and not status:
            status, status_raw = "replica", why
    for use in vals("uses"):
        s, why = STATE_OF_USE.get(qid(use) or "", (None, None))
        if s and not status:
            status, status_raw = s, why
    for cq, why in INACTIVE_CLASSES.items():
        if cq in classes and not status:
            status, status_raw = "inactive", why
    if not status and retired and not (first_lit and first_lit > retired):
        status, status_raw = "inactive", f"Wikidata service retirement (P730): {retired}"
    if not status and dissolved_vals:
        # P576 "dissolved, abolished or demolished" does not say which: no status claim, but the
        # date is kept as an event with that caveat (merge lists these for review).
        status_raw = (f"Wikidata end date (P576): {dissolved or 'unknown value'}; it does not say whether "
                      "the light was discontinued or the structure demolished")

    out_of_scope = next((why for cq, why in OUT_OF_SCOPE_CLASSES.items() if cq in classes), None)

    # Structure
    struct_type = next((t for cq, t in STRUCTURE_TYPE_CLASSES.items() if cq in classes), None)
    mats = sorted({MATERIALS[qid(m)] for m in vals("materials") if qid(m) in MATERIALS})
    material = mats[0] if len(mats) == 1 else ("mixed" if len(mats) > 1 else None)
    if struct_type is None and material in ("brick", "stone") and kind in ("lighthouse", "range_lights", "pier_light"):
        struct_type = "conical_masonry" if role not in ("dwelling",) else None
    elif struct_type is None and material == "cast_iron":
        struct_type = "cast_iron"
    elif struct_type is None and material == "concrete" and kind != "life_saving_station":
        struct_type = "concrete"
    qrows = d["quantities"]
    height_m, heights = quantity(qrows, "height", UNIT_M)
    focal_m, focals = quantity(qrows, "focal", UNIT_M)
    range_nm, ranges = quantity(qrows, "range", UNIT_NM)
    elev_m, _elevs = quantity(qrows, "elevation", UNIT_M)

    chars = vals("chars")
    characteristic = chars[0].strip() if chars else None
    if characteristic is not None and not characteristic:
        characteristic = None

    # Registers and numbers
    registers = []
    for n in sorted(set(vals("nrhp"))):
        registers.append({"register": "NRHP", "number": n, "url": f"https://npgallery.nps.gov/AssetDetail/NRIS/{n}"})
    for n in sorted(set(vals("crhp"))):
        registers.append({"register": "Canadian Register of Historic Places", "number": n,
                          "url": f"https://www.historicplaces.ca/en/rep-reg/place-lieu.aspx?id={n}"})
    for n in sorted(set(vals("hl"))):
        registers.append({"register": "Heritage Lighthouse (Canada)", "number": n,
                          "url": f"https://www.pc.gc.ca/apps/dfhd/page_hl_eng.aspx?id={n}"})
    for n in sorted(set(vals("fhbro"))):
        registers.append({"register": "Federal Heritage Building (Canada)", "number": n,
                          "url": f"https://www.pc.gc.ca/apps/dfhd/page_fhbro_eng.aspx?id={n}"})
    for n in sorted(set(vals("nsr"))):
        registers.append({"register": "Nova Scotia Register of Historic Places", "number": n, "url": None})
    for n in sorted(set(vals("pei"))):
        registers.append({"register": "PEI Register of Historic Places", "number": n, "url": None})
    present = {"P649": bool(vals("nrhp")), "P3211": bool(vals("hl")), "P3197": bool(vals("fhbro"))}
    events = []
    for item in vals("designations"):
        uri, label, start = (item.split("=", 2) + ["", ""])[:3]
        dq = qid(uri) or ""
        year = parse_year(start)
        if dq in NRHP_DESIGNATIONS and year:
            events.append({"year": year, "event": "nrhp_listed", "note": None, "from": "wikidata"})
        elif dq in CA_DESIGNATIONS and year:
            events.append({"year": year, "event": "heritage_designated", "note": label or None, "from": "wikidata"})
        covered = DESIGNATION_COVERED.get(dq)
        if covered and present.get(covered):
            continue
        if label and not any(r["register"] == label for r in registers):
            registers.append({"register": label, "number": None, "url": None})
    aton = {
        "uscg_llnr": (vals("uscg") or [None])[0],
        "arlhs": (vals("arlhs") or [None])[0],
        "ccg_list_number": (vals("ccg") or [None])[0],
        "nga": (vals("nga") or [None])[0],
    }

    # Events
    if built:
        events.append({"year": built, "event": "built", "note": None, "from": "wikidata"})
    if first_lit:
        events.append({"year": first_lit, "event": "first_lit", "note": None, "from": "wikidata"})
    if retired:
        events.append({"year": retired, "event": "deactivated", "note": None, "from": "wikidata"})
    if dissolved and status == "lost":
        events.append({"year": dissolved, "event": "removed", "note": "Wikidata end date (P576).", "from": "wikidata"})
    elif dissolved:
        events.append({"year": dissolved, "event": "other",
                       "note": "Wikidata gives this as the end date, without saying whether the light was discontinued or the structure taken down.",
                       "from": "wikidata"})
    for item in vals("events"):
        uri, label, when = (item.split("=", 2) + ["", ""])[:3]
        ev = EVENT_ITEMS.get(qid(uri) or "")
        year = parse_year(when)
        if ev and year:
            events.append({"year": year, "event": ev, "note": EVENT_NOTES.get(qid(uri) or ""), "from": "wikidata"})
    events = sorted({(e["year"], e["event"]): e for e in events}.values(), key=lambda e: (e["year"], e["event"]))

    photos = [p for p in (commons_photo(u) for u in sorted(vals("images"))) if p]
    links = [{"label": "Wikidata", "url": f"https://www.wikidata.org/wiki/{q}", "kind": "wikidata"}]
    for key, label in (("enwiki", "Wikipedia"), ("frwiki", "Wikipédia (français)"), ("eswiki", "Wikipedia (español)")):
        if first(key):
            links.append({"label": label, "url": first(key), "kind": "wikipedia"})
    if first("commonscat"):
        cat = first("commonscat").replace(" ", "_")
        links.append({"label": "Wikimedia Commons category", "url": f"https://commons.wikimedia.org/wiki/Category:{urllib.parse.quote(cat)}", "kind": "commons"})
    if first("website"):
        links.append({"label": "Official website", "url": first("website"), "kind": "website"})
    for n in vals("arlhs")[:1]:
        links.append({"label": f"ARLHS World List of Lights {n}", "url": f"https://wlol.arlhs.com/lighthouse/{n}.html", "kind": "register"})
    for page in vals("ld")[:1]:
        links.append({"label": "Lighthouse Directory (Rowlett)", "url": f"https://www.ibiblio.org/lighthouse/{page}.htm", "kind": "reference"})

    operators = vals("operators")
    owners = vals("owners")
    agency = operators[0] if operators else (owners[0] if owners else None)
    ownership = ownership_of(owners) or ownership_of(operators)

    extra: dict = {"wikidata_qid": q, "selected_by": sorted(groups)}
    if classes:
        extra["wikidata_classes"] = [f"{k} {v_}" for k, v_ in sorted(classes.items())]
    if len(coords) > 1:
        extra["other_coordinates"] = [{"lat": x["lat"], "lon": x["lon"], "part": x["part"]} for x in coords[1:]]
    if pos["prec"] is not None:
        extra["coordinate_precision_deg"] = pos["prec"]
    if p131_labels:
        extra["located_in"] = p131_labels
    if region_from != "wikidata_p131":
        extra["region_from"] = region_from
    if len(heights) > 1 or any(h["value"] is None for h in heights):
        extra["heights"] = heights
    if len(focals) > 1 or any(h["value"] is None for h in focals):
        extra["focal_heights"] = focals
    if ranges:
        extra["ranges"] = ranges
    if len(chars) > 1:
        extra["characteristics"] = chars
    if elev_m is not None:
        extra["elevation_m"] = elev_m
    if station_level:
        extra["station_level"] = True
    if out_of_scope:
        extra["out_of_scope"] = out_of_scope
    if dissolved_vals:
        extra["p576"] = dissolved or "unknown value"
    if owners:
        extra["owners"] = owners
    if operators:
        extra["operators"] = operators

    relations = {}
    reps = sorted({f"wikidata:{qid(x)}" for x in vals("replaces") if qid(x)})
    rby = sorted({f"wikidata:{qid(x)}" for x in vals("replacedBy") if qid(x)})
    if reps:
        relations["replaces"] = reps
    if rby:
        relations["replaced_by"] = rby

    precision = "exact" if (pos["prec"] is None or pos["prec"] <= 0.002) else "approximate"
    rec = {
        "key": f"wikidata:{q}",
        "url": f"https://www.wikidata.org/wiki/{q}",
        "name": name,
        "other_names": other_names,
        "country": country,
        "region": region,
        "county": county,
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "precision": precision,
        "kind": kind,
        "kind_raw": "; ".join(f"{label or k}" for k, label in sorted(classes.items())) or None,
        "role": role,
        "status": status,
        "status_raw": status_raw,
        "structure": {
            "type": struct_type, "material": material, "built": built,
            "height_m": height_m, "status": {"lost": "lost", "ruins": "ruins"}.get(status or "", None),
        },
        "light": {
            "first_lit": first_lit, "deactivated": retired, "characteristic": characteristic,
            "focal_height_m": focal_m, "range_nm": range_nm, "fog_signal": None, "lens": None,
        },
        "setting": "offshore" if struct_type in OFFSHORE_TYPES else None,
        "registers": registers,
        "aton": aton,
        "agency": agency,
        "ownership": ownership,
        "events": events,
        "photos": photos,
        "links": links,
        "relations": relations,
        "extra": extra,
    }
    return rec, None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch Fresnel's Wikidata extract")
    ap.add_argument("--refresh", action="store_true", help="ignore the cache and query again")
    args = ap.parse_args(argv)

    found = select_items(args.refresh)
    c.log(f"wikidata: {len(found)} items selected: " + ", ".join(
        f"{g} {n}" for g, n in sorted(Counter(g for gs in found.values() for g in gs).items())))
    qids = sorted(found, key=lambda x: int(x[1:]))
    details = fetch_details(qids, args.refresh)
    lookup = regions.region_lookup(c.RAW_ROOT)
    records, skipped = [], Counter()
    skipped_items: dict[str, list[str]] = {}
    for q in qids:
        rec, why = build_record(q, found[q], details[q], lookup)
        if rec:
            records.append(rec)
        else:
            skipped[why] += 1
            skipped_items.setdefault(why, []).append(q)
    cache_files = sorted(c.raw_dir("wikidata").glob("*.json"))
    c.write_source_json(
        OUT_PATH, source="wikidata",
        title="Wikidata: lighthouses, light stations, lightships and life-saving stations of the United States and Canada",
        url=SPARQL_URL,
        license_text="CC0 1.0 (Wikidata). Images keep their own licences on Wikimedia Commons.",
        records=records,
        notes={"selected": len(found), "written": len(records), "skipped": dict(sorted(skipped.items())),
               "skipped_items": {k: v_[:200] for k, v_ in sorted(skipped_items.items())}},
        retrieved=c.retrieved_date(*cache_files),
    )
    by_country = Counter(r["country"] for r in records)
    by_kind = Counter(r["kind"] for r in records)
    by_status = Counter(r["status"] for r in records)
    c.log(f"wikidata: wrote {len(records)} records to {OUT_PATH}; skipped {dict(skipped)}")
    c.log(f"  country {dict(by_country)}; kind {dict(by_kind)}; status {dict(by_status)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
