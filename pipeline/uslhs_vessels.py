"""The US Lighthouse Society's records of lightship stations and the vessels that served them
(archives.uslhs.org, "(c) U.S. Lighthouse Society, all rights reserved": facts only, each linked).

A lightship station's page lists its **vessel assignments** (vessel, start year, end year) and links each vessel's page
(`/node/<id>`), which gives the hull number (`LV-87`), the Coast Guard's later number (`WAL 512`), the years built and
retired, whether it exists, and the vessel's own **station assignments** (station name, years). The research-corpus
agent already crawls every place page into `$FRESNEL_RAW_ROOT/uslhs/place/<slug>.html`; the vessel pages are fetched
here, one request every 2 s through `_records.polite_get` (robots.txt honoured, one clock per host shared with every
other process), once, into `$FRESNEL_RAW_ROOT/uslhs/vessel/<node>.html`.

Python 3.12, standard library only.
"""
from __future__ import annotations

import html as htmllib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import _records as rx  # noqa: E402

SITE = "https://archives.uslhs.org"


def fields_of(page: str) -> list[tuple[str, str, str | None]]:
    """The page's labelled values in order: (label, text, href of the first link in the value or None)."""
    out = []
    for m in re.finditer(r'<div class="field_label">(.*?)</div>\s*(.*?)(?=<div class="field |<div class="field_label"|</article>|<h2)', page, re.S):
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip().rstrip(":").strip()
        href = re.search(r'href="([^"]+)"', m.group(2))
        value = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()
        out.append((label, value, href.group(1) if href else None))
    return out


def int_or_none(s: str | None) -> int | None:
    m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", s or "")
    return int(m.group(1)) if m else None


def parse_station_page(page: str) -> dict:
    """A lightship station place page -> established, discontinued, state, location, alternate names (from the comment's
    "Alternate name:" line, a fact), the data source ("1850 LL" is the Light List the entry rests on) and the vessel
    assignments [{"node", "label", "start", "end"}]."""
    rec: dict = {"vessels": []}
    cur: dict | None = None
    for label, value, href in fields_of(page):
        if label == "Year Established":
            rec["established"] = int_or_none(value)
        elif label == "Year Discontinued":
            rec["discontinued"] = int_or_none(value)
        elif label == "Source":
            rec["data_source"] = value or None
        elif label == "Location":
            rec["location"] = value or None
        elif label == "U.S. State":
            rec["state_name"] = value or None
        elif label == "Vessel":
            cur = {"node": int(re.search(r"/node/(\d+)", href).group(1)) if href and re.search(r"/node/(\d+)", href) else None,
                   "label": value, "start": None, "end": None}
            rec["vessels"].append(cur)
        elif label == "Start Year" and cur is not None:
            cur["start"] = int_or_none(value)
        elif label == "End Year" and cur is not None:
            cur["end"] = int_or_none(value)
        elif label == "Comments":
            m = re.match(r"Alternate names?:\s*(.*)$", value, re.I)
            rec["alternate_name"] = (m.group(1).strip() or None) if m else None
    return rec


def parse_vessel_page(page: str) -> dict:
    """A vessel page -> title, type, hull number, WAL number, years built and retired, whether it exists, remarks and the
    vessel's own station assignments [{"station", "start", "end"}]."""
    rec: dict = {"stations": []}
    title = re.search(r"<title>(.*?)</title>", page, re.S)
    rec["title"] = re.sub(r"\s*\|\s*USLHS Digital Archive.*$", "", htmllib.unescape(title.group(1))).strip() if title else None
    cur: dict | None = None
    for label, value, _href in fields_of(page):
        if label == "Type of Vessel":
            rec["type"] = value
        elif label == "LV Name/Number":
            rec["hull"] = value
        elif label == "WAL Number":
            rec["wal"] = value or None
        elif label == "Year Built":
            rec["built"] = int_or_none(value)
        elif label == "Year Retired":
            rec["retired"] = int_or_none(value)
        elif label == "Existing":
            rec["existing"] = value.lower().startswith("y")
        elif label == "LV Station Name":
            cur = {"station": value, "start": None, "end": None}
            rec["stations"].append(cur)
        elif label == "Year Started" and cur is not None:
            cur["start"] = int_or_none(value)
        elif label == "Year Ended" and cur is not None:
            cur["end"] = int_or_none(value)
        elif label == "Remarks" or (not label and rec.get("remarks") is None):
            pass
    m = re.search(r"Remarks\s*(?:</h\d>|</div>)?\s*(.*?)(?:Entered by|More Information)", re.sub(r"<[^>]+>", "\n", page), re.S)
    if m:
        rec["remarks"] = re.sub(r"\s+", " ", htmllib.unescape(m.group(1))).strip() or None
    return rec


def place_dir() -> Path:
    return c.RAW_ROOT / "uslhs" / "place"


def vessel_dir() -> Path:
    return c.RAW_ROOT / "uslhs" / "vessel"


def lightship_places() -> list[dict]:
    path = c.RAW_ROOT / "uslhs" / "places.json"
    return [p for p in json.loads(path.read_text(encoding="utf-8")) if p.get("type") == "Lightship Station"]


def station_pages() -> dict[str, dict]:
    """slug -> parsed station page, for every Lightship Station place in the corpus crawl."""
    out = {}
    for p in lightship_places():
        f = place_dir() / f"{p['slug']}.html"
        out[p["slug"]] = parse_station_page(f.read_text(encoding="utf-8", errors="replace")) if f.exists() else {"vessels": []}
    return out


def fetch_vessel_pages(nodes: list[int]) -> list[int]:
    """Fetch the vessel pages not cached yet; returns the nodes that could not be fetched."""
    failed = []
    for n in sorted(set(nodes)):
        dest = vessel_dir() / f"{n}.html"
        try:
            rx.polite_get(f"{SITE}/node/{n}", dest, timeout=120)
        except (c.FetchError, rx.Blocked) as e:
            c.log(f"uslhs vessel {n}: {e}")
            failed.append(n)
    return failed


def vessel_pages() -> dict[int, dict]:
    out = {}
    for f in sorted(vessel_dir().glob("*.html")):
        out[int(f.stem)] = parse_vessel_page(f.read_text(encoding="utf-8", errors="replace"))
    return out


def main() -> int:
    pages = station_pages()
    nodes = sorted({v["node"] for p in pages.values() for v in p["vessels"] if v["node"]})
    c.log(f"{len(pages)} lightship station pages, {len(nodes)} distinct vessel pages; fetching those not cached")
    failed = fetch_vessel_pages(nodes)
    c.log(f"done; {len(failed)} failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
