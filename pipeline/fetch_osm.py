#!/usr/bin/env python3
"""Fetch lighthouses and major lights in the United States (its territories included) and
Canada from OpenStreetMap, and write data/sources/osm.json (DESIGN.md 3.1/3.2).

OpenStreetMap data is ODbL 1.0, (c) OpenStreetMap contributors. We read it through QLever's OSM
planet SPARQL endpoint (https://qlever.dev/api/osm-planet, University of Freiburg; osm2rdf), not
Overpass: overpass-api.de's robots.txt disallows /api/ for every agent and Fresnel honours
robots.txt (DESIGN.md section 2, "Endpoint rulings"); qlever.dev has no robots.txt. A handful of
queries, cached under RAW_ROOT/osm/, our User-Agent, one request every 2 s, backoff on 429/5xx.

Selection: every element (node, way or relation) inside the OSM boundary relation of the United
States (148838), Canada (1428125), Puerto Rico (4422604), the US Virgin Islands (286898), Guam
(306001), the Northern Mariana Islands (306004), American Samoa (2177187) or the US Minor Outlying
Islands (2185386), tagged as one of LIGHTHOUSE_FORMS: man_made=lighthouse; building=lighthouse;
historic=lighthouse; the lifecycle forms disused:/was:/abandoned:/demolished:/razed:/removed:/
destroyed:/ruins:man_made=lighthouse; or seamark:type=light_major / light_vessel. A boundary
relation reaches out over the territorial sea (12 nautical miles), so offshore lights on reefs and
shoals are inside it.

Per element we read every tag (one query) and the geometry (one query; a way's or relation's
position is the centroid of its outline).

What the tags mean (each rule is a field of the source record):

- kind: range_lights for a name with Range / Front / Rear, or seamark:light:category front,
  rear, upper, lower or leading; pier_light for a pier, pierhead, breakwater, jetty or mole name;
  lightship for seamark:type=light_vessel; harbor_light for a man_made=lighthouse that carries
  seamark:type=light_minor (a small light that OSM still maps as a lighthouse); lighthouse
  otherwise.
- status claim: demolished:/razed:/removed:/destroyed: forms -> lost; ruins:man_made, ruins=yes or
  historic=ruins -> ruins; disused:/abandoned:/was: forms, disused=yes, or seamark:status
  extinguished -> inactive (the structure is mapped, the light is out); a lighthouse carrying a
  light (seamark:light:character or :colour) -> active; otherwise no claim.
- light: the characteristic is written in Light List form from seamark:light:character, :group,
  :colour and :period ("Fl(2) W 10s"); sector lights (seamark:light:1:*) give their first
  sector's characteristic with the others kept in extra; focal height from seamark:light:height
  (metres), range from seamark:light:range (nautical miles), fog signal from
  seamark:fog_signal:category.
- extra.enrich_only: a seamark:type=light_major element with no lighthouse tag (a light on a pole,
  a skeleton tower, or a separate light node beside a mapped lighthouse). The merge lets it add its
  light to a station it lies on, never start one (DESIGN.md section 1: no modern beacons).
- extra.minor_beacon_suspect: elements that OSM itself suggests are minor beacons rather than
  lighthouses: a fixme saying "beacon" (787 of Canada's 1,485 lighthouses were imported from
  NRCan CanVec with "fixme=could be a beacon with a light", survey_canada.md 1.7), a
  seamark:type=light_minor with no name, or a name that is a numbered aid ("Light 147",
  "Daybeacon", "Aid to Navigation"), in each case with no register, heritage or Wikidata link. The merge never
  starts a station from one; it lists them for review.
- extra.decorative_hint: tags that suggest a decorative "lighthouse" (miniature golf, a shop, a
  restaurant, a playground, a garden ornament): the merge lists these for review, never hides on
  a hint alone.

Usage: python3 pipeline/fetch_osm.py [--refresh]
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

ENDPOINT = "https://qlever.dev/api/osm-planet"
OUT_PATH = c.REPO / "data" / "sources" / "osm.json"
KEY = "https://www.openstreetmap.org/wiki/Key:"
OSM = "https://www.openstreetmap.org/"

PREFIXES = """PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
PREFIX osmrel: <https://www.openstreetmap.org/relation/>
PREFIX osmway: <https://www.openstreetmap.org/way/>
PREFIX osmnode: <https://www.openstreetmap.org/node/>
PREFIX ogc: <http://www.opengis.net/rdf#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
"""

# Boundary relation -> (country, region or None: the region of a territory's own relation).
BOUNDARIES = {
    "148838": ("US", None), "1428125": ("CA", None), "4422604": ("US", "PR"), "286898": ("US", "VI"),
    "306001": ("US", "GU"), "306004": ("US", "MP"), "2177187": ("US", "AS"), "2185386": ("US", "UM"),
}
LIFECYCLE_PREFIXES = ("disused", "was", "abandoned", "demolished", "razed", "removed", "destroyed", "ruins")
LIGHTHOUSE_FORMS = [("man_made", "lighthouse"), ("building", "lighthouse"), ("historic", "lighthouse")] + [
    (f"{p}:man_made", "lighthouse") for p in LIFECYCLE_PREFIXES] + [
    ("seamark:type", "light_major"), ("seamark:type", "light_vessel")]
LOST_PREFIXES = ("demolished", "razed", "removed", "destroyed")
INACTIVE_PREFIXES = ("disused", "abandoned", "was")

CHARACTER = {
    "f": "F", "fl": "Fl", "lfl": "LFl", "oc": "Oc", "iso": "Iso", "q": "Q", "vq": "VQ", "uq": "UQ",
    "iq": "IQ", "ivq": "IVQ", "iuq": "IUQ", "mo": "Mo", "ffl": "FFl", "fl.lfl": "Fl+LFl", "oc.fl": "OcFl",
    "flfl": "FFl", "al.fl": "Al.Fl", "al.lfl": "Al.LFl", "al.oc": "Al.Oc", "al.iso": "Al.Iso",
    "al.f": "Al", "al": "Al", "al.q": "Al.Q", "q.lfl": "Q+LFl", "vq.lfl": "VQ+LFl", "uq.lfl": "UQ+LFl",
}
COLOUR = {"white": "W", "red": "R", "green": "G", "yellow": "Y", "blue": "Bu", "orange": "Or", "violet": "Vi", "amber": "Am"}
RANGE_CATEGORIES = {"front", "rear", "upper", "lower", "leading"}
DECORATIVE_TAGS = [("leisure", "miniature_golf"), ("leisure", "playground"), ("leisure", "garden"),
                   ("amenity", "restaurant"), ("amenity", "fast_food"), ("amenity", "cafe"), ("amenity", "bar"),
                   ("amenity", "pub"), ("amenity", "ice_cream"), ("tourism", "theme_park"), ("attraction", "*"),
                   ("shop", "*"), ("craft", "*"), ("office", "*"), ("amenity", "car_wash"), ("amenity", "fuel")]
DECORATIVE_NAME_RE = re.compile(r"\b(mini(ature)? golf|putt|golf|replica|decorative|ornamental|model|toy|"
                                r"car wash|restaurant|motel|hotel|mall|plaza|playground)\b", re.I)


def run_query(name: str, query: str, refresh: bool = False) -> list[dict]:
    query = PREFIXES + query
    path = c.raw_dir("osm") / f"{name}_{c.cache_key(query)}.json"
    if not path.exists() or refresh:
        c.log(f"osm: query {name}")
        body = urllib.parse.urlencode({"query": query}).encode()
        c.fetch_cached(ENDPOINT, path, data=body, timeout=300, force=refresh, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        })
    text = path.read_text(encoding="utf-8")
    data, end = json.JSONDecoder().raw_decode(text.lstrip())
    if text.lstrip()[end:].strip():  # QLever sometimes repeats its answer; keep the first (fetch_wikidata.py)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    if "results" not in data:
        raise c.FetchError(f"not a SPARQL answer: {path}")
    return data["results"]["bindings"]


def v(row: dict, key: str) -> str | None:
    x = row.get(key, {}).get("value")
    return x if x not in (None, "") else None


def element_id(uri: str | None) -> str | None:
    """"https://www.openstreetmap.org/way/123" -> "way/123"."""
    if not uri or not uri.startswith(OSM):
        return None
    rest = uri[len(OSM):]
    return rest if re.fullmatch(r"(node|way|relation)/\d+", rest) else None


def sparql_element(eid: str) -> str:
    kind, num = eid.split("/")
    return {"node": "osmnode:", "way": "osmway:", "relation": "osmrel:"}[kind] + num


def select_elements(refresh: bool) -> dict[str, set[str]]:
    """Element id -> the boundary relations that contain it."""
    rels = " ".join(f"osmrel:{r}" for r in BOUNDARIES)
    forms = " UNION ".join('{ ?o osmkey:%s "%s" . }' % (k, val) for k, val in LIGHTHOUSE_FORMS)
    query = "SELECT DISTINCT ?o ?r WHERE { VALUES ?r { %s } ?r ogc:sfContains ?o . %s }" % (rels, forms)
    out: dict[str, set[str]] = {}
    for row in run_query("select", query, refresh):
        eid = element_id(v(row, "o"))
        rel = (v(row, "r") or "").rsplit("/", 1)[-1]
        if eid and rel in BOUNDARIES:
            out.setdefault(eid, set()).add(rel)
    return out


def fetch_tags_and_geometry(eids: list[str], refresh: bool) -> tuple[dict[str, dict], dict[str, str]]:
    tags: dict[str, dict] = {e: {} for e in eids}
    wkts: dict[str, str] = {}
    for i in range(0, len(eids), 1500):
        part = eids[i:i + 1500]
        values = "VALUES ?o { %s }" % " ".join(sparql_element(e) for e in part)
        n = i // 1500
        q_tags = 'SELECT ?o ?k ?val WHERE { %s ?o ?k ?val . FILTER(STRSTARTS(STR(?k), "%s")) }' % (values, KEY)
        for row in run_query(f"tags_{n:02d}", q_tags, refresh):
            eid = element_id(v(row, "o"))
            k = (v(row, "k") or "")[len(KEY):]
            if eid in tags and k and v(row, "val") is not None:
                tags[eid][urllib.parse.unquote(k)] = v(row, "val")
        q_geom = "SELECT ?o ?wkt WHERE { %s ?o geo:hasGeometry/geo:asWKT ?wkt . }" % values
        for row in run_query(f"geom_{n:02d}", q_geom, refresh):
            eid = element_id(v(row, "o"))
            if eid and v(row, "wkt"):
                wkts[eid] = v(row, "wkt")
    return tags, wkts


# ---------------------------------------------------------------------------------------------
# Parsing helpers (unit-tested in test_fetchers.py)
# ---------------------------------------------------------------------------------------------

def wkt_point(wkt: str) -> tuple[float, float] | None:
    """(lat, lon) of a WKT geometry: the point itself, or the mean of a polygon's or line's outer
    ring (good enough for a tower: its outline is a few metres across)."""
    nums = re.findall(r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)", wkt)
    if not nums:
        return None
    w = wkt.lstrip().upper()
    if w.startswith("POINT"):
        lon, lat = float(nums[0][0]), float(nums[0][1])
        return lat, lon
    # The first ring only (a polygon's outer boundary); drop the closing vertex.
    first_ring = re.search(r"\(\s*\(?\s*([^()]+)\)", wkt)
    pts = re.findall(r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)", first_ring.group(1)) if first_ring else nums
    pts = [(float(a), float(b)) for a, b in pts]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    lon = sum(p[0] for p in pts) / len(pts)
    lat = sum(p[1] for p in pts) / len(pts)
    return lat, lon


def parse_float(value: str | None) -> float | None:
    if not value:
        return None
    m = re.match(r"\s*(-?\d+(?:[.,]\d+)?)", value)
    return float(m.group(1).replace(",", ".")) if m else None


def parse_length_m(value: str | None) -> float | None:
    """"24.384" -> 24.4; "80 ft" / "80'" -> 24.4; "12 m" -> 12.0."""
    if not value:
        return None
    x = parse_float(value)
    if x is None:
        return None
    if re.search(r"(ft|feet|foot|')\s*$", value.strip(), re.I):
        return round(x * 0.3048, 2)
    return round(x, 2)


def characteristic(tags: dict, prefix: str = "seamark:light:") -> str | None:
    """Light List form from seamark tags: character Fl, group 2, colour white, period 10 ->
    "Fl(2) W 10s". None when no character is tagged."""
    ch = (tags.get(prefix + "character") or "").strip()
    if not ch:
        return None
    code = CHARACTER.get(ch.lower(), ch)
    group = (tags.get(prefix + "group") or "").strip()
    if group and group not in ("1",):
        code = f"{code}({group})"
    colours = [COLOUR.get(x.strip().lower(), x.strip()) for x in re.split(r"[;,]", tags.get(prefix + "colour") or "") if x.strip()]
    parts = [code]
    if colours:
        parts.append("".join(colours) if code.startswith("Al") else " ".join(dict.fromkeys(colours)))
    period = parse_float(tags.get(prefix + "period"))
    if period:
        parts.append(f"{period:g}s")
    return " ".join(parts)


def light_tags(tags: dict) -> tuple[str | None, float | None, float | None, list[str]]:
    """(characteristic, focal height m, range nm, every sector's characteristic)."""
    main = characteristic(tags)
    sectors = []
    i = 1
    while any(k.startswith(f"seamark:light:{i}:") for k in tags):
        s = characteristic(tags, f"seamark:light:{i}:")
        if s:
            sectors.append(s)
        i += 1
    char = main or (sectors[0] if sectors else None)
    height = parse_float(tags.get("seamark:light:height") or tags.get("seamark:light:1:height"))
    rng = parse_float(tags.get("seamark:light:range") or tags.get("seamark:light:1:range"))
    if rng is None and sectors:
        ranges = [parse_float(tags.get(f"seamark:light:{j}:range")) for j in range(1, i)]
        ranges = [x for x in ranges if x is not None]
        rng = max(ranges) if ranges else None
    return char, height, rng, sectors


def lighthouse_forms(tags: dict) -> list[str]:
    return [f"{k}={val}" for k, val in LIGHTHOUSE_FORMS if tags.get(k) == val]


def is_structure(tags: dict) -> bool:
    """A lighthouse tag of some form (not only a seamark light)."""
    return any(tags.get(k) == "lighthouse" for k, _ in LIGHTHOUSE_FORMS if k != "seamark:type")


def status_claim(tags: dict) -> tuple[str | None, str | None]:
    for p in LOST_PREFIXES:
        if tags.get(f"{p}:man_made") == "lighthouse":
            return "lost", f"{p}:man_made=lighthouse"
    if tags.get("ruins:man_made") == "lighthouse" or tags.get("ruins") in ("yes", "lighthouse") or tags.get("historic") == "ruins":
        return "ruins", "ruins tag"
    for p in INACTIVE_PREFIXES:
        if tags.get(f"{p}:man_made") == "lighthouse":
            return "inactive", f"{p}:man_made=lighthouse"
    if tags.get("disused") == "yes":
        return "inactive", "disused=yes"
    if (tags.get("seamark:status") or "").lower() in ("extinguished", "permanently extinguished", "not_in_operation"):
        return "inactive", f"seamark:status={tags['seamark:status']}"
    if tags.get("man_made") == "lighthouse" and (tags.get("seamark:light:character") or tags.get("seamark:light:colour")
                                                 or tags.get("seamark:light:1:character")):
        return "active", "a lighthouse carrying seamark:light tags"
    return None, None


def name_of(tags: dict) -> str | None:
    for k in ("name", "name:en", "seamark:name", "official_name"):
        if tags.get(k) and tags[k].strip():
            return re.sub(r"\s+", " ", tags[k]).strip()
    return None


def kind_and_role(tags: dict, name: str | None) -> tuple[str, str | None]:
    n = (name or "").lower()
    cat = {x.strip() for x in re.split(r"[;,]", (tags.get("seamark:light:category") or "").lower()) if x.strip()}
    role = None
    if "front" in cat or "lower" in cat or re.search(r"\bfront\b", n) and not re.search(r"\brear\b", n):
        role = "front_range"
    elif "rear" in cat or "upper" in cat or re.search(r"\brear\b", n) and not re.search(r"\bfront\b", n):
        role = "rear_range"
    if tags.get("seamark:type") == "light_vessel":
        return "lightship", None
    if (re.search(r"\brange\b", n) and re.search(r"\blights?\b|\bfront\b|\brear\b|\bbeacon\b|\brange\b$", n)) or (cat & RANGE_CATEGORIES):
        return "range_lights", role
    if re.search(r"\b(pier ?head|pier|breakwater|jetty|mole)\b", n):
        return "pier_light", None
    if (tags.get("man_made") == "lighthouse" and tags.get("seamark:type") == "light_minor"
            and not re.search(r"\blight ?(house|station)\b|\bphare\b|\bfaro\b", n)):
        return "harbor_light", None
    return "lighthouse", None


def structure_type(tags: dict) -> tuple[str | None, str | None]:
    """(structures[].type, material) from tower:construction and the material tags."""
    construction = (tags.get("tower:construction") or "").lower()
    mat_raw = (tags.get("building:material") or tags.get("material") or tags.get("tower:material") or "").lower()
    material = {"brick": "brick", "stone": "stone", "granite": "stone", "masonry": "stone", "wood": "wood",
                "timber": "wood", "concrete": "concrete", "reinforced_concrete": "concrete", "cast_iron": "cast_iron",
                "iron": "iron", "steel": "steel", "metal": "steel", "aluminium": "aluminium", "fiberglass": "fiberglass",
                "plastic": "fiberglass"}.get(mat_raw)
    t = None
    if construction in ("lattice", "framework", "skeleton", "truss"):
        t = "skeletal"
    elif material in ("brick", "stone"):
        t = "conical_masonry"
    elif material == "cast_iron":
        t = "cast_iron"
    elif material == "concrete":
        t = "concrete"
    elif material == "wood":
        t = "wood_frame"
    return t, material


def decorative_hint(tags: dict, name: str | None) -> str | None:
    for k, val in DECORATIVE_TAGS:
        if k in tags and (val == "*" or tags[k] == val):
            return f"{k}={tags[k]}"
    if name and DECORATIVE_NAME_RE.search(name):
        return f"name: {name}"
    return None


NUMBERED_AID_RE = re.compile(r"\b(light|daybeacon|beacon|lt)\s*#?\d+[a-z]?\b|\baid to navigation\b|\bdaybeacon\b|\bdaymark\b", re.I)


def minor_beacon_hint(tags: dict, name: str | None) -> str | None:
    fixme = (tags.get("fixme") or tags.get("FIXME") or "")
    linked = tags.get("wikidata") or tags.get("ref:nrhp") or tags.get("heritage") or tags.get("wikipedia")
    if name and NUMBERED_AID_RE.search(name) and not linked:
        return f"a numbered aid or daybeacon by its name: {name}"
    if re.search(r"\bbeacon\b", fixme, re.I) and not linked:
        return f"fixme={fixme}"
    if tags.get("seamark:type") == "light_minor" and not name and not linked:
        return "seamark:type=light_minor, unnamed"
    return None


def build_record(eid: str, tags: dict, wkt: str | None, rels: set[str], lookup) -> tuple[dict | None, str | None]:
    if not wkt:
        return None, "no_geometry"
    pt = wkt_point(wkt)
    if not pt:
        return None, "no_geometry"
    lat, lon = pt
    countries = {BOUNDARIES[r][0] for r in rels}
    territory = next((BOUNDARIES[r][1] for r in sorted(rels) if BOUNDARIES[r][1]), None)
    if len(countries) != 1:
        return None, "two_countries"
    country = countries.pop()
    region, how = territory, "territory_relation"
    if not region:
        region, how, _km = lookup.lookup(lat, lon, country)
    if not region:
        tagged = regions.parse_region(tags.get("addr:state") or tags.get("addr:province") or "", country)
        region, how = tagged, "addr_tag"
    if not region:
        return None, "no_region"

    name = name_of(tags)
    other_names = []
    for k in ("alt_name", "old_name", "official_name", "name:en", "name:fr", "name:es", "seamark:name", "loc_name", "short_name"):
        for alt in re.split(r";", tags.get(k) or ""):
            alt = alt.strip()
            if alt and alt != name and alt not in other_names:
                other_names.append(alt)
    kind, role = kind_and_role(tags, name)
    status, status_raw = status_claim(tags)
    char, focal, rng, sectors = light_tags(tags)
    stype, material = structure_type(tags)
    height = parse_length_m(tags.get("height") or tags.get("seamark:landmark:height"))
    built = None
    m = re.match(r"^\s*(?:~|c\.?\s*|before\s+|after\s+)?(\d{4})", tags.get("start_date") or "")
    if m and 1500 <= int(m.group(1)) <= 2100:
        built = int(m.group(1))
    registers = []
    if tags.get("ref:nrhp"):
        for n in re.split(r"[;,]", tags["ref:nrhp"]):
            n = n.strip()
            if n:
                registers.append({"register": "NRHP", "number": n, "url": f"https://npgallery.nps.gov/AssetDetail/NRIS/{n}"})
    links = [{"label": "OpenStreetMap", "url": f"https://www.openstreetmap.org/{eid}", "kind": "osm"}]
    if tags.get("website") and tags["website"].startswith(("http://", "https://")):
        links.append({"label": "Website", "url": tags["website"], "kind": "website"})
    if tags.get("wikipedia") and ":" in tags["wikipedia"]:
        lang, title = tags["wikipedia"].split(":", 1)
        if re.fullmatch(r"[a-z]{2,3}", lang):
            links.append({"label": "Wikipedia" if lang == "en" else f"Wikipedia ({lang})",
                          "url": f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title.strip().replace(' ', '_'))}", "kind": "wikipedia"})
    wikidata = tags.get("wikidata") if re.fullmatch(r"Q\d+", tags.get("wikidata") or "") else None
    events = []
    if built:
        events.append({"year": built, "event": "built", "note": None, "from": "osm"})

    extra: dict = {"forms": lighthouse_forms(tags), "region_from": how, "osm_tags": dict(sorted(tags.items()))}
    if wikidata:
        extra["wikidata"] = wikidata
    if sectors:
        extra["light_sectors"] = sectors
    if tags.get("seamark:light:reference"):
        extra["light_reference"] = tags["seamark:light:reference"]
    if tags.get("access"):
        extra["access_tag"] = tags["access"]
    if not is_structure(tags):
        extra["enrich_only"] = "A seamark light with no lighthouse tag: it may add its light to a station, never start one."
    hint = minor_beacon_hint(tags, name)
    if hint:
        extra["minor_beacon_suspect"] = hint
    deco = decorative_hint(tags, name)
    if deco and not (char or tags.get("seamark:type") or wikidata or registers):
        extra["decorative_hint"] = deco

    aton = {"uscg_llnr": None, "arlhs": None, "ccg_list_number": None, "nga": None}
    ref = tags.get("seamark:light:reference") or ""
    mref = re.match(r"^\s*(?:USCG\s+)?(\d)-(\d+(?:\.\d+)?)\s*$", ref)
    if country == "US" and mref:
        aton["uscg_llnr"] = f"{mref.group(1)}-{mref.group(2)}"
    rec = {
        "key": f"osm:{eid}",
        "url": f"https://www.openstreetmap.org/{eid}",
        "name": name,
        "other_names": other_names,
        "country": country,
        "region": region,
        "county": None,
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "precision": "exact",
        "kind": kind,
        "kind_raw": "; ".join(extra["forms"]) or None,
        "role": role,
        "status": status,
        "status_raw": status_raw,
        "structure": {"type": stype, "material": material, "built": built, "height_m": height,
                      "status": {"lost": "lost", "ruins": "ruins"}.get(status or "", "standing")},
        "light": {"first_lit": None, "deactivated": None, "characteristic": char, "focal_height_m": focal,
                  "range_nm": rng, "fog_signal": (tags.get("seamark:fog_signal:category") or None), "lens": None},
        "setting": None,
        "registers": registers,
        "aton": aton,
        "agency": tags.get("operator") or None,
        "ownership": None,
        "events": events,
        "photos": [],
        "links": links,
        "relations": {},
        "extra": extra,
    }
    return rec, None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch Fresnel's OpenStreetMap extract")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    found = select_elements(args.refresh)
    eids = sorted(found, key=lambda e: (e.split("/")[0], int(e.split("/")[1])))
    c.log(f"osm: {len(eids)} elements selected")
    tags, wkts = fetch_tags_and_geometry(eids, args.refresh)
    lookup = regions.region_lookup(c.RAW_ROOT)
    records, skipped = [], Counter()
    for eid in eids:
        rec, why = build_record(eid, tags[eid], wkts.get(eid), found[eid], lookup)
        if rec:
            records.append(rec)
        else:
            skipped[why] += 1
    cache_files = sorted(c.raw_dir("osm").glob("*.json"))
    c.write_source_json(
        OUT_PATH, source="osm",
        title="OpenStreetMap: lighthouses and major lights in the United States and Canada",
        url="https://www.openstreetmap.org/copyright",
        license_text="ODbL 1.0. (c) OpenStreetMap contributors. Read through QLever (qlever.dev/api/osm-planet).",
        records=records,
        notes={"selected": len(eids), "written": len(records), "skipped": dict(sorted(skipped.items())),
               "endpoint": ENDPOINT},
        retrieved=c.retrieved_date(*cache_files),
    )
    flags = Counter(k for r in records for k in ("enrich_only", "minor_beacon_suspect", "decorative_hint") if r["extra"].get(k))
    c.log(f"osm: wrote {len(records)} records; skipped {dict(skipped)}")
    c.log(f"  country {dict(Counter(r['country'] for r in records))}; kind {dict(Counter(r['kind'] for r in records))}")
    c.log(f"  status {dict(Counter(r['status'] for r in records))}; flags {dict(flags)}; unnamed {sum(1 for r in records if not r['name'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
