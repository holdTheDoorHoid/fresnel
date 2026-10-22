"""The lightship vessels and the can't-place-yet list, as the site loads them (DESIGN.md 3.5 and 4).

`build_site_data.py` calls these four functions; everything here is plain data in, plain data out:

- `scan(records)`: which station holds which source record (`lightship_stations:five-fathom-bank` -> `us-nj-five-fathom-bank`).
  A station is found by the key a source record carries, never by an id guessed from a name.
- `load_vessels(dir)`: `data/vessels/<id>.json` (pipeline/build_vessels.py writes them).
- `station_vessels(vessels, key_to_id, visible)`: station id -> the vessels that served it (a lightship station) or
  that lie there now (a surviving hull's berth). The station's `s/<id>.json` carries this as `vessels`.
- `vessel_page(vessel, key_to_id, visible)`: the `v/<id>.json` the vessel's page is made from: the career with each
  station linked to its page (when it has one on the map) and the berth.
- `unplaced(sources_dir, key_to_id, vessels)`: `unplaced.json`: the stations the sources name but no source places.

Python 3.12, standard library only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Iterable

# The sources whose records can be tied to a station on the map by their key
KEYED_SOURCES = ("lightship_stations", "lss_reports")


def scan(records: Iterable[dict], usable: Callable[[dict], bool] = lambda r: True) -> tuple[dict[str, str], dict[str, str]]:
    """(source key -> station id, station id -> name) over the stations that will be published."""
    key_to_id: dict[str, str] = {}
    visible: dict[str, str] = {}
    for rec in records:
        if not isinstance(rec, dict) or rec.get("merged_into") or rec.get("hidden") or not usable(rec):
            continue
        visible[rec["id"]] = rec["name"]
        for s in rec.get("sources") or []:
            if isinstance(s, dict) and s.get("source") in KEYED_SOURCES and isinstance(s.get("key"), str):
                key_to_id.setdefault(s["key"], rec["id"])
    return key_to_id, visible


def load_vessels(directory: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if directory.is_dir():
        for f in sorted(directory.glob("*.json")):
            try:
                v = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(v, dict) and v.get("id") == f.stem:
                out[v["id"]] = v
    return out


def _first(stints: list[dict]) -> int:
    years = [s["start"] for s in stints if isinstance(s.get("start"), int)]
    return min(years) if years else 9999


def station_vessels(vessels: dict[str, dict], key_to_id: dict[str, str], visible: dict[str, str]) -> dict[str, list[dict]]:
    """station id -> [{id, hull, names, role, stints}], ordered by the first year served; role is "served" or "berth"."""
    out: dict[str, list[dict]] = {}
    for vid in sorted(vessels):
        v = vessels[vid]
        stints: dict[str, list[dict]] = {}
        for line in v.get("career") or []:
            sid = key_to_id.get(line.get("station_key") or "")
            if sid:
                stints.setdefault(sid, []).append({"start": line.get("start"), "end": line.get("end")})
        for sid, ss in stints.items():
            out.setdefault(sid, []).append({"id": vid, "hull": v["hull"], "names": v.get("names") or [], "role": "served", "stints": ss})
        berth = v.get("berth") or {}
        if berth.get("station_id") in visible:
            out.setdefault(berth["station_id"], []).append({"id": vid, "hull": v["hull"], "names": v.get("names") or [], "role": "berth", "stints": []})
    for sid, lst in out.items():
        lst.sort(key=lambda x: (x["role"] != "served", _first(x["stints"]), x["id"]))
    return out


def vessel_page(v: dict, key_to_id: dict[str, str], visible: dict[str, str]) -> dict:
    career = []
    for line in v.get("career") or []:
        sid = key_to_id.get(line.get("station_key") or "")
        career.append({"station": line["station"], "station_id": sid if sid in visible else None,
                       "start": line.get("start"), "end": line.get("end")})
    berth = v.get("berth")
    if berth and berth.get("station_id") in visible:
        berth = {k: berth[k] for k in ("station_id", "name", "lat", "lon", "note") if berth.get(k) is not None}
    else:
        berth = None
    return {"id": v["id"], "hull": v["hull"], "wal": v.get("wal"), "names": v.get("names") or [], "built": v.get("built"),
            "retired": v.get("retired"), "fate": v.get("fate") or {}, "berth": berth, "career": career, "sources": v.get("sources") or []}


def _years(rec: dict) -> tuple[int | None, int | None]:
    light = rec.get("light") or {}
    first, last = light.get("first_lit"), light.get("deactivated")
    listed = (rec.get("extra") or {}).get("years_listed") or []
    if first is None and listed:
        first = min(listed)
    if last is None and listed and rec.get("kind") == "life_saving_station":
        last = max(listed)
    return first, last


def unplaced(sources_dir: Path, key_to_id: dict[str, str], vessels: dict[str, dict]) -> dict:
    """The stations that the lightship and life-saving sources name and that no source places on the map: those with no
    position that no station on the map holds. Each carries the reason, so a reader knows what would settle it."""
    by_key: dict[str, list[str]] = {}
    for vid in sorted(vessels):
        for line in vessels[vid].get("career") or []:
            if line.get("station_key") and vid not in by_key.setdefault(line["station_key"], []):
                by_key[line["station_key"]].append(vid)
    items: list[dict] = []
    for source in KEYED_SOURCES:
        path = sources_dir / f"{source}.json"
        if not path.is_file():
            continue
        for rec in json.loads(path.read_text(encoding="utf-8")).get("records") or []:
            if rec.get("lat") is not None or rec["key"] in key_to_id:
                continue
            extra = rec.get("extra") or {}
            first, last = _years(rec)
            item = {
                "key": rec["key"], "kind": rec["kind"], "name": rec["name"], "other_names": rec.get("other_names") or [],
                "region": rec.get("region"), "country": rec.get("country") or "US", "first": first, "last": last,
                "reason": extra.get("unplaced_reason") or "no source gives a position",
                # a depot, a bell boat or a station that was never built has no mooring to suggest
                "suggest": not (extra.get("not_a_mooring") or extra.get("never_built")),
                "vessels": [{"id": vid, "hull": vessels[vid]["hull"]} for vid in by_key.get(rec["key"], [])],
            }
            if extra.get("location_text"):
                item["where"] = extra["location_text"]
            if extra.get("locality"):
                item["where"] = extra["locality"]
            if rec.get("url"):
                item["url"] = rec["url"]
            items.append(item)
    items.sort(key=lambda x: (x["kind"], x["country"], x["region"] or "~", x["name"]))
    return {
        "note": "Stations the sources name that no source gives a position for, and that no station on the map holds yet.",
        "count": len(items),
        "stations": items,
    }
