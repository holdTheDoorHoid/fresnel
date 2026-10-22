#!/usr/bin/env python3
"""Build the keepers index's committed files from the U.S. Lighthouse Society archive cache
(DESIGN.md 3.6): data/people/<person-id>.json, data/rosters/<dir>/<station-id>.json and
data/people_report.json.

Reads the parsed cache that the corpus crawl and `research/roster.py build` leave under
$FRESNEL_RAW_ROOT/uslhs/ (places.json, rosters.json; git-ignored) and the stations in data/stations/.
It never fetches anything: the archive is crawled only by `research/roster.py crawl`, politely, and the
~24,000 person pages are never read (a roster line already names the person's record and the years).

The archive is "All Rights Reserved": only facts are kept (names, roles, years, places), each person and
each station roster links to the archive's own page, and no race or sex field is read.

  people/<id>.json            one archive person record = one person, with every stint at every place; people whose
                              service begins in 1950 or later, ends after 1960 or carries no year are not written
                              (the living-people rule, keepers.py)
  rosters/<dir>/<id>.json     for each US station, the roster of each archive place it shows, every line as the
                              archive prints it (withheld people included, with no page), and how the place was matched
  people_report.json          counts only, never a withheld name

A run on an unchanged cache writes the same bytes, and removes files for people the rule now withholds.

Usage: python3 pipeline/build_people.py [--check]     (--check writes nothing and prints the report)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import keepers as kp  # noqa: E402
import regions  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


def load_stations(stations_dir: Path) -> list[dict]:
    out = []
    for path in sorted(stations_dir.rglob("*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(rec, dict) and rec.get("id"):
            out.append({k: rec.get(k) for k in ("id", "name", "country", "region", "kind", "hidden", "merged_into", "sources", "other_names", "location")})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cache", type=Path, default=c.RAW_ROOT / "uslhs", help="the archive cache (places.json, rosters.json)")
    ap.add_argument("--stations", type=Path, default=DATA / "stations")
    ap.add_argument("--out", type=Path, default=DATA, help="writes <out>/people, <out>/rosters and <out>/people_report.json")
    ap.add_argument("--check", action="store_true", help="write nothing; print the report")
    args = ap.parse_args(argv)

    for f in ("places.json", "rosters.json"):
        if not (args.cache / f).is_file():
            print(f"{args.cache / f} is missing: run `research/roster.py crawl` and `research/roster.py build` first", file=sys.stderr)
            return 2
    places = json.loads((args.cache / "places.json").read_text(encoding="utf-8"))
    rosters = json.loads((args.cache / "rosters.json").read_text(encoding="utf-8"))
    stations = load_stations(args.stations)

    sys.path.insert(0, str(REPO / "research"))
    import roster  # noqa: E402  (the same station-to-place matching research agents use)
    result = kp.build(places, rosters, stations, resolve=roster.resolve_station)
    report = result["report"]
    report["built_from"] = "research/roster.py build (the corpus crawl of archives.uslhs.org)"
    report["stations_checked"] = sum(1 for s in stations if s.get("country") == "US" and not s.get("hidden") and not s.get("merged_into"))

    print(json.dumps(report, indent=1))
    if args.check:
        return 0
    people_files = {f"{pid}.json": rec for pid, rec in result["people"].items()}
    roster_files = {f"{regions.station_dir(sid)}/{sid}.json": rec for sid, rec in result["station_rosters"].items()}
    w, r = kp.write_tree(args.out / "people", people_files)
    print(f"people: {w} written, {r} removed, {len(people_files)} in all")
    w, r = kp.write_tree(args.out / "rosters", roster_files)
    print(f"rosters: {w} written, {r} removed, {len(roster_files)} in all")
    (args.out / "people_report.json").write_text(kp.dump(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
