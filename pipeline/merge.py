#!/usr/bin/env python3
"""Merge the source extracts (data/sources/*.json) into canonical station records
(data/stations/<dir>/<id>.json), as in Firefinder (DESIGN.md 3, "Merge").

Rules (the same as Firefinder's where they apply; DESIGN.md 3.5 has the full text):

- **Never deletes.** A station file keeps its id forever. A station whose records all vanish from
  the extracts is kept as it is. Two stations found to be one keep both ids: one is retired with
  `merged_into` and the site redirects its address.
- **Ids are permanent** (`<country>-<region>-<slug>`); new ones are numbered -2, -3 in a fixed
  order (region, slug, north to south, first key), so a run from scratch gives the same ids.
- **Memory.** Every source key a station holds (`sources[].key`, with the structure it describes
  in `sources[].part`) brings that record back to the same station and structure on the next run.
- **Locked fields** (`locked`, set by research or a human edit) are never overwritten.
- **Deterministic.** Sources in a fixed order, records by key, ties by position. Re-running with
  unchanged inputs writes nothing (a file is rewritten only when something other than `updated`
  changed).
- Writes `data/merge_report.json`: counts, matches, conflicts, and the lists a human should look
  at (range lights it could not pair, records it would not show, decorative suspects, possible
  duplicates).

**A station is the named light at a place** (DESIGN.md 3.2); its records are grouped into
*parts*, one per physical structure (successive towers, a front and a rear range light). Each
part becomes one entry of `structures`.

Matching, per source in SOURCE_ORDER (then any other source, alphabetically), records by key:

1. Memory (above).
2. An OpenStreetMap element's `wikidata=` tag: the station holding that Wikidata item, if it is
   within 10 km (a tag on something farther away is listed for review instead; Wikidata's
   coordinates for some offshore lights are kilometres out).
3. Place and name: a station of the same country and kind group within reach, best name first,
   then nearest. Accepted when the names agree strongly (score >= 0.85) within 1 km; partly
   (>= 0.5), or one side has no usable name, within 250 m; or whatever the names within 60 m,
   unless they are opposites (North / South, Front / Rear, Inner / Outer: score 0.2, never
   joined). A record joining a station that already holds a record of its own source needs a
   strong name (successive towers, "Old X" beside "X", and duplicates); those joins are listed.
4. Otherwise the record starts a new station, if it may: an OpenStreetMap seamark light with no
   lighthouse tag (extra.enrich_only), an element OSM itself marks as a likely minor beacon
   (extra.minor_beacon_suspect), a record with no name, and a register listing that covers a
   group of stations ("Apostle Islands Lighthouses") never start one; they may only add to a
   station they lie on (within 300 m with a strong name, 150 m otherwise), and are listed in the
   report when they join none.

Then:

- **Range lights.** A station holding only a front range light and one holding only a rear one,
  with the same base name in the same region within 3 km and no other candidate, become one
  `range_lights` station with two structures. Ambiguous groups and lone halves are left as they
  are and listed.
- **Successors.** Wikidata's replaces / replaced by (P1365 / P1366) between two stations become
  `related` links (preceded_by / succeeded_by); a life-saving station within 1.5 km of a light
  station links both ways.

Field precedence (first source with a value wins): name, region, county, kind, structure facts
(type, material, built, height), light dates, ATON numbers, agency: Wikidata > OSM. Location and
the light as charted (characteristic, focal height, range, fog signal): OSM > Wikidata (OSM
positions are mapped on the tower; its seamark tags follow the current chart). Status: see
station_status().

Python 3.12, standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge_ca  # noqa: E402  (Canada's rules: identifiers, curation, staffing)
import regions  # noqa: E402
import record_joins as _real_decisions  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


class _NoDecisions:
    """record_joins.py's lists, all empty: what merge.run() uses unless the command line (or a caller) hands it
    the real ones, so a test on synthetic stations is never touched by decisions about real ones."""
    RECORD_JOINS: dict = {}
    NO_POSITION: set = set()
    KEEP_APART_PAIRS: set = set()
    NAME_PICKS: dict = {}
    STATUS_PICKS: dict = {}
    HIDE: dict = {}
    KEEP_VISIBLE: set = set()
    NOT_DUPLICATES: set = set()
    REPLICA_OF: dict = {}
    SUCCESSION: list = []


record_joins = _NoDecisions()   # the decisions in force; main() sets record_joins.py's (set_decisions)


def set_decisions(module) -> None:
    global record_joins
    record_joins = module

# Matching order: records of an earlier source start stations first, a later source joins them. Wikidata and
# OpenStreetMap lead; the Canadian sources keep the order they had when only they existed (alphabetical, with
# LighthouseFriends and Rowlett shared by both countries); the US sources of 2026-10-21 (DESIGN 2.3) follow their
# own order. The sources never share a station across the border, so the two orders do not interact. A source
# missing from the list comes after the listed ones, alphabetically.
SOURCE_ORDER = ["wikidata", "osm",
                "ca_lightships_lifesaving", "ca_staffed_lightstations", "ccg_list_of_lights", "lighthousefriends",
                "parks_canada_hl", "uslhs", "nrhp", "territories", "rowlett", "uscg_light_list", "enc", "uslhs_passport"]
PRECEDENCE = {
    "name": ["wikidata", "osm", "lighthousefriends", "uslhs", "territories", "rowlett", "nrhp"],
    "location": ["osm", "wikidata", "territories", "lighthousefriends", "uslhs", "nrhp"],
    "region": ["wikidata", "osm", "lighthousefriends", "uslhs", "territories", "nrhp"],
    "kind": ["wikidata", "osm", "lighthousefriends", "uslhs", "territories", "nrhp"],
    "structure": ["wikidata", "osm", "uslhs", "rowlett", "territories", "nrhp"],
    "charted": ["osm", "wikidata", "territories", "uslhs", "rowlett"],
    "light_dates": ["wikidata", "osm", "uslhs", "rowlett", "territories", "lighthousefriends"],
    "other": ["wikidata", "osm", "uscg_light_list", "rowlett", "territories", "uslhs", "nrhp", "lighthousefriends"],
    "visit": ["uslhs_passport", "lighthousefriends", "uslhs", "wikidata", "osm"],
    "access": ["lighthousefriends", "uslhs", "wikidata", "osm"],
    "stay": ["uslhs_passport", "lighthousefriends", "wikidata", "osm"],
}
merge_ca.register(PRECEDENCE)  # ranks the Canadian sources in the tables above
# The charted light of a US station: NOAA's ENC first, then the Coast Guard's Light List (DESIGN 2.3); the
# Canadian List of Lights, if it leads the field, stays first (the sources never share a station).
_charted = PRECEDENCE["charted"]
_at = 1 if _charted and _charted[0] == "ccg_list_of_lights" else 0
_charted[_at:_at] = ["enc", "uscg_light_list"]
KIND_GROUP = {"lighthouse": "light", "range_lights": "light", "pier_light": "light", "harbor_light": "light",
              "lightship_station": "lightship_station", "lightship": "lightship",
              "life_saving_station": "life_saving_station"}
# Sources whose record of a charted characteristic is a weak sign that the light is lit today (an old
# Wikidata statement; a Light List or ENC entry that may belong to a modern light beside the old tower):
# beaten by any explicit "inactive" or "lost".
WEAK_ACTIVE_SOURCES = ("wikidata", "enc", "uscg_light_list")
CHARTED_SOURCES = ("enc", "uscg_light_list")
STRONG = 0.85
PARTIAL = 0.5
R_STRONG, R_PARTIAL, R_ANY = 1000.0, 250.0, 60.0
R_ENRICH_STRONG, R_ENRICH = 300.0, 150.0
R_PART = 150.0
R_OSM_DOUBLE = 60.0
R_WIKIDATA_TAG = 10000.0
R_NAMESAKE_M = 8000.0   # the report lists stations this close with the same name (near_namesakes)
R_NAMESAKE_JOIN = 10000.0   # a record joins the one station of its region this close whose name agrees strongly
R_HARD_KEY = 10000.0   # a shared NRHP / ARLHS / Light List number joins records up to this far apart
R_RANGE_PAIR = 3000.0
R_LSS_NEAR = 1500.0
CONFLICT_DISTANCE_M = 500.0
CELL_DEG = 0.05

# ---------------------------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------------------------

GENERIC_WORDS = {
    "light", "lights", "lighthouse", "lighthouses", "lightstation", "lightstations", "station", "stations",
    "phare", "phares", "faro", "faros", "tower", "museum", "historic", "site", "patrimonial", "the", "of",
    "de", "du", "des", "la", "le", "les", "l", "d", "del", "el", "los", "las", "and", "et", "y", "at",
    "life", "saving", "lifesaving", "lifeboat", "coast", "guard", "boathouse", "house", "keeper", "keepers",
    "us", "united", "states", "lightship", "lightvessel", "vessel", "no", "number", "aid", "navigational",
    "centre", "center", "beacon", "lamp",
}
SUCCESSION_WORDS = {"old", "new", "original", "first", "second", "third", "former", "present", "current"}
ABBREVIATIONS = {
    "pt": "point", "pte": "pointe", "st": "saint", "ste": "sainte", "mt": "mount", "ft": "fort",
    "hbr": "harbor", "harbour": "harbor", "is": "island", "isl": "island", "hd": "head",
    "n": "north", "s": "south", "e": "east", "w": "west", "lt": "light", "lh": "lighthouse",
    "lts": "lights", "bkw": "breakwater", "bw": "breakwater", "bkwtr": "breakwater", "lss": "lifesaving",
    "pierhead": "pierhead", "lightkeeper": "keeper", "lightkeepers": "keepers", "nord": "north", "sud": "south",
}
OPPOSITES = [("north", "south"), ("east", "west"), ("upper", "lower"), ("front", "rear"), ("inner", "outer"),
             ("high", "low"), ("big", "little"), ("great", "little")]
RANGE_ROLE_WORDS = {"front", "rear", "upper", "lower", "range", "leading"}
PLACEHOLDER_NAMES = {"unnamed", "unknown", "no name", "none", "?", "lighthouse", "light", "phare", "faro"}
# Buildings of a light station other than the light: they join the station as a structure, and
# start a station of their own only when Wikidata describes them and no light station is near.
ANCILLARY_RE = re.compile(
    r"\b(keeper'?s?'? (quarters|dwelling|house|cottage|residence)( museum)?|oil shed|pump ?house|rain ?shed|shed|"
    r"tram ?way|walkway|ramp|utility building|work ?shi?op|foundation|assistant keeper'?s?'? (quarters|dwelling|house)|"
    r"(1st|2nd|3rd|first|second|third) assistant|keepers'? (quarters|dwelling|house)|quarters|dwelling|cottage|"
    r"power ?house|oil ?house|fog ?(signal|horn|alarm)( house| building)?|signal house|generator|boat ?house|barn|"
    r"cistern|bungalow|workshop|garage|store ?house|privy|visitor cent(er|re)|gift shop|interpretive cent(er|re)|"
    r"radio (beacon|station)|engine house|whistle house|siren house|bell (tower|house))\b", re.I)
ROLE_BY_ANCILLARY = [(re.compile(r"fog|signal house|whistle|siren|bell", re.I), "fog_signal"),
                     (re.compile(r"oil ?house", re.I), "oil_house"),
                     (re.compile(r"boat ?house", re.I), "boathouse"),
                     (re.compile(r"keeper|quarters|dwelling|cottage|residence|assistant|bungalow", re.I), "dwelling")]
TOWER_ROLES = (None, "tower", "front_range", "rear_range")
LIGHT_WORD_RE = re.compile(r"\b(light|lights|lighthouse|lighthouses|light ?station|phare|faro|beacon|range)\b", re.I)


def is_ancillary_name(name: str) -> bool:
    """True when the name's last words name a station building: "Point Reyes Lighthouse Visitor
    Center", "2nd Assistant Keeper's Quarters", "Fog Signal Building" (not "Cottage Point Light")."""
    for m in ANCILLARY_RE.finditer(name):
        rest = name[m.end():].strip(" .,-")
        if not rest or re.fullmatch(r"(no\.?\s*\d+|#?\d+|[ivx]+|and \w+( \w+)?|buildings?|shed|house)", rest, re.I):
            return True
    return False
GROUP_NAME_RE = re.compile(r"\blighthouses\b|\blight stations\b|^lights of\b|^lighthouses of\b|\bphares\b", re.I)
GROUP_CLASSES = ("Q1497375 ", "Q18247357 ")


def ascii_fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")


def clean_name(name: str | None) -> str | None:
    if name is None:
        return None
    s = re.sub(r"\s+", " ", str(name)).strip().strip(".").strip()
    if not s or ascii_fold(s).lower() in PLACEHOLDER_NAMES or re.fullmatch(r"[Qq]\d+", s):  # a Wikidata item with no label
        return None
    letters = [ch for ch in s if ch.isalpha()]
    if letters and all(ch.isupper() for ch in letters) and len(letters) > 3 and " " in s:
        s = " ".join(w[:1] + w[1:].lower() for w in s.split(" "))
    return s


def name_tokens(s: str) -> list[str]:
    s = ascii_fold(s).lower()
    s = re.sub(r"\bu\.\s?s\.", " us ", s)
    s = re.sub(r"(?<=\w)'s\b", "s", s)  # "Shott's" is Shotts, not "Shott South" (S is the abbreviation of South)
    s = s.replace("'", " ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return [ABBREVIATIONS.get(t, t) for t in s.split()]


@dataclass(frozen=True)
class NameForm:
    full: str   # generic words removed: "old cape henry"
    core: str   # also without old/new/original: "cape henry"

    @property
    def squash(self) -> str:
        return self.core.replace(" ", "")


def name_variants(name: str | None, others: list[str] | None = None) -> list[str]:
    out: list[str] = []
    for raw in [name, *(others or [])]:
        c = clean_name(raw)
        if not c:
            continue
        # "(old)", "(new)", "(1803)" say which tower: they stay part of the name.
        c = re.sub(r"\((\s*(?:old|new|original|first|second|third|former|\d{4})\s*)\)", lambda m_: " " + m_.group(1).strip() + " ", c, flags=re.I)
        main = re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", c)).strip()
        if main:
            out.append(main)
        for paren in re.findall(r"\(([^)]*)\)", c):
            p = paren.strip()
            if p and not re.fullmatch(r"(replica|ruins?|demolished|gone|site|lv-?\s*\d+|wal-?\s*\d+|\d+)", p, re.I):
                out.append(p)
        for part in re.split(r"\s*/\s*", main):
            if part and part != main:
                out.append(part)
    seen, uniq = set(), []
    for v in out:
        if v.lower() not in seen:
            seen.add(v.lower())
            uniq.append(v)
    return uniq


def name_form(variant: str) -> NameForm:
    toks = [t for t in name_tokens(variant) if t not in GENERIC_WORDS]
    core = [t for t in toks if t not in SUCCESSION_WORDS]
    return NameForm(" ".join(toks), " ".join(core))


def name_forms(name: str | None, others: list[str] | None = None) -> list[NameForm]:
    return [f for f in (name_form(v) for v in name_variants(name, others)) if f.core]


def _pair_score(a: NameForm, b: NameForm) -> float:
    if a.full == b.full:
        return 1.0
    ta, tb = set(a.core.split()), set(b.core.split())
    for x, y in OPPOSITES:
        if (x in ta and y in tb and y not in ta and x not in tb) or (y in ta and x in tb and x not in ta and y not in tb):
            return 0.2
    na, nb = {t for t in ta if t.isdigit()}, {t for t in tb if t.isdigit()}
    if na and nb and na != nb:
        return 0.2
    if a.core == b.core or a.squash == b.squash:
        return 0.95
    ratio = difflib.SequenceMatcher(None, a.squash, b.squash).ratio()
    score = 0.85 if ratio >= 0.9 and min(len(a.squash), len(b.squash)) >= 6 else ratio * 0.9
    if ta and tb and (ta < tb or tb < ta):
        score = max(score, 0.6)
    return round(score, 3)


def name_score(forms_a: list[NameForm], forms_b: list[NameForm]) -> float | None:
    """0..1 similarity of two stations' names, or None when either has no usable name.
    1.0 same name; 0.95 same once Old/New are dropped ("Old Cape Henry" / "Cape Henry");
    0.85 a slip in a long name; 0.6 one name inside the other; 0.2 opposites or different numbers
    ("North Pier" / "South Pier", "Range Front" / "Range Rear", "Station No. 14" / "No. 35")."""
    if not forms_a or not forms_b:
        return None
    return max(_pair_score(a, b) for a in forms_a for b in forms_b)


def range_base(name: str) -> str:
    """The name a range's two halves share: "Haig Point Range front light" -> "haig point"."""
    toks = [t for t in name_tokens(re.sub(r"\([^)]*\)", " ", name)) if t not in GENERIC_WORDS and t not in RANGE_ROLE_WORDS]
    return " ".join(toks)


SLUG_LEADING = [r"^phare (?:de |du |de la |des |d')?", r"^faro (?:de |del |de la |de los )?", r"^site patrimonial (?:du |de la |de l')?",
                r"^united states lightship ", r"^u\.?s\.? lightship "]
SLUG_TRAILING = {"light", "lighthouse", "lights", "lightstation", "station", "tower", "the"}


def slugify(name: str, kind: str) -> str:
    s = ascii_fold(name).lower().replace("'", "").replace("&", " and ")
    for pat in SLUG_LEADING:
        s = re.sub(pat, "lightship " if "lightship" in pat else "", s)
    toks = re.sub(r"[^a-z0-9]+", " ", s).split()
    if kind not in ("life_saving_station",):
        while len(toks) > 1 and toks[-1] in SLUG_TRAILING:
            toks.pop()
        if len(toks) > 1 and toks[-1] == "light":
            toks.pop()
    slug = "-".join(toks)
    if len(slug) > 70:
        slug = slug[:70].rsplit("-", 1)[0]
    return slug or "light"


def range_station_name(front_name: str) -> str:
    """"Haig Point Range front light" -> "Haig Point Range Lights";
    "Nantucket Cliff Front Range Light" -> "Nantucket Cliff Range Lights"."""
    s = re.sub(r"\s*\([^)]*\)", "", front_name)
    s = re.sub(r"\b(front|rear|lower|upper)\b", " ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+(light ?house|light|lights|beacon|lightstation|light station)$", "", s, flags=re.I).strip()
    if re.search(r"\brange$", s, re.I):
        return f"{s} Lights"
    return f"{s} Range Lights"


# ---------------------------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------------------------

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def cell_of(lat: float, lon: float) -> tuple[int, int]:
    return (math.floor(lat / CELL_DEG), math.floor(lon / CELL_DEG))


def cells_around(lat: float, lon: float, radius_m: float) -> list[tuple[int, int]]:
    cy, cx = cell_of(lat, lon)
    span_lat = math.ceil(radius_m / (CELL_DEG * 111_000)) or 1
    span_lon = math.ceil(radius_m / (CELL_DEG * 111_000 * max(0.05, math.cos(math.radians(lat))))) or 1
    out = []
    for dy in range(-span_lat, span_lat + 1):
        for dx in range(-span_lon, span_lon + 1):
            x = cx + dx
            # wrap at 180 degrees (the Aleutians)
            n = round(360 / CELL_DEG)
            x = (x + n // 2) % n - n // 2
            out.append((cy + dy, x))
    return out


# ---------------------------------------------------------------------------------------------
# Records, parts, stations
# ---------------------------------------------------------------------------------------------

def source_rank(field: str, source: str) -> tuple[int, str]:
    order = PRECEDENCE.get(field, SOURCE_ORDER)
    return (order.index(source), "") if source in order else (len(order), source)


class Rec:
    def __init__(self, source: str, raw: dict) -> None:
        self.source = source
        self.raw = raw
        self.key: str = raw["key"]
        self.name: str | None = clean_name(raw.get("name"))
        self.other_names: list[str] = [n for n in (raw.get("other_names") or []) if isinstance(n, str)]
        self.country: str | None = raw.get("country")
        self.region: str | None = raw.get("region")
        self.lat: float | None = raw.get("lat")
        self.lon: float | None = raw.get("lon")
        if raw.get("key") in record_joins.NO_POSITION:    # a position a human has found wrong (record_joins.py)
            self.lat = self.lon = None
        self.kind: str = raw.get("kind") or "lighthouse"
        self.role: str | None = raw.get("role")
        self.status: str | None = raw.get("status")
        ex = raw.get("extra") or {}
        self.extra = ex
        self.enrich_only = bool(ex.get("enrich_only"))
        self.suspect = ex.get("minor_beacon_suspect")
        self.station_level = bool(ex.get("station_level"))
        self.out_of_scope = ex.get("out_of_scope")
        self.possibly_lost = bool(ex.get("possibly_lost"))
        self.wikidata_tag = ex.get("wikidata") if source != "wikidata" else None
        classes = " ".join(ex.get("wikidata_classes") or []) + " "
        self.group_listing = bool(self.name and GROUP_NAME_RE.search(self.name)) or any(g in classes for g in GROUP_CLASSES)
        self.forms = name_forms(self.name, self.other_names)
        self.join_keys = merge_ca.identifiers(raw)       # Canadian identifiers that name one structure
        self.start_blocked = merge_ca.start_blocker(source, raw)
        self.name_join_ok = bool(ex.get("station_level")) and source == "rowlett"
        bare = re.sub(r"\s*\([^)]*\)", "", self.name or "").strip()
        self.ancillary = bool(bare and is_ancillary_name(bare) and self.role not in ("front_range", "rear_range")
                              and self.kind != "life_saving_station")
        # OpenStreetMap marks every building of a historic light station historic=lighthouse
        # ("Oil Shed", "Quarters A", "Tram Way"): with no lighthouse tag of its own and no light
        # word in its name, such an element is a station building, not a light.
        forms_ = ex.get("forms") or []
        if (source == "osm" and forms_ == ["historic=lighthouse"] and self.name
                and not LIGHT_WORD_RE.search(self.name)):
            self.ancillary = True
        if self.ancillary and self.role is None:
            self.role = next((r for rx, r in ROLE_BY_ANCILLARY if rx.search(self.name)), "other")
        self.light = raw.get("light") or {}
        self.structure = raw.get("structure") or {}
        # What a visitor can do, as a source says it (LighthouseFriends icons, the Society's lists):
        # only keys the source knows are present, and a missing key never means false.
        self.visit = raw.get("visit") or {}
        self.stay = raw.get("stay") if isinstance(raw.get("stay"), dict) else None
        self.access = raw.get("access") or {}
        # Weak "active" claim from Wikidata: a charted characteristic and no deactivation or end date.
        self.status_claim = self.status
        if (source in WEAK_ACTIVE_SOURCES and self.status is None and self.light.get("characteristic")
                and not self.light.get("deactivated") and not self.possibly_lost and self.kind in KIND_GROUP
                and KIND_GROUP[self.kind] == "light"):
            self.status_claim = "active_weak"
        # A light Wikidata says went out, with an end date that may mean the tower went too: out,
        # if a current map shows the structure; otherwise no claim (station_status()).
        if source == "wikidata" and self.possibly_lost and self.light.get("deactivated") and self.status is None:
            self.status_claim = "inactive_if_standing"

    @property
    def has_point(self) -> bool:
        return isinstance(self.lat, (int, float)) and isinstance(self.lon, (int, float))

    @property
    def can_start(self) -> bool:
        return (bool(self.name) and self.has_point and not self.start_blocked and not self.enrich_only and not self.suspect and not self.group_listing
                and not (self.ancillary and self.source != "wikidata"))

    @property
    def hard_keys(self) -> list[str]:
        """Identifiers two records of one station share whatever their names or positions: the NRHP
        reference number, the ARLHS number and the Light List number (a register listing that covers
        several stations has none)."""
        if self.group_listing or self.country != "US":    # Canada's identifiers are merge_ca.py's
            return []
        keys = []
        for reg in self.raw.get("registers") or []:
            if reg.get("register") == "NRHP" and reg.get("number"):
                keys.append("nrhp:" + str(reg["number"]).strip())
        for x in self.extra.get("xref") or []:     # another source's own id for the same station (lhf:765)
            keys.append("xref:" + str(x))
        aton = self.raw.get("aton") or {}
        if aton.get("arlhs"):
            keys.append("arlhs:" + re.sub(r"[^A-Z0-9]", "", str(aton["arlhs"]).upper()))
        if aton.get("uscg_llnr"):
            keys.append("llnr:" + re.sub(r"-0+(?=\d)", "-", str(aton["uscg_llnr"]).strip()))
        return keys

    @property
    def is_replica(self) -> bool:
        """A scale copy of a light (DESIGN 3.2): a source says `replica`, or the name says so."""
        return self.status == "replica" or bool(re.search(r"\breplica\b", self.name or "", re.I))

    @property
    def quiet(self) -> bool:
        """A record the report need not list when it joins nothing (a charted light with no station)."""
        return bool(self.extra.get("quiet_unmatched"))

    @property
    def standing_evidence(self) -> bool:
        """An OpenStreetMap element mapping the structure today (not a lifecycle 'gone' form)."""
        if self.extra.get("standing"):  # a designated heritage lighthouse stands (Heritage Lighthouse Protection Act)
            return True
        return self.source == "osm" and not self.enrich_only and self.status not in ("lost", "ruins")

    def dist(self, lat: float, lon: float) -> float:
        return haversine_m(self.lat, self.lon, lat, lon)


class Part:
    def __init__(self, anchor: str, role: str | None) -> None:
        self.anchor = anchor
        self.role = role
        self.recs: list[Rec] = []

    def structure_recs(self) -> list[Rec]:
        return [r for r in self.recs if not r.station_level] or self.recs

    def pos(self) -> tuple[float, float] | None:
        cands = [r for r in self.structure_recs() if r.has_point and not r.enrich_only] or [r for r in self.recs if r.has_point]
        if not cands:
            return None
        best = sorted(cands, key=lambda r: (source_rank("location", r.source), r.raw.get("precision") != "exact", r.key))[0]
        return best.lat, best.lon

    def forms(self) -> list[NameForm]:
        out = []
        for r in self.recs:
            out += r.forms
        return out


class Station:
    _seq = 0

    def __init__(self, existing: dict | None = None, path: Path | None = None) -> None:
        Station._seq += 1
        self.seq = Station._seq
        self.idx = -1
        self.existing = existing
        self.path = path
        self.id: str | None = existing.get("id") if existing else None
        self.parts: list[Part] = []
        self.station_recs: list[Rec] = []
        self.absorbed_into: "Station | None" = None
        self.retiring = False     # every record is pinned elsewhere (record_joins.py): the station will be retired
        self.joins: list[dict] = []

    def recs(self) -> list[Rec]:
        out = list(self.station_recs)
        for p in self.parts:
            out += p.recs
        return out

    def forms(self, starting_only: bool = False) -> list[NameForm]:
        out = []
        for r in self.recs():
            if not starting_only or r.can_start:
                out += r.forms
        if not out and self.existing:
            out = name_forms(self.existing.get("name"), self.existing.get("other_names"))
        return out

    def points(self, starting_only: bool = False) -> list[tuple[float, float]]:
        pts = [r for r in self.recs() if r.has_point and (not starting_only or r.can_start)]
        if pts:
            return [(r.lat, r.lon) for r in pts]
        loc = (self.existing or {}).get("location") or {}
        if isinstance(loc.get("lat"), (int, float)):
            return [(loc["lat"], loc["lon"])]
        return []

    def country(self) -> str | None:
        for r in self.recs():
            if r.country:
                return r.country
        return (self.existing or {}).get("country")

    def kind_group(self) -> str | None:
        for r in self.recs():
            if not r.enrich_only:
                return KIND_GROUP.get(r.kind)
        if self.existing:
            return KIND_GROUP.get(self.existing.get("kind"))
        return None

    def is_replica(self) -> bool:
        recs = [r for r in self.recs() if r.can_start]
        return bool(recs) and all(r.is_replica for r in recs) or any(r.status == "replica" for r in recs)

    def min_dist(self, lat: float, lon: float, starting_only: bool = False) -> float:
        return min((haversine_m(a, b, lat, lon) for a, b in self.points(starting_only)), default=float("inf"))

    def part_by_anchor(self, anchor: str) -> Part | None:
        return next((p for p in self.parts if p.anchor == anchor), None)


# ---------------------------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------------------------

def load_sources(sources_dir: Path) -> tuple[dict[str, dict], dict[str, list[Rec]]]:
    headers: dict[str, dict] = {}
    recs: dict[str, list[Rec]] = {}
    for path in sorted(sources_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("kind") == "reference":
            continue
        sid = data.get("source") or path.stem
        headers[sid] = {k: data.get(k) for k in ("title", "url", "retrieved", "license")}
        recs[sid] = sorted((Rec(sid, r) for r in data.get("records") or [] if r.get("key")), key=lambda r: r.key)
    return headers, recs


def ordered_sources(sources: list[str]) -> list[str]:
    return [s for s in SOURCE_ORDER if s in sources] + sorted(s for s in sources if s not in SOURCE_ORDER)


def load_stations(stations_dir: Path) -> list[tuple[Path, dict]]:
    out = []
    for path in sorted(stations_dir.rglob("*.json")) if stations_dir.is_dir() else []:
        try:
            out.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except json.JSONDecodeError as e:
            raise SystemExit(f"{path} is not valid JSON: {e}")
    return out


# ---------------------------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------------------------

class Matcher:
    def __init__(self) -> None:
        self.stations: list[Station] = []
        self.grid: dict[tuple[int, int], set[int]] = defaultdict(set)
        self.by_id: dict[str, Station] = {}
        self.memory: dict[str, tuple[Station, str]] = {}
        self.station_of_key: dict[str, Station] = {}
        self.how = Counter()
        self.unshown: list[dict] = []
        self.same_source_joins: list[dict] = []
        self.wikidata_tag_far: list[dict] = []
        self.retired: list[tuple[Station, Station]] = []
        self.key_index: dict[str, list[Station]] = defaultdict(list)   # hard keys (rec.hard_keys) -> stations
        self.quiet_unmatched: Counter = Counter()
        self.quiet_recs: list[Rec] = []
        self.name_region_joins: list[dict] = []
        self.namesake_joins: list[dict] = []
        self.overrides: list[dict] = []
        self.deferred: list[tuple] = []     # (record, the key of a record it is pinned to) waiting for a later source
        self.ignore_pins: set[str] = set()
        self.ca_curation = merge_ca.Curation()
        self.unshown_recs: list[Rec] = []
        self.ca_far: list[dict] = []
        self.ca_ambiguous: list[dict] = []
        self.kind_group = KIND_GROUP

    def add_existing(self, path: Path, rec: dict) -> None:
        st = Station(rec, path)
        st.idx = len(self.stations)
        self.stations.append(st)
        if st.id:
            self.by_id[st.id] = st
        if rec.get("merged_into"):
            return
        keys = [s_["key"] for s_ in rec.get("sources") or [] if isinstance(s_, dict) and s_.get("key")]
        if keys and all(k in record_joins.RECORD_JOINS and not self.pinned_here(record_joins.RECORD_JOINS[k], st, keys) for k in keys):
            st.retiring = True    # every record goes to another station: it will be retired and nothing joins it
            return
        for s in rec.get("sources") or []:
            if isinstance(s, dict) and s.get("key"):
                self.memory[s["key"]] = (st, s.get("part") or "station")
        self.index(st)

    @staticmethod
    def pinned_here(target: str, st: Station, keys: list[str]) -> bool:
        """Whether a RECORD_JOINS target names this station itself: its id (with or without "new:") or one of its records."""
        return (target[4:] if target.startswith("new:") else target) == st.id or target in keys

    def index(self, st: Station) -> None:
        for lat, lon in st.points():
            self.grid[cell_of(lat, lon)].add(st.idx)

    def near(self, lat: float, lon: float, radius: float) -> list[Station]:
        seen: set[int] = set()
        for cell in cells_around(lat, lon, radius):
            seen |= self.grid.get(cell, set())
        out = [self.stations[i] for i in sorted(seen)]
        return [s for s in out if s.absorbed_into is None and not (s.existing or {}).get("merged_into")]

    def new_station(self) -> Station:
        st = Station()
        st.idx = len(self.stations)
        self.stations.append(st)
        return st

    def attach(self, rec: Rec, st: Station, how: str, anchor: str | None = None) -> None:
        self.how[how] += 1
        self.station_of_key[rec.key] = st
        merge_ca.index_record(self, rec, st)
        for hk in rec.hard_keys:
            if st not in self.key_index[hk]:
                self.key_index[hk].append(st)
        if not rec.has_point and st.parts and anchor is None and rec.country == "US":
            anchor = "station"   # a record with no position describes the station, never a structure of its own
        if anchor == "station" or (anchor is None and rec.station_level and st.parts):
            st.station_recs.append(rec)
        else:
            part = st.part_by_anchor(anchor) if anchor else None
            if part is None and anchor:
                part = Part(anchor, rec.role)
                st.parts.append(part)
            if part is None:
                part = self.choose_part(rec, st)
            if part is None:
                st.station_recs.append(rec)
            else:
                part.recs.append(rec)
                if part.role is None and rec.role:
                    part.role = rec.role
        if rec.has_point:
            self.grid[cell_of(rec.lat, rec.lon)].add(st.idx)

    @staticmethod
    def choose_part(rec: Rec, st: Station) -> Part | None:
        """The structure of `st` that `rec` describes, else a new one. A record that only enriches (a charted
        light, a Library of Congress item) or whose position is the register's batch-derived point never
        starts a structure of its own: with none near it, it is None and joins the station as a whole."""
        best, best_key = None, None
        limited = rec.country == "US" and (rec.enrich_only or (rec.source == "nrhp" and rec.raw.get("precision") != "exact"))
        for p in st.parts:
            if p.role and rec.role and p.role != rec.role:
                continue
            pos = p.pos()
            if pos is None or not rec.has_point:
                continue
            d = rec.dist(*pos)
            same = [r for r in p.recs if r.source == rec.source and not r.station_level]
            if same:
                double = rec.source == "osm" and d <= R_OSM_DOUBLE and all(r.source == "osm" for r in same)
                # The same name, word for word, within 150 m: one structure listed twice by a source
                # (an OSM node and its building, a duplicate Wikidata item), not a second tower.
                twin = d <= R_PART and rec.forms and all(r.forms and {f.full for f in r.forms} & {f.full for f in rec.forms} for r in same)
                # ... unless the two say they were built in different years: successive towers of one name
                b1 = rec.structure.get("built")
                if twin and rec.country == "US" and isinstance(b1, int) and any(isinstance(r.structure.get("built"), int) and abs(r.structure["built"] - b1) >= 3
                                                        for r in same):
                    twin = False
                if not double and not twin and not rec.enrich_only:
                    continue
                if rec.enrich_only and d > R_PART:
                    continue
            s = name_score(rec.forms, p.forms())
            if bool(rec.ancillary) != any(r.ancillary for r in p.recs if not r.station_level):
                continue  # a keeper's house is never the tower
            if d > R_PART and not (s is not None and s >= STRONG):
                continue
            key = (-(s if s is not None else 0.5), d, p.anchor)
            if best_key is None or key < best_key:
                best, best_key = p, key
        if best is None:
            if limited and st.parts:
                return None
            best = Part(rec.key, rec.role)
            st.parts.append(best)
        return best

    def candidates(self, rec: Rec) -> list[tuple[tuple, Station, float, float | None]]:
        if not rec.has_point:
            return []
        group = KIND_GROUP.get(rec.kind)
        limited = not rec.can_start
        r_strong, r_partial, r_any = (R_ENRICH_STRONG, R_ENRICH, R_ANY) if limited else (R_STRONG, R_PARTIAL, R_ANY)
        out = []
        for st in self.near(rec.lat, rec.lon, r_strong):
            if st.country() and rec.country and st.country() != rec.country:
                continue
            g = st.kind_group()
            if g and group and g != group:
                continue
            # A record that may not start a station is judged only against the records that
            # started or joined stations as starters, so the order the others arrive in never
            # changes where they go (a first run and a run with memory agree).
            d = st.min_dist(rec.lat, rec.lon, starting_only=limited)
            if d > r_strong:
                continue
            s = name_score(rec.forms, st.forms(starting_only=limited))
            if s is not None and s <= 0.2 and merge_ca.names_exclude(rec, s):
                continue
            if self.ca_curation.kept_apart(rec.key, merge_ca.station_keys(st)) or self.ca_curation.barred(rec.key, st):
                continue  # curation (data/curation_ca.json): not the same structure
            # A scale copy is its own station, whatever it is called: it joins the light it copies only on the spot
            if rec.country == "US" and d > r_any and (rec.is_replica != st.is_replica() or (limited and st.is_replica() and rec.source in CHARTED_SOURCES)):
                continue
            # A second record of one source in a station must be the same structure (a strong name), unless it
            # is the other half of a range: a front and a rear light are two structures by definition.
            same = any(r.source == rec.source and not r.station_level and (r.can_start or not limited)
                       and not (rec.role in ("front_range", "rear_range") and r.role in ("front_range", "rear_range") and r.role != rec.role)
                       for r in st.recs())
            if rec.ancillary:
                # A station building joins the nearest light station within 300 m, whatever its name.
                if d <= R_ENRICH_STRONG and g in (None, "light"):
                    out.append(((0.0, round(d, 1), st.seq), st, d, s))
                continue
            ok = ((s is not None and s >= STRONG and d <= r_strong)
                  or ((s is None or s >= PARTIAL) and d <= r_partial)
                  or (d <= r_any))
            if ok and same and not rec.station_level:
                double = rec.source == "osm" and d <= R_OSM_DOUBLE and (s is None or s >= PARTIAL)
                ok = double or (s is not None and s >= STRONG) or rec.enrich_only
            if ok:
                out.append(((-(s if s is not None else 0.5), round(d, 1), st.seq), st, d, s))
        out.sort(key=lambda x: x[0])
        return out

    # -- joins a human has decided (record_joins.py) and joins on a shared identifier ---------

    def pinned_station(self, target: str) -> Station | None:
        """The station a RECORD_JOINS target names: a station id, the key of a record it holds, or "new:<id>", a
        station of that id which this pin starts (two stations from one: Old and New Point Loma); once it is a file
        the id finds it."""
        if target.startswith("new:"):
            sid = target[4:]
            st = self.by_id.get(sid)
            if st is None:
                st = self.new_station()
                st.id = sid
                self.by_id[sid] = st
            return st
        st = self.by_id.get(target) or self.station_of_key.get(target)
        if st is None and target in self.memory:
            st = self.memory[target][0]
        while st is not None and st.absorbed_into is not None:
            st = st.absorbed_into
        return st

    def kept_apart(self, rec: Rec, st: Station) -> bool:
        return any(frozenset((rec.key, r.key)) in record_joins.KEEP_APART_PAIRS for r in st.recs())

    def by_hard_key(self, rec: Rec) -> Station | None:
        """The one station holding a record with the same NRHP number, ARLHS number or Light List number
        (same country, a compatible kind, and within R_HARD_KEY of the record when both have positions).
        Several holders: the nearest, when the record has a position; else none (ambiguous)."""
        found: list[Station] = []
        for hk in rec.hard_keys:
            for st in self.key_index.get(hk, []):
                if st.absorbed_into is not None or (st.existing or {}).get("merged_into") or st in found:
                    continue
                if st.country() and rec.country and st.country() != rec.country:
                    continue
                g = st.kind_group()
                if g and KIND_GROUP.get(rec.kind) and g != KIND_GROUP.get(rec.kind):
                    continue
                if self.kept_apart(rec, st) or rec.is_replica != st.is_replica():
                    continue
                if rec.region and first_region(st) and rec.region != first_region(st) and not hk.startswith("nrhp:"):
                    continue   # a Light List or ARLHS number copied into another state's entry (a register lists a vessel where it is moored)
                if rec.has_point and st.points() and st.min_dist(rec.lat, rec.lon) > R_HARD_KEY:
                    continue
                found.append(st)
        if not found:
            return None
        if len(found) == 1:
            return found[0]
        if rec.has_point:
            found.sort(key=lambda st: (st.min_dist(rec.lat, rec.lon), st.seq))
            return found[0]
        return None

    def by_name_in_region(self, rec: Rec) -> Station | None:
        """A record with no position joins the one station of its region whose name agrees strongly
        (>= STRONG), when no other station is within 0.1 of that score. Listed in the report."""
        if not rec.region or not rec.forms:
            return None
        scored = []
        for st in self.live():
            if st.country() and rec.country and st.country() != rec.country:
                continue
            g = st.kind_group()
            if g and KIND_GROUP.get(rec.kind) and g != KIND_GROUP.get(rec.kind):
                continue
            if first_region(st) != rec.region or self.kept_apart(rec, st) or rec.is_replica != st.is_replica():
                continue
            s = name_score(rec.forms, st.forms(starting_only=True))
            if s is not None and s >= STRONG:
                scored.append((s, st))
        if not scored:
            return None
        scored.sort(key=lambda x: (-x[0], x[1].seq))
        if len(scored) > 1 and scored[0][0] - scored[1][0] < 0.1:
            return None
        return scored[0][1]

    def far_namesake(self, rec: Rec) -> Station | None:
        """A source that pins a light a few kilometres from where another source does (a vanished tower, a
        light on a shoal) still means the same light when exactly one station of its region and kind has
        the same name (score >= STRONG, never opposites) within R_NAMESAKE_JOIN. A station that already
        holds a starting record of the record's own source is a different tower, not this one. Listed in
        the report (`namesake_joins`) for review."""
        if rec.country != "US" or not rec.has_point or not rec.name or not rec.can_start or not rec.region:
            return None
        group = KIND_GROUP.get(rec.kind)
        found = []
        for st in self.near(rec.lat, rec.lon, R_NAMESAKE_JOIN):
            if st.country() and rec.country and st.country() != rec.country:
                continue
            g = st.kind_group()
            if g and group and g != group:
                continue
            if first_region(st) != rec.region or self.kept_apart(rec, st) or rec.is_replica != st.is_replica():
                continue
            if any(r.source == rec.source and not r.station_level and r.can_start for r in st.recs()):
                continue
            d = st.min_dist(rec.lat, rec.lon, starting_only=True)
            if d > R_NAMESAKE_JOIN:
                continue
            sc = name_score(rec.forms, st.forms(starting_only=True))
            if sc is not None and sc >= STRONG:
                found.append((sc, d, st))
        return found[0][2] if len(found) == 1 else None

    def match_source(self, recs: list[Rec]) -> None:
        for rec in recs:
            pin = record_joins.RECORD_JOINS.get(rec.key) if rec.key not in self.ignore_pins else None
            if pin:
                # A pinned record waits until every other record is placed, in a first run and in a run with
                # memory alike: where it lands among a station's structures then depends only on them.
                self.deferred.append((rec, pin))
                continue
            if rec.key in self.memory:
                st, anchor = self.memory[rec.key]
                if st.absorbed_into is None:
                    self.attach(rec, st, "memory", anchor)
                    continue
            if rec.wikidata_tag:
                st = self.station_of_key.get(f"wikidata:{rec.wikidata_tag}")
                if st is not None and rec.has_point:
                    d = st.min_dist(rec.lat, rec.lon)
                    if d <= R_WIKIDATA_TAG and (st.country() in (None, rec.country)):
                        target = next((p for p in st.parts if any(r.key == f"wikidata:{rec.wikidata_tag}" for r in p.recs)), None)
                        anchor = None
                        if target is not None and (not target.role or not rec.role or target.role == rec.role):
                            if not any(r.source == rec.source for r in target.recs) or d <= R_OSM_DOUBLE:
                                anchor = target.anchor
                        self.attach(rec, st, "wikidata_tag", anchor)
                        continue
                    self.wikidata_tag_far.append({"key": rec.key, "name": rec.name, "wikidata": rec.wikidata_tag,
                                                  "distance_m": round(d), "station_name": (st.recs() or [rec])[0].name})
            hit = merge_ca.curated_join(self, rec)
            if hit is not None:
                self.attach(rec, hit, "curated_join")
                continue
            hit = merge_ca.identifier_join(self, rec)
            if hit is not None:
                self.attach(rec, hit[0], "identifier", hit[1])
                continue
            st = self.by_hard_key(rec)
            if st is not None:
                self.attach(rec, st, "hard_key")
                continue
            if not rec.has_point and rec.country == "US":
                st = self.by_name_in_region(rec)
                if st is not None:
                    self.attach(rec, st, "name_region")
                    self.name_region_joins.append({"key": rec.key, "name": rec.name, "station": st})
                    continue
            cands = [c for c in self.candidates(rec) if not self.kept_apart(rec, c[1])]
            if not cands and not rec.has_point:
                hit = merge_ca.name_join(self, rec, name_forms, name_score)
                if hit is not None:
                    self.attach(rec, hit, "name_only")
                    continue
            if cands:
                _k, st, d, s = cands[0]
                if any(r.source == rec.source and not r.station_level for r in st.recs()) and not rec.enrich_only and not rec.ancillary:
                    self.same_source_joins.append({"key": rec.key, "name": rec.name, "joined": sorted(
                        r.key for r in st.recs() if r.source == rec.source), "distance_m": round(d), "score": s})
                self.attach(rec, st, "place_name")
                continue
            if rec.can_start and rec.has_point:
                st = self.far_namesake(rec)
                if st is not None:
                    d_ns = round(st.min_dist(rec.lat, rec.lon, starting_only=True))
                    self.attach(rec, st, "namesake")
                    self.namesake_joins.append({"key": rec.key, "name": rec.name, "station": st, "distance_m": d_ns})
                    continue
                st = self.new_station()
                self.attach(rec, st, "new")
                continue
            if rec.quiet:
                self.quiet_unmatched[rec.source] += 1
                self.quiet_recs.append(rec)
                continue
            reason = merge_ca.unshown_reason(rec) or (
                      "seamark light with no lighthouse tag" if rec.enrich_only else
                      "a station building (keeper's house, fog signal, visitor centre) with no light station near" if rec.ancillary else
                      f"OpenStreetMap suggests a minor beacon ({rec.suspect})" if rec.suspect else
                      "a register listing that covers several stations" if rec.group_listing else
                      "no name in any source" if not rec.name else "no position")
            self.unshown.append({"key": rec.key, "name": rec.name, "region": rec.region, "kind": rec.kind,
                                 "lat": rec.lat, "lon": rec.lon, "reason": reason})
            self.unshown_recs.append(rec)

    # -- after matching ---------------------------------------------------------------------

    def apply_deferred(self) -> None:
        """Records pinned to a record of a source matched after theirs (an OpenStreetMap element pinned to a
        LighthouseFriends one): attached now that every source has been matched; a pin that still points
        nowhere is ignored and the record is matched as if there were none."""
        pending, self.deferred = self.deferred, []
        pending.sort(key=lambda it: it[0].key)   # the order the pinned records arrived in differs between a first run and a run with memory
        for rec, pin in pending:
            st = self.pinned_station(pin)
            if st is not None:
                self.attach(rec, st, "override")
                self.overrides.append({"key": rec.key, "to": pin})
            else:
                self.ignore_pins.add(rec.key)
                self.match_source([rec])

    def retry_hard_keys(self) -> int:
        """After both matching passes, give every US record that joined nothing one more try by the numbers it
        shares with a station: its partner may have been placed after it (records of one pass go in key order,
        and a run with memory puts the remembered ones first), so the order must not decide. Repeats while
        records join. Returns how many did."""
        total = 0
        while True:
            n = 0
            for rec in list(self.unshown_recs) + list(self.quiet_recs):
                if rec.country != "US" or not rec.hard_keys:
                    continue
                st = self.by_hard_key(rec)
                if st is None:
                    continue
                self.attach(rec, st, "hard_key")
                if rec in self.unshown_recs:
                    self.unshown_recs.remove(rec)
                    self.unshown[:] = [u for u in self.unshown if u["key"] != rec.key]
                else:
                    self.quiet_recs.remove(rec)
                    self.quiet_unmatched[rec.source] -= 1
                n += 1
            total += n
            if not n:
                return total

    def retry_unmatched(self) -> int:
        """After the pinned records are placed, give every US record that joined nothing one more try by position and
        name. A record of the second pass is matched before a pinned record has moved its station onto the right
        spot, and a run with memory still has the station's earlier position in the grid, so the first try may or may
        not have found it: this one sees the same stations in both. Returns how many joined."""
        total = 0
        while True:
            n = 0
            for rec in sorted(list(self.unshown_recs) + list(self.quiet_recs), key=lambda r: r.key):
                if rec.country != "US" or not rec.has_point:
                    continue
                cands = [c for c in self.candidates(rec) if not self.kept_apart(rec, c[1])]
                if not cands:
                    continue
                self.attach(rec, cands[0][1], "late_place_name")
                if rec in self.unshown_recs:
                    self.unshown_recs.remove(rec)
                    self.unshown[:] = [u for u in self.unshown if u["key"] != rec.key]
                else:
                    self.quiet_recs.remove(rec)
                    self.quiet_unmatched[rec.source] -= 1
                n += 1
            total += n
            if not n:
                return total

    def fold_whole_range_parts(self) -> None:
        """A station with a front and a rear range structure and a further structure that is only the item for the
        range as a whole (Wikidata's 'Nantucket Harbor Range Lights') keeps that item as a record of the station,
        not as a third structure."""
        for st in self.live():
            roles = {p.role for p in st.parts}
            if st.country() != "US" or not {"front_range", "rear_range"} <= roles:
                continue
            for p in list(st.parts):
                if p.role is None and p.recs and all(r.kind == "range_lights" and r.role is None and re.search(r"\brange\b", r.name or "", re.I)
                                                      and not r.enrich_only for r in p.recs):
                    st.station_recs += p.recs
                    st.parts.remove(p)

    def fold_positionless_parts(self) -> None:
        """A structure none of whose records has a position (its position was found wrong: NO_POSITION) is not a
        structure of its own when the station has another: its records describe the station as a whole."""
        for st in self.live():
            if len(st.parts) < 2 or st.country() != "US":
                continue
            for p in list(st.parts):
                if not any(r.has_point for r in p.recs) and any(q is not p and any(r.has_point for r in q.recs) for q in st.parts):
                    st.station_recs += p.recs
                    st.parts.remove(p)

    def retire_emptied(self) -> None:
        """A published station all of whose records RECORD_JOINS sent to one other station is that station
        (a duplicate, or twin lights that are one station): it is retired, its file kept with `merged_into`
        (DESIGN 3.2, ids are permanent). One whose records went to several stations stays as it is."""
        for st in self.stations:
            if st.absorbed_into is not None or not st.existing or st.existing.get("merged_into") or st.recs():
                continue
            keys = [k["key"] for k in st.existing.get("sources") or [] if isinstance(k, dict) and k.get("key")]
            if not keys or not all(k in record_joins.RECORD_JOINS for k in keys):
                continue
            targets = {id(self.station_of_key[k]): self.station_of_key[k] for k in keys if k in self.station_of_key}
            if len(targets) != 1:
                continue
            target = next(iter(targets.values()))
            while target.absorbed_into is not None:
                target = target.absorbed_into
            if target is st:
                continue
            st.absorbed_into = target
            self.retired.append((st, target))

    def live(self) -> list[Station]:
        return [s for s in self.stations if s.absorbed_into is None and not s.retiring and not (s.existing or {}).get("merged_into")]

    def pair_ranges(self) -> dict:
        report = {"pairs": [], "ambiguous": [], "unpaired": []}
        groups: dict[tuple, dict[str, list[Station]]] = defaultdict(lambda: {"front_range": [], "rear_range": [], "whole": []})
        for st in self.live():
            if st.kind_group() != "light" or not st.parts:
                continue
            roles = {p.role for p in st.parts}
            name = best_name(st) or ""
            if any(r.kind == "range_lights" and r.role is None for r in st.station_recs):
                continue  # the item for a whole range already holds its halves
            if roles in ({"front_range"}, {"rear_range"}):
                role = roles.pop()
            elif roles == {None} and len(st.parts) == 1 and any(r.kind == "range_lights" for r in st.recs()) \
                    and re.search(r"\brange\b", name, re.I):
                role = "whole"
            else:
                continue
            base = range_base(name)
            if base:
                groups[(st.country(), first_region(st), base)][role].append(st)
        for key in sorted(groups, key=lambda k: (k[0] or "", k[1] or "", k[2])):
            g = groups[key]
            fronts, rears, wholes = g["front_range"], g["rear_range"], g["whole"]
            if not fronts and not rears:
                continue
            entry = {"region": key[1], "base": key[2],
                     "front": sorted(best_name(s) or "" for s in fronts), "rear": sorted(best_name(s) or "" for s in rears)}
            if len(wholes) == 1 and len(fronts) <= 1 and len(rears) <= 1:
                whole = wholes[0]
                halves = fronts + rears
                d = max(min(haversine_m(a, b, c, e) for a, b in whole.points() for c, e in h.points()) for h in halves)
                if d <= R_RANGE_PAIR:
                    # The item for the whole range becomes the station; its own record describes the
                    # station, the halves its two structures.
                    keep = whole
                    for h in halves:
                        if h.id and not keep.id:
                            keep = h
                    for p in list(whole.parts):
                        if p.role is None:
                            whole.station_recs += p.recs
                            whole.parts.remove(p)
                    for h in [whole] + halves:
                        if h is keep:
                            continue
                        keep.parts += h.parts
                        keep.station_recs += h.station_recs
                        h.parts, h.station_recs = [], []
                        h.absorbed_into = keep
                        if h.id:
                            self.retired.append((h, keep))
                    for rec in keep.recs():
                        self.station_of_key[rec.key] = keep
                    self.index(keep)
                    report["pairs"].append({**entry, "whole": best_name(keep), "distance_m": round(d)})
                    continue
            if len(fronts) == 1 and len(rears) == 1:
                f, r = fronts[0], rears[0]
                d = min(haversine_m(a, b, c, e) for a, b in f.points() for c, e in r.points())
                if d <= R_RANGE_PAIR:
                    keep, gone = (f, r)
                    if r.id and not f.id:
                        keep, gone = r, f
                    keep.parts += gone.parts
                    keep.station_recs += gone.station_recs
                    gone.parts, gone.station_recs = [], []
                    gone.absorbed_into = keep
                    if gone.id:
                        self.retired.append((gone, keep))
                    for rec in keep.recs():
                        self.station_of_key[rec.key] = keep
                    self.index(keep)
                    report["pairs"].append({**entry, "distance_m": round(d)})
                    continue
                entry["distance_m"] = round(d)
                report["unpaired"].append({**entry, "why": f"front and rear are {round(d)} m apart (over {R_RANGE_PAIR:.0f} m)"})
            elif fronts and rears:
                report["ambiguous"].append({**entry, "why": "more than one front or rear of this name in the region"})
            else:
                report["unpaired"].append({**entry, "why": "only one half found"})
        return report


def first_region(st: Station) -> str | None:
    for r in sorted(st.recs(), key=lambda r: source_rank("region", r.source)):
        if r.region:
            return r.region
    return (st.existing or {}).get("region")


_SUCCESSION_LEAD_RE = re.compile(r"^(old|new|original|former|the old|site patrimonial)\b", re.I)


def best_name(st: Station) -> str | None:
    recs = sorted((r for r in st.recs() if r.name), key=lambda r: (source_rank("name", r.source), r.enrich_only, r.station_level, r.key))
    if not recs:
        return (st.existing or {}).get("name")
    roles = {p.role for p in st.parts}
    if {"front_range", "rear_range"} <= roles:
        front = next((r for r in recs if r.role == "front_range"), None)
        both = next((r for r in recs if r.role is None and re.search(r"\brange\b", r.name, re.I)), None)
        if both:
            return both.name
        if front:
            return range_station_name(front.name)
    for r in recs:
        if not _SUCCESSION_LEAD_RE.search(r.name) and not r.enrich_only:
            return r.name
    return recs[0].name


# ---------------------------------------------------------------------------------------------
# Resolving a station's fields
# ---------------------------------------------------------------------------------------------

LIGHT_RANK = {"active": 0, "active_weak": 1, "inactive": 2, "inactive_if_standing": 3}
MUSEUM_CLASSES = ("Q33506 ", "Q1863818 ", "Q756102 ", "Q2087181 ")
BNB_CLASSES = ("Q367914 ",)
EVENT_ORDER = ["built", "first_lit", "rebuilt", "replaced", "relit", "automated", "deactivated", "nrhp_listed",
               "heritage_designated", "relocated", "removed", "destroyed", "other"]


def _classes(rec: Rec) -> str:
    return " ".join(rec.extra.get("wikidata_classes") or []) + " "


def part_state(part: Part) -> tuple[str, list[str]]:
    """standing / lost / ruins / unknown for one structure, and the conflicting claims."""
    recs = part.structure_recs()
    standing = any(r.standing_evidence for r in recs)
    lost = [r for r in recs if r.status == "lost"]
    ruins = [r for r in recs if r.status == "ruins"]
    notes = []
    if standing and (lost or ruins):
        notes = [f"{r.source} says {r.status}" for r in lost + ruins]
        return "standing", notes
    if standing:
        return "standing", notes
    if lost:
        return "lost", notes
    if ruins:
        return "ruins", notes
    return "unknown", notes


def station_status(st: Station) -> tuple[str, str | None, list[dict]]:
    """(status, status_note, conflicts). The rules:

    - replica when any source says so;
    - lost when every structure is lost (ruins when some are ruins), and no current map shows one;
    - active when a source shows the light lit (an OSM lighthouse with seamark light tags; or
      Wikidata with a characteristic and no deactivation, when nothing says otherwise);
    - inactive when a source says the light is out and a structure stands or nothing says it went;
      but a Wikidata end date (P576) with no current map of the structure gives unknown, with a
      note that it may be gone;
    - unknown otherwise.
    """
    recs = [r for r in st.recs() if not r.enrich_only] or st.recs()
    conflicts: list[dict] = []
    if any(r.status == "replica" for r in recs):
        return "replica", None, conflicts
    tower_parts = [p for p in st.parts if p.role in TOWER_ROLES] or st.parts
    states = [part_state(p) for p in tower_parts] or [("unknown", [])]
    for p, (state, notes) in zip(tower_parts, states):
        if notes:
            conflicts.append({"field": "status", "values": [{"source": "osm", "value": "standing"}] + [
                {"source": n.split(" says ")[0], "value": n.split(" says ")[1]} for n in notes],
                "note": "A source says this structure is gone, but OpenStreetMap maps it today."})
    kinds = [s for s, _ in states]
    # A source with no position settles "gone" only when nothing else says whether a tower stands.
    unplaced = [r.status for r in st.station_recs if not r.has_point and r.status in ("active", "inactive", "lost", "ruins")] \
        if st.country() == "US" else []
    if kinds and all(k == "unknown" for k in kinds) and unplaced and all(u in ("lost", "ruins") for u in unplaced):
        return ("ruins" if "ruins" in unplaced else "lost"), None, conflicts
    if kinds and all(k == "lost" for k in kinds):
        return "lost", None, conflicts
    if kinds and all(k in ("lost", "ruins") for k in kinds):
        return "ruins", None, conflicts
    standing = any(k == "standing" for k in kinds)
    light_claims = sorted(((LIGHT_RANK[r.status_claim], source_rank("charted", r.source), r.key, r)
                           for r in recs if r.status_claim in LIGHT_RANK and (r.has_point or r.country != "US")
                           and (r.status_claim != "inactive_if_standing" or standing)), key=lambda x: x[:3])
    claimed = {c[3].status_claim.replace("_weak", "").replace("_if_standing", "") for c in light_claims}
    if {"active", "inactive"} <= claimed:
        conflicts.append({"field": "status", "values": [{"source": c[3].source, "value": c[3].status_claim.replace("_weak", "").replace("_if_standing", "")}
                                                        for c in light_claims], "note": "Sources differ on whether the light is still lit."})
    possibly_lost = any(r.possibly_lost for r in recs)
    if light_claims:
        top = light_claims[0][3].status_claim
        if top == "active":
            return "active", None, conflicts
        if "inactive" in claimed and not (possibly_lost and not standing):
            return "inactive", None, conflicts
        if top == "active_weak":
            return "active", None, conflicts
    if possibly_lost and not standing:
        p = next(r for r in recs if r.possibly_lost)
        end = p.extra.get("p576")
        when = f" ({end})" if isinstance(end, int) else ""
        return "unknown", (f"Wikidata gives an end date{when} without saying whether the light was discontinued or the "
                           "tower taken down, and no current map shows a structure here. It may be gone."), conflicts
    # No other source says: a source with no position (Rowlett's directory) may, when all its entries agree.
    if len(set(unplaced)) == 1 and unplaced[0] in ("active", "inactive"):
        return unplaced[0], "Taken from sources that give no usable position for this light (Rowlett's Lighthouse Directory, or a record whose coordinates are known to be wrong).", conflicts
    return "unknown", None, conflicts


def pick(recs: list[Rec], field: str, getter):
    # a secondary light of a station (a directional or sector light, an emergency light) comes after the main one
    for r in sorted(recs, key=lambda r: (source_rank(field, r.source), r.enrich_only, bool(r.extra.get("secondary")), r.key)):
        val = getter(r)
        if val not in (None, "", [], {}):
            return val, r
    return None, None


VISIT_KEYS = ("grounds_open", "climbable", "museum", "tours", "boat_only", "passport_stamp")


def visit_stay_access(recs: list["Rec"], visit: dict, stay: dict | None, access_note: str | None, use) -> tuple:
    """What the sources say about visiting, staying and access (3.2), field by field: the first source
    in PRECEDENCE["visit" / "stay" / "access"] with a value wins. A source lists only what it knows
    (LighthouseFriends lists the icons that are true), so a missing key never overrides a value and is
    never read as false. Returns (visit, stay, access level, access note)."""
    for key in VISIT_KEYS:
        if visit.get(key) is not None:
            continue
        val, r = pick(recs, "visit", lambda r, k=key: r.visit.get(k))
        if val is not None:
            visit[key] = val
            use(r, "visit")
    notes = []
    for r in sorted(recs, key=lambda r: (source_rank("visit", r.source), r.key)):
        n = r.visit.get("note")
        if isinstance(n, str) and n and n not in notes:
            notes.append(n)
            use(r, "visit")
    if notes:
        visit["note"] = " ".join(notes)
    # Among the Society's entries for one station a place to sleep outranks a volunteer program.
    stay_order = {"inn": 0, "rental": 1, "hostel": 2, "keeper_program": 3}
    cands = sorted((r for r in recs if r.stay), key=lambda r: (source_rank("stay", r.source), stay_order.get(r.stay.get("type"), 9), r.key))
    got, s_rec = (cands[0].stay, cands[0]) if cands else (None, None)
    if got:
        stay = dict(got)
        use(s_rec, "stay")
    level, l_rec = pick(recs, "access", lambda r: r.access.get("level") if r.access.get("level") not in (None, "unknown") else None)
    if level:
        use(l_rec, "access")
    notes = [access_note] if access_note else []
    for r in sorted(recs, key=lambda r: (source_rank("access", r.source), r.key)):
        n = r.access.get("note")
        if isinstance(n, str) and n and n not in notes:
            notes.append(n)
            use(r, "access")
    return visit, stay, level or "unknown", " ".join(notes) or None


def resolve(st: Station, today: str) -> tuple[dict, dict]:
    """(the station record, a few facts for the report)."""
    # Attach order differs between a first run and a run with memory: resolve from a fixed order.
    def rkey(r: Rec) -> tuple:
        return (source_rank("other", r.source), r.key)

    for p in st.parts:
        p.recs.sort(key=rkey)
    st.station_recs.sort(key=rkey)
    st.parts.sort(key=lambda p: p.anchor)
    recs = sorted(st.recs(), key=rkey)
    main_recs = [r for r in recs if not r.enrich_only] or recs
    used: dict[str, set[str]] = defaultdict(set)

    def use(rec: Rec | None, field: str) -> None:
        if rec is not None:
            used[rec.key].add(field)

    name = best_name(st)
    name_rec = next((r for r in recs if r.name == name), None)
    use(name_rec, "name")
    others = []
    for r in sorted(recs, key=lambda r: (source_rank("name", r.source), r.key)):
        if r.ancillary:  # a keeper's house or fog-signal building names itself, not the station
            continue
        for n in [r.name, *r.other_names]:
            n = clean_name(n)
            if n and n != name and n not in others:
                others.append(n)

    # Kind
    kinds = [r.kind for r in sorted(main_recs, key=lambda r: (source_rank("kind", r.source), r.key))]
    roles = {p.role for p in st.parts}
    group = st.kind_group() or "light"
    if group != "light":
        kind = group
    elif {"front_range", "rear_range"} & roles or "range_lights" in kinds:
        kind = "range_lights"
    else:
        kind = kinds[0] if kinds else "lighthouse"
        if kind == "harbor_light" and any(k != "harbor_light" for k in kinds):
            kind = next(k for k in kinds if k != "harbor_light")
    _, kind_rec = pick(main_recs, "kind", lambda r: r.kind if r.kind == kind else None)
    use(kind_rec, "kind")

    # Parts in a fixed order, and the one the map pin stands on
    def part_built(p: Part):
        b, _ = pick(p.structure_recs(), "structure", lambda r: r.structure.get("built"))
        return b

    role_order = {"front_range": 0, "rear_range": 1, "tower": 2, None: 2, "dwelling": 3}
    parts = sorted([p for p in st.parts if p.recs], key=lambda p: (part_built(p) is None, part_built(p) or 0,
                                                                   role_order.get(p.role, 4), p.anchor))
    # The map pin: a range's front light; else the (latest) structure showing a light; else the
    # latest one a current map shows; else the latest structure that is not a dwelling.
    pin_part = None
    if parts:
        fronts = [p for p in parts if p.role == "front_range"]
        lit = [p for p in parts if any(r.status_claim in ("active", "active_weak") for r in p.recs)]
        mapped = [p for p in parts if any(r.standing_evidence for r in p.recs)]
        towers = [p for p in parts if p.role != "dwelling"] or parts
        pin_part = fronts[0] if fronts else (lit or mapped or towers)[-1]
    pos = pin_part.pos() if pin_part else None
    loc_rec = None
    if pin_part:
        cands = [r for r in pin_part.structure_recs() if r.has_point and not r.enrich_only] or [r for r in pin_part.recs if r.has_point]
        loc_rec = sorted(cands, key=lambda r: (source_rank("location", r.source), r.raw.get("precision") != "exact", r.key))[0] if cands else None
    if pos is None:
        pts = [r for r in recs if r.has_point]
        loc_rec = sorted(pts, key=lambda r: (source_rank("location", r.source), r.key))[0]
        pos = (loc_rec.lat, loc_rec.lon)
    use(loc_rec, "location")
    location = {"lat": round(pos[0], 6), "lon": round(pos[1], 6),
                "precision": (loc_rec.raw.get("precision") if loc_rec else None) or "exact",
                "from": loc_rec.source if loc_rec else None}

    region, region_rec = pick(main_recs, "region", lambda r: r.region)
    if region and not regions.in_region_box(region, pos[0], pos[1]) and loc_rec and loc_rec.region:
        region, region_rec = loc_rec.region, loc_rec
    use(region_rec, "region")
    country = regions.country_of(region) or (region_rec.country if region_rec else None)
    county, county_rec = pick(main_recs, "region", lambda r: r.raw.get("county"))
    use(county_rec, "county")

    status, status_note, conflicts = station_status(st)
    status_note = merge_ca.status_note(recs, status, status_note)

    # Structures
    structures = []
    if kind not in ("lightship", "lightship_station"):
        for p in parts:
            srecs = p.structure_recs()
            stype, r1 = pick(srecs, "structure", lambda r: r.structure.get("type"))
            mat, r2 = pick(srecs, "structure", lambda r: r.structure.get("material"))
            built, r3 = pick(srecs, "structure", lambda r: r.structure.get("built"))
            height, r4 = pick(srecs, "structure", lambda r: r.structure.get("height_m"))
            for r in (r1, r2, r3, r4):
                use(r, "structures")
            state, _ = part_state(p)
            if state == "unknown" and status in ("active", "inactive"):
                state = "standing"
            role = p.role or ("tower" if group == "light" else "other")
            if any(r.role == "dwelling" for r in srecs) and not any(r.role != "dwelling" for r in srecs):
                role = "dwelling"
            sname = None
            if len(parts) > 1:
                sname, _ = pick(srecs, "name", lambda r: r.name)
            entry = {"role": role, "name": sname, "type": stype, "material": mat, "built": built,
                     "height_m": round(height, 1) if isinstance(height, (int, float)) else None,
                     "status": state, "note": None,
                     "from": (r1 or r2 or r3 or r4 or srecs[0]).source}
            ppos = p.pos()
            if ppos and haversine_m(ppos[0], ppos[1], pos[0], pos[1]) > 25:
                entry["location"] = {"lat": round(ppos[0], 6), "lon": round(ppos[1], 6)}
            structures.append(entry)

    # The light
    light = None
    if group in ("light", "lightship", "lightship_station"):
        ordered = ([r for r in (pin_part.recs if pin_part else [])] + [r for r in recs if not pin_part or r not in pin_part.recs])
        first_lit = min((r.light.get("first_lit") for r in recs if isinstance(r.light.get("first_lit"), int)), default=None)
        fl_rec = next((r for r in recs if r.light.get("first_lit") == first_lit), None) if first_lit else None
        deactivated, dz_rec = (None, None)
        if status in ("inactive", "lost", "ruins", "unknown", "relocated"):
            deactivated, dz_rec = pick(recs, "light_dates", lambda r: r.light.get("deactivated"))
        char, c_rec = pick(ordered, "charted", lambda r: r.light.get("characteristic"))
        focal, f_rec = pick(ordered, "charted", lambda r: r.light.get("focal_height_m"))
        rng, g_rec = pick(ordered, "charted", lambda r: r.light.get("range_nm"))
        fog, o_rec = pick(ordered, "charted", lambda r: r.light.get("fog_signal"))
        lens, l_rec = pick(ordered, "charted", lambda r: r.light.get("lens") if isinstance(r.light.get("lens"), dict) else None)
        for r in (fl_rec, dz_rec, c_rec, f_rec, g_rec, o_rec, l_rec):
            use(r, "light")
        if first_lit and deactivated and first_lit > deactivated:
            conflicts.append({"field": "light.first_lit", "values": [{"source": fl_rec.source, "value": first_lit},
                              {"source": dz_rec.source, "value": deactivated}],
                              "note": f"A source gives the light's service entry ({first_lit}) after its retirement "
                                      f"({deactivated}); it may have been relit. Neither is shown as the first lighting."})
            first_lit = None
        frm = next((r.source for r in (c_rec, fl_rec, f_rec, g_rec, dz_rec) if r), None)
        light = {"first_lit": first_lit, "deactivated": deactivated, "lens": dict(lens) if lens else None, "characteristic": char,
                 "focal_height_m": round(focal, 1) if isinstance(focal, (int, float)) else None,
                 "range_nm": round(rng, 1) if isinstance(rng, (int, float)) else None,
                 "fog_signal": fog, "from": frm}
        chars = {re.sub(r"\s+", " ", str(r.light.get("characteristic"))).strip().lower(): r for r in main_recs
                 if r.light.get("characteristic") and (pin_part is None or r in pin_part.recs)}
        if len({k.replace(" ", "") for k in chars}) > 1:
            conflicts.append({"field": "light.characteristic", "values": [{"source": r.source, "value": r.light.get("characteristic")}
                              for r in sorted(chars.values(), key=lambda r: (source_rank("charted", r.source), r.key))],
                              "note": "Sources give different characteristics (often an old one beside the current one, or a sector)."})
        focals = sorted({round(r.light["focal_height_m"], 1) for r in main_recs if isinstance(r.light.get("focal_height_m"), (int, float))
                         and (pin_part is None or r in pin_part.recs)})
        if len(focals) > 1 and focals[-1] - focals[0] > 3:
            conflicts.append({"field": "light.focal_height_m", "values": [{"source": r.source, "value": r.light["focal_height_m"]}
                              for r in main_recs if isinstance(r.light.get("focal_height_m"), (int, float)) and (pin_part is None or r in pin_part.recs)],
                              "note": "Sources differ by more than 3 m."})

    for k_, f_ in merge_ca.fields_used(recs).items():
        used[k_] |= f_

    # Registers, numbers, agency
    registers, seen_reg = [], {}
    for r in sorted(recs, key=lambda r: (source_rank("other", r.source), r.key)):
        for reg in r.raw.get("registers") or []:
            k = (reg.get("register"), reg.get("number"))
            if not reg.get("register"):
                continue
            if k not in seen_reg:
                entry = {"register": reg["register"], "number": reg.get("number"), "url": reg.get("url")}
                seen_reg[k] = entry
                registers.append(entry)
                use(r, "registers")
            entry = seen_reg[k]
            # The same listing from another source adds what the first lacks: the NRHP workbook gives the
            # listed date, the National Historic Landmark date and the nomination link (3.2).
            for extra_key in ("url", "listed", "nhl", "nomination"):
                if reg.get(extra_key) and not entry.get(extra_key):
                    entry[extra_key] = reg[extra_key]
                    use(r, "registers")
    registers.sort(key=lambda g: (g["register"] != "NRHP", g["number"] is None, g["register"], g["number"] or ""))
    aton = {}
    for k in ("uscg_llnr", "arlhs", "ccg_list_number", "nga"):
        val, r = pick(recs, "other", lambda r: (r.raw.get("aton") or {}).get(k))
        aton[k] = val
        use(r, "aton")
    agency, ag_rec = pick(main_recs, "other", lambda r: r.raw.get("agency"))
    use(ag_rec, "agency")
    ownership, ow_rec = pick(main_recs, "other", lambda r: r.raw.get("ownership"))
    use(ow_rec, "ownership")

    # Events
    events, seen_ev = [], set()
    for r in sorted(recs, key=lambda r: (source_rank("light_dates", r.source), r.key)):
        for e in r.raw.get("events") or []:
            k = (e.get("year"), e.get("event"))
            if not isinstance(e.get("year"), int):
                continue
            if k in seen_ev:
                # the same event from a later source: keep the first, but take a note it lacks
                prior = next(x for x in events if (x["year"], x["event"]) == k)
                if not prior["note"] and e.get("note") and country == "US":
                    prior["note"] = e["note"]
                    use(r, "events")
                continue
            seen_ev.add(k)
            events.append({"year": e["year"], "event": e["event"], "note": e.get("note"), "from": e.get("from") or r.source})
            use(r, "events")
    events.sort(key=lambda e: (e["year"], EVENT_ORDER.index(e["event"]) if e["event"] in EVENT_ORDER else 99, e["event"]))
    built_years = sorted({e["year"] for e in events if e["event"] in ("built", "first_lit") and (e.get("from") != "rowlett" or country != "US")})
    if len(built_years) > 1 and built_years[-1] - built_years[0] >= 2 and len(parts) <= 1:
        firsts = {}
        for r in (x for x in main_recs if x.has_point or country != "US"):
            fl = r.light.get("first_lit") or r.structure.get("built")
            if isinstance(fl, int):
                firsts.setdefault(r.source, fl)
        if len(set(firsts.values())) > 1:
            conflicts.append({"field": "first_year", "values": [{"source": s, "value": y} for s, y in sorted(firsts.items(), key=lambda x: source_rank("light_dates", x[0]))],
                              "note": "Sources give different first years (often the first tower against the present one)."})

    if light is not None and country == "US":
        ends = {}
        for r in sorted(main_recs, key=lambda r: (source_rank("light_dates", r.source), r.key)):
            y = r.light.get("deactivated")
            if isinstance(y, int) and r.source not in ends:
                ends[r.source] = y
        if len(ends) > 1 and max(ends.values()) - min(ends.values()) >= 2:
            conflicts.append({"field": "light.deactivated", "values": [{"source": s_, "value": y} for s_, y in ends.items()],
                              "note": "Sources give different years for the light going out (a retirement against a later removal, "
                                      "or the first against the last of several towers)."})

    automated = [e for e in events if e["event"] == "automated"]
    staffing = {"status": "automated", "as_of": str(automated[-1]["year"])} if automated and status in ("active", "inactive") else {"status": "unknown", "as_of": None}

    access_note = None
    acc_tags = sorted({r.extra.get("access_tag") for r in recs if r.extra.get("access_tag")})
    if acc_tags:
        access_note = "OpenStreetMap tags the structure access=" + "/".join(acc_tags) + "."
    museum = True if any(any(c in _classes(r) for c in MUSEUM_CLASSES) for r in recs) else None
    visit = {"grounds_open": None, "climbable": None, "museum": museum, "tours": None, "boat_only": None,
             "passport_stamp": None, "note": None}
    stay = None
    if any(any(c in _classes(r) for c in BNB_CLASSES) for r in recs):
        site = next((l["url"] for r in recs for l in r.raw.get("links") or [] if l.get("kind") == "website"), None)
        stay = {"type": "inn", "provider": None, "url": site, "season": None,
                "note": "Wikidata classes it as a bed and breakfast. Check with the operator before planning a stay.", "checked": None}
    visit, stay, access_level, access_note = visit_stay_access(recs, visit, stay, access_note, use)

    setting = None
    if any(r.raw.get("setting") == "offshore" for r in recs):
        setting = "offshore"
    elif kind == "pier_light":
        setting = "pier"

    photos, seen_ph = [], set()
    for r in sorted(recs, key=lambda r: (source_rank("other", r.source), r.key)):
        for ph in r.raw.get("photos") or []:
            if ph.get("url") and ph["url"] not in seen_ph:
                seen_ph.add(ph["url"])
                photos.append(ph)
                use(r, "photos")
    links, seen_ln = [], set()
    for r in sorted(recs, key=lambda r: (source_rank("other", r.source), r.key)):
        for ln in r.raw.get("links") or []:
            u = ln.get("url")
            if u and u.rstrip("/") not in seen_ln:
                seen_ln.add(u.rstrip("/"))
                links.append({"label": ln.get("label") or u, "url": u, "kind": ln.get("kind") or "other"})

    # Location conflicts: records of one structure more than 500 m apart
    for p in parts:
        # Only positions a source gives as exact are compared: the register's batch-derived points and
        # the pin of a vanished tower are approximations, not disagreements.
        pts = [r for r in p.structure_recs() if r.has_point and not r.enrich_only and (r.raw.get("precision", "exact") == "exact" or country != "US")]
        if len(pts) > 1:
            ppos = p.pos()
            far = [r for r in pts if r.dist(*ppos) > CONFLICT_DISTANCE_M]
            if far:
                conflicts.append({"field": "location", "values": [{"source": r.source, "value": [round(r.lat, 5), round(r.lon, 5)]} for r in pts],
                                  "distance_m": round(max(r.dist(*ppos) for r in far)),
                                  "note": "Sources place this structure more than 500 m apart."})

    sources = []
    for p_label, rs in [("station", st.station_recs)] + [(p.anchor, p.recs) for p in parts]:
        for r in rs:
            sources.append({"source": r.source, "key": r.key, "part": p_label, "fields": sorted(used.get(r.key, set()))})
    sources.sort(key=lambda s: (source_rank("other", s["source"]), s["key"]))

    independent = {r.source for r in main_recs if r.has_point and haversine_m(r.lat, r.lon, pos[0], pos[1]) <= CONFLICT_DISTANCE_M}
    verification = "facts" if len(independent) >= 2 and not any(c["field"] == "status" for c in conflicts) else "unverified"

    hidden, hidden_reason = False, None
    scope = [r.out_of_scope for r in main_recs]
    if scope and all(scope):
        hidden, hidden_reason = True, scope[0]

    rec = {
        "id": st.id, "name": name, "other_names": others,
        "country": country, "region": region, "county": county,
        "water": None, "setting": setting, "kind": kind,
        "location": location, "status": status, "status_note": status_note,
        "structures": structures, "light": light, "registers": registers, "aton": aton,
        "agency": agency, "ownership": ownership or "unknown",
        "access": {"level": access_level, "note": access_note},
        "staffing": staffing, "visit": visit, "stay": stay,
        "events": events, "keepers_count": None, "related": [],
        "photos": photos, "links": links, "sources": sources, "conflicts": conflicts,
        "verification": verification, "locked": [],
        "hidden": hidden, "hidden_reason": hidden_reason,
        "updated": today,
    }
    merge_ca.apply(rec, recs)  # staffing, access, visit and stay from the Canadian sources; the Admiralty number
    facts = {"pin_part": pin_part.anchor if pin_part else None}
    return rec, facts


FIELD_ORDER = ["id", "name", "other_names", "country", "region", "county", "water", "setting", "kind", "location",
               "status", "status_note", "structures", "light", "registers", "aton", "agency", "ownership", "access",
               "staffing", "visit", "stay", "events", "keepers_count", "related", "photos", "links", "sources",
               "conflicts", "verification", "locked", "hidden", "hidden_reason", "merged_into", "updated"]


def ordered(rec: dict) -> dict:
    out = {k: rec[k] for k in FIELD_ORDER if k in rec}
    for k in sorted(rec):
        if k not in out:
            out[k] = rec[k]
    return out


def dump(rec: dict) -> str:
    return json.dumps(ordered(rec), indent=2, ensure_ascii=False) + "\n"


def without_updated(rec: dict) -> dict:
    return {k: v for k, v in rec.items() if k != "updated"}


def apply_existing(new: dict, existing: dict | None) -> dict:
    """Locked fields keep their values; research/verified are never downgraded; keys the merge
    does not produce (a research summary, a human note) are kept."""
    if not existing:
        return new
    for k, v in existing.items():
        if k not in new:
            new[k] = v
    locked = [f for f in existing.get("locked") or [] if isinstance(f, str)]
    new["locked"] = locked
    for f in locked:
        top = f.split(".", 1)[0]
        if top in existing:
            if "." in f and isinstance(existing.get(top), dict) and isinstance(new.get(top), dict):
                sub = f.split(".", 1)[1]
                if sub in existing[top]:
                    new[top][sub] = existing[top][sub]
            else:
                new[top] = existing[top]
    if existing.get("verification") in ("researched", "verified"):
        new["verification"] = existing["verification"]
    if existing.get("related"):
        keep = [r for r in existing["related"] if isinstance(r, dict) and r.get("from") == "human"]
        new["related"] = keep + [r for r in new["related"] if r not in keep]
    return new


def assign_ids(new: list[tuple[Station, dict]], taken: set[str]) -> None:
    def slug_of(rec: dict) -> str:
        return f"{regions.id_prefix(rec['country'], rec['region'])}-{slugify(rec['name'], rec['kind'])}"

    items = sorted(new, key=lambda it: (slug_of(it[1]), -it[1]["location"]["lat"], it[1]["location"]["lon"],
                                        min((s["key"] for s in it[1]["sources"]), default="")))
    for st, rec in items:
        base = slug_of(rec)
        cand, n = base, 1
        while cand in taken:
            n += 1
            cand = f"{base}-{n}"
        taken.add(cand)
        st.id = cand
        rec["id"] = cand


def link_related(resolved: list[tuple[Station, dict]], m: Matcher) -> dict:
    by_station = {id(st): rec for st, rec in resolved}
    succession = []
    for st, rec in resolved:
        for r in st.recs():
            for rel, kind in (("replaces", "preceded_by"), ("replaced_by", "succeeded_by")):
                for target in (r.raw.get("relations") or {}).get(rel, []):
                    other = m.station_of_key.get(target)
                    while other is not None and other.absorbed_into is not None:
                        other = other.absorbed_into
                    if other is None or other is st or id(other) not in by_station:
                        continue
                    orec = by_station[id(other)]
                    entry = {"id": orec["id"], "relation": kind, "name": orec["name"]}
                    if entry not in rec["related"]:
                        rec["related"].append(entry)
                        succession.append({"from": rec["id"], "relation": kind, "to": orec["id"]})
    # Life-saving stations near light stations, both ways.
    lights = [(st, rec) for st, rec in resolved if KIND_GROUP.get(rec["kind"]) == "light" and not rec["hidden"]]
    lsss = [(st, rec) for st, rec in resolved if rec["kind"] == "life_saving_station" and not rec["hidden"]]
    near_pairs = 0
    for _, lrec in lsss:
        for _, rec in lights:
            d = haversine_m(lrec["location"]["lat"], lrec["location"]["lon"], rec["location"]["lat"], rec["location"]["lon"])
            if d <= R_LSS_NEAR:
                a = {"id": lrec["id"], "relation": "life_saving_station_nearby", "name": lrec["name"]}
                b = {"id": rec["id"], "relation": "light_station_nearby", "name": rec["name"]}
                if a not in rec["related"]:
                    rec["related"].append(a)
                if b not in lrec["related"]:
                    lrec["related"].append(b)
                near_pairs += 1
    for _, rec in resolved:
        rec["related"].sort(key=lambda x: (x.get("relation") or "", x.get("id") or ""))
    return {"succession_links": sorted(succession, key=lambda x: (x["from"], x["to"])), "life_saving_near_light": near_pairs}


def apply_decisions(resolved: list[tuple[Station, dict]]) -> dict:
    """The station-level decisions of record_joins.py, applied to the merged records: STATUS_PICKS, HIDE,
    REPLICA_OF (status replica, related replica_of both ways) and SUCCESSION (older / newer lights that are two
    stations, linked both ways). An id that matches no station is listed in the report, not an error."""
    by_id = {rec["id"]: rec for _, rec in resolved}
    applied, missing = Counter(), []

    def get(i: str) -> dict | None:
        rec = by_id.get(i)
        if rec is None:
            missing.append(i)
        return rec

    def link(rec: dict, relation: str, other: dict) -> None:
        entry = {"id": other["id"], "relation": relation, "name": other["name"]}
        if entry not in rec["related"]:
            rec["related"].append(entry)
            rec["related"].sort(key=lambda x: (x.get("relation") or "", x.get("id") or ""))

    for sid, (status, note) in sorted(record_joins.STATUS_PICKS.items()):
        rec = get(sid)
        if rec:
            rec["status"], rec["status_note"] = status, note
            rec["conflicts"] = [c_ for c_ in rec["conflicts"] if c_["field"] != "status"]
            if status in ("lost", "ruins"):
                for st_ in rec["structures"]:
                    if st_["role"] in ("tower", "front_range", "rear_range") and st_["status"] in ("standing", "unknown"):
                        st_["status"] = status      # the buildings around a vanished tower may stand
            applied["status"] += 1
    for sid, nm in sorted(record_joins.NAME_PICKS.items()):
        rec = get(sid)
        if rec and rec["name"] != nm:
            rec["other_names"] = [n for n in [rec["name"], *rec["other_names"]] if n != nm]
            rec["name"] = nm
            applied["name"] += 1
    for sid, reason in sorted(record_joins.HIDE.items()):
        rec = get(sid)
        if rec:
            rec["hidden"], rec["hidden_reason"] = True, reason
            applied["hidden"] += 1
    for copy_id, original_id in sorted(record_joins.REPLICA_OF.items()):
        copy, original = get(copy_id), get(original_id)
        if copy and original:
            copy["status"] = "replica"
            copy["status_note"] = None
            link(copy, "replica_of", original)
            link(original, "replica", copy)
            applied["replica"] += 1
    for old_id, new_id in record_joins.SUCCESSION:
        old, new = get(old_id), get(new_id)
        if old and new:
            link(old, "succeeded_by", new)
            link(new, "preceded_by", old)
            applied["succession"] += 1
    return {"applied": dict(applied), "ids_not_found": sorted(set(missing))}


def retired_record(existing: dict, into: str, today: str) -> dict:
    return ordered({
        "id": existing["id"], "name": existing.get("name"), "country": existing.get("country"),
        "region": existing.get("region"), "kind": existing.get("kind"), "location": existing.get("location"),
        "status": existing.get("status"), "verification": existing.get("verification", "unverified"),
        "sources": [], "hidden": True, "hidden_reason": f"Merged into {into}: the same station",
        "merged_into": into, "updated": today,
    })


INLAND_REGIONS = {"AZ", "NV", "UT", "CO", "NM", "OK", "KS", "NE", "SD", "ND", "MT", "WY", "ID", "IA", "MO", "AR",
                  "TN", "KY", "WV", "AB", "SK"}


def run(sources_dir: Path, stations_dir: Path, report_path: Path | None, today: str, write: bool = True) -> dict:
    Station._seq = 0
    headers, by_source = load_sources(sources_dir)
    existing = load_stations(stations_dir)
    m = Matcher()
    m.ca_curation = merge_ca.Curation(merge_ca.load_curation(sources_dir.parent / "curation_ca.json"))
    merge_ca.prepare(by_source, m.ca_curation)
    for path, rec in existing:
        m.add_existing(path, rec)
    merge_ca.detach(m, m.ca_curation)
    # Records that may start a station first (every source in order), then the ones that may only
    # join one, so those always see every station; with the memory of an earlier run this makes a
    # second run identical to the first.
    order = ordered_sources(list(by_source))
    for sid in order:
        m.match_source([r for r in by_source[sid] if r.can_start or r.key in m.memory])
    for sid in order:
        m.match_source([r for r in by_source[sid] if not (r.can_start or r.key in m.memory)])
    m.apply_deferred()
    m.fold_positionless_parts()
    m.fold_whole_range_parts()
    merge_ca.retry_unshown(m)
    merge_ca.merge_stations(m, m.ca_curation)
    merge_ca.retry_unshown(m)  # records tied to both of two stations that curation has just made one
    m.retry_hard_keys()
    m.retry_unmatched()
    m.retire_emptied()
    ranges = m.pair_ranges()

    resolved: list[tuple[Station, dict]] = []
    for st in m.live():
        if not st.recs():
            continue
        rec, _facts = resolve(st, today)
        resolved.append((st, rec))
    taken = {s.id for s in m.stations if s.id}
    assign_ids([(st, rec) for st, rec in resolved if not st.id], taken)
    for st, rec in resolved:
        rec["id"] = st.id
        merge_ca.curate(rec, m.ca_curation, [r.key for r in st.recs()])
    links = link_related(resolved, m)
    decisions = apply_decisions(resolved)
    links["decisions"] = decisions

    written = unchanged = 0
    outputs: list[tuple[Path, str]] = []
    for st, rec in resolved:
        rec = apply_existing(rec, st.existing)
        if st.existing and without_updated(ordered(rec)) == without_updated(ordered(st.existing)):
            rec["updated"] = st.existing.get("updated", today)
        path = stations_dir / regions.station_dir(rec["id"]) / f"{rec['id']}.json"
        text = dump(rec)
        if path.exists() and path.read_text(encoding="utf-8") == text:
            unchanged += 1
            continue
        outputs.append((path, text))
    for gone, keep in m.retired:
        path = gone.path or (stations_dir / regions.station_dir(gone.id) / f"{gone.id}.json")
        outputs.append((path, dump(retired_record(gone.existing, keep.id, today))))
    if write:
        for path, text in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            written += 1

    report = build_report(m, resolved, headers, ranges, links)
    report["canada"], ca_run = merge_ca.report(m, resolved, by_source)
    report["_run"] = {"files_changed": len(outputs), "files_unchanged": unchanged,
                      "record_matches": dict(sorted(m.how.items())), "range_pairs_made": len(ranges["pairs"]),
                      "canada": ca_run}
    if write and report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        saved = {k: v for k, v in report.items() if k != "_run"}
        text = json.dumps(saved, indent=1, ensure_ascii=False) + "\n"
        if not report_path.exists() or report_path.read_text(encoding="utf-8") != text:
            report_path.write_text(text, encoding="utf-8")
    return report


def build_report(m: Matcher, resolved: list[tuple[Station, dict]], headers: dict, ranges: dict, links: dict) -> dict:
    """The review file. It describes the merged state, not what this run did (that is printed),
    so a re-run with unchanged inputs leaves it byte for byte the same."""
    visible = [rec for _, rec in resolved if not rec["hidden"]]
    hidden = [rec for _, rec in resolved if rec["hidden"]]

    def counts(rs: list[dict], key) -> dict:
        return dict(sorted(Counter(key(r) for r in rs).items(), key=lambda kv: str(kv[0])))

    both = [rec for rec in visible if {s["source"] for s in rec["sources"]} >= {"wikidata", "osm"}]
    tag_confirmed = 0
    for st, rec in resolved:
        if rec["hidden"]:
            continue
        qids = {r.key[len("wikidata:"):] for r in st.recs() if r.source == "wikidata"}
        if any(r.wikidata_tag in qids for r in st.recs() if r.source == "osm"):
            tag_confirmed += 1
    # Stations holding two starting records of one source (successive towers, "Old X" beside
    # "X", or a duplicate in that source), and OSM wikidata= tags that point at another station.
    same_source, tag_elsewhere = [], []
    station_of_qid = {}
    for st, rec in resolved:
        for r in st.recs():
            if r.source == "wikidata":
                station_of_qid[r.key[len("wikidata:"):]] = rec["id"]
    for st, rec in resolved:
        by_src = defaultdict(list)
        for r in st.recs():
            if r.can_start and not r.station_level and not r.ancillary:
                by_src[r.source].append(r)
        for src, rs in sorted(by_src.items()):
            if len(rs) > 1:
                same_source.append({"id": rec["id"], "name": rec["name"], "source": src,
                                    "records": [{"key": r.key, "name": r.name} for r in sorted(rs, key=lambda r: r.key)]})
        for r in st.recs():
            if r.source == "osm" and r.wikidata_tag and station_of_qid.get(r.wikidata_tag) not in (None, rec["id"]):
                tag_elsewhere.append({"key": r.key, "name": r.name, "in": rec["id"], "wikidata": r.wikidata_tag,
                                      "wikidata_station": station_of_qid[r.wikidata_tag]})
    same_source.sort(key=lambda x: (x["id"], x["source"]))
    tag_elsewhere.sort(key=lambda x: x["key"])
    paired = []
    for st, rec in resolved:
        roles = [s["role"] for s in rec["structures"]]
        if not rec["hidden"] and "front_range" in roles and "rear_range" in roles:
            paired.append({"id": rec["id"], "name": rec["name"]})
    ranges = {"paired": sorted(paired, key=lambda x: x["id"]), "ambiguous": ranges["ambiguous"], "unpaired": ranges["unpaired"]}
    # a status with no evidence behind it that the light is still there: only the Wikidata end-date case
    # (stations whose status a human settled in record_joins.py, and statuses taken from a source with no
    # position, are not suspects)
    possibly_lost = [{"id": r["id"], "name": r["name"], "note": r["status_note"]} for r in visible
                     if r.get("status_note") and (r["country"] != "US" or (r["status"] == "unknown" and r["id"] not in record_joins.STATUS_PICKS))]
    decorative = []
    for st, rec in resolved:
        if rec["hidden"] or rec["id"] in record_joins.KEEP_VISIBLE or rec["id"] in record_joins.REPLICA_OF or \
                (rec["id"] in record_joins.STATUS_PICKS and record_joins.STATUS_PICKS[rec["id"]][0] == "replica"):
            continue    # decided in record_joins.py
        hints = sorted({r.extra.get("decorative_hint") for r in st.recs() if r.extra.get("decorative_hint")})
        only_osm = {s["source"] for s in rec["sources"]} == {"osm"}
        no_light = not (rec.get("light") or {}).get("characteristic") and not rec["registers"]
        why = []
        if hints:
            why.append("tags: " + "; ".join(hints))
        if only_osm and no_light and rec["region"] in INLAND_REGIONS:
            why.append("inland, OpenStreetMap only, no charted light or register")
        if only_osm and no_light and re.search(r"\b(replica|mini|golf|model)\b", rec["name"], re.I):
            why.append("name")
        if why:
            decorative.append({"id": rec["id"], "name": rec["name"], "region": rec["region"], "why": why})
    # An OpenStreetMap-only station with no charted light that shares its name with a registered
    # station of another region: often a replica (Lake Havasu's copies of famous lights) or a
    # decorative copy.
    known: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for st, rec in resolved:
        if rec["hidden"] or not any(r.source == "wikidata" for r in st.recs()) or not rec["registers"]:
            continue
        for f in name_forms(rec["name"]):
            if len(f.core.split()) >= 2:
                known[f.core].append((rec["id"], rec["region"]))
    by_id = {d["id"]: d for d in decorative}
    for st, rec in resolved:
        if rec["hidden"] or {s["source"] for s in rec["sources"]} != {"osm"} or (rec.get("light") or {}).get("characteristic"):
            continue
        twins = sorted({i for f in name_forms(rec["name"]) for i, reg in known.get(f.core, []) if reg != rec["region"]})
        if twins:
            entry = by_id.get(rec["id"])
            if entry is None:
                entry = {"id": rec["id"], "name": rec["name"], "region": rec["region"], "why": []}
                decorative.append(entry)
                by_id[rec["id"]] = entry
            entry["why"].append("shares its name with " + ", ".join(twins[:3]) + " (a replica?)")
    # Possible duplicates: two visible stations within 150 m.
    close = []
    pts = sorted(((rec["location"]["lat"], rec["location"]["lon"], rec["id"], rec["name"], rec["kind"]) for rec in visible))
    for i, a in enumerate(pts):
        for b in pts[i + 1:]:
            if b[0] - a[0] > 0.002:
                break
            d = haversine_m(a[0], a[1], b[0], b[1])
            if d <= 150 and KIND_GROUP.get(a[4]) == KIND_GROUP.get(b[4]):
                close.append({"a": a[2], "a_name": a[3], "b": b[2], "b_name": b[3], "distance_m": round(d)})
    # Stations of one kind group within R_NAMESAKE_M whose names agree strongly: duplicates the 150 m test
    # misses (a lost tower pinned a kilometre off by one source). Reviewed pairs (record_joins) are left out.
    near_names = []
    forms = {rec["id"]: name_forms(rec["name"], rec.get("other_names")) for rec in visible}
    for i, a in enumerate(pts):
        for b in pts[i + 1:]:
            if b[0] - a[0] > R_NAMESAKE_M / 111000.0:
                break
            d = haversine_m(a[0], a[1], b[0], b[1])
            if d <= 150 or d > R_NAMESAKE_M or KIND_GROUP.get(a[4]) != KIND_GROUP.get(b[4]):
                continue
            if frozenset((a[2], b[2])) in record_joins.NOT_DUPLICATES:
                continue
            sc = name_score(forms[a[2]], forms[b[2]])
            if sc is not None and sc >= STRONG:
                near_names.append({"a": a[2], "a_name": a[3], "b": b[2], "b_name": b[3], "distance_m": round(d), "score": sc})
    close = [x for x in close if frozenset((x["a"], x["b"])) not in record_joins.NOT_DUPLICATES]
    multi = [{"id": rec["id"], "name": rec["name"], "structures": [s.get("name") for s in rec["structures"]]}
             for rec in visible if len([s for s in rec["structures"] if s["role"] not in ("front_range", "rear_range")]) > 1]
    conflicts = Counter(c["field"] for rec in visible for c in rec["conflicts"])
    unshown = sorted(m.unshown, key=lambda u: u["key"])
    report = {
        "note": "Written by pipeline/merge.py. Lists for a human to review; nothing here is applied automatically.",
        "sources": {sid: h for sid, h in sorted(headers.items())},
        "counts": {
            "stations": len(visible),
            "hidden": len(hidden),
            "merged_away": len({st.id for st in m.stations if (st.existing or {}).get("merged_into")} | {gone.id for gone, _keep in m.retired}),
            "by_country": counts(visible, lambda r: r["country"]),
            "by_region": counts(visible, lambda r: r["region"]),
            "by_kind": counts(visible, lambda r: r["kind"]),
            "by_country_kind": {c: counts([r for r in visible if r["country"] == c], lambda r: r["kind"])
                                for c in sorted({r["country"] for r in visible})},
            "by_status": counts(visible, lambda r: r["status"]),
            "by_verification": counts(visible, lambda r: r["verification"]),
            "by_sources": counts(visible, lambda r: "+".join(sorted({s["source"] for s in r["sources"]}))),
            "wikidata_and_osm": len(both),
            "wikidata_and_osm_by_tag": tag_confirmed,
            "conflicts": dict(sorted(conflicts.items())),
            "not_shown": dict(sorted(Counter(u["reason"].split(" (")[0] for u in unshown).items())),
            "unmatched_not_listed": dict(sorted(m.quiet_unmatched.items())),
        },
        "hidden": [{"id": r["id"], "name": r["name"], "reason": r["hidden_reason"]} for r in sorted(hidden, key=lambda r: r["id"])],
        "range_lights": ranges,
        "successive_structures": sorted(multi, key=lambda x: x["id"]),
        "same_source_stations": same_source,
        "wikidata_tag_elsewhere": tag_elsewhere,
        "possibly_lost": sorted(possibly_lost, key=lambda x: x["id"]),
        "decorative_suspects": sorted(decorative, key=lambda x: x["id"]),
        "possible_duplicates": close,
        "near_namesakes": near_names,
        "joins_to_review": {
            "by_name_in_region": sorted(({"key": j["key"], "name": j["name"], "station": j["station"].id} for j in m.name_region_joins),
                                        key=lambda x: x["key"]),
            "by_unique_namesake": sorted(({"key": j["key"], "name": j["name"], "station": j["station"].id,
                                           "distance_m": j["distance_m"]} for j in m.namesake_joins), key=lambda x: x["key"]),
        },
        "related": links,
        "not_shown": unshown,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Merge data/sources into data/stations")
    ap.add_argument("--sources", type=Path, default=DATA / "sources")
    ap.add_argument("--stations", type=Path, default=DATA / "stations")
    ap.add_argument("--report", type=Path, default=DATA / "merge_report.json")
    ap.add_argument("--today", default=dt.date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    set_decisions(_real_decisions)
    report = run(args.sources, args.stations, args.report, args.today, write=not args.dry_run)
    c, run_ = report["counts"], report["_run"]
    print(f"merge: {c['stations']} stations shown, {c['hidden']} hidden, {c['merged_away']} merged away; "
          f"{run_['files_changed']} files written, {run_['files_unchanged']} unchanged")
    print(f"  by country {c['by_country']}; by kind {c['by_kind']}")
    print(f"  by status {c['by_status']}; wikidata+osm {c['wikidata_and_osm']} ({c['wikidata_and_osm_by_tag']} confirmed by an OSM wikidata tag)")
    print(f"  this run: matches {run_['record_matches']}; range pairs made {run_['range_pairs_made']}")
    print(f"  not shown {c['not_shown']}; conflicts {c['conflicts']}")
    ca_run = run_.get("canada") or {}
    if ca_run.get("joined_by"):
        print(f"  Canada: joined by {ca_run['joined_by']}; {len(ca_run['identifier_ambiguous'])} identifiers point at two stations, "
              f"{len(ca_run['identifier_far'])} at one too far away; curation applied {ca_run['curation_applied']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
