#!/usr/bin/env python3
"""Build the data files the Fresnel website loads (DESIGN.md section 4, "What the site loads").

Reads the canonical stations (data/stations/**/*.json), stories (data/stories/<id>.md),
research (data/research/<id>.json: its keepers roster and sources), the vocabularies
(data/vocab.json) and the source extract headers (data/sources/*.json), and writes
web/public/data/:

  stations.geojson  every visible station as a point, with short property names (FORMAT below,
                    repeated in meta.json "format")
  s/<id>.json       the full canonical record, plus, when they exist:
                      story_html       the story (story_md.markdown_to_html)
                      chapters         [{"id", "title"}] for the story's `## ` headings
                      keepers          the research roster (DESIGN.md 3.6), each line
                                       {name, role, from, to, note, cite[]}
                      research_sources [{n, title, publisher, url, accessed}] the cites point at
                      research         {researched, verdict, confidence} for the page's line
  meta.json         counts, regions, the source list with credit lines and retrieved dates,
                    build date, and the geojson format legend
  redirects.json    {"redirects": {old id: new id}} for stations the merge folded into others
                    (merged_into); the prerender step writes a redirecting page at each old address

Hidden records (hidden: true) and retired ones (merged_into) are not published. A record that
fails basic checks is skipped with a warning, so one bad file never takes the site down; pass
--strict to fail instead. If data/stations/ is empty and --fallback-fixtures is given, the
sample records in web/fixtures/ are used, with a loud banner and "fixtures": true in meta.json
(the site then shows a "Sample data" notice).

Python 3.12, standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regions  # noqa: E402
import story_md  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
FIXTURES = REPO / "web" / "fixtures"
DEFAULT_OUT = REPO / "web" / "public" / "data"
MARKER = ".fresnel-site-data"

ID_RE = re.compile(r"^[a-z]{2}-[a-z0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")

FORMAT = {
    "i": "id",
    "n": "name",
    "r": "region: state, territory, province or territory code (pipeline/regions.py; unique across countries)",
    "cc": "country, ISO 3166-1 alpha-2 (absent = US)",
    "c": "county or local unit (absent = unknown)",
    "k": "kind (vocab.kind)",
    "s": "status (vocab.status)",
    "v": "verification (vocab.verification)",
    "a": "access level (vocab.access; absent = unknown)",
    "sf": "staffing when people live or keep there: staffed or volunteer (absent = otherwise)",
    "bo": "1 = reached only by boat (absent = no, or not recorded)",
    "cl": "1 = the tower can be climbed (absent = no, or not recorded)",
    "sy": "1 = somewhere to stay: rental, inn, hostel or keeper program (absent = none recorded)",
    "tr": "1 = on tribal land: ownership tribal (absent = no, or not recorded)",
    "rg": "1 = on a heritage register such as the NRHP or the Canadian Register (absent = none recorded)",
    "o": "other names joined with | (absent = none)",
    "y0": "first year a light is recorded here: first lit, or built when that is all we have (absent = unknown)",
    "y1": "year the light went out or the station was lost (absent = still lit or standing, or not recorded)",
    "st": "1 = has a researched story (absent = not yet)",
    "fh": "the light's focal height in metres, as in light.focal_height_m (absent = not recorded)",
    "rn": "the light's charted range in nautical miles, as in light.range_nm (absent = not recorded)",
}

KNOWN_SOURCES: dict[str, dict[str, str]] = {
    "wikidata": {
        "title": "Wikidata",
        "url": "https://www.wikidata.org/",
        "license": "CC0 1.0",
        "credit": "Wikidata contributors (CC0)",
    },
    "osm": {
        "title": "OpenStreetMap",
        "url": "https://www.openstreetmap.org/copyright",
        "license": "ODbL 1.0",
        "credit": "© OpenStreetMap contributors",
    },
}

START_EVENTS = ("first_lit", "built")
END_EVENTS = ("deactivated", "destroyed", "burned", "collapsed", "removed")
LOST_STATUSES = ("lost", "ruins")


class Log:
    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet
        self.warnings = 0
        self.gha = os.environ.get("GITHUB_ACTIONS") == "true"

    def info(self, msg: str) -> None:
        if not self.quiet:
            print(msg)

    def warn(self, msg: str, file: Path | None = None) -> None:
        self.warnings += 1
        if self.gha:
            loc = f" file={file}" if file else ""
            print(f"::warning{loc}::{msg}")
        else:
            print(f"WARNING: {msg}" + (f" ({file})" if file else ""), file=sys.stderr)


def _num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_record(rec: object) -> str | None:
    """A problem description, or None if the record is usable for the site."""
    if not isinstance(rec, dict):
        return "not a JSON object"
    rid = rec.get("id")
    if not isinstance(rid, str) or not ID_RE.match(rid) or len(rid) > 120:
        return f"id {rid!r} is missing or not of the form <country>-<region>-<slug>"
    if not isinstance(rec.get("name"), str) or not rec["name"].strip():
        return "name is missing"
    loc = rec.get("location")
    if not isinstance(loc, dict) or not _num(loc.get("lat")) or not _num(loc.get("lon")):
        return "location.lat / location.lon missing"
    if not (-90 <= loc["lat"] <= 90 and -180 <= loc["lon"] <= 180):
        return "coordinates out of range"
    for key in ("region", "kind", "status", "verification"):
        if not isinstance(rec.get(key), str):
            return f"{key} is missing"
    return None


def _event_years(rec: dict, names: tuple[str, ...]) -> list[int]:
    return [e["year"] for e in rec.get("events") or []
            if isinstance(e, dict) and e.get("event") in names and isinstance(e.get("year"), int)]


def year_range(rec: dict) -> tuple[int | None, int | None]:
    """(first year a light is recorded here, the year it ended). The start is the light's
    first_lit year, else the earliest first_lit or built event, else the earliest structure's
    built year. The end is given only for a station whose light is out or which is lost: its
    light.deactivated year, else the latest ending event."""
    light = rec.get("light") if isinstance(rec.get("light"), dict) else {}
    starts = [y for y in [light.get("first_lit")] if isinstance(y, int)]
    starts += _event_years(rec, START_EVENTS)
    starts += [s["built"] for s in rec.get("structures") or [] if isinstance(s, dict) and isinstance(s.get("built"), int)]
    y0 = min(starts) if starts else None
    y1 = None
    if rec.get("status") in ("inactive", "lost", "ruins", "relocated"):
        ends = [y for y in [light.get("deactivated")] if isinstance(y, int)]
        ends += _event_years(rec, END_EVENTS)
        y1 = max(ends) if ends else None
    if y0 is not None and y1 is not None and y1 < y0:
        y1 = None
    return y0, y1


def country_of(rec: dict) -> str:
    c = rec.get("country")
    return c if isinstance(c, str) and c else (regions.country_of(rec.get("region")) or "US")


def feature(rec: dict, has_story: bool = False) -> dict:
    loc = rec["location"]
    props: dict[str, object] = {
        "i": rec["id"],
        "n": rec["name"],
        "r": rec["region"],
        "k": rec["kind"],
        "s": rec["status"],
        "v": rec["verification"],
    }
    country = country_of(rec)
    if country != "US":
        props["cc"] = country
    if isinstance(rec.get("county"), str) and rec["county"].strip():
        props["c"] = rec["county"].strip()
    access = (rec.get("access") or {}).get("level")
    if isinstance(access, str) and access != "unknown":
        props["a"] = access
    staffing = (rec.get("staffing") or {}).get("status")
    if staffing in ("staffed", "volunteer"):
        props["sf"] = staffing
    visit = rec.get("visit") or {}
    if visit.get("boat_only") is True:
        props["bo"] = 1
    if visit.get("climbable") is True:
        props["cl"] = 1
    if isinstance(rec.get("stay"), dict) and rec["stay"]:
        props["sy"] = 1
    if rec.get("ownership") == "tribal":
        props["tr"] = 1
    if rec.get("registers"):
        props["rg"] = 1
    others = [n for n in rec.get("other_names") or [] if isinstance(n, str) and n.strip()]
    if others:
        props["o"] = "|".join(n.replace("|", "/") for n in others)
    y0, y1 = year_range(rec)
    if y0 is not None:
        props["y0"] = y0
    if y1 is not None:
        props["y1"] = y1
    if has_story:
        props["st"] = 1
    # The light's height and range, for the map's range rings (DESIGN.md section 4, the light at night).
    light = rec.get("light") if isinstance(rec.get("light"), dict) else {}
    for key, field in (("fh", "focal_height_m"), ("rn", "range_nm")):
        if _num(light.get(field)) and light[field] > 0:
            props[key] = round(float(light[field]), 1)
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [round(loc["lon"], 5), round(loc["lat"], 5)]},
        "properties": props,
    }


def regions_meta(by_region: Counter) -> dict:
    """Countries and regions in listing order (the US's states and DC alphabetically, then its
    territories, then Canada's provinces and territories), with counts."""
    out = []
    for c in regions.COUNTRY_ORDER:
        codes = [code for code in regions.REGION_NAMES if regions.REGION_COUNTRY[code] == c]
        main = sorted((code for code in codes if code not in regions.US_TERRITORIES), key=regions.region_name)
        terr = [code for code in regions.US_TERRITORIES if code in codes]
        out.append({
            "code": c, "name": regions.COUNTRY_NAMES[c], "region_words": list(regions.REGION_WORDS[c]),
            "regions": [{"code": code, "name": regions.region_name(code), "territory": code in regions.US_TERRITORIES,
                         "stations": by_region.get(code, 0)} for code in main + terr],
        })
    return {"countries": out}


# ---------------------------------------------------------------------------------------
# Research: the keepers roster and the sources its lines cite (DESIGN.md 3.6)
# ---------------------------------------------------------------------------------------

KEEPER_KEYS = ("name", "role", "from", "to", "from_approx", "to_approx", "note", "cite", "person", "other_stations")
SOURCE_KEYS = ("n", "title", "publisher", "url", "accessed", "date")


def load_research(path: Path, log: Log) -> dict | None:
    if not path.is_file():
        return None
    try:
        res = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        log.warn(f"research file is not valid JSON: {e}", path)
        return None
    return res if isinstance(res, dict) else None


def research_extras(res: dict) -> dict:
    """What a station page takes from its research file: the roster, the sources it cites and
    the research line. Shapes are checked by validate.py; here, anything malformed is left out."""
    out: dict = {}
    keepers = []
    for k in res.get("keepers") or []:
        if isinstance(k, dict) and isinstance(k.get("name"), str) and k["name"].strip():
            keepers.append({key: k.get(key) for key in KEEPER_KEYS if k.get(key) is not None})
    if keepers:
        out["keepers"] = keepers
    sources = []
    for s in res.get("sources") or []:
        if isinstance(s, dict) and isinstance(s.get("n"), int):
            sources.append({key: s.get(key) for key in SOURCE_KEYS if s.get(key) is not None})
    if sources:
        out["research_sources"] = sources
    ver = res.get("verification") if isinstance(res.get("verification"), dict) else {}
    line = {"researched": res.get("researched"), "checked": ver.get("checked"),
            "verdict": ver.get("verdict"), "confidence": res.get("confidence")}
    if any(v is not None for v in line.values()):
        out["research"] = {k: v for k, v in line.items() if v is not None}
    return out


def _write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _prepare_out(out: Path) -> None:
    out = out.resolve()
    if out in (REPO, REPO.parent, Path(out.anchor)) or out == Path.home():
        raise SystemExit(f"Refusing to write site data into {out}")
    if out.exists() and any(out.iterdir()) and not (out / MARKER).exists():
        raise SystemExit(f"{out} is not empty and was not made by this script; refusing to clear it")
    out.mkdir(parents=True, exist_ok=True)
    (out / MARKER).write_text("Generated by pipeline/build_site_data.py. Safe to delete.\n")
    if (out / "s").exists():
        shutil.rmtree(out / "s")
    (out / "s").mkdir()


def load_source_headers(sources_dir: Path, log: Log) -> dict[str, dict]:
    headers: dict[str, dict] = {}
    for path in sorted(sources_dir.glob("*.json")) if sources_dir.is_dir() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            log.warn(f"source extract is not valid JSON: {e}", path)
            continue
        if not isinstance(data, dict) or data.get("kind") == "reference":
            continue
        sid = data.get("source") or path.stem
        headers[sid] = {
            "title": data.get("title"), "url": data.get("url"), "license": data.get("license"),
            "credit": data.get("credit"), "retrieved": data.get("retrieved"),
            "records": len(data.get("records") or []),
        }
    return headers


def build(stations_dir: Path, stories_dir: Path, research_dir: Path, sources_dir: Path, vocab_path: Path,
          out: Path, *, fixtures: bool = False, strict: bool = False, log: Log | None = None) -> dict:
    log = log or Log()
    files = sorted(stations_dir.rglob("*.json")) if stations_dir.is_dir() else []
    vocab = json.loads(vocab_path.read_text(encoding="utf-8")) if vocab_path.is_file() else {}
    headers = load_source_headers(sources_dir, log)

    _prepare_out(out)
    features: list[dict] = []
    seen: dict[str, Path] = {}
    counts: dict[str, Counter] = {k: Counter() for k in ("status", "kind", "region", "verification", "country")}
    by_country_kind: dict[str, Counter] = {}
    hidden = skipped = stories = rosters = registered = 0
    merged: dict[str, str] = {}
    names: dict[str, str] = {}
    cited: Counter[str] = Counter()
    any_fixture = fixtures

    for path in files:
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            log.warn(f"skipped, not valid JSON: {e}", path)
            skipped += 1
            continue
        if isinstance(rec, dict) and isinstance(rec.get("merged_into"), str) and rec["merged_into"]:
            merged[str(rec.get("id"))] = rec["merged_into"]
            continue
        problem = check_record(rec)
        if problem:
            log.warn(f"skipped: {problem}", path)
            skipped += 1
            continue
        if rec.get("hidden"):
            hidden += 1
            continue
        rid = rec["id"]
        if rid in seen:
            log.warn(f"skipped duplicate id {rid} (first seen in {seen[rid]})", path)
            skipped += 1
            continue
        seen[rid] = path
        any_fixture = any_fixture or bool(rec.get("fixture"))
        for field in ("kind", "status", "verification"):
            allowed = vocab.get(field)
            if allowed and rec.get(field) not in allowed:
                log.warn(f"{rid}: {field} {rec[field]!r} is not in data/vocab.json", path)

        story = stories_dir / f"{rid}.md"
        has_story = story.is_file()
        if has_story:
            md = story.read_text(encoding="utf-8")
            rec["story_html"] = story_md.markdown_to_html(md, title=rec.get("name"))
            chapters = story_md.chapters_of(md)
            if chapters:
                rec["chapters"] = chapters
            stories += 1
        res = load_research(research_dir / f"{rid}.json", log)
        if res:
            rec.update(research_extras(res))
            rosters += bool(rec.get("keepers"))
        _write_json(out / "s" / f"{rid}.json", rec)
        features.append(feature(rec, has_story))
        country = country_of(rec)
        counts["status"][rec["status"]] += 1
        counts["kind"][rec["kind"]] += 1
        counts["region"][rec["region"]] += 1
        counts["country"][country] += 1
        counts["verification"][rec["verification"]] += 1
        by_country_kind.setdefault(country, Counter())[rec["kind"]] += 1
        registered += bool(rec.get("registers"))
        names[rid] = rec["name"]
        for s in rec.get("sources") or []:
            if isinstance(s, dict) and isinstance(s.get("source"), str):
                cited[s["source"]] += 1

    if strict and skipped:
        raise SystemExit(f"{skipped} record(s) failed checks (see warnings above); --strict is set")

    features.sort(key=lambda f: f["properties"]["i"])
    _write_json(out / "stations.geojson", {"type": "FeatureCollection", "features": features})
    redirects = {old: new for old, new in sorted(merged.items()) if new in names}
    for old, new in sorted(merged.items()):
        if new not in names:
            log.warn(f"{old} was merged into {new}, which is not a visible station; no redirect for it")
    _write_json(out / "redirects.json", {
        "note": "Stations the merge folded into others (merged_into): the old address redirects to the new one.",
        "redirects": redirects,
    })

    source_ids = list(KNOWN_SOURCES) + sorted((set(headers) | set(cited)) - set(KNOWN_SOURCES))
    sources = []
    for sid in source_ids:
        known = KNOWN_SOURCES.get(sid, {})
        head = headers.get(sid, {})
        title = head.get("title") or known.get("title") or sid
        sources.append({
            "id": sid,
            "title": title,
            "url": head.get("url") or known.get("url"),
            "license": head.get("license") or known.get("license"),
            "credit": known.get("credit") or head.get("credit") or title,
            "retrieved": head.get("retrieved"),
            "records": head.get("records"),
            "stations": cited.get(sid, 0),
        })

    meta = {
        "built": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "fixtures": any_fixture,
        "counts": {
            "total": len(features),
            "hidden": hidden,
            "merged": len(redirects),
            "skipped": skipped,
            "stories": stories,
            "rosters": rosters,
            "registered": registered,
            "by_status": dict(sorted(counts["status"].items())),
            "by_kind": dict(sorted(counts["kind"].items())),
            "by_region": dict(sorted(counts["region"].items())),
            "by_country": dict(sorted(counts["country"].items())),
            "by_country_kind": {c: dict(sorted(k.items())) for c, k in sorted(by_country_kind.items())},
            "by_verification": dict(sorted(counts["verification"].items())),
        },
        "regions": regions_meta(counts["region"]),
        "sources": sources,
        "format": {"stations.geojson": FORMAT},
    }
    _write_json(out / "meta.json", meta)
    size = (out / "stations.geojson").stat().st_size
    log.info(f"Wrote {len(features)} stations ({hidden} hidden, {len(redirects)} merged into others, "
             f"{skipped} skipped, {stories} stories, {rosters} keeper rosters) to {out}; "
             f"stations.geojson is {size / 1024:.0f} KiB")
    return meta


def _fixture_banner(log: Log, stations_dir: Path) -> None:
    bar = "=" * 78
    print("\n".join([
        bar,
        "USING FIXTURE DATA (sample records), NOT THE REAL STATION DATABASE",
        f"  {stations_dir} has no station records yet, so this build uses",
        f"  {FIXTURES}/stations instead. The site will show a 'Sample data' banner.",
        bar,
    ]))
    if log.gha:
        print("::warning title=Site built from fixture data::data/stations/ is empty, so the site shows the sample records in web/fixtures/.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--stations", type=Path, default=DATA / "stations")
    ap.add_argument("--stories", type=Path, default=None, help="story Markdown (default: data/stories)")
    ap.add_argument("--research", type=Path, default=None, help="research JSON (default: data/research)")
    ap.add_argument("--sources", type=Path, default=DATA / "sources")
    ap.add_argument("--vocab", type=Path, default=DATA / "vocab.json")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--fallback-fixtures", action="store_true", help="use web/fixtures when data/stations is empty")
    ap.add_argument("--strict", action="store_true", help="fail if any record is skipped")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    log = Log(args.quiet)

    stations, stories, research = args.stations, args.stories, args.research
    fixtures = False
    if not (stations.is_dir() and any(stations.rglob("*.json"))):
        if not args.fallback_fixtures:
            print(f"No station records found in {stations}. Use --fallback-fixtures to build from "
                  "web/fixtures, or --stations to point at another folder.", file=sys.stderr)
            return 2
        _fixture_banner(log, stations)
        stations = FIXTURES / "stations"
        stories = stories or FIXTURES / "stories"
        research = research or FIXTURES / "research"
        fixtures = True
    build(stations, stories or DATA / "stories", research or DATA / "research", args.sources, args.vocab, args.out,
          fixtures=fixtures, strict=args.strict, log=log)
    if log.warnings:
        log.info(f"{log.warnings} warning(s); see above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
