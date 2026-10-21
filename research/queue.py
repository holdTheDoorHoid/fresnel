#!/usr/bin/env python3
"""Story-research queue: stations without a story, in priority order, and a compact brief for each.

  research/queue.py --summary            counts by priority tier, then per country and region
  research/queue.py --next 30            ids of the next 30 stations
  research/queue.py --briefs ID [ID...]  compact JSON briefs (what a researcher needs, nothing else)

Select with --country US|CA and --region ME,NS,... (codes or names; combine with --summary/--next).

Priority (within a tier, stations with more sources and links first: more to work with):
  1 standing lights (active, inactive, relocated) on a register (NRHP, a Canadian heritage designation)
  2 other standing lights
  3 lightship stations, surviving lightships and life-saving stations
  4 lost lights and ruins
  5 status unknown
Replicas come last of all. Hidden stations and retired ids (merged_into) are never queued."""
import argparse, glob, json, os, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "pipeline"))  # appended, never first: nothing here may shadow the standard library
import regions  # noqa: E402

STANDING = {"active", "inactive", "relocated"}
LIGHT_KINDS = {"lighthouse", "range_lights", "pier_light", "harbor_light"}


def stations(country=None, region_codes=None):
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "stations", "*", "*.json"))):
        with open(f, encoding="utf-8") as fh:
            s = json.load(fh)
        if s.get("hidden") or s.get("merged_into"):
            continue
        if country and str(s.get("country") or "").upper() != country:
            continue
        if region_codes and str(s.get("region") or "").upper() not in region_codes:
            continue
        yield s


def station_path(sid):
    hits = glob.glob(os.path.join(ROOT, "data", "stations", "*", glob.escape(f"{sid}.json")))
    return hits[0] if hits else None


def has_story(sid):
    return os.path.exists(os.path.join(ROOT, "data", "stories", f"{sid}.md"))


def tier(s):
    status, kind = s.get("status"), s.get("kind")
    if status == "replica":
        return 6
    if kind in LIGHT_KINDS and status in STANDING:
        return 1 if s.get("registers") else 2
    if kind in ("lightship_station", "lightship", "life_saving_station") and status != "unknown":
        return 3
    if status in ("lost", "ruins"):
        return 4
    return 5


def weight(s):
    return len({x.get("source") for x in s.get("sources") or []}) * 10 + len(s.get("links") or [])


def queue(country=None, region_codes=None):
    todo = [s for s in stations(country, region_codes) if not has_story(s["id"])]
    todo.sort(key=lambda s: (tier(s), -weight(s), s["id"]))
    return todo


def register_label(r):
    return " ".join(str(x) for x in (r.get("register"), r.get("number")) if x)


def source_pages(s):
    pages = []
    for link in s.get("links") or []:
        if link.get("url") and link.get("kind") != "osm":
            pages.append(f'{link.get("label")}: {link["url"]}')
    for r in s.get("registers") or []:
        if r.get("url"):
            pages.append(f'{register_label(r)}: {r["url"]}')
    return list(dict.fromkeys(pages))


def brief(s):
    loc = s.get("location") or {}
    country = str(s.get("country") or "").upper()
    region = str(s.get("region") or "").upper()
    light = {k: v for k, v in (s.get("light") or {}).items() if v not in (None, [], {}) and k != "from"}
    structures = []
    for st in s.get("structures") or []:
        bits = [st.get("role"), st.get("type"), st.get("material"), st.get("built") and f'built {st["built"]}',
                st.get("height_m") and f'{st["height_m"]} m', st.get("status"), st.get("note")]
        structures.append(", ".join(str(b) for b in bits if b))
    b = {
        "id": s["id"], "name": s["name"], "other_names": s.get("other_names") or None,
        "kind": s.get("kind"), "status": s.get("status"), "status_note": s.get("status_note"),
        "country": {"US": "United States", "CA": "Canada"}.get(country, country),
        "region": region or None, "region_name": regions.region_name(region) or None,
        "local_unit": regions.local_unit_label(country, region, s.get("county")),
        "water": s.get("water"), "setting": s.get("setting"),
        "lat": loc.get("lat"), "lon": loc.get("lon"), "position_from": loc.get("from"),
        "structures": structures or None, "light": light or None,
        "registers": [register_label(r) for r in s.get("registers") or []] or None,
        "aton": {k: v for k, v in (s.get("aton") or {}).items() if v} or None,
        "agency": s.get("agency"), "ownership": s.get("ownership"),
        "access": (s.get("access") or {}).get("level"), "staffing": (s.get("staffing") or {}).get("status"),
        "events": [f'{e.get("year")} {e.get("event")}' + (f' ({e["note"]})' if e.get("note") else "") for e in s.get("events") or []] or None,
        "related": [f'{r.get("relation")}: {r.get("id")}' for r in s.get("related") or []] or None,
        "source_pages": source_pages(s) or None,
        "conflicts": [c.get("note") or f'{c.get("field")}: ' + ", ".join(f'{v.get("source")}={v.get("value")}' for v in c.get("values") or []) for c in s.get("conflicts") or []] or None,
    }
    return {k: v for k, v in b.items() if v not in (None, [], {}, "unknown")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--next", type=int, metavar="N")
    ap.add_argument("--briefs", nargs="+", metavar="ID")
    ap.add_argument("--country")
    ap.add_argument("--region", action="append")
    a = ap.parse_args()
    if a.briefs:
        out = []
        for sid in a.briefs:
            p = station_path(sid)
            if p:
                with open(p, encoding="utf-8") as fh:
                    out.append(brief(json.load(fh)))
            else:
                print(f"no station {sid}", file=sys.stderr)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    country = a.country.upper() if a.country else None
    codes = None
    if a.region:
        codes = set()
        for v in a.region:
            for part in v.split(","):
                code = regions.parse_region(part.strip())
                if not code:
                    sys.exit(f"unknown region {part!r}")
                codes.add(code)
    q = queue(country, codes)
    if a.next:
        print("\n".join(s["id"] for s in q[: a.next]))
    if a.summary or not a.next:
        print(f"{len(q)} stations without a story")
        for t, n in sorted(Counter(tier(s) for s in q).items()):
            print(f"  tier {t}: {n}")
        for r, n in Counter(f'{s.get("country")}-{s.get("region")}' for s in q).most_common():
            print(f"  {r}: {n}")


if __name__ == "__main__":
    main()
