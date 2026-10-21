"""Human decisions the merge cannot take from the data (DESIGN.md 3.9), each with its evidence in
docs/sources/review_2026-10-us.md.

RECORD_JOINS     a source record's key -> the station it belongs to: a station id (permanent) or the key of
                 any record that station holds. merge.py attaches the record there before it tries its key
                 memory, a shared register number or the position. A station all of whose records are sent
                 elsewhere this way is retired: its file stays (ids never change), hidden, with `merged_into`
                 naming the station that took its records, and the site sends its old address to the new one.
KEEP_APART_PAIRS pairs of record keys that are two stations, though their names and positions agree: the
                 matcher never puts them in one station.
STATUS_PICKS     station id -> (status, note): a status a human has settled from evidence the sources do not
                 agree on (or that no source states); the note is shown beside it.
HIDE             station id -> reason: shown on the map no more (a decorative "lighthouse" that never served as
                 an aid to navigation, a vessel's name, a duplicate listing); the file stays.
KEEP_VISIBLE     station ids reviewed and kept, so the report's decorative-suspect list no longer names them.
NOT_DUPLICATES   pairs of station ids reviewed and found to be two stations, so the report's possible-duplicate
                 list no longer names them (twins at one site, a light and its own range light...).
REPLICA_OF       station id of a scale copy -> the station id of the light it copies (DESIGN 3.2: status `replica`,
                 related `replica_of`).
SUCCESSION       pairs (older id, newer id) of separately named successive lights (Old and New Point Loma): related
                 `succeeded_by` / `preceded_by` both ways.
"""
from __future__ import annotations

RECORD_JOINS: dict[str, str] = {}
KEEP_APART_PAIRS: set[frozenset] = set()
STATUS_PICKS: dict[str, tuple[str, str]] = {}
HIDE: dict[str, str] = {}
KEEP_VISIBLE: set[str] = set()
NOT_DUPLICATES: set[frozenset] = set()
REPLICA_OF: dict[str, str] = {}
SUCCESSION: list[tuple[str, str]] = []
