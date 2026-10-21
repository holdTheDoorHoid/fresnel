#!/usr/bin/env python3
"""Russ Rowlett's Lighthouse Directory, the Canadian pages; adds them to data/sources/rowlett.json
(DESIGN.md 2.3, 3.8). The source id is `rowlett`, shared with any US fetcher: this module is the
Canadian function, `fetch_canada()`, and its writer keeps the non-Canadian records the file already
holds.

Source: https://www.ibiblio.org/lighthouse/<page>.htm, 39 regional pages for Canada (ab sk mb bcn
bcs bcv nbe nbn nbs lab nfln nfle nflw nscbe nscbw nse nsnw nss nsbf pei peiw ongb onno onnw onso
onse onsw onlh qcc qce qcn qcs qcsw qcw nwt nvt), static UTF-8 HTML, 50-120 KB each. robots.txt:
`Crawl-delay: 2`, disallows only unrelated project directories. The survey's copies
(RAW_ROOT/survey/canada/ibiblio/) are read in place of fetching again.

Licence: (c) 2026 Russ Rowlett and the University of North Carolina at Chapel Hill. Facts only
(years, status, identifiers, a few numbers), never the text; the credit line and a link to the
region's page go on every station that uses it.

An entry is a `<dt>` (the name, usually an anchor to Lighthouse Friends' page for the light) followed
by a `<dd>` (the description). What is read, and nothing of the prose:

- name: the `<dt>` text without Rowlett's marks. `*` marks a notable light, `#` a light that no longer
  exists, `[...]` a minor light, and `(n)` after the name is the number of the tower now (or last)
  standing there ("Quaker Island (3)" is the third tower). Other parentheses are other names or
  "relocated to X". These become `extra.notable`, `extra.gone`, `extra.minor_marker`,
  `extra.tower_number`.
- years: the opening clause, "1981 (station established 1883)", "Date unknown (station established
  1874)", "2012 replica of 1867 lighthouse". An exact tower year is `structure.built` and a `built`
  event; the station's year is `light.first_lit` and a `first_lit` event. "Around 1900", "1950s" and
  a "?" are kept in `extra` as text, not as a year.
- status: `active` ("Active", "Reactivated"), `inactive` ("Inactive since 1984", "Apparently
  inactive"), `lost` (a `#` mark, or "Demolished / Destroyed / Removed / Replaced in 2015. This was a
  tower..."), `replica`. Years in "since 1984", "Demolished in 2003" become `deactivated`, `removed`
  and `destroyed` events.
- focal plane and the tower's height in metres, its material.
- the identifiers that join the other sources: ARLHS (`CAN-422`), the Canadian Coast Guard List of
  Lights number (`CCG A-456`: the volume's letter, then the number), the Admiralty number
  (`H3680`), the NGA number, and the Lighthouse Friends id in the anchor. They are written in
  `aton`/`registers` and as `extra.join_keys`, which the merge reads.
- access, as Rowlett states it ("Accessible only by boat", "Site open, tower closed"): `extra.access`.
- owner / site manager text (`agency`).

The Directory has no coordinates, so a record carries none: it can only join a station that
another source has placed, by an identifier or a name. (A station-level record: `extra.station_level`.)

Usage: python3 pipeline/fetch_rowlett.py [--refresh]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ca_common as cc  # noqa: E402
import _common as c  # noqa: E402

SOURCE = "rowlett"
OUT_PATH = c.REPO / "data" / "sources" / f"{SOURCE}.json"
PAGE_URL = "https://www.ibiblio.org/lighthouse/{page}.htm"
LICENSE = ("(c) 2026 Russ Rowlett and the University of North Carolina at Chapel Hill. Facts only (years, status, "
           "identifiers), with credit and a link to the Directory page.")
PAGES = {
    "ab": ("AB", "Alberta"), "sk": ("SK", "Saskatchewan"), "mb": ("MB", "Manitoba"),
    "bcn": ("BC", "British Columbia: north coast"), "bcs": ("BC", "British Columbia: south, interior"),
    "bcv": ("BC", "British Columbia: Vancouver Island"),
    "nbe": ("NB", "New Brunswick: east"), "nbn": ("NB", "New Brunswick: north"), "nbs": ("NB", "New Brunswick: south"),
    "lab": ("NL", "Labrador"), "nfln": ("NL", "Newfoundland: north"), "nfle": ("NL", "Newfoundland: east"),
    "nflw": ("NL", "Newfoundland: west and south"),
    "nscbe": ("NS", "Nova Scotia: Cape Breton east"), "nscbw": ("NS", "Nova Scotia: Cape Breton west"),
    "nse": ("NS", "Nova Scotia: eastern shore"), "nsnw": ("NS", "Nova Scotia: northwest"),
    "nss": ("NS", "Nova Scotia: south"), "nsbf": ("NS", "Nova Scotia: Bay of Fundy"),
    "pei": ("PE", "Prince Edward Island"), "peiw": ("PE", "Prince Edward Island: west"),
    "ongb": ("ON", "Ontario: Georgian Bay"), "onno": ("ON", "Ontario: north"), "onnw": ("ON", "Ontario: northwest"),
    "onso": ("ON", "Ontario: southern Ontario"), "onse": ("ON", "Ontario: southeast"), "onsw": ("ON", "Ontario: southwest"),
    "onlh": ("ON", "Ontario: Lake Huron"),
    "qcc": ("QC", "Quebec: centre"), "qce": ("QC", "Quebec: east"), "qcn": ("QC", "Quebec: north shore"),
    "qcs": ("QC", "Quebec: south"), "qcsw": ("QC", "Quebec: southwest"), "qcw": ("QC", "Quebec: west"),
    "nwt": ("NT", "Northwest Territories"), "nvt": (None, "Nunavut and northern Quebec"),
}
SURVEY_DIR = cc.SURVEY / "ibiblio"

# ---------------------------------------------------------------------------------------------
# Reading a page into (name block, description block) pairs
# ---------------------------------------------------------------------------------------------


class EntryParser(HTMLParser):
    """Pairs each <dd> with the <dt> before it. Rowlett's pages leave tags open and put section
    headings in <dt> without a <dd>, so the entry's name is the last <dt> before its <dd>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.entries: list[dict] = []
        self._cur: str | None = None
        self._buf: list[str] = []
        self._hrefs: list[str] = []
        self._last_dt: dict | None = None
        self._last_dt_used = False

    def _flush(self) -> None:
        if self._cur is None:
            return
        text = re.sub(r"\s+", " ", "".join(self._buf).replace("\xa0", " ")).strip()
        block = {"text": text, "hrefs": list(self._hrefs)}
        if self._cur == "dt":
            self._last_dt, self._last_dt_used = block, False
        elif self._last_dt is not None and not self._last_dt_used:
            self._last_dt_used = True
            self.entries.append({"dt": self._last_dt, "dd": block})
        self._cur, self._buf, self._hrefs = None, [], []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("dt", "dd"):
            self._flush()
            self._cur = tag
        elif tag in ("br", "p") and self._cur:
            self._buf.append(" ")
        elif tag == "a" and self._cur:
            href = dict(attrs).get("href")
            if href:
                self._hrefs.append(href)
        elif tag in ("dl", "table", "tr", "td") and self._cur:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag in ("dt", "dd"):
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._cur:
            self._buf.append(data)

    def close(self) -> None:
        self._flush()
        super().close()


def read_entries(page_html: str) -> list[dict]:
    p = EntryParser()
    p.feed(page_html.lstrip("﻿"))
    p.close()
    return p.entries


# ---------------------------------------------------------------------------------------------
# Reading an entry
# ---------------------------------------------------------------------------------------------

LEAD_RE = re.compile(r"^(?:\d{4}|Date unknown|Around|About|Late|Early|After|Before|Circa|c\.)")
LHF_RE = re.compile(r"lighthousefriends\.com/light\.asp\?ID=(\d+)", re.I)
ARLHS_RE = re.compile(r"\bCAN-?(\d{1,4})\b")
CCG_RE = re.compile(r"\bCCG\s+((?:[A-Z]-?\d+(?:\.\d+)?)(?:\s*[;,/]\s*[A-Z]-?\d+(?:\.\d+)?)*)")
ADM_RE = re.compile(r"\bAdmiralty\s+(H\d+(?:\.\d+)?)")
NGA_RE = re.compile(r"\bNGA\s+(\d{1,5}(?:-\d+)?)")
EXACT_YEAR_RE = re.compile(r"^(\d{4})(?![\ds?(])(?!\s*\(\?\))")
GONE_RE = re.compile(r"^(?:demolished|destroyed|removed|replaced|burned|burnt|collapsed|dismantled|washed away|"
                     r"lighthouse destroyed|lost|gone|sank)\b", re.I)
INACTIVE_RE = re.compile(r"^(?:inactive|apparently inactive|officially inactive|deactivated|recently deactivated|"
                         r"light discontinued|discontinued|inaactive)\b", re.I)
ACTIVE_RE = re.compile(r"^(?:active|activ|reactivated|currently active)\b", re.I)
RANGE_WORDS_RE = re.compile(r"(?:(?:upper|lower|inner|outer|main|secondary)\s+)?(?:range(?:\s+(?:front|rear|lights?))?|front(?:\s+range)?|rear(?:\s+range)?)", re.I)
WORD_YEAR = r"(?:the\s+)?(?:early\s+|mid\s+|late\s+|around\s+|about\s+|ca\.?\s+)?(\d{4})(s?)"


def good_alt_name(x: str) -> bool:
    """An other name worth keeping: not punctuation, a generic word, a range half or "ex-..."."""
    return bool(re.search(r"[A-Za-zÀ-ÿ]{3}", x)) and not RANGE_WORDS_RE.fullmatch(x) \
        and not re.fullmatch(r"(?:lantern|lights?|tower|old|new|replica|relocated.*|ex-.*)", x, re.I)


def clean_name(dt_text: str) -> tuple[str, dict]:
    """(the light's name, its marks and parentheses) from a <dt> text."""
    marks: dict = {"notable": False, "gone": False, "minor_marker": False, "tower_number": None,
                   "alt_names": [], "notes": []}
    s = dt_text.strip()
    # A name sometimes follows a section heading in the same <dt>; the marks come just before it.
    if "#" in s:
        marks["gone"] = True
    if "*" in s:
        marks["notable"] = True
    s = s.replace("*", "").replace("#", "").strip()
    if s.startswith("[") and "]" in s:
        marks["minor_marker"] = True
        s = s.replace("[", "", 1)
        s = s[::-1].replace("]", "", 1)[::-1]
    # Parentheses, innermost first ("Red River Mouth (Red River Range Rear (2))").
    while True:
        m = re.search(r"\(([^()]*)\)", s)
        if not m:
            break
        inner = m.group(1).strip()
        n = re.fullmatch(r"(\d+)\s*\??", inner)
        if n:
            marks["tower_number"] = int(n.group(1))
        elif re.match(r"(relocated|moved)\b", inner, re.I):
            marks["notes"].append(inner)
        elif inner.lower() in ("replica", "replicas"):
            marks["notes"].append("replica")
        elif re.fullmatch(r"[A-Za-z]{0,3}\d+\s*\??", inner):
            pass
        elif RANGE_WORDS_RE.fullmatch(inner):
            # "Cole Shoal (Range Front)": the words name which half of a range this is
            s = (s[:m.start()] + " " + inner + " " + s[m.end():]).strip()
            continue
        else:
            marks["alt_names"] += [x.strip() for x in re.split(r",\s*", inner) if good_alt_name(x.strip())]
        s = (s[:m.start()] + " " + s[m.end():]).strip()
    if "(" in s:  # an unclosed parenthesis in the page: the rest is another name
        s, _, rest = s.partition("(")
        marks["alt_names"] += [x.strip() for x in re.split(r",\s*", rest.strip(" )")) if good_alt_name(x.strip())]
    base = re.sub(r"\s+", " ", s).strip(" .;,")
    return base, marks


def parse_years(dd: str) -> dict:
    """The opening clause of a description."""
    m = re.match(r"(.*?)(?:\.\s|\.$)", dd)
    head = m.group(1) if m else dd[:120]
    out: dict = {"head": head, "built": None, "built_text": None, "established": None, "established_uncertain": False,
                 "replica_of": None}
    lead = head.split("(")[0].strip() if not head.startswith("(") else head
    ex = EXACT_YEAR_RE.match(lead)
    if ex:
        out["built"] = int(ex.group(1))
    elif lead:
        out["built_text"] = lead
    est = re.search(r"station established\s+(?:in\s+)?(?:around\s+|about\s+)?(\d{4})(\s*\?)?", dd[:max(len(head), 1) + 90], re.I)
    if est:
        out["established"] = int(est.group(1))
        out["established_uncertain"] = bool(est.group(2))
    rep = re.search(r"replica of (\d{4})", head, re.I)
    if rep:
        out["replica_of"] = int(rep.group(1))
    return out


def status_of(dd: str, gone_mark: bool, head: str) -> tuple[str | None, str | None]:
    """(status, the words it rests on) from the sentence after the opening clause."""
    rest = dd[len(head):].lstrip(" .")
    first = rest[:160]
    if re.search(r"replica of \d{4}", head, re.I) and not gone_mark and not GONE_RE.match(first):
        return "replica", head
    if gone_mark or GONE_RE.match(first):
        return "lost", first[:60] if first else None
    if INACTIVE_RE.match(first):
        return "inactive", first[:60]
    if ACTIVE_RE.match(first):
        # "Active (inactive officially since 1958)", "Reactivated ... but now unofficial": a light is
        # shown, but the aid is not official: no claim either way.
        paren = re.match(r"\w+\s*\(([^)]*)\)", first)
        if paren and re.search(r"\b(?:inactive|unofficial|not official|officially|decorative)\b", paren.group(1), re.I) \
                and not first.lower().startswith("reactivated (inactive"):
            return None, first[:60]
        if re.match(r"reactivated.{0,60}\bunofficial\b", first, re.I):
            return None, first[:60]
        return "active", first[:30]
    return None, None


def year_after(pattern: str, text: str) -> int | None:
    m = re.search(pattern, text, re.I)
    return int(m.group(1)) if m and not m.group(2 if m.lastindex and m.lastindex >= 2 else 0) == "s" else None


def exact_year(pattern: str, text: str) -> int | None:
    m = re.search(pattern + r"(?!\d)(?!s\b)", text, re.I)
    return int(m.group(1)) if m else None


MATERIAL_WORDS = [(re.compile(r"\bcast[- ]iron\b", re.I), "cast_iron", "cast_iron"),
                  (re.compile(r"\bfiberglass\b", re.I), "fiberglass", None),
                  (re.compile(r"\bconcrete\b", re.I), "concrete", "concrete"),
                  (re.compile(r"\bwood(?:en)?\b", re.I), "wood", "wood_frame"),
                  (re.compile(r"\bbrick\b", re.I), "brick", "conical_masonry"),
                  (re.compile(r"\b(?:stone|granite|limestone|sandstone|masonry)\b", re.I), "stone", "conical_masonry"),
                  (re.compile(r"\b(?:steel|iron)\b", re.I), "steel", None),
                  (re.compile(r"\baluminum|aluminium\b", re.I), "aluminium", None)]
HEIGHT_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*m\s*\((?:approx\.\s*)?\d+(?:-\d+)?\s*ft\)\s*([^.;]{0,90}?)\b"
                       r"(tower|lighthouse|mast|post|pole|cylinder|building|house|column|pyramid|structure|light)\b", re.I)


def structure_facts(dd: str, head: str) -> dict:
    """Height and material of the tower the description names (not the focal plane)."""
    rest = dd[len(head):]
    height, material, stype = None, None, None
    for m in HEIGHT_RE.finditer(rest):
        before = rest[max(0, m.start() - 14):m.start()].lower()
        if "plane" in before or "(?)" in before:
            continue
        height = float(m.group(1))
        desc = m.group(2) + " " + m.group(3)
        best = None
        for rx, mat, typ in MATERIAL_WORDS:
            mm = rx.search(desc)
            if mm and (best is None or mm.start() < best[0]):
                best = (mm.start(), mat, typ)
        if best:
            material, stype = best[1], best[2]
        if re.search(r"\bskelet(?:al|on)\b", desc, re.I):
            stype = "skeletal"
        break
    return {"height_m": height, "material": material, "type": stype}


ACCESS_PATTERNS = [
    ("boat_only", re.compile(r"accessible only by (?:boat|air|boat or (?:air|plane|helicopter)|helicopter|water)|"
                             r"reachable only by (?:boat|air)", re.I)),
    ("site_open", re.compile(r"\bsite (?:and (?:tower|lighthouse) )?open\b|\bsite open\b|\bgrounds open\b", re.I)),
    ("site_closed", re.compile(r"\bsite(?: and (?:tower|lighthouse|lantern))? closed\b|\bsite and (?:tower|lighthouse) closed\b", re.I)),
    ("tower_open", re.compile(r"\b(?:tower|lighthouse) open\b|site and (?:tower|lighthouse) open|tower and lantern room open", re.I)),
    ("tower_closed", re.compile(r"\b(?:tower|lighthouse|interior)(?: and lantern)? closed\b|site and tower closed", re.I)),
    ("site_unknown", re.compile(r"\bsite status unknown\b", re.I)),
]


def access_of(dd: str) -> dict:
    found = {k: True for k, rx in ACCESS_PATTERNS if rx.search(dd)}
    out: dict = {}
    if found.get("boat_only"):
        out["boat_only"] = True
    if found.get("site_open") and not found.get("site_closed"):
        out["site"] = "open"
    elif found.get("site_closed") and not found.get("site_open"):
        out["site"] = "closed"
    elif found.get("site_unknown"):
        out["site"] = "unknown"
    if found.get("tower_closed") and not found.get("tower_open"):
        out["tower"] = "closed"
    elif found.get("tower_open") and not found.get("tower_closed"):
        out["tower"] = "open"
    return out


def owner_of(dd: str) -> str | None:
    m = re.search(r"(?:Owner/site manager|Owner and site manager|Owner/manager|Owner|Site manager)\s*:\s*([^.;]{2,90}?)(?:[.;]|\s\(\?\)|\sSite\b|$)", dd)
    if not m:
        return None
    v = re.sub(r"\s*\(\?\)\s*$", "", m.group(1)).strip(" ,")
    return v or None


def ownership_of(owner: str | None) -> str | None:
    if not owner:
        return None
    o = owner.lower()
    if re.search(r"coast guard|fisheries and oceans|parks canada|transport canada|department of|public works|federal|canadian wildlife", o):
        return "federal"
    if re.search(r"province|provincial|bc parks|ontario parks|parcs|sépaq|sepaq|crown", o):
        return "provincial"
    if re.search(r"\b(town|city|village|municipality|county|municipal|township|regional)\b", o):
        return "local"
    if re.search(r"private|individual", o):
        return "private"
    if re.search(r"society|association|foundation|friends|museum|trust|heritage|historical|committee", o):
        return "nonprofit"
    return None


def norm_ccg(value: str) -> str:
    """"A-456" -> "A456", "I-0563" -> "I563", "N-049" -> "N49", "I-0114.1" -> "I114.1"."""
    m = re.fullmatch(r"([A-Z])-?0*(\d+(?:\.\d+)?)", value.strip())
    if not m:
        return value.strip()
    num = m.group(2)
    return f"{m.group(1)}{num}"


def norm_arlhs(digits: str) -> str:
    return f"CAN{int(digits)}"


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", " and ")).strip("-")
    return s[:80] or "light"


def build_record(page: str, entry: dict, seen: dict[str, int]) -> dict | None:
    dd = entry["dd"]["text"]
    if not LEAD_RE.match(dd):
        return None
    name, marks = clean_name(entry["dt"]["text"])
    if not name or len(name) > 90:
        return None
    region, _label = PAGES[page]
    years = parse_years(dd)
    status, status_words = status_of(dd, marks["gone"], years["head"])
    facts = structure_facts(dd, years["head"])
    focal = re.search(r"focal plane\s+(\d+(?:\.\d+)?)\s*m", dd)
    arlhs = sorted({norm_arlhs(m) for m in ARLHS_RE.findall(dd[dd.find("ARLHS"):])}) if "ARLHS" in dd else []
    ccg = []
    for m in CCG_RE.finditer(dd):
        ccg += [norm_ccg(v) for v in re.split(r"\s*[;,/]\s*", m.group(1))]
    adm = ADM_RE.findall(dd)
    nga = NGA_RE.findall(dd)
    lhf = sorted({m for h in entry["dt"]["hrefs"] + entry["dd"]["hrefs"] for m in LHF_RE.findall(h)})
    owner = owner_of(dd)
    k = slug(name)
    seen[k] = seen.get(k, 0) + 1
    key = f"{SOURCE}:{page}:{k}" + (f"-{seen[k]}" if seen[k] > 1 else "")
    events = []
    if years["built"]:
        events.append({"year": years["built"], "event": "built", "note": "Year of the tower described by the Lighthouse Directory",
                       "from": SOURCE})
    if years["established"] and not years["established_uncertain"]:
        events.append({"year": years["established"], "event": "first_lit", "note": "Station established", "from": SOURCE})
    tail = re.split(r"(?<=[a-z0-9\)])\.\s", dd[len(years["head"]):].lstrip(" ."), maxsplit=1)[0]  # the status sentence
    d_year = exact_year(r"(?:inactive|deactivated|discontinued)\s+(?:since|in)\s+(?:the\s+)?(\d{4})", tail)
    if d_year:
        events.append({"year": d_year, "event": "deactivated", "note": None, "from": SOURCE})
    r_year = exact_year(r"(?:demolished|removed|dismantled|replaced)\s+(?:in|by .{0,20}? in)\s+(\d{4})", tail)
    if r_year:
        events.append({"year": r_year, "event": "removed", "note": None, "from": SOURCE})
    x_year = exact_year(r"destroyed\s+(?:by [a-z ]{0,20}?)?in\s+(\d{4})", tail)
    if x_year:
        events.append({"year": x_year, "event": "destroyed", "note": None, "from": SOURCE})
    kind = "range_lights" if re.search(r"\brange\b", name, re.I) else "lighthouse"
    if re.search(r"\b(pier|breakwater|jetty|mole)\b", name, re.I):
        kind = "pier_light"
    role = "front_range" if re.search(r"\bfront\b", name, re.I) else "rear_range" if re.search(r"\brear\b", name, re.I) else None
    if kind == "range_lights" and role is None and not re.search(r"\brange\b", name, re.I):
        kind = "lighthouse"
    join_keys = [f"lhf:{i}" for i in lhf] + [f"arlhs:{a}" for a in arlhs] + [f"ccg:{x}" for x in ccg] + [f"adm:{a}" for a in adm]
    return {
        "key": key,
        "url": PAGE_URL.format(page=page),
        "name": name,
        "other_names": marks["alt_names"],
        "country": "CA",
        "region": region,
        "county": None,
        "lat": None,
        "lon": None,
        "precision": None,
        "kind": kind,
        "kind_raw": None,
        "role": role,
        "status": status,
        "status_raw": status_words,
        "structure": {"type": facts["type"], "material": facts["material"], "built": years["built"],
                      "height_m": facts["height_m"], "status": None},
        "light": {"first_lit": years["established"] if not years["established_uncertain"] else None,
                  "deactivated": d_year, "characteristic": None,
                  "focal_height_m": float(focal.group(1)) if focal else None,
                  "range_nm": None, "fog_signal": None, "lens": None},
        "setting": None,
        "registers": [],
        "aton": {"uscg_llnr": None, "arlhs": arlhs[0] if arlhs else None, "ccg_list_number": ccg[0] if ccg else None,
                 "nga": nga[0] if nga else None, "admiralty": adm[0] if adm else None},
        "agency": owner,
        "ownership": ownership_of(owner),
        "events": events,
        "photos": [],
        "links": [{"label": "Lighthouse Directory (Rowlett)", "url": PAGE_URL.format(page=page), "kind": "reference"}],
        "relations": {},
        "extra": {
            "station_level": True,
            "page": page,
            "gone": marks["gone"] or status == "lost",
            "notable": marks["notable"],
            "minor_marker": marks["minor_marker"],
            "tower_number": marks["tower_number"],
            "notes": marks["notes"],
            "built_text": years["built_text"],
            "established": years["established"],
            "established_uncertain": years["established_uncertain"],
            "replica_of": years["replica_of"],
            "access": access_of(dd),
            "lhf_ids": lhf,
            "ccg_numbers": ccg,
            "all_arlhs": arlhs,
            "join_keys": join_keys,
        },
    }


def fetch_canada(refresh: bool = False) -> tuple[list[dict], dict, list[Path]]:
    cache = c.raw_dir(SOURCE) / "ca"
    records, paths, notes = [], [], {"by_page": {}, "skipped_entries": 0}
    for page in PAGES:
        p = cache / f"{page}.htm"
        body = cc.cached_get(PAGE_URL.format(page=page), p, SURVEY_DIR / f"{page}.htm", refresh=refresh)
        paths.append(p)
        seen: dict[str, int] = {}
        n = 0
        for entry in read_entries(cc.decode(body, "utf-8-sig", "cp1252")):
            rec = build_record(page, entry, seen)
            if rec is None:
                notes["skipped_entries"] += 1
                continue
            records.append(rec)
            n += 1
        notes["by_page"][page] = n
    return records, notes, paths


def write_union(records: list[dict], notes: dict, retrieved: str) -> int:
    kept, header_notes = [], {}
    if OUT_PATH.exists():
        old = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        kept = [r for r in old.get("records", []) if r.get("country") != "CA"]
        header_notes = dict(old.get("notes") or {})
    header_notes["canada"] = notes
    c.write_source_json(OUT_PATH, source=SOURCE, title="Lighthouse Directory (Russ Rowlett)",
                        url="https://www.ibiblio.org/lighthouse/", license_text=LICENSE, records=kept + records,
                        notes=header_notes, retrieved=retrieved)
    return len(kept)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--refresh", action="store_true", help="fetch again instead of using the cache")
    args = ap.parse_args(argv)
    records, notes, paths = fetch_canada(args.refresh)
    kept = write_union(records, notes, c.retrieved_date(*paths))
    c.log(f"rowlett: {len(records)} Canadian records written, {kept} other records kept; "
          f"{notes['skipped_entries']} entries skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
