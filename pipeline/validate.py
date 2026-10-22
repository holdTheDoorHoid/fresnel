#!/usr/bin/env python3
"""Check the database before the site is built (DESIGN.md section 4: validate.py gates the build).

Errors (exit status 1):

- a station file that is not valid JSON, has no id, or whose id is not `<country>-<region>-<slug>`,
  does not match its file name, or sits in the wrong folder (regions.station_dir);
- two files with one id;
- a missing required field, or a value outside data/vocab.json (kind, status, setting, structure
  type / role / material / status, lens status, staffing, ownership, access level, verification,
  event, relation, link kind, stay type);
- a position that is not a number, or lies outside every box of the station's country (a sign
  slip or a station filed under the wrong country), or a region of another country;
- `merged_into` naming a station that does not exist, is hidden, or is itself retired; a story or
  research file left under a retired id or under no station at all;
- a research file whose keepers roster is malformed (DESIGN.md 3.6: each line has a name, a
  role, from / to as a year or a "YYYY" / "YYYY-MM-DD" string or null, a note or null, and cite:
  one or more numbers of the file's own `sources`);
- a research roster line whose `person` is not an archive person id, or whose `other_stations` entry has no
  name or no cite (DESIGN.md 3.6: only a cited connection adds service elsewhere to a person);
- a keepers-index record (data/people, data/rosters) that breaks the rules: a person file whose id does not
  match its file name, with a stint that begins in 1950 or later, ends after 1960 or has no year at all
  (the living-people rule: such a person must have no file), any race or sex field, a `possibly` hint to a
  person with no file; a roster for something that is not a station;
- a story footnote reference with no definition;
- a source extract without its header, or with two records of one key.

Warnings (printed, not fatal): a position outside its own region's box but inside the country (a
light on a border or offshore), a related id that is not a station.

An empty data/stations/ passes (the site then builds from fixtures).

Usage: python3 pipeline/validate.py [--stations DIR] [--research DIR] [--stories DIR] [--sources DIR]
                                    [--people DIR] [--rosters DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keepers as keeper_rules  # noqa: E402
import regions  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
ID_RE = re.compile(r"^(?P<c>[a-z]{2})-(?P<r>[a-z]{2})-[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
REQUIRED = ("id", "name", "country", "region", "kind", "location", "status", "structures", "registers",
            "events", "sources", "verification", "hidden")
FN_REF_RE = re.compile(r"\[\^([^\]\s]+)\](?!:)")
FN_DEF_RE = re.compile(r"^\[\^([^\]\s]+)\]:", re.M)


class Problems:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: object, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: object, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def _num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_vocab(p: Problems, where: str, vocab: dict, field: str, value: object, allow_none: bool = True) -> None:
    allowed = vocab.get(field)
    if allowed is None:
        return
    if value is None and allow_none:
        return
    if value not in allowed:
        p.error(where, f"{field} {value!r} is not in data/vocab.json")


def check_station(p: Problems, path: Path, rec: dict, vocab: dict, stations_dir: Path) -> None:
    where = path.relative_to(stations_dir.parent) if stations_dir.parent in path.parents else path
    rid = rec.get("id")
    m = ID_RE.match(rid) if isinstance(rid, str) else None
    if not m:
        p.error(where, f"id {rid!r} is not of the form <country>-<region>-<slug>")
        return
    if path.stem != rid:
        p.error(where, f"file name does not match id {rid}")
    if path.parent.name != regions.station_dir(rid):
        p.error(where, f"should be in data/stations/{regions.station_dir(rid)}/")
    if rec.get("merged_into"):
        return  # a retired stub: checked against its target later
    for k in REQUIRED:
        if k not in rec:
            p.error(where, f"missing {k}")
    region, country = rec.get("region"), rec.get("country")
    if regions.country_of(region) is None:
        p.error(where, f"unknown region {region!r}")
    elif regions.country_of(region) != country:
        p.error(where, f"region {region} is not in country {country}")
    if f"{(country or '').lower()}-{(region or '').lower()}" != f"{m.group('c')}-{m.group('r')}":
        p.error(where, f"id prefix does not match country {country} and region {region}")
    loc = rec.get("location") or {}
    if not (_num(loc.get("lat")) and _num(loc.get("lon"))):
        p.error(where, "location.lat / location.lon missing")
    else:
        lat, lon = loc["lat"], loc["lon"]
        if not regions.in_country(country, lat, lon):
            p.error(where, f"position {lat}, {lon} is outside {regions.COUNTRY_NAMES.get(country, country)} "
                           f"({regions.flag_coordinate(region, lat, lon)})")
        elif not regions.in_region_box(region, lat, lon):
            p.warn(where, f"position {lat}, {lon} is outside {regions.region_name(region)}'s box")
    for field in ("kind", "status", "setting", "verification", "ownership"):
        check_vocab(p, where, vocab, field, rec.get(field), allow_none=field in ("setting", "ownership"))
    for s in rec.get("structures") or []:
        if not isinstance(s, dict):
            p.error(where, "a structure is not an object")
            continue
        check_vocab(p, where, vocab, "structure_role", s.get("role"), allow_none=False)
        check_vocab(p, where, vocab, "structure_type", s.get("type"))
        check_vocab(p, where, vocab, "structure_material", s.get("material"))
        check_vocab(p, where, vocab, "structure_status", s.get("status"), allow_none=False)
        if s.get("built") is not None and not isinstance(s.get("built"), int):
            p.error(where, f"structure built {s.get('built')!r} is not a year")
    light = rec.get("light")
    if isinstance(light, dict) and isinstance(light.get("lens"), dict):
        check_vocab(p, where, vocab, "lens_status", light["lens"].get("status"))
    for key, field in (("access", "access"), ("staffing", "staffing")):
        obj = rec.get(key) or {}
        val = obj.get("level") if key == "access" else obj.get("status")
        check_vocab(p, where, vocab, field, val)
    if isinstance(rec.get("stay"), dict):
        check_vocab(p, where, vocab, "stay_type", rec["stay"].get("type"), allow_none=False)
    for e in rec.get("events") or []:
        check_vocab(p, where, vocab, "event", e.get("event"), allow_none=False)
        if not isinstance(e.get("year"), int):
            p.error(where, f"event {e.get('event')} has no year")
        if e.get("event") == "other" and not e.get("note"):
            p.error(where, "an 'other' event needs a note")
    for r in rec.get("related") or []:
        check_vocab(p, where, vocab, "relation", r.get("relation"), allow_none=False)
    for ln in rec.get("links") or []:
        check_vocab(p, where, vocab, "link_kind", ln.get("kind"))
        if not str(ln.get("url") or "").startswith(("http://", "https://")):
            p.error(where, f"link {ln.get('url')!r} is not http(s)")
    if rec.get("hidden") and not rec.get("hidden_reason"):
        p.error(where, "hidden without a hidden_reason")


def check_research(p: Problems, path: Path, res: object) -> None:
    if not isinstance(res, dict):
        p.error(path, "not a JSON object")
        return
    numbers = {s.get("n") for s in res.get("sources") or [] if isinstance(s, dict)}
    keepers = res.get("keepers")
    if keepers is None:
        return
    if not isinstance(keepers, list):
        p.error(path, "keepers is not a list")
        return
    for i, k in enumerate(keepers):
        at = f"{path} keepers[{i}]"
        if not isinstance(k, dict):
            p.error(at, "not an object")
            continue
        if not isinstance(k.get("name"), str) or not k["name"].strip():
            p.error(at, "name is missing")
        if k.get("role") is not None and not (isinstance(k["role"], str) and k["role"].strip()):
            p.error(at, "role must be text (as the source gives it) or null")
        for f in ("from", "to"):
            v = k.get(f)
            if v is not None and not (isinstance(v, int) and 1500 <= v <= 2100) and not (isinstance(v, str) and DATE_RE.match(v)):
                p.error(at, f"{f} {v!r} is not a year, a 'YYYY' / 'YYYY-MM-DD' string or null")
        if k.get("note") is not None and not isinstance(k["note"], str):
            p.error(at, "note must be text or null")
        cite = k.get("cite")
        if not isinstance(cite, list) or not cite or not all(isinstance(c, int) for c in cite):
            p.error(at, "cite must list one or more source numbers")
        elif any(c not in numbers for c in cite):
            p.error(at, f"cites {sorted(set(cite) - numbers)}, which the file's sources do not have")
        if k.get("person") is not None and not (isinstance(k["person"], str) and keeper_rules.PERSON_ID_RE.match(k["person"])):
            p.error(at, f"person {k['person']!r} is not an archive person id (the slug of archives.uslhs.org/people/<slug>)")
        for j, o in enumerate(k.get("other_stations") or []):
            if not (isinstance(o, dict) and isinstance(o.get("name"), str) and o["name"].strip()):
                p.error(at, f"other_stations[{j}] has no name")
            elif not (isinstance(o.get("cite"), list) and o["cite"] and all(isinstance(c, int) for c in o["cite"])):
                p.error(at, f"other_stations[{j}] ({o['name']}) has no cite: service elsewhere joins a person only with a source")
            elif any(c not in numbers for c in o["cite"]):
                p.error(at, f"other_stations[{j}] cites {sorted(set(o['cite']) - numbers)}, which the file's sources do not have")


FORBIDDEN_KEYS = {"race", "sex", "gender", "ethnicity"}


def _forbidden(obj: object) -> str | None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and k.lower() in FORBIDDEN_KEYS:
                return k
            found = _forbidden(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _forbidden(v)
            if found:
                return found
    return None


def check_people(p: Problems, people_dir: Path | None, rosters_dir: Path | None, recs: dict[str, dict]) -> None:
    """data/people and data/rosters: the keepers index's committed files (pipeline/keepers.py)."""
    ids: set[str] = set()
    files: dict[str, dict] = {}
    for path in sorted(people_dir.glob("*.json")) if people_dir and people_dir.is_dir() else []:
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            p.error(path, f"not valid JSON: {e}")
            continue
        if not isinstance(rec, dict):
            p.error(path, "not a JSON object")
            continue
        if rec.get("id") != path.stem:
            p.error(path, f"id {rec.get('id')!r} does not match the file name")
        if not keeper_rules.PERSON_ID_RE.match(path.stem):
            p.error(path, "the file name is not an archive person id")
        if not isinstance(rec.get("name"), str) or not rec["name"].strip():
            p.error(path, "name is missing")
        stints = rec.get("stints")
        if not isinstance(stints, list) or not stints:
            p.error(path, "stints must be a non-empty list")
            continue
        for i, s in enumerate(stints):
            if not isinstance(s, dict) or not isinstance(s.get("place"), str) or not s["place"]:
                p.error(path, f"stints[{i}] has no place")
                continue
            for f in ("from", "to"):
                v = s.get(f)
                if v is not None and not (isinstance(v, int) and not isinstance(v, bool) and keeper_rules.MIN_YEAR <= v <= keeper_rules.MAX_YEAR):
                    p.error(path, f"stints[{i}].{f} {v!r} is not a year")
        years = [{"from": s.get("from") if isinstance(s, dict) else None, "to": s.get("to") if isinstance(s, dict) else None} for s in stints]
        why = keeper_rules.withhold_reason(years)
        if why:
            p.error(path, f"this person is withheld by the living-people rule ({why}): a withheld person must have no file (DESIGN.md 3.6)")
        bad = _forbidden(rec)
        if bad:
            p.error(path, f"carries a race or sex field ({bad!r}), which the site never keeps")
        ids.add(path.stem)
        files[path.stem] = rec
    for pid, rec in files.items():
        for o in rec.get("possibly") or []:
            if o == pid or o not in ids:
                p.error(people_dir / f"{pid}.json" if people_dir else pid, f"possibly {o!r} is not another person with a file")
    for path in sorted(rosters_dir.rglob("*.json")) if rosters_dir and rosters_dir.is_dir() else []:
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            p.error(path, f"not valid JSON: {e}")
            continue
        sid = rec.get("station") if isinstance(rec, dict) else None
        if not isinstance(sid, str) or sid != path.stem:
            p.error(path, f"station {sid!r} does not match the file name")
            continue
        if path.parent.name != regions.station_dir(sid):
            p.error(path, f"should be in data/rosters/{regions.station_dir(sid)}/")
        target = recs.get(sid)
        if target is None:
            p.error(path, f"roster for {sid}, which is not a station")
        elif target.get("hidden") or target.get("merged_into"):
            p.warn(path, f"roster for {sid}, which is hidden or retired: run pipeline/build_people.py again")
        bad = _forbidden(rec)
        if bad:
            p.error(path, f"carries a race or sex field ({bad!r}), which the site never keeps")
        for pl in rec.get("places") or []:
            for i, l in enumerate(pl.get("lines") or []):
                if not (isinstance(l, dict) and isinstance(l.get("name"), str) and l["name"].strip() and isinstance(l.get("person"), str)):
                    p.error(path, f"a line of {pl.get('slug')} has no name or no person id")
                    break


def check_story(p: Problems, path: Path, text: str) -> None:
    defs = set(FN_DEF_RE.findall(text))
    for ref in sorted(set(FN_REF_RE.findall(text))):
        if ref not in defs:
            p.error(path, f"footnote [^{ref}] has no definition")


def check_sources(p: Problems, sources_dir: Path) -> None:
    for path in sorted(sources_dir.glob("*.json")) if sources_dir.is_dir() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            p.error(path, f"not valid JSON: {e}")
            continue
        for k in ("source", "title", "retrieved", "license", "records"):
            if k not in data:
                p.error(path, f"header has no {k}")
        keys = [r.get("key") for r in data.get("records") or []]
        if len(keys) != len(set(keys)):
            p.error(path, "two records share a key")


def validate(stations_dir: Path, research_dir: Path, stories_dir: Path, sources_dir: Path, vocab_path: Path,
             people_dir: Path | None = None, rosters_dir: Path | None = None) -> Problems:
    p = Problems()
    vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
    recs: dict[str, dict] = {}
    for path in sorted(stations_dir.rglob("*.json")) if stations_dir.is_dir() else []:
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            p.error(path, f"not valid JSON: {e}")
            continue
        if not isinstance(rec, dict):
            p.error(path, "not a JSON object")
            continue
        rid = rec.get("id")
        if isinstance(rid, str) and rid in recs:
            p.error(path, f"id {rid} is used by two files")
        check_station(p, path, rec, vocab, stations_dir)
        if isinstance(rid, str):
            recs[rid] = rec
    for rid, rec in recs.items():
        target = rec.get("merged_into")
        if target:
            t = recs.get(target)
            if t is None or t.get("hidden") or t.get("merged_into"):
                p.error(rid, f"merged_into {target} is not a visible station")
        for r in rec.get("related") or []:
            if r.get("id") not in recs:
                p.warn(rid, f"related id {r.get('id')} is not a station")
    for folder, kind in ((research_dir, "research"), (stories_dir, "story")):
        for path in sorted(folder.glob("*.json" if kind == "research" else "*.md")) if folder.is_dir() else []:
            rid = path.stem
            if rid not in recs:
                p.error(path, f"{kind} file for {rid}, which is not a station")
            elif recs[rid].get("merged_into"):
                p.error(path, f"{kind} file under {rid}, retired into {recs[rid]['merged_into']}: move it there")
            text = path.read_text(encoding="utf-8")
            if kind == "research":
                try:
                    check_research(p, path, json.loads(text))
                except json.JSONDecodeError as e:
                    p.error(path, f"not valid JSON: {e}")
            else:
                check_story(p, path, text)
    check_sources(p, sources_dir)
    check_people(p, people_dir, rosters_dir, recs)
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Fresnel's station database")
    ap.add_argument("--stations", type=Path, default=DATA / "stations")
    ap.add_argument("--research", type=Path, default=DATA / "research")
    ap.add_argument("--stories", type=Path, default=DATA / "stories")
    ap.add_argument("--sources", type=Path, default=DATA / "sources")
    ap.add_argument("--people", type=Path, default=DATA / "people")
    ap.add_argument("--rosters", type=Path, default=DATA / "rosters")
    ap.add_argument("--vocab", type=Path, default=DATA / "vocab.json")
    ap.add_argument("--quiet", action="store_true", help="print errors only")
    args = ap.parse_args(argv)
    p = validate(args.stations, args.research, args.stories, args.sources, args.vocab, args.people, args.rosters)
    if not args.quiet:
        for w in p.warnings:
            print(f"warning: {w}")
    for e in p.errors:
        print(f"ERROR: {e}", file=sys.stderr)
    n = len(list(args.stations.rglob("*.json"))) if args.stations.is_dir() else 0
    k = len(list(args.people.glob("*.json"))) if args.people.is_dir() else 0
    print(f"validate: {n} station files, {k} people files, {len(p.errors)} errors, {len(p.warnings)} warnings")
    return 1 if p.errors else 0


if __name__ == "__main__":
    sys.exit(main())
