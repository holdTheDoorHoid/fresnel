"""Canada's rules of the merge (pipeline/merge.py calls these at a few marked places; DESIGN.md 3.9
and 2.3). Everything Canadian that is not a plain source-order or precedence entry lives here, so
the US branch can change merge.py without touching it.

- **Identifiers join records** (`identifier_join`). The Canadian sources carry numbers that name one
  structure: the Heritage Lighthouse id (`hl:14432`), the Coast Guard List of Lights number
  (`ccg:A456`), the Admiralty number (`adm:H3680`), the ARLHS number (`arlhs:CAN422`) and Lighthouse
  Friends' id (`lhf:2027`). A record that shares one with a station already built joins it, within
  5 km when it has a position. A record with no position (the Lighthouse Directory, the staffed list)
  can join by nothing else, and by a unique name in its province as a last resort (`name_join`).
  Keys that point at two stations are left alone and listed.
- **Records that may not start a station** (`start_blocker`): a small modern aid in the Coast Guard
  List of Lights (a tower, pole or skeleton tower that is not a lighthouse) and a record with no
  position. They only add their facts to a station another source started.
- **Staffing, access and visiting** (`apply`): the staffed-lightstation list sets `staffing` and the
  access label; Lighthouse Friends' flags and the Lighthouse Directory's wording set boat only,
  climbable, grounds open, private and lodging; the Admiralty number goes in `aton`.
- **Status notes** (`status_note`): where the historic structure is gone but the Coast Guard still
  lists a light there, and where the Lighthouse Directory lists a light as gone that another source
  shows standing.
- **Curation** (`data/curation_ca.json`, `load_curation`): explicit decisions with reasons from the
  review of the merge report (docs/sources/review_2026-10-ca.md): `rekind` (a record is another
  kind), `join` (records of one structure), `apart` (records that are not), `hide` (a station that is
  not a light, by id or by record key), `rename` (a station's display name), `detach` (a record filed
  under the wrong station by an earlier run is forgotten, to be joined elsewhere) and `merge_stations`
  (two existing stations are one: one id is retired with `merged_into`, as the permanent-ids rule
  requires).

Python 3.12, standard library only; no import from merge.py (the Rec / Station objects are used by
duck typing).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

R_IDENTIFIER_M = 5000.0
CA_SOURCES_ORDER = ["parks_canada_hl", "lighthousefriends", "ccg_list_of_lights", "rowlett"]

# ---------------------------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------------------------


def norm_ccg(value: str | None) -> str | None:
    """"A-456" -> "A456", "I-0563" -> "I563", "N-049" -> "N49"; None without a volume letter."""
    m = re.fullmatch(r"\s*([A-Z])-?\s*0*(\d+(?:\.\d+)?)\s*", value or "")
    return f"{m.group(1)}{m.group(2)}" if m else None


def norm_adm(value: str | None) -> str | None:
    """"H 0443.4" -> "H443.4"."""
    m = re.fullmatch(r"\s*([A-Z])\s*0*(\d+(?:\.\d+)?)\s*", value or "")
    return f"{m.group(1)}{m.group(2)}" if m else None


def norm_arlhs(value: str | None) -> str | None:
    m = re.fullmatch(r"\s*CAN-?\s*0*(\d+)\s*", value or "")
    return f"CAN{m.group(1)}" if m else None


def identifiers(raw: dict) -> list[str]:
    """Join keys of a source record: the ones the fetcher wrote (`extra.join_keys`) plus those its
    registers and ATON numbers give (Wikidata, OpenStreetMap)."""
    if raw.get("country") != "CA":
        return []
    ex = raw.get("extra") or {}
    keys = list(ex.get("join_keys") or [])
    if ex.get("lhf_id"):
        keys.append(f"lhf:{ex['lhf_id']}")
    for reg in raw.get("registers") or []:
        if reg.get("register") == "Heritage Lighthouse (Canada)" and reg.get("number"):
            keys.append(f"hl:{str(reg['number']).strip()}")
    aton = raw.get("aton") or {}
    for key, fn, prefix in (("ccg_list_number", norm_ccg, "ccg"), ("arlhs", norm_arlhs, "arlhs"), ("admiralty", norm_adm, "adm")):
        v = fn(aton.get(key))
        if v:
            keys.append(f"{prefix}:{v}")
    v = norm_adm(ex.get("light_reference"))
    if v:
        keys.append(f"adm:{v}")
    out, seen = [], set()
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def start_blocker(source: str, raw: dict) -> str | None:
    """Why a record may never start a station, or None."""
    ex = raw.get("extra") or {}
    if source == "ccg_list_of_lights" and not ex.get("clear_lighthouse"):
        return "a small aid in the Coast Guard's List of Lights (a tower, pole or skeleton tower) with no station near"
    return None


def unshown_reason(rec) -> str | None:
    """Reason text for a Canadian record that joined nothing, else None (the caller's own text)."""
    if not rec.has_point and rec.name:
        return "no position, and no identifier or unique name joined it to a station"
    blocker = getattr(rec, "start_blocked", None)
    return blocker or None


# ---------------------------------------------------------------------------------------------
# Curation
# ---------------------------------------------------------------------------------------------

EMPTY_CURATION = {"rekind": [], "join": [], "apart": [], "hide": [], "merge_stations": [], "rename": [], "detach": []}


def load_curation(path: Path | None) -> dict:
    data = dict(EMPTY_CURATION)
    if path and path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        for k in EMPTY_CURATION:
            data[k] = list(raw.get(k) or [])
        for k, entries in data.items():
            for e in entries:
                if not e.get("reason"):
                    raise SystemExit(f"{path}: a {k} entry has no reason: {e}")
    return data


class Curation:
    def __init__(self, data: dict | None = None) -> None:
        self.data = data or dict(EMPTY_CURATION)
        self.join_group: dict[str, set[str]] = {}
        for e in self.data["join"]:
            group = set(e["keys"])
            for k in group:
                self.join_group.setdefault(k, set()).update(group)
        self.apart_pairs: set[frozenset] = set()
        for e in self.data["apart"]:
            ks = e["keys"]
            for i, a in enumerate(ks):
                for b in ks[i + 1:]:
                    self.apart_pairs.add(frozenset((a, b)))
        self.hide_ids = {e["id"]: e["reason"] for e in self.data["hide"] if e.get("id")}
        self.hide_keys = {e["key"]: e["reason"] for e in self.data["hide"] if e.get("key")}
        self.rename_ids = {e["id"]: e for e in self.data["rename"]}
        self.detach_from = {e["key"]: e["from_station"] for e in self.data["detach"]}
        self.detach_reasons = {e["key"]: e["reason"] for e in self.data["detach"]}
        self.applied: dict[str, list] = defaultdict(list)

    def kept_apart(self, rec_key: str, station_keys: set[str]) -> bool:
        return any(frozenset((rec_key, k)) in self.apart_pairs for k in station_keys)

    def barred(self, rec_key: str, station) -> bool:
        """True when `detach` says this record must not be filed under this station (by id)."""
        sid = self.detach_from.get(rec_key)
        return sid is not None and getattr(station, "id", None) == sid

    def joined_with(self, rec_key: str) -> set[str]:
        return self.join_group.get(rec_key, set()) - {rec_key}


def detach(matcher, curation: Curation) -> None:
    """Forget that an earlier run filed a record under a given station (curation `detach`: the record's
    source gives it the wrong position, or it was joined by a name that fits the wrong light). The record
    is matched afresh and may not join that station again; a `join` entry can send it to the right one."""
    for key, sid in curation.detach_from.items():
        held = matcher.memory.get(key)
        if held is not None and getattr(held[0], "id", None) == sid:
            matcher.memory.pop(key)
            curation.applied["detach"].append({"key": key, "from": sid, "reason": curation.detach_reasons[key]})


def prepare(by_source: dict[str, list], curation: Curation) -> None:
    """Apply `rekind` before any matching: the record's kind (and so its kind group) changes."""
    by_key = {r.key: r for recs in by_source.values() for r in recs}
    for e in curation.data["rekind"]:
        rec = by_key.get(e["key"])
        if rec is None:
            curation.applied["rekind_missing"].append(e["key"])
            continue
        rec.kind = e["kind"]
        rec.raw["kind"] = e["kind"]
        if e.get("status") is not None:
            rec.status = rec.status_claim = e["status"]
        curation.applied["rekind"].append({"key": e["key"], "kind": e["kind"], "reason": e["reason"]})


# ---------------------------------------------------------------------------------------------
# Joining by identifier or name
# ---------------------------------------------------------------------------------------------


def names_exclude(rec, score: float) -> bool:
    """merge.candidates() drops a station whose name scores 0.2 or less. That score means opposites
    (North / South, Front / Rear) or different numbers, but a name with nothing in common also scores
    low. Canadian sources name one light several ways (the Coast Guard's "Toronto East Entrance Outer"
    is Mimico's lighthouse; Lighthouse Friends' "Perkwakwia Point" is Michipicoten Harbour), so for a
    Canadian record only real opposites (exactly 0.2) keep two lights apart; the 60 m rule still
    limits how near an unrelated name may be to join."""
    return not (rec.country == "CA" and score < 0.199)


def index_record(matcher, rec, st) -> None:
    """Remember which station holds each of this record's identifiers."""
    ids = getattr(matcher, "ca_ids", None)
    if ids is None:
        ids = matcher.ca_ids = defaultdict(list)
    for k in getattr(rec, "join_keys", ()):
        if st not in ids[k]:
            ids[k].append(st)


def station_keys(st) -> set[str]:
    """Every record key a station holds or held (its earlier runs' sources[] too, which are its memory)."""
    return {r.key for r in st.recs()} | {x["key"] for x in (st.existing or {}).get("sources", []) if isinstance(x, dict) and x.get("key")}


def _live(st):
    while getattr(st, "absorbed_into", None) is not None:
        st = st.absorbed_into
    return st


def identifier_join(matcher, rec):
    """(station, anchor) for the station that holds one of this record's identifiers, else None.

    Several stations holding the keys: the one holding the most, if that is unique; else none (listed
    in matcher.ca_ambiguous). A record with a position joins only within R_IDENTIFIER_M. `anchor` is
    the part of the keyed record, so the record joins that structure rather than starting a new one."""
    keys = getattr(rec, "join_keys", ())
    ids = getattr(matcher, "ca_ids", None)
    if not keys or not ids:
        return None
    votes: dict[int, tuple] = {}
    for k in keys:
        for st in ids.get(k, ()):
            st = _live(st)
            if (st.existing or {}).get("merged_into"):
                continue
            entry = votes.setdefault(id(st), [st, []])
            if k not in entry[1]:
                entry[1].append(k)
    cands = []
    for st, held in votes.values():
        if st.country() and rec.country and st.country() != rec.country:
            continue
        cur = getattr(matcher, "ca_curation", None)
        if cur is not None and (cur.kept_apart(rec.key, station_keys(st)) or cur.barred(rec.key, st)):
            continue
        if rec.has_point and st.min_dist(rec.lat, rec.lon) > R_IDENTIFIER_M:
            matcher.ca_far.append({"key": rec.key, "name": rec.name, "identifiers": held,
                                   "distance_m": round(st.min_dist(rec.lat, rec.lon)), "station": (st.recs() or [rec])[0].name})
            continue
        cands.append((len(held), st, held))
    if not cands:
        return None
    if rec.role in ("front_range", "rear_range") and len(cands) > 1:
        # a front light does not join the station that holds only the rear light of its range, nor the reverse
        opposite = "rear_range" if rec.role == "front_range" else "front_range"
        kept = [c for c in cands if not (c[1].parts and all(p.role == opposite for p in c[1].parts))]
        cands = kept or cands
    cands.sort(key=lambda c: -c[0])
    if len(cands) > 1 and cands[0][0] == cands[1][0]:
        matcher.ca_ambiguous.append({"key": rec.key, "name": rec.name, "identifiers": sorted(keys),
                                     "stations": sorted({(s.recs() or [rec])[0].name or "?" for _n, s, _h in cands})})
        return None
    _n, st, held = cands[0]
    anchor = None
    if not rec.station_level:
        for p in st.parts:
            if any(set(r.join_keys) & set(held) for r in p.recs):
                if not (p.role and rec.role and p.role != rec.role):
                    anchor = p.anchor
                break
        if anchor is None and rec.has_point and not rec.can_start and st.parts:
            # a record that may not start a station (an OpenStreetMap element marked a minor beacon) and
            # that an identifier ties to this one is the same light: it joins the nearest structure
            # rather than becoming a second tower
            near = [(rec.dist(*p.pos()), p.anchor) for p in st.parts if p.pos() and not (p.role and rec.role and p.role != rec.role)]
            if near:
                anchor = min(near)[1]
    return st, anchor


def retry_unshown(matcher) -> int:
    """After both matching passes, give every record that joined nothing one more try by identifier:
    its partner may have been placed after it (the order of two records of the same pass must not
    decide, or a second run with memory would differ from the first). Returns how many joined."""
    n = 0
    for rec in list(getattr(matcher, "unshown_recs", [])):
        if not rec.join_keys:
            continue
        hit = identifier_join(matcher, rec)
        if hit is None:
            continue
        matcher.attach(rec, hit[0], "identifier", hit[1])
        matcher.unshown[:] = [u for u in matcher.unshown if u["key"] != rec.key]
        matcher.unshown_recs.remove(rec)
        n += 1
    # what an earlier try listed about records that have since joined is no longer true
    joined = set(matcher.station_of_key)
    matcher.ca_ambiguous[:] = [x for x in matcher.ca_ambiguous if x["key"] not in joined]
    matcher.ca_far[:] = [x for x in matcher.ca_far if x["key"] not in joined]
    return n


def curated_join(matcher, rec):
    """The station holding a record that curation says is the same structure, else None."""
    cur = getattr(matcher, "ca_curation", None)
    if cur is None:
        return None
    for k in sorted(cur.joined_with(rec.key)):
        st = matcher.station_of_key.get(k)
        if st is not None:
            st = _live(st)
            cur.applied["join"].append({"key": rec.key, "with": k})
            return st
    return None


def name_join(matcher, rec, forms_of, score_of):
    """A position-less record with a name and a province joins the one station of that province and
    kind group whose name agrees fully with it (score >= 0.95), if exactly one does. `forms_of` and
    `score_of` are merge.py's name forms and scorer."""
    if rec.has_point or not rec.name or not rec.region or not getattr(rec, "name_join_ok", False):
        return None
    forms = forms_of(rec.name, rec.other_names)
    if not forms:
        return None
    hits = []
    for st in matcher.live():
        if st.country() != rec.country:
            continue
        if not any(r.region == rec.region for r in st.recs()) and (st.existing or {}).get("region") != rec.region:
            continue
        g = st.kind_group()
        if g and matcher.kind_group.get(rec.kind) and g != matcher.kind_group.get(rec.kind):
            continue
        s = score_of(forms, st.forms(starting_only=True))
        if s is not None and s >= 0.95:
            roles = {p.role for p in st.parts if p.role in ("front_range", "rear_range")}
            if rec.role in ("front_range", "rear_range") and roles and rec.role not in roles:
                continue
            hits.append(st)
    if len(hits) == 1:
        if not hasattr(matcher, "ca_name_joins"):
            matcher.ca_name_joins = []
        matcher.ca_name_joins.append({"key": rec.key, "name": rec.name, "region": rec.region,
                                      "station": (hits[0].recs() or [rec])[0].name})
        return hits[0]
    return None


# ---------------------------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------------------------

LHF_NOTES = {
    "private": "Lighthouse Friends marks it as private property with no access without permission.",
    "interior_open": "Lighthouse Friends: interior open or a museum on site.",
}
STAFFED_NOTE = ("Staffed lightstation: the keepers' home and workplace. Visit only where the station welcomes visitors, "
                "and never land uninvited.")


def fields_used(recs) -> dict[str, set[str]]:
    """Which records supply staffing / access / visit / stay / aton here (for sources[].fields)."""
    used: dict[str, set[str]] = defaultdict(set)
    for r in recs:
        ex = r.extra
        if ex.get("staffing"):
            used[r.key] |= {"staffing", "access"}
        if ex.get("flags"):
            used[r.key] |= {"visit"}
        if (ex.get("access") or {}) and r.source == "rowlett":
            used[r.key] |= {"visit"}
        if (r.raw.get("aton") or {}).get("admiralty"):
            used[r.key] |= {"aton"}
    return used


def apply(rec: dict, recs) -> dict:
    """Fill staffing, access, visit and stay of a canonical record from the Canadian sources.
    Returns what it did (for the report)."""
    did: dict = {}
    if rec.get("country") != "CA":
        return did
    by_source = defaultdict(list)
    for r in recs:
        by_source[r.source].append(r)

    # --- Admiralty number
    adm = None
    for r in sorted(recs, key=lambda r: r.key):
        a = (r.raw.get("aton") or {}).get("admiralty") or norm_adm((r.extra or {}).get("light_reference"))
        if a:
            adm = norm_adm(a) or a
            break
    if adm:
        rec["aton"]["admiralty"] = adm

    # --- flags from Lighthouse Friends, wording from the Lighthouse Directory
    flags = set()
    for r in by_source.get("lighthousefriends", []):
        flags |= set(r.extra.get("flags") or [])
    rowlett = {}
    for r in by_source.get("rowlett", []):
        for k, v in (r.extra.get("access") or {}).items():
            rowlett.setdefault(k, v)
    visit, access = rec["visit"], rec["access"]
    notes = []
    if "boat" in flags or rowlett.get("boat_only"):
        visit["boat_only"] = True
    if "climb" in flags:
        visit["climbable"] = True
    elif rowlett.get("tower") == "closed" and visit.get("climbable") is None:
        visit["climbable"] = False
    if visit.get("grounds_open") is None:
        if rowlett.get("site") == "open" or {"climb", "interior_open"} & flags:
            visit["grounds_open"] = True
        elif rowlett.get("site") == "closed":
            visit["grounds_open"] = False
    if "interior_open" in flags:
        notes.append(LHF_NOTES["interior_open"])
    open_corroborated = rowlett.get("tower") == "open" or bool({"climb", "interior_open"} & flags)
    if "private" in flags and access.get("level") in (None, "unknown"):
        access["level"] = "private"
        notes.append(LHF_NOTES["private"])
    elif rowlett.get("site") == "closed" and not open_corroborated and access.get("level") in (None, "unknown"):
        access["level"] = "closed"
        notes.append("The Lighthouse Directory says the site is closed to visitors.")
    elif rowlett.get("site") == "open" and open_corroborated and access.get("level") in (None, "unknown"):
        access["level"] = "public"
        notes.append("The Lighthouse Directory says the site is open" + (" and the tower open." if rowlett.get("tower") == "open" else "."))
    if notes:
        visit["note"] = " ".join(notes) if not visit.get("note") else visit["note"] + " " + " ".join(notes)
    if "lodging" in flags and not rec.get("stay"):
        rec["stay"] = {"type": "inn", "provider": None, "url": None, "season": None,
                       "note": "Lighthouse Friends marks overnight lodging here (an inn, bed and breakfast or rental). Check with the operator before planning a stay.",
                       "checked": None}
    elif "keeper_program" in flags and not rec.get("stay"):
        rec["stay"] = {"type": "keeper_program", "provider": None, "url": None, "season": None,
                       "note": "Lighthouse Friends marks a volunteer keeper programme here. Check with the operator.", "checked": None}

    # --- staffing (the curated list; the newest evidence wins over an automation event)
    staffed = sorted(by_source.get("ca_staffed_lightstations", []), key=lambda r: r.key)
    if staffed:
        s = staffed[0].extra
        rec["staffing"] = {**s["staffing"], "basis": s.get("basis"), "check": bool(s.get("check")),
                           "evidence": [{"label": e["label"], "url": e["url"], "date": e.get("date")} for e in s.get("evidence", [])]}
        a = s.get("access") or {}
        if a.get("level"):
            access["level"] = a["level"]
        access["note"] = " ".join(x for x in (a.get("note"), access.get("note")) if x) or None
        did["staffing"] = s["staffing"]["status"]
    return did


def status_note(st_recs, status: str, note: str | None) -> str | None:
    """Add to the status note where the Canadian sources disagree about whether anything stands."""
    ccg = [r for r in st_recs if r.source == "ccg_list_of_lights"]
    gone_row = [r for r in st_recs if r.source == "rowlett" and r.extra.get("gone")]
    extra = []
    if status == "lost" and ccg:
        nums = ", ".join(sorted({r.raw.get("aton", {}).get("ccg_list_number") or r.key for r in ccg})[:3])
        extra.append(f"The historic structure is gone, but the Coast Guard's List of Lights still shows a light here (list no. {nums}), "
                     "a modern aid that took its place.")
    if status in ("active", "inactive", "unknown") and gone_row and not any(r.status == "lost" for r in st_recs):
        extra.append("The Lighthouse Directory lists the tower it describes as gone; the light shown here may be a successor on the same site.")
    if not extra:
        return note
    return " ".join(x for x in [note, *extra] if x)


# ---------------------------------------------------------------------------------------------
# Station-level curation after matching
# ---------------------------------------------------------------------------------------------


def merge_stations(matcher, curation: Curation) -> None:
    """Retire a station whose structures another existing station holds (curation `merge_stations`).
    The retired id stays on disk with `merged_into` (ids are permanent)."""
    for e in curation.data["merge_stations"]:
        keep = matcher.by_id.get(e["keep"])
        gone = matcher.by_id.get(e["retire"])
        if keep is None or gone is None:
            curation.applied["merge_stations_missing"].append(e)
            continue
        if (gone.existing or {}).get("merged_into"):
            continue  # retired by an earlier run: nothing left to do, and the file stays as it is
        keep, gone = _live(keep), _live(gone)
        if keep is gone:
            continue
        keep.parts += gone.parts
        keep.station_recs += gone.station_recs
        gone.parts, gone.station_recs = [], []
        gone.absorbed_into = keep
        matcher.retired.append((gone, keep))
        for r in keep.recs():
            matcher.station_of_key[r.key] = keep
        matcher.index(keep)
        curation.applied["merge_stations"].append({"keep": e["keep"], "retire": e["retire"], "reason": e["reason"]})


def curate(rec: dict, curation: Curation, keys: list[str]) -> None:
    """Apply `rename` and `hide` to a resolved record: rename by id (the id never changes), hide by id
    or by any of its record keys."""
    e = curation.rename_ids.get(rec.get("id"))
    if e is not None and rec.get("name") != e["name"]:
        if rec.get("name") and rec["name"] not in rec["other_names"]:
            rec["other_names"] = [rec["name"], *rec["other_names"]]
        rec["other_names"] = [n for n in rec["other_names"] if n != e["name"]]
        curation.applied["rename"].append({"id": rec["id"], "from": rec["name"], "to": e["name"], "reason": e["reason"]})
        rec["name"] = e["name"]
    reason = curation.hide_ids.get(rec.get("id"))
    if reason is None:
        reason = next((curation.hide_keys[k] for k in keys if k in curation.hide_keys), None)
    if reason is not None:
        rec["hidden"] = True
        rec["hidden_reason"] = reason
        curation.applied["hide"].append({"id": rec.get("id"), "reason": reason})


# ---------------------------------------------------------------------------------------------
# Source precedence and the report
# ---------------------------------------------------------------------------------------------

# (field, "after" | "before", anchor source, [sources]): where the Canadian sources rank in
# merge.PRECEDENCE. The anchor is looked up by name, so the US branch can add its own sources to
# the same lists without disturbing these.
PRECEDENCE_RULES = [
    ("name", "after", "osm", ["parks_canada_hl", "lighthousefriends", "ccg_list_of_lights", "rowlett"]),
    ("location", "after", "osm", ["ccg_list_of_lights", "parks_canada_hl", "lighthousefriends"]),
    ("region", "after", "osm", ["parks_canada_hl", "lighthousefriends", "ccg_list_of_lights", "rowlett"]),
    ("kind", "after", "osm", ["parks_canada_hl", "lighthousefriends", "rowlett", "ccg_list_of_lights"]),
    ("structure", "after", "osm", ["parks_canada_hl", "rowlett"]),
    ("charted", "before", "osm", ["ccg_list_of_lights"]),
    ("light_dates", "after", "osm", ["rowlett"]),
    ("other", "after", "osm", ["parks_canada_hl", "lighthousefriends", "ccg_list_of_lights", "rowlett"]),
]


def register(precedence: dict) -> None:
    for field, where, anchor, sources in PRECEDENCE_RULES:
        order = precedence.setdefault(field, [])
        for s in sources:
            if s in order:
                order.remove(s)
        at = order.index(anchor) if anchor in order else len(order)
        at = at + 1 if where == "after" else at
        order[at:at] = sources


def report(m, resolved, by_source) -> tuple[dict, dict]:
    """(the Canadian part of data/merge_report.json, what this run did). The first describes the
    merged state, so a re-run with unchanged inputs leaves the file as it is; the second (how records
    joined, which identifiers pointed at two stations, which curation entries applied) is printed by
    merge.py and kept out of the file, because a run with memory takes the joins it remembers."""
    ca = [(st, rec) for st, rec in resolved if rec.get("country") == "CA"]
    visible = [rec for _st, rec in ca if not rec["hidden"]]

    def counts(key) -> dict:
        out: dict = defaultdict(int)
        for r in visible:
            out[key(r)] += 1
        return dict(sorted(out.items(), key=lambda kv: str(kv[0])))

    sources_of = lambda st: sorted({r.source for r in st.recs()})  # noqa: E731
    staffed = [rec for _st, rec in ca if (rec.get("staffing") or {}).get("status") == "staffed" and not rec["hidden"]]
    destaffed = [rec for _st, rec in ca if (rec.get("staffing") or {}).get("check") is False
                 and (rec.get("staffing") or {}).get("status") == "automated" and rec["access"].get("level") == "restricted"]
    staffed_recs = by_source.get("ca_staffed_lightstations", [])
    joined_keys = {r.key for _st, _rec in ca for r in _st.recs()}
    lhf_only = [rec for st, rec in ca if sources_of(st) == ["lighthousefriends"] and not rec["hidden"]]
    ccg_only = [rec for st, rec in ca if "ccg_list_of_lights" in sources_of(st)
                and not ({"wikidata", "osm", "lighthousefriends", "parks_canada_hl"} & set(sources_of(st)))]
    curation = m.ca_curation.data
    state = {
        "counts": {
            "stations": len(visible), "hidden": len([1 for _s, r in ca if r["hidden"]]),
            "by_region": counts(lambda r: r["region"]), "by_status": counts(lambda r: r["status"]),
            "by_kind": counts(lambda r: r["kind"]), "by_verification": counts(lambda r: r["verification"]),
            "by_staffing": counts(lambda r: (r.get("staffing") or {}).get("status")),
            "by_access": counts(lambda r: (r.get("access") or {}).get("level")),
            "by_sources": counts(lambda r: "+".join(sorted({s["source"] for s in r["sources"]}))),
        },
        "staffed": {
            "listed": len(staffed_recs),
            "staffed_stations": len(staffed),
            "not_joined_to_a_station": sorted(r.name for r in staffed_recs if r.key not in joined_keys),
            "rest_only_on_the_2010_list": sorted(rec["id"] for rec in staffed if (rec.get("staffing") or {}).get("check")),
            "destaffed_2024": sorted(rec["id"] for rec in destaffed),
        },
        "rowlett_not_joined": sorted(u["key"] for u in m.unshown if u["key"].startswith("rowlett:")),
        "lighthousefriends_only_standing": sorted(({"id": r["id"], "name": r["name"], "region": r["region"], "kind": r["kind"]}
                                                    for r in lhf_only if r["status"] != "lost"), key=lambda x: x["id"]),
        "ccg_started_stations": sorted(({"id": r["id"], "name": r["name"], "region": r["region"]} for r in ccg_only), key=lambda x: x["id"]),
        "curation_entries": {k: len(v) for k, v in curation.items()},
    }
    run = {
        "joined_by": {k: v for k, v in sorted(m.how.items()) if k in ("identifier", "name_only", "curated_join")},
        "joined_by_name_only": sorted(getattr(m, "ca_name_joins", []), key=lambda x: x["key"]),
        "identifier_far": sorted(m.ca_far, key=lambda x: x["key"]),
        "identifier_ambiguous": sorted(m.ca_ambiguous, key=lambda x: x["key"]),
        "curation_applied": {k: len(v) for k, v in sorted(m.ca_curation.applied.items())},
    }
    return state, run
