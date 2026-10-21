#!/usr/bin/env python3
"""Canadian Coast Guard List of Lights, Buoys and Fog Signals (2026 edition): the lit fixed aids
that are lighthouses or sit where a station is; writes data/sources/ccg_list_of_lights.json
(DESIGN.md 2.3, 3.8).

Source: https://www.notmar.gc.ca/list-livre-en.php (Notices to Mariners, Canadian Coast Guard),
which links five volumes (Newfoundland and Labrador, Atlantic, Inland Waters, Pacific, Arctic) of
numbered sections, each an HTML table (`<table class="wb-tables ...">`, one `<tr>` per aid). A
section is `.../publications/list-lights/<volume>/<code>-en.php`. About 130 sections; the fetcher
reads the index, then each section once (2 s apart, robots.txt honoured: only /zip-publication-*
and /tmp/ are disallowed), caching every page under RAW_ROOT/ccg_list_of_lights/.

Licence: (c) His Majesty the King in Right of Canada, as represented by the Canadian Coast Guard,
2026. No open licence is stated, so only facts are taken (position, characteristic, focal height,
range, the kind of structure and its height, the list and Admiralty numbers), with credit and a
link to the volume.

What a row gives (its cells): list number (+ the international Admiralty number `H####` in italics
under it), name (bold in Newfoundland and Labrador for a major light station), location text and the
position to 0.1 arc-second, characteristic (`Fl`), colour (`W`), period (`4s`), focal height above
water (m), nominal range (nm), a description of the structure with its height above ground (m), and
remarks (seasonal or year round, fog signal). Buoys are rows in italics (`<em>`): never taken.

**Which rows are kept** (`classify`): fixed aids only. A row is `lighthouse_like` when the structure
description is a tower or building of the lighthouse kind (a "tower", "lighthouse" or "building"
that is not a skeleton, pipe, pile, dolphin, pole, mast or post) or the name says lighthouse, light
station or range. Every lit structure of that kind is kept. Any other fixed aid (skeleton towers,
poles, piles, dolphins, masts, posts) is kept only when it lies within MATCH_M of a Canadian record
in the other extracts (Wikidata, OpenStreetMap, the heritage lighthouses): those add the charted
light to a station the other sources already hold. The rest, thousands of small beacons, are counted
in the header and not written. `extra.lighthouse_like` and `extra.aid_class` carry the decision, so
the merge can refuse to start a station from a skeleton tower.

Usage: python3 pipeline/fetch_ccg_list_of_lights.py [--refresh] [--no-match]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ca_common as cc  # noqa: E402
import _common as c  # noqa: E402

SOURCE = "ccg_list_of_lights"
OUT_PATH = c.REPO / "data" / "sources" / f"{SOURCE}.json"
HOST = "https://www.notmar.gc.ca"
INDEX_URL = f"{HOST}/list-livre-en.php"
VOLUME_URL = HOST + "/publications/list-lights/{vol}/{vol_code}volumee.pdf"
SECTION_RE = re.compile(r'href="(/publications/list-lights/([a-z\-]+)/([a-z]+)(\d+)-en\.php)"')
# volume directory -> (code in file names, list-number prefix used by Wikidata P3920 and the Directory, title)
VOLUMES = {
    "newfoundland": ("nl", "N", "Newfoundland and Labrador"),
    "atl": ("atl", "A", "Atlantic Coast and the St. Lawrence to Montreal"),
    "inland-waters": ("iw", "C", "Inland Waters"),
    "pac": ("pac", "P", "Pacific Coast"),
    "arc": ("arc", "X", "Arctic Coast"),
}
LICENSE = ("(c) His Majesty the King in Right of Canada, as represented by the Canadian Coast Guard, 2026. "
           "No open licence stated: facts only (position, characteristic, height, range, structure), with credit and link.")
MATCH_M = 150.0


def section_links(index_html: str) -> list[tuple[str, str, str]]:
    """(path, volume directory, section code) for every numbered section the index links (front
    matter, index pages and annexes have no digits in their code and are not aids)."""
    seen, out = set(), []
    for path, vol, code, num in SECTION_RE.findall(index_html):
        if vol in VOLUMES and path not in seen:
            seen.add(path)
            out.append((path, vol, f"{code}{num}"))
    return out


def cache_name(path: str) -> str:
    return path.removeprefix("/publications/list-lights/").replace("/", "__")


def fetch_pages(refresh: bool = False) -> tuple[str, list[tuple[str, str, str, Path]]]:
    """The index and every section, cached. Returns (index html, [(path, volume, code, cache path)])."""
    cache = c.raw_dir(SOURCE)
    index_path = cache / "list-livre-en.php"
    index_html = cc.decode(cc.cached_get(INDEX_URL, index_path, cc.SURVEY / "ccg" / "list-livre-en.php", refresh=refresh))
    sections = section_links(index_html)
    out = []
    for n, (path, vol, code) in enumerate(sections, 1):
        p = cache / cache_name(path)
        legacy = cc.SURVEY / "ccg" / Path(path).name
        if not p.exists() or refresh:
            c.log(f"ccg_list_of_lights: section {n}/{len(sections)} {path}")
        cc.cached_get(HOST + path, p, legacy, refresh=refresh)
        out.append((path, vol, code, p))
    return index_html, out
