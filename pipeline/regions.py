"""Countries and their regions: the one table every part of the pipeline reads
(DESIGN.md 3.3; mirrored for the site by web/src/lib/regions.ts).

- A station's `country` is an ISO 3166-1 alpha-2 code ("US", "CA"); its `region` the state,
  territory, province or territory code inside it, as the postal services write them ("ME",
  "PR", "GU", "NS", "QC"). The US territories are regions of the US (owner decision
  2026-10-21): Puerto Rico PR, the US Virgin Islands VI, Guam GU, the Northern Mariana Islands
  MP, American Samoa AS, and the US Minor Outlying Islands UM (Navassa, Midway, Wake...).
  The District of Columbia is DC.
- Ids are `<country>-<region>-<slug>`, lower case: `us-me-portland-head`, `us-pr-punta-higuero`,
  `ca-ns-sambro-island`.
- Station files: `data/stations/<dir>/<id>.json`, where `<dir>` is the bare code for a US state
  or territory (`me/`, `pr/`) and `<country>-<region>` for any other country (`ca-ns/`), as in
  Firefinder. A two-letter folder is always a US state or territory; a hyphenated one names its
  country, so a future country whose codes repeat a US one (Australia's WA) never shares a folder.
  `station_dir()` is the rule.
- Region codes are unique across the countries listed here (checked at import), so a region code
  alone says its country.

Bounding boxes are padded and for sanity checks only: they flag a sign slip or a row filed under
the wrong region for a human; they never move a point. Several regions need more than one box:
Alaska (the Aleutians cross the 180th meridian: Attu is at 172.9 E), Hawaii (the Northwestern
Hawaiian Islands), the Minor Outlying Islands (scattered across the Pacific, and Navassa in the
Caribbean). Guam and the Northern Marianas lie near 145 E and American Samoa near 170 W.

`RegionLookup` finds the region of a point from two public-domain boundary files cached under
RAW_ROOT: the US Census Bureau's TIGERweb state boundaries (the states, DC, PR, VI, GU, MP and
AS, drawn out over their waters, so most offshore lights fall inside them) and Natural Earth's
admin-1 polygons (Canada's provinces and territories, and the Minor Outlying Islands). A point
inside no polygon (a light on a reef or a rock the generalised coastline leaves out) takes the
region found by probing outward in rings, up to about 60 km, when exactly one region answers at
the nearest ring that finds any.

Python 3.12, standard library only.
"""
from __future__ import annotations

import functools
import json
import math
import re
import unicodedata
from pathlib import Path

COUNTRY_NAMES = {"US": "United States", "CA": "Canada"}
COUNTRY_IN_TEXT = {"US": "the United States", "CA": "Canada"}
REGION_WORDS = {"US": ("state or territory", "states and territories"),
                "CA": ("province or territory", "provinces and territories")}
COUNTRY_ORDER = ["US", "CA"]

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
US_OTHER = {
    "DC": "District of Columbia",
    "PR": "Puerto Rico", "VI": "U.S. Virgin Islands", "GU": "Guam",
    "MP": "Northern Mariana Islands", "AS": "American Samoa",
    "UM": "U.S. Minor Outlying Islands",
}
# The territories, for page copy ("Puerto Rico, a US territory").
US_TERRITORIES = ("PR", "VI", "GU", "MP", "AS", "UM")
CA_PROVINCES = {
    "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador", "NS": "Nova Scotia", "NT": "Northwest Territories",
    "NU": "Nunavut", "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
    "SK": "Saskatchewan", "YT": "Yukon",
}
REGION_NAMES_BY_COUNTRY = {"US": {**US_STATES, **US_OTHER}, "CA": CA_PROVINCES}

CA_FRENCH = {
    "AB": "Alberta", "BC": "Colombie-Britannique", "MB": "Manitoba", "NB": "Nouveau-Brunswick",
    "NL": "Terre-Neuve-et-Labrador", "NS": "Nouvelle-Écosse", "NT": "Territoires du Nord-Ouest",
    "NU": "Nunavut", "ON": "Ontario", "PE": "Île-du-Prince-Édouard", "QC": "Québec",
    "SK": "Saskatchewan", "YT": "Yukon",
}
_ALIASES = {
    "pq": "QC", "que": "QC", "province of quebec": "QC", "province de quebec": "QC",
    "newfoundland": "NL", "labrador": "NL", "nfld": "NL", "nf": "NL",
    "nwt": "NT", "n.w.t": "NT", "yukon territory": "YT", "yk": "YT",
    "pei": "PE", "p.e.i": "PE", "b.c": "BC", "n.b": "NB", "n.s": "NS",
    "washington state": "WA", "district of columbia": "DC", "washington, d.c": "DC",
    "virgin islands": "VI", "us virgin islands": "VI", "united states virgin islands": "VI",
    "commonwealth of puerto rico": "PR", "northern marianas": "MP", "cnmi": "MP",
    "commonwealth of the northern mariana islands": "MP",
    "united states minor outlying islands": "UM", "us minor outlying islands": "UM",
    "minor outlying islands": "UM",
}

REGION_COUNTRY: dict[str, str] = {}
for _c, _tbl in REGION_NAMES_BY_COUNTRY.items():
    for _code in _tbl:
        if _code in REGION_COUNTRY:  # pragma: no cover - a table edit gone wrong
            raise RuntimeError(f"region code {_code} is used by {REGION_COUNTRY[_code]} and {_c}; "
                               "qualify region keys by country first (regions.py)")
        REGION_COUNTRY[_code] = _c
REGION_NAMES: dict[str, str] = {code: name for tbl in REGION_NAMES_BY_COUNTRY.values() for code, name in tbl.items()}

# Wikidata items for the territories and DC, for sources that name the place rather than a code.
WIKIDATA_REGION_ITEMS = {
    "Q1183": "PR", "Q11703": "VI", "Q16635": "GU", "Q16644": "MP", "Q16641": "AS",
    "Q16645": "UM", "Q61": "DC",
}
# The Wikidata country items whose places are Fresnel regions (P17 values).
WIKIDATA_COUNTRY_ITEMS = {"Q30": "US", "Q16": "CA", **{q: "US" for q in WIKIDATA_REGION_ITEMS if q != "Q61"}}

# ---------------------------------------------------------------------------------------------
# Boxes: (lat_min, lat_max, lon_min, lon_max), padded. A region may have several.
# Padded further than Firefinder's at sea: offshore lights (Frying Pan Shoals, Nantucket Shoals,
# St. Paul Island, Mona Island) sit well outside a state's land.
# ---------------------------------------------------------------------------------------------

REGION_BOXES: dict[str, list[tuple[float, float, float, float]]] = {
    "AL": [(29.9, 35.1, -88.6, -84.8)],
    "AK": [(51.0, 71.8, -180.0, -129.0), (51.0, 53.3, 172.0, 180.0)],
    "AZ": [(31.1, 37.1, -114.9, -108.9)],
    "AR": [(32.9, 36.6, -94.7, -89.5)],
    "CA": [(32.3, 42.1, -124.6, -114.0)],
    "CO": [(36.9, 41.1, -109.2, -101.9)],
    "CT": [(40.9, 42.1, -73.8, -71.7)],
    "DE": [(38.3, 39.9, -75.9, -74.8)],
    "FL": [(24.3, 31.1, -87.7, -79.7)],
    "GA": [(30.3, 35.1, -85.7, -80.4)],
    "HI": [(18.7, 22.4, -160.4, -154.6), (22.3, 28.6, -178.5, -160.0)],
    "ID": [(41.9, 49.1, -117.3, -110.9)],
    "IL": [(36.9, 42.6, -91.6, -87.0)],
    "IN": [(37.7, 41.9, -88.2, -84.7)],
    "IA": [(40.3, 43.6, -96.7, -90.0)],
    "KS": [(36.9, 40.1, -102.1, -94.5)],
    "KY": [(36.4, 39.2, -89.6, -81.9)],
    "LA": [(28.5, 33.1, -94.1, -88.7)],
    "ME": [(42.9, 47.5, -71.2, -66.8)],
    "MD": [(37.8, 39.8, -79.5, -74.9)],
    "MA": [(40.3, 43.0, -73.6, -69.0)],
    "MI": [(41.6, 48.4, -90.5, -82.1)],
    "MN": [(43.4, 49.5, -97.3, -89.4)],
    "MS": [(29.9, 35.1, -91.7, -88.0)],
    "MO": [(35.9, 40.7, -95.9, -89.0)],
    "MT": [(44.3, 49.1, -116.1, -104.0)],
    "NE": [(39.9, 43.1, -104.2, -95.3)],
    "NV": [(34.9, 42.1, -120.1, -113.9)],
    "NH": [(42.6, 45.4, -72.6, -70.4)],
    "NJ": [(38.6, 41.4, -75.6, -73.6)],
    "NM": [(31.2, 37.1, -109.1, -102.9)],
    "NY": [(40.3, 45.1, -79.8, -71.7)],
    "NC": [(33.3, 36.7, -84.4, -75.0)],
    "ND": [(45.9, 49.1, -104.1, -96.5)],
    "OH": [(38.3, 42.0, -84.9, -80.4)],
    "OK": [(33.5, 37.1, -103.1, -94.3)],
    "OR": [(41.9, 46.4, -124.8, -116.4)],
    "PA": [(39.6, 42.4, -80.6, -74.6)],
    "RI": [(40.9, 42.1, -71.9, -71.0)],
    "SC": [(31.9, 35.3, -83.5, -78.4)],
    "SD": [(42.4, 46.1, -104.1, -96.3)],
    "TN": [(34.9, 36.8, -90.4, -81.6)],
    "TX": [(25.6, 36.6, -106.7, -93.4)],
    "UT": [(36.9, 42.1, -114.2, -108.9)],
    "VT": [(42.6, 45.1, -73.5, -71.4)],
    "VA": [(36.5, 39.5, -83.7, -75.0)],
    "WA": [(45.5, 49.1, -124.9, -116.9)],
    "WV": [(37.1, 40.7, -82.7, -77.6)],
    "WI": [(42.4, 47.4, -93.0, -86.2)],
    "WY": [(40.9, 45.1, -111.2, -104.0)],
    "DC": [(38.7, 39.0, -77.2, -76.9)],
    # US territories
    "PR": [(17.7, 18.7, -68.1, -65.1)],              # Mona and Desecheo to Culebra and Vieques
    "VI": [(17.6, 18.5, -65.2, -64.5)],
    "GU": [(13.1, 13.8, 144.5, 145.1)],              # about 145 E
    "MP": [(14.0, 20.7, 144.8, 146.2)],
    "AS": [(-14.7, -10.9, -171.2, -168.0)],          # about 170 W; Swains Island at 11 S
    "UM": [(18.2, 18.6, -75.2, -74.8),               # Navassa Island
           (28.1, 28.5, -177.6, -177.2),             # Midway Atoll
           (19.1, 19.4, 166.5, 166.8),               # Wake Island
           (16.6, 16.9, -169.7, -169.3),             # Johnston Atoll
           (5.7, 6.6, -162.6, -161.9),               # Palmyra Atoll, Kingman Reef
           (-0.5, 0.9, -176.8, -159.9)],             # Howland, Baker, Jarvis
    # Canada
    "AB": [(48.9, 60.1, -120.1, -109.9)],
    "BC": [(48.2, 60.1, -139.2, -114.0)],
    "MB": [(48.9, 60.1, -102.2, -88.9)],
    "NB": [(44.4, 48.2, -69.2, -63.7)],
    "NL": [(46.5, 60.5, -67.9, -52.5)],
    "NS": [(43.3, 47.3, -66.5, -59.5)],              # Sable Island; St. Paul Island at 47.2 N
    "NT": [(59.9, 78.9, -136.6, -101.9)],
    "NU": [(51.6, 83.2, -121.1, -61.0)],
    "ON": [(41.6, 56.9, -95.2, -74.3)],
    "PE": [(45.9, 47.1, -64.5, -61.9)],
    "QC": [(44.9, 62.6, -79.8, -57.1)],
    "SK": [(48.9, 60.1, -110.1, -101.3)],
    "YT": [(59.9, 69.7, -141.1, -123.7)],
}


def country_of(region: str | None) -> str | None:
    """"NS" -> "CA", "ME" -> "US", "PR" -> "US"; None for an unknown code."""
    return REGION_COUNTRY.get((region or "").upper()) if region else None


def region_name(region: str | None) -> str:
    if not region:
        return ""
    return REGION_NAMES.get(region.upper(), region)


def region_with_country(region: str | None) -> str:
    """"Maine"; "Puerto Rico"; "Nova Scotia, Canada" (page copy)."""
    name = region_name(region)
    c = country_of(region)
    if c and c != "US" and name:
        return f"{name}, {COUNTRY_NAMES[c]}"
    return name


def id_prefix(country: str | None, region: str | None) -> str:
    """"us-me", "ca-ns". A missing region is "xx" (validate.py rejects it)."""
    c = (country or country_of(region) or "US").lower()
    return f"{c}-{(region or 'xx').lower()}"


def station_dir(station_id: str) -> str:
    """The data/stations/ folder of a station: "me" for us-me-..., "pr" for us-pr-...,
    "ca-ns" for ca-ns-..."""
    parts = station_id.split("-")
    if len(parts) < 2:
        return "xx"
    return parts[1] if parts[0] == "us" else f"{parts[0]}-{parts[1]}"


def fold(text: str) -> str:
    """Lower case, accents dropped, spaces collapsed: "Québec" -> "quebec"."""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", t).strip()


_BY_NAME: dict[str, str] = {}
for _code, _name in REGION_NAMES.items():
    _BY_NAME[fold(_name)] = _code
_BY_NAME["us virgin islands"] = "VI"
for _code, _name in CA_FRENCH.items():
    _BY_NAME[fold(_name)] = _code
    _BY_NAME[fold(_name).replace("-", " ")] = _code
for _alias, _code in _ALIASES.items():
    _BY_NAME[_alias] = _code


def parse_region(text: str | None, country: str | None = None) -> str | None:
    """A region code from a code, an ISO 3166-2 code or a name, English or French: "Maine",
    "ME", "US-ME", "Puerto Rico", "CA-NS", "Québec", "Colombie-Britannique" -> code. None when
    the text names no region (or one of another country than `country`). Never guesses."""
    if not text:
        return None
    t = fold(str(text)).strip(" .,")
    m = re.fullmatch(r"(us|ca)-([a-z]{2})", t)
    if m:
        code = m.group(2).upper()
        code = code if REGION_COUNTRY.get(code) == m.group(1).upper() else None
    elif len(t) == 2 and t.upper() in REGION_COUNTRY:
        code = t.upper()
    else:
        code = _BY_NAME.get(t) or _BY_NAME.get(t.replace(".", "")) or _BY_NAME.get(t.replace("-", " "))
    if code and country and REGION_COUNTRY.get(code) != country.upper():
        return None
    return code


def _in_box(box: tuple, lat: float, lon: float) -> bool:
    a, b, c, d = box
    return a <= lat <= b and c <= lon <= d


def in_region_box(region: str | None, lat: float, lon: float) -> bool:
    """True when the point is inside one of the region's boxes. Unknown regions: True (no claim)."""
    boxes = REGION_BOXES.get((region or "").upper())
    if not boxes:
        return True
    return any(_in_box(b, lat, lon) for b in boxes)


def regions_at(lat: float, lon: float, country: str | None = None) -> list[str]:
    """Every region whose box holds the point (boxes overlap along borders), in code order."""
    out = []
    for code, boxes in sorted(REGION_BOXES.items()):
        if country and REGION_COUNTRY.get(code) != country:
            continue
        if any(_in_box(b, lat, lon) for b in boxes):
            out.append(code)
    return out


def in_country(country: str | None, lat: float, lon: float) -> bool:
    c = (country or "").upper()
    return any(_in_box(b, lat, lon) for code, boxes in REGION_BOXES.items()
               if REGION_COUNTRY.get(code) == c for b in boxes)


def in_coverage(lat: float, lon: float) -> bool:
    """Inside the area Fresnel covers: any region box of any country listed."""
    return any(_in_box(b, lat, lon) for boxes in REGION_BOXES.values() for b in boxes)


def flag_coordinate(region: str | None, lat: float, lon: float) -> str | None:
    """A short problem code, or None if the coordinate looks plausible for the region.

    North America is west of Greenwich and north of the equator, so a positive longitude or a
    negative latitude is a sign slip -- except inside a box of the region itself (the Aleutians
    west of 180, Guam, the Northern Marianas, Wake, American Samoa)."""
    boxes = REGION_BOXES.get((region or "").upper())
    if boxes and any(_in_box(b, lat, lon) for b in boxes):
        return None
    if not boxes:
        return "unknown_region"
    if lon > 0 and in_region_box(region, lat, -lon):
        return "lon_positive_sign"
    if lat < 0 and in_region_box(region, -lat, lon):
        return "lat_negative_sign"
    return "outside_region_bbox"


# ---------------------------------------------------------------------------------------------
# Local units ("county" in the data model)
# ---------------------------------------------------------------------------------------------

AK_CENSUS_AREAS = {
    "aleutians west", "bethel", "chugach", "copper river", "dillingham", "hoonah-angoon",
    "kusilvak", "nome", "prince of wales-hyder", "southeast fairbanks", "yukon-koyukuk",
    "valdez-cordova", "wade hampton", "skagway-hoonah-angoon", "wrangell-petersburg",
    "prince of wales-outer ketchikan",
}
_UNIT_SUFFIX_RE = re.compile(
    r"\b(County|Parish|Borough|Census Area|Municipality|City and Borough|Municipio|District|"
    r"Island|Islands|Village)$", re.I)


def local_unit_label(country: str | None, region: str | None, county: str | None) -> str | None:
    """The local unit as a page writes it: "Cumberland County", "Plaquemines Parish", "Nome
    Census Area", "Ponce" (Puerto Rico's municipios are written bare, as Puerto Rico writes them),
    a Canadian unit exactly as its source names it. None when there is no county."""
    if not county or not str(county).strip():
        return None
    c = str(county).strip()
    country = (country or country_of(region) or "US").upper()
    if country != "US":
        return c
    reg = (region or "").upper()
    if _UNIT_SUFFIX_RE.search(c) or "/" in c or reg in US_TERRITORIES or reg == "DC":
        return c
    if reg == "LA":
        return f"{c} Parish"
    if reg == "AK":
        return f"{c} Census Area" if fold(c) in AK_CENSUS_AREAS else f"{c} Borough"
    return f"{c} County"


# ---------------------------------------------------------------------------------------------
# Point in region
# ---------------------------------------------------------------------------------------------

CENSUS_STATES_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
    "State_County/MapServer/0/query?where=1%3D1&outFields=STUSAB,STATE,NAME"
    "&outSR=4326&f=geojson&geometryPrecision=3"
)
NATURAL_EARTH_ADMIN1_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/"
    "ne_10m_admin_1_states_provinces.geojson")


def _ring_bbox(ring) -> tuple[float, float, float, float]:
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


class _Polys:
    """Polygons of one region, each with its bbox, for quick point-in-polygon tests."""

    def __init__(self) -> None:
        self.parts: list[tuple[tuple[float, float, float, float], list]] = []

    def add(self, geom: dict) -> None:
        if not geom:
            return
        polys = geom.get("coordinates") if geom.get("type") == "MultiPolygon" else [geom.get("coordinates")]
        for poly in polys or []:
            if poly and poly[0]:
                self.parts.append((_ring_bbox(poly[0]), poly))

    @staticmethod
    def _inside(lon: float, lat: float, poly) -> bool:
        inside = False
        for ring in poly:
            n = len(ring)
            j = n - 1
            for i in range(n):
                x1, y1 = ring[i][0], ring[i][1]
                x2, y2 = ring[j][0], ring[j][1]
                if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
                j = i
        return inside

    def contains(self, lat: float, lon: float) -> bool:
        for (x0, y0, x1, y1), poly in self.parts:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and self._inside(lon, lat, poly):
                return True
        return False


class RegionLookup:
    """Point -> region code, from the Census state boundaries (US and its territories, waters
    included) and Natural Earth admin-1 (Canada, the Minor Outlying Islands)."""

    PROBE_KM = (2, 5, 10, 20, 35, 60)
    PROBE_DIRECTIONS = 16

    def __init__(self, census_path: Path | None, admin1_path: Path | None) -> None:
        self.polys: dict[str, _Polys] = {}
        if census_path and census_path.exists():
            data = json.loads(census_path.read_text(encoding="utf-8"))
            for feat in data.get("features", []):
                code = (feat.get("properties") or {}).get("STUSAB")
                if code in REGION_COUNTRY:
                    self.polys.setdefault(code, _Polys()).add(feat.get("geometry") or {})
        if admin1_path and admin1_path.exists():
            data = json.loads(admin1_path.read_text(encoding="utf-8"))
            for feat in data.get("features", []):
                p = feat.get("properties") or {}
                iso_a2 = p.get("iso_a2")
                iso = str(p.get("iso_3166_2") or "")
                if iso_a2 == "CA" and iso.startswith("CA-"):
                    code = iso[3:]
                elif iso_a2 == "UM":
                    code = "UM"
                elif iso_a2 in ("US", "PR", "VI", "GU", "MP", "AS") and iso_a2 != "US" and iso_a2 not in self.polys:
                    code = iso_a2  # only when the Census file is missing
                else:
                    continue
                if code in REGION_COUNTRY:
                    self.polys.setdefault(code, _Polys()).add(feat.get("geometry") or {})
        # A stable order, so ties are broken the same way every run.
        self.codes = sorted(self.polys)

    def _hits(self, lat: float, lon: float, country: str | None) -> list[str]:
        return [c for c in self.codes
                if (not country or REGION_COUNTRY[c] == country) and self.polys[c].contains(lat, lon)]

    def lookup(self, lat: float, lon: float, country: str | None = None) -> tuple[str | None, str | None, float | None]:
        """(region, method, km): method "inside" or "nearest" (km = the probe ring that found it),
        or (None, reason, None): "none_near" or "ambiguous"."""
        hits = self._hits(lat, lon, country)
        if len(hits) == 1:
            return hits[0], "inside", 0.0
        if len(hits) > 1:
            return None, "ambiguous", 0.0
        coslat = max(math.cos(math.radians(lat)), 0.05)
        for km in self.PROBE_KM:
            found: dict[str, int] = {}
            for i in range(self.PROBE_DIRECTIONS):
                a = 2 * math.pi * i / self.PROBE_DIRECTIONS
                dlat = km / 111.2 * math.cos(a)
                dlon = km / (111.2 * coslat) * math.sin(a)
                lo = lon + dlon
                if lo > 180:
                    lo -= 360
                if lo < -180:
                    lo += 360
                for code in self._hits(lat + dlat, lo, country):
                    found[code] = found.get(code, 0) + 1
            if len(found) == 1:
                return next(iter(found)), "nearest", float(km)
            if len(found) > 1:
                # Two regions at the same distance (a light in a strait between two): take the
                # one most of the probes found, if one clearly leads; otherwise say so.
                ranked = sorted(found.items(), key=lambda kv: (-kv[1], kv[0]))
                if ranked[0][1] >= 2 * ranked[1][1]:
                    return ranked[0][0], "nearest", float(km)
                return None, "ambiguous", float(km)
        return None, "none_near", None


@functools.lru_cache(maxsize=2)
def region_lookup(raw_root: Path) -> RegionLookup:
    """RegionLookup over the cached boundary files, fetched once if missing."""
    import _common as c

    census = raw_root / "census" / "states.geojson"
    admin1 = raw_root / "natural_earth" / "ne_10m_admin_1_states_provinces.geojson"
    if not census.exists():
        c.fetch_cached(CENSUS_STATES_URL, census, timeout=300)
    if not admin1.exists():
        c.fetch_cached(NATURAL_EARTH_ADMIN1_URL, admin1, timeout=300)
    return RegionLookup(census, admin1)
