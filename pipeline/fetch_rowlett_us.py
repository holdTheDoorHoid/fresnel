#!/usr/bin/env python3
"""Russ Rowlett's Lighthouse Directory, US pages -> data/sources/rowlett.json (DESIGN.md 2.3).

The Lighthouse Directory (University of North Carolina at Chapel Hill, hosted at ibiblio.org/lighthouse/)
describes lights worldwide in hand-written paragraphs, one per tower. Its text is copyrighted ("copying
portions for personal use and study; all other rights reserved"), so this fetcher takes **facts only**:
the years, the status word, the ARLHS, USCG and Admiralty numbers, the cross-reference to
LighthouseFriends, and a link to the page. Nothing of the prose is kept. It is a **second opinion**, not
a position source: the pages give no coordinates (only Google Maps links), so every record has no
position and joins a station by number (ARLHS, USCG Light List, the LighthouseFriends id Rowlett links
to) or, failing that, by name within its state.

One `<dt>` (the name, with markers: `#` a light lost since 2000, `*` and `**` Rowlett's marks, `[ ]` a
fog signal or other building, `(2)` the second tower of a station) and one `<dd>` per tower. Readings of
the dd, which opens "1859 (station established 1834). Active; focal plane ...":

- the year in front is the tower's (`structure.built`); "Date unknown" is none; "station established N"
  is the station's first year (`light.first_lit`);
- the first status words: "Active" / "Reactivated" -> `active`; "Inactive since N", "Decommissioned N",
  "Deactivated in N" -> `inactive` with `light.deactivated`; "Removed / Demolished / Destroyed /
  Collapsed / Burned / Replaced" -> `lost` (the year, when given, an event); "a decorative light" ->
  noted, no status;
- "ARLHS USA-513", "USCG 1-1390" (a buoy's number is not taken), "Admiralty J0028".

The years go to the timeline as events (a tower's `built`, the station's `first_lit`, `deactivated`,
`removed`), so a second opinion shows beside the first and never replaces it.

The extract `data/sources/rowlett.json` is shared with the Canadian fetcher (fetch_rowlett.py): each writes
only its own country's records and keeps the other's.

Usage: python3 pipeline/fetch_rowlett_us.py [--refresh]
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "sources" / "rowlett.json"
SOURCE = "rowlett"
BASE = "https://www.ibiblio.org/lighthouse/"
SURVEY_CACHE = "survey/us/rowlett"

# page -> (region, label). The directory's US and territory pages (2026-10-21 index).
PAGES: dict[str, tuple[str, str]] = {
    "ak.htm": ("AK", "Alaska"), "al.htm": ("AL", "Alabama"), "ar.htm": ("AR", "Arkansas"),
    "asm.htm": ("AS", "American Samoa"), "az.htm": ("AZ", "Arizona"),
    "ca.htm": ("CA", "California: North"), "ca2.htm": ("CA", "California: South"), "co.htm": ("CO", "Colorado"),
    "ct.htm": ("CT", "Connecticut"), "de.htm": ("DE", "Delaware"),
    "fl.htm": ("FL", "Florida: East Coast"), "flkey.htm": ("FL", "Florida: Keys"), "flw.htm": ("FL", "Florida: West Coast"),
    "ga.htm": ("GA", "Georgia"), "gu.htm": ("GU", "Guam"), "hi.htm": ("HI", "Hawaii"), "ia.htm": ("IA", "Iowa"),
    "id.htm": ("ID", "Idaho"), "il.htm": ("IL", "Illinois"), "in.htm": ("IN", "Indiana"), "ks.htm": ("KS", "Kansas"),
    "ky.htm": ("KY", "Kentucky"), "la.htm": ("LA", "Louisiana"),
    "macape.htm": ("MA", "Massachusetts: Cape Cod"), "ma.htm": ("MA", "Massachusetts: North"),
    "maso.htm": ("MA", "Massachusetts: South"), "mde.htm": ("MD", "Maryland: Eastern Shore"), "md.htm": ("MD", "Maryland"),
    "me.htm": ("ME", "Maine: East"), "me2.htm": ("ME", "Maine: South"),
    "minel.htm": ("MI", "Michigan"), "minwl.htm": ("MI", "Michigan"), "misel.htm": ("MI", "Michigan"),
    "misu.htm": ("MI", "Michigan"), "miup.htm": ("MI", "Michigan"), "miwl.htm": ("MI", "Michigan"),
    "miwu.htm": ("MI", "Michigan"), "mn.htm": ("MN", "Minnesota"), "mnp.htm": ("MP", "Northern Mariana Islands"),
    "mo.htm": ("MO", "Missouri"), "ms.htm": ("MS", "Mississippi"), "nc.htm": ("NC", "North Carolina"),
    "ne.htm": ("NE", "Nebraska"), "nh.htm": ("NH", "New Hampshire"), "nj.htm": ("NJ", "New Jersey"),
    "nv.htm": ("NV", "Nevada"), "nvi.htm": ("UM", "Navassa Island"),
    "nydn.htm": ("NY", "New York: City and Hudson River"), "nyli.htm": ("NY", "New York: Long Island"),
    "nyup.htm": ("NY", "New York: Central and Northern"), "nyw.htm": ("NY", "New York: Western"),
    "oh.htm": ("OH", "Ohio"), "ok.htm": ("OK", "Oklahoma"), "or.htm": ("OR", "Oregon"),
    "pa.htm": ("PA", "Pennsylvania: Northwest"), "pase.htm": ("PA", "Pennsylvania: Southeast"),
    "pr.htm": ("PR", "Puerto Rico"), "ri.htm": ("RI", "Rhode Island"), "sc.htm": ("SC", "South Carolina"),
    "tn.htm": ("TN", "Tennessee"), "tx.htm": ("TX", "Texas: Southeast"), "txs.htm": ("TX", "Texas: South"),
    "umi.htm": ("UM", "U.S. Minor Outlying Islands"), "ut.htm": ("UT", "Utah"), "va.htm": ("VA", "Virginia"),
    "vi.htm": ("VI", "U.S. Virgin Islands"), "vt.htm": ("VT", "Vermont"),
    "wa.htm": ("WA", "Washington"), "waps.htm": ("WA", "Washington: Puget Sound"),
    "wi.htm": ("WI", "Wisconsin"), "wi2.htm": ("WI", "Wisconsin"), "widp.htm": ("WI", "Wisconsin: Door Peninsula"),
    "wv.htm": ("WV", "West Virginia"),
}


# ---------------------------------------------------------------------------------------------
# Walking the page
# ---------------------------------------------------------------------------------------------

class EntryParser(HTMLParser):
    """Collects (name, dd text, dd links) in page order. A dt's name is its last bold text outside the
    red section headings; a dd belongs to the nearest dt before it."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.entries: list[dict] = []
        self._in_dt = self._in_dd = False
        self._bold = 0
        self._red = 0
        self._seg: list[str] = []
        self._segments: list[str] = []
        self._dd: list[str] = []
        self._links: list[str] = []
        self.name: str | None = None
        self._font_stack: list[bool] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        a = dict(attrs)
        if tag == "dt":
            self._in_dt, self._segments, self._seg, self._bold, self._red = True, [], [], 0, 0
        elif tag == "dd":
            self._in_dd, self._dd, self._links = True, [], []
        elif tag in ("b", "strong") and self._in_dt:
            self._bold += 1
            self._seg = []
        elif tag == "font" and self._in_dt:
            red = (a.get("color") or "").lower().lstrip("#") in ("ff0000", "red")
            self._font_stack.append(red)
            self._red += 1 if red else 0
        elif tag == "a" and self._in_dd and a.get("href"):
            self._links.append(a["href"])
        elif tag == "br" and self._in_dd:
            self._dd.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("b", "strong") and self._in_dt and self._bold:
            self._bold -= 1
            if not self._bold and not self._red:
                seg = " ".join("".join(self._seg).split())
                if seg:
                    self._segments.append(seg)
            if not self._bold:
                self._seg = []
        elif tag == "font" and self._in_dt and self._font_stack:
            if self._font_stack.pop():
                self._red -= 1
        elif tag == "dt" and self._in_dt:
            self._in_dt = False
            self.name = self._segments[-1] if self._segments else None
        elif tag == "dd" and self._in_dd:
            self._in_dd = False
            text = " ".join("".join(self._dd).split())
            if self.name and text:
                self.entries.append({"name": self.name, "text": text, "links": list(self._links)})
            self.name = None

    def handle_data(self, data: str) -> None:
        if self._in_dt and self._bold and not self._red:
            self._seg.append(data)
        elif self._in_dd:
            self._dd.append(data)


def parse_page(page_html: str) -> list[dict]:
    p = EntryParser()
    p.feed(page_html)
    return p.entries


# ---------------------------------------------------------------------------------------------
# Reading an entry
# ---------------------------------------------------------------------------------------------

YEAR = r"(1[5-9]\d\d|20\d\d)"
LOST_RE = re.compile(r"^(removed|demolished|destroyed|collapsed|burned|razed|dismantled|lost|washed away|replaced|"
                     r"deactivated and removed|decommissioned and removed|swept away|sank|vanished)\b", re.I)


def read_name(raw: str) -> dict:
    name = html.unescape(raw).strip()
    marks = re.match(r"^([#*]+)\s*", name)
    lost_mark = bool(marks and "#" in marks.group(1))
    name = re.sub(r"^[#*\s]+", "", name).strip()
    bracket = bool(re.match(r"^\[.*\]$", name))
    name = name.strip("[]").strip()
    tower, alts = None, []
    while True:
        m = re.search(r"\s*\(([^()]*)\)\s*$", name)
        if not m:
            break
        inner = m.group(1).strip()
        name = name[:m.start()].strip()
        if re.fullmatch(r"\d\??", inner):
            tower = int(inner[0])
        elif inner and not re.match(r"(relocated|replica|moved|formerly|now|see|ruins|lost|demolished)", inner, re.I):
            alts.append(inner)
    return {"name": name, "alts": alts, "tower": tower, "lost_mark": lost_mark, "bracket": bracket}


def read_text(text: str) -> dict:
    """The facts in a dd's paragraph (never its prose)."""
    out: dict = {"built": None, "established": None, "status": None, "deactivated": None, "lost_year": None,
                 "replica": False, "decorative": False, "arlhs": None, "uscg": None, "admiralty": None,
                 "relocated": None, "status_text": None}
    head, _, rest = text.partition(". ")
    # "1859 (station established 1834)"; "Date unknown (station established 1873)"; "1873"
    m = re.match(rf"^(?:About |Approx\.? |c\.? |Before |After )?{YEAR}", head)
    if m:
        out["built"] = int(m.group(1))
    em = re.search(rf"station (?:was )?established (?:in )?(?:about )?{YEAR}", head)
    if em:
        out["established"] = int(em.group(1))
    if re.search(r"replica of", head, re.I):
        out["replica"] = True
    rm = re.search(rf"relocated.*?{YEAR}", head)
    if rm:
        out["relocated"] = int(rm.group(1))
    # the status sentence is the first one after the date; it may be the "head" when there is no date sentence
    status_s = rest.strip() if (m or head.lower().startswith("date unknown") or head.lower().startswith("about")) else text
    status_s = re.split(r"(?<=[.;])\s", status_s)[0] if status_s else ""
    out["status_text"] = status_s[:80] if status_s else None
    sy = re.search(YEAR, status_s)
    if re.match(r"^(active|reactivated|relit|lit)\b", status_s, re.I):
        out["status"] = "active"
    elif re.match(r"^(inactive|decommissioned|deactivated|discontinued|retired)\b", status_s, re.I):
        out["status"] = "inactive"
        if re.match(r"^(inactive since|decommissioned|deactivated|discontinued)", status_s, re.I) and sy and \
                not re.search(rf"{YEAR}\s*-\s*{YEAR}", status_s):
            out["deactivated"] = int(sy.group(1))
        if re.search(r"\band (later )?(removed|demolished|destroyed)\b", status_s, re.I):
            out["status"] = "lost"
            out["lost_year"] = None
    elif LOST_RE.match(status_s):
        out["status"] = "lost"
        out["lost_year"] = int(sy.group(1)) if sy else None
    if re.search(r"\ba decorative (?:light|lighthouse|beacon|tower)\b|\bnot an aid to navigation\b", text[:400], re.I):
        out["decorative"] = True
    a = re.search(r"ARLHS ([A-Z]{3}-\d{2,3})", text)
    if a:
        out["arlhs"] = a.group(1)
    for u in re.finditer(r"(.{0,30})USCG (\d)-(\d+)", text):
        if not re.search(r"buoy|bell|whistle|gong", u.group(1), re.I):
            out["uscg"] = f"{u.group(2)}-{u.group(3)}"
            break
    j = re.search(r"Admiralty\s+(J\d{4}(?:\.\d+)?)", text)
    if j:
        out["admiralty"] = j.group(1)
    return out


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", rx_fold(s).lower()).strip("-")


def rx_fold(s: str) -> str:
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))


def build_record(page: str, region: str, label: str, entry: dict, used: Counter) -> dict | None:
    nm = read_name(entry["name"])
    if not nm["name"] or len(nm["name"]) > 90:
        return None
    fa = read_text(entry["text"])
    if fa["built"] is None and fa["status"] is None and not fa["arlhs"] and not re.match(r"^Date unknown", entry["text"]):
        return None   # not a light's entry (a section blurb, a map credit)
    base = f"{page[:-4]}:{slug(nm['name'])}" + (f"-{nm['tower']}" if nm["tower"] else "")
    used[base] += 1
    ident = base if used[base] == 1 else f"{base}-{used[base]}"
    url = BASE + page
    status = fa["status"]
    if nm["lost_mark"] and status != "active":
        status = "lost"
    shown = f"{nm['name']} (Replica)" if fa["replica"] else nm["name"]   # a copy keeps the word: it is its own station
    rec = rx.new_record(SOURCE, ident, shown, url=url, region=region, lat=None, lon=None, precision="approximate",
                        kind="lighthouse", status=status)
    rec["other_names"] = nm["alts"]
    rec["kind_raw"] = entry["name"]
    rec["status_raw"] = fa["status_text"]
    rec["structure"]["built"] = fa["built"]
    if fa["replica"]:
        rec["status"] = "replica"
    rec["light"]["first_lit"] = fa["established"]
    if fa["status"] in ("inactive", "lost") and fa["deactivated"]:
        rec["light"]["deactivated"] = fa["deactivated"]
    ev = []
    note = f"Tower {nm['tower']}" if nm["tower"] else None
    if fa["built"]:
        ev.append({"year": fa["built"], "event": "built", "note": (note + " (Rowlett's Lighthouse Directory)") if note else
                   "Rowlett's Lighthouse Directory", "from": SOURCE})
    if fa["established"]:
        ev.append({"year": fa["established"], "event": "first_lit", "note": "Station established (Rowlett's Lighthouse Directory)", "from": SOURCE})
    if fa["deactivated"] and fa["status"] == "inactive":
        ev.append({"year": fa["deactivated"], "event": "deactivated", "note": "Rowlett's Lighthouse Directory", "from": SOURCE})
    if fa["lost_year"] and fa["status"] == "lost":
        ev.append({"year": fa["lost_year"], "event": "removed", "note": "Rowlett's Lighthouse Directory", "from": SOURCE})
    rec["events"] = ev
    rec["aton"]["arlhs"] = fa["arlhs"]
    rec["aton"]["uscg_llnr"] = fa["uscg"]
    rec["links"] = [{"label": f"Lighthouse Directory: {label}", "url": url, "kind": "reference"}]
    xref = []
    for href in entry["links"]:
        m = re.search(r"lighthousefriends\.com/light\.asp\?ID=(\d+)", href, re.I)
        if m:
            xref.append(f"lhf:{m.group(1)}")
    extra: dict = {"page": page, "tower": nm["tower"], "admiralty": fa["admiralty"], "decorative": fa["decorative"] or None,
                   "xref": sorted(set(xref)) or None, "relocated": fa["relocated"]}
    rec["extra"] = {k: v for k, v in extra.items() if v is not None}
    # An active light the other sources lack is a modern aid with no history to start a station for; the
    # merge report counts it instead of listing it. A lost, inactive or undated entry stays on the list.
    if status in ("active", None):
        rec["extra"]["quiet_unmatched"] = True
    if nm["bracket"]:
        # Rowlett puts a fog signal building, a minor light or a post in square brackets: it may add to a
        # station the other sources have, never start one
        rec["extra"]["enrich_only"] = True
        rec["extra"]["bracket"] = True
    return rec


# ---------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------

def get_pages(refresh: bool) -> dict[str, Path]:
    cache = c.raw_dir(SOURCE)
    survey = c.RAW_ROOT / SURVEY_CACHE
    out = {}
    for page in PAGES:
        p = cache / page
        old = survey / page
        if not p.exists() and not refresh and old.exists():
            shutil.copyfile(old, p)
        if not p.exists() or refresh:
            rx.polite_get(BASE + page, p, force=refresh)
        out[page] = p
    return out


def extract(pages: dict[str, Path]) -> tuple[list[dict], dict]:
    records, stats = [], Counter()
    for page, path in pages.items():
        region, label = PAGES[page]
        used: Counter = Counter()
        text = path.read_bytes().decode("latin-1")
        for entry in parse_page(text):
            rec = build_record(page, region, label, entry, used)
            if rec is None:
                stats["skipped"] += 1
                continue
            records.append(rec)
            stats[rec["status"] or "no status"] += 1
    return records, dict(stats)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch Fresnel's Lighthouse Directory extract")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    pages = get_pages(args.refresh)
    records, stats = extract(pages)
    rx.write_extract(
        OUT_PATH, source=SOURCE,
        title="Russ Rowlett's Lighthouse Directory: United States and territories",
        url=BASE,
        license_text="Copyright Russ Rowlett and the University of North Carolina at Chapel Hill; all other rights reserved. "
                     "Facts only (years, status, ARLHS / USCG / Admiralty numbers) with a link to the page; no text is copied.",
        credit="Russ Rowlett, The Lighthouse Directory (UNC Chapel Hill), used for facts with a link",
        records=records, notes={"pages": len(pages), "records_by_status": stats},
        retrieved=c.retrieved_date(*pages.values()), country="US")
    c.log(f"rowlett: wrote {len(records)} records from {len(pages)} pages; {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
