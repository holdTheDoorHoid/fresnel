#!/usr/bin/env python3
"""Lightship vessel records -> data/vessels/<id>.json (DESIGN.md 3.5).

One record per vessel in the US Lighthouse Society's vessel pages (`uslhs_vessels.py`; "(c) U.S. Lighthouse Society": facts
only, each linked): its **hull number** (`lv-87`; a vessel the Society numbers WLV or WAL only is `wlv-604`, `wal-612`; a ship
the Society knows by a letter code or a name is `lv-zz`, `kewaunee`), the names it carried, the year built and retired, its
**career** (each station it served with years, as the vessel's own page gives them, joined to the station's record by the key
`lightship_stations:<slug>`: a station is found by its key, never by an id that a later merge may number differently), its
**fate**, and, for a survivor, its **berth**.

- *Fate*: `survives` where the Society says the hull exists; else `lost` (a remark that says sunk, wrecked, foundered,
  burned or lost), `scrapped` (scrapped, broken up, cut down), `sold` (sold, privately owned) or `unknown`. The remark's own
  words are not kept (the Society's text); the year it names is kept as the year of the fate.
- *Berth*: a survivor's berth is a station on the map of kind `lightship` (from Wikidata, the National Register and
  Lighthouse Friends: `data/stations/`), found by the hull number or the name the station's other names carry; the berth
  carries that station's id, which is permanent (its name and point are read from the published station when the site is built). A survivor that no station on the map carries gets no berth here (the one
  the sources name no berth for, LV-75, "possibly scrapped 2013"); nothing is added to the map for it.

Python 3.12, standard library only. Needs the corpus's USLHS cache (`$FRESNEL_RAW_ROOT/uslhs/`); `data/stations/` is read when
it exists (without it the vessels have no berth link).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import fetch_lightship_stations as fls  # noqa: E402
import uslhs_vessels as uv  # noqa: E402

VESSELS_DIR = c.REPO / "data" / "vessels"
STATIONS_DIR = c.REPO / "data" / "stations"
CREDIT = "U.S. Lighthouse Society Digital Archive (Lighthouse Research Catalog): facts only, with a link"

LOST = re.compile(r"\b(sunk|sank|wreck|wrecked|foundered|burn(?:ed|t)|lost|capsized|destroyed|collision)\b", re.I)
SCRAPPED = re.compile(r"\b(scrapp?ed|broken up|cut down|dismantled)\b", re.I)
SOLD = re.compile(r"\b(sold|privately owned|private(?:ly)? owned)\b", re.I)
DOUBT = re.compile(r"\b(possibly|probably|perhaps|may have been)\s+(scrapped|sunk|lost|broken up|destroyed)\b", re.I)
YEAR = re.compile(r"\b(1[89]\d\d|20[0-2]\d)\b")


def slug_of(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def hull_id(title: str | None, hull: str | None, wal: str | None) -> tuple[str, str, str | None]:
    """(id, hull as written, WAL number as written) from the vessel page's title "Lightship: LV-087" and fields."""
    t = re.sub(r"^Lightship:\s*", "", (title or "").strip())
    t = re.sub(r"\s+More Information.*$", "", t)
    m = re.match(r"(LV|WLV|WAL)\s*-\s*0*(\d+)\b", t)
    if m:
        kind, n = m.group(1), int(m.group(2))
        label = f"{kind}-{n}"
        wal_n = re.search(r"\bWAL[ -]?0*(\d+)\b", wal or "")
        return f"{kind.lower()}-{n}", label, (f"WAL-{wal_n.group(1)}" if wal_n and kind != "WAL" else None)
    m = re.match(r"LV\s*-\s*([A-Z]{1,2})\b(?:\s*\(([^)]*)\))?", t)        # a ship the Society knows by its letter code
    if m:
        return f"lv-{m.group(1).lower()}", f"LV-{m.group(1)}", None
    m = re.match(r"LV\s*-\s*([A-Za-z][A-Za-z ]+?)(?:\s*\(([^)]*)\))?$", t)  # "LV- Kewaunee (Privately Owned)"
    if m:
        return slug_of(m.group(1)), m.group(1).strip(), None
    return slug_of(t) + "-vessel", t, None


def vessel_names(title: str | None) -> list[str]:
    """Names in the title's parentheses that are ship names ("LV- AA (Caesar)" -> Caesar), not notes ("Privately Owned")."""
    out = []
    for inner in re.findall(r"\(([^()]*)\)", title or ""):
        if re.search(r"privately owned|supply vessel|referred to as", inner, re.I):
            continue
        out.append(re.sub(r"^USRC\s+", "", inner).strip())
    return out


def fate_of(v: dict) -> dict:
    remarks = v.get("remarks") or ""
    year = None
    if v.get("existing"):
        status = "survives"
    elif LOST.search(remarks):
        status = "lost"
    elif SCRAPPED.search(remarks):
        status = "scrapped"
    elif SOLD.search(remarks):
        status = "sold"
    else:
        status = "unknown"
    doubtful = bool(v.get("existing")) and bool(DOUBT.search(remarks))
    if status not in ("survives", "unknown") or doubtful:
        years = [int(y) for y in YEAR.findall(remarks)]
        year = years[-1] if years else (None if doubtful else v.get("retired"))
    out = {"status": status, "year": year, "existing": bool(v.get("existing"))}
    if doubtful:
        out["doubtful"] = True      # the Society says she exists and also that she was possibly scrapped (LV-75, "possibly scrapped 2013")
    return out


def hull_numbers_of_station(rec: dict) -> set[int]:
    """Hull numbers a map station of kind `lightship` carries in its names: "Lightship Nantucket LV 112/WAL 534", "No. 83"."""
    text = " ".join([rec.get("name") or ""] + [n for n in rec.get("other_names") or [] if isinstance(n, str)])
    nums = {int(n) for n in re.findall(r"\b(?:LV|WLV|WAL)[ -]?0*(\d{1,3})\b", text)}
    nums |= {int(n) for n in re.findall(r"\b(?:No\.?|Lightship #?|LIGHT VESSEL)\s*0*(\d{2,3})\b", text, re.I)}
    return nums


def survivor_stations() -> list[dict]:
    out = []
    if not STATIONS_DIR.is_dir():
        return out
    for f in sorted(STATIONS_DIR.rglob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if d.get("kind") == "lightship" and not d.get("merged_into"):
            out.append({"id": d["id"], "name": d["name"], "lat": (d.get("location") or {}).get("lat"), "lon": (d.get("location") or {}).get("lon"),
                        "hulls": hull_numbers_of_station(d), "status": d.get("status"),
                        "sources": [s["source"] + ":" + s["key"] for s in d.get("sources") or []]})
    return out


# A map station that names no hull number the rule above can read, tied to the vessel by hand with the reason
BERTH_BY_HAND = {
    "wlv-196": ("us-ak-umatilla", "named 'Lightship Umatilla WLV-196' on Lighthouse Friends; the Society says she was renamed Bio Researcher (private)"),
    "wal-612": ("us-ma-nantucket-i", "Lighthouse Friends' Nantucket I (WLV-612)"),
    "wal-613": ("us-ma-nantucket-i", "the same map station holds Lighthouse Friends' Nantucket II (WLV 613) with Nantucket I"),
    # one vessel, once the pinned join (record_joins.py) has folded us-wa-swiftsure-2 into this station; the plain id survives
    "lv-83": ("us-wa-swiftsure", "Swiftsure, the lightship at Lake Union, Seattle (Wikidata, Lighthouse Friends and the National Register describe one vessel)"),
}
# The names the map's own sources give the surviving hulls (Wikidata labels, National Register names, Lighthouse Friends)
SURVIVOR_NAMES = {
    "lv-79": ["Barnegat"], "lv-83": ["Swiftsure"], "lv-87": ["Ambrose"], "lv-101": ["Portsmouth"], "lv-103": ["Huron"],
    "lv-107": ["Winter Quarter"], "lv-112": ["Nantucket"], "lv-114": ["New Bedford"], "lv-115": ["Frying Pan"],
    "lv-116": ["Chesapeake"], "lv-118": ["Overfalls"], "wal-612": ["Nantucket I"], "wal-613": ["Nantucket II"],
    "wlv-196": ["Umatilla"], "wlv-604": ["Columbia"], "wlv-605": ["Relief"],
}


def berth_of(rec: dict, stations: list[dict]) -> dict | None:
    by_id = {st["id"]: st for st in stations}
    if rec["id"] in BERTH_BY_HAND and BERTH_BY_HAND[rec["id"]][0] in by_id:
        sid, why = BERTH_BY_HAND[rec["id"]]
        st = by_id[sid]
        return {"station_id": sid, "name": st["name"], "basis": why}
    nums = {int(re.search(r"(\d+)", x).group(1)) for x in (rec["hull"], rec.get("wal")) if x and re.search(r"\d", x)}
    kind_ok = (lambda st: any(n >= 190 for n in st["hulls"] & nums)) if rec["id"].startswith(("wlv-", "wal-")) else (lambda st: True)
    cands = [st for st in stations if st["hulls"] & nums and kind_ok(st) and not any(v[0] == st["id"] for v in BERTH_BY_HAND.values())]
    if not cands:
        return None
    st = sorted(cands, key=lambda s: s["id"])[0]
    out = {"station_id": st["id"], "name": st["name"], "basis": "the hull number in the map station's names"}
    if len(cands) > 1:
        out["also"] = [x["id"] for x in cands[1:]]
    return out


def build() -> dict[str, dict]:
    place_by_name: dict[str, str] = {}
    for p in uv.lightship_places():
        if p["slug"] in fls.FOLDED_STUBS:
            continue
        name, alts, _nb = fls.station_name(p["name"])
        if p["slug"] in fls.NAME_FIX:
            name, alts = fls.NAME_FIX[p["slug"]][0], fls.NAME_FIX[p["slug"]][1] + alts
        key = "lightship_stations:" + re.sub(r"-lightship-station.*$", "", p["slug"])
        place_by_name[fls.squash(name)] = key
        for a in alts:
            place_by_name.setdefault(fls.squash(a), key)
    stations = survivor_stations()
    out: dict[str, dict] = {}
    for node, v in sorted(uv.vessel_pages().items()):
        vid, label, wal = hull_id(v.get("title"), v.get("hull"), v.get("wal"))
        if vid in out:
            vid = f"{vid}-{node}"
        career = []
        for s in v.get("stations") or []:
            key = place_by_name.get(fls.squash(re.sub(r"\s*\(.*?\)", "", s["station"])))
            career.append({"station": s["station"], "station_key": key, "start": s["start"], "end": s["end"]})
        rec = {
            "id": vid, "hull": label, "wal": wal, "names": vessel_names(v.get("title")) or SURVIVOR_NAMES.get(vid, []), "built": v.get("built"), "retired": v.get("retired"),
            "career": career, "fate": fate_of(v), "berth": None,
            "sources": [{"label": f"US Lighthouse Society Digital Archive: {re.sub(r'^Lightship: ', '', v.get('title') or label)} (vessel record)",
                         "url": f"{uv.SITE}/node/{node}", "credit": CREDIT}],
        }
        out[vid] = rec
    for rec in out.values():
        if rec["fate"]["status"] == "survives" or rec["id"] in ("lv-71", "lv-114"):
            rec["berth"] = berth_of(rec, stations)
            if rec["berth"] and rec["fate"]["status"] != "survives":
                rec["berth"]["note"] = "not afloat: the map station marks where the hulk or wreck lies (National Register, Wikidata)"
    return out


def write(vessels: dict[str, dict]) -> None:
    VESSELS_DIR.mkdir(parents=True, exist_ok=True)
    for vid, rec in vessels.items():
        text = json.dumps(rec, indent=1, ensure_ascii=False) + "\n"
        path = VESSELS_DIR / f"{vid}.json"
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")


def main() -> int:
    vessels = build()
    write(vessels)
    surv = [v for v in vessels.values() if v["fate"]["status"] == "survives"]
    c.log(f"vessels: {len(vessels)} records, {len(surv)} survivors ({sum(1 for v in surv if v['berth'])} with a berth on the map); "
          f"{sum(1 for v in vessels.values() for s in v['career'] if s['station_key'])} career lines joined to a station")
    return 0


if __name__ == "__main__":
    sys.exit(main())
