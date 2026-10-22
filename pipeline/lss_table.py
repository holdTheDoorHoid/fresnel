"""Reads the station tables of the US Life-Saving Service annual reports (OCR text from the Internet
Archive, kept by research/corpus.py) into rows: district, name, state, locality, latitude, longitude.

Every report from 1884 on prints "Life-saving districts and stations": for each district, the name of
each station, its state, its locality, and (from 1884) an approximate latitude and longitude in
degrees, minutes and seconds. The scans are read by OCR that cuts the table into column fragments, and
the fragments arrive in different orders in different volumes and even in different districts of one
volume:

- *row order* (1909, most districts): name, state, locality, latitude, longitude, row by row;
- *column order* (1884, 1909's 13th district): all the names, then all the states, then all the
  localities, then the coordinates, for a block of stations;
- *split numbers* (1909's 7th district): the degrees, minutes and seconds each on a line of their own;
- *paired blocks* (1909's 5th district): two names, two states, two localities, then latitude,
  latitude, longitude, longitude.

All of them are the same thing seen through different cuts: a **block** is, in order, `k` names, `k`
state cells, some locality cells, then `2k` coordinates (a latitude and a longitude for each station,
in station order: all the latitudes then all the longitudes, or alternating). A latitude is told from a
longitude by its degrees (a United States station's latitude is below 50, apart from Alaska's; its
longitude 66 or more). A block is read only when its counts agree (k names, k states, 2k numbers, k
latitudes, k longitudes); anything else is *unclean* and its stations are not given a position.
A number whose OCR is damaged (a letter in it, two numbers run together, minutes or seconds over 59) makes
that station's position unreadable; it is never guessed (DESIGN.md 2: a row we cannot read is listed for
review).

The module is pure text -> rows; `fetch_lss_reports.py` reads the corpus, joins the years and writes the
extract. Python 3.12, standard library only.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------------------------
# Districts and states
# ---------------------------------------------------------------------------------------------

ORDINALS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
            "eleventh", "twelfth", "thirteenth"]
DISTRICT_RE = re.compile(r"^\W*([A-Za-z]{3,10})\s+D[A-Za-z]{3,6}[CEG]T\W*(.*)$")


def district_number(line: str) -> int | None:
    """"SEVENTH DISTRICT." -> 7; OCR slips ("FIEST DISTEICT", "SECOXD DISTBICT") are read by closeness to the
    ordinal word. A line of ordinary prose that starts with a word and "district" is not mistaken for a
    heading: the heading's first word must be close to an ordinal and the rest of the line short."""
    m = DISTRICT_RE.match(line.strip())
    if not m:
        return None
    word = m.group(1).lower()
    best, score = None, 0.0
    for i, o in enumerate(ORDINALS, 1):
        r = difflib.SequenceMatcher(None, word, o).ratio()
        if r > score:
            best, score = i, r
    if score < 0.74 or len(line.strip()) > 70:
        return None
    return best


# Cell text (letters only, lower case) -> state code. "do" (ditto) repeats the state above.
STATE_WORDS = {
    "maine": "ME", "me": "ME", "newhampshire": "NH", "nh": "NH", "massachusetts": "MA", "mass": "MA", "ma": "MA",
    "rhodeisland": "RI", "ri": "RI", "connecticut": "CT", "conn": "CT", "ct": "CT", "newyork": "NY", "ny": "NY",
    "newjersey": "NJ", "nj": "NJ", "pennsylvania": "PA", "penn": "PA", "pa": "PA", "delaware": "DE", "del": "DE",
    "maryland": "MD", "md": "MD", "virginia": "VA", "va": "VA", "northcarolina": "NC", "nc": "NC", "ncar": "NC",
    "southcarolina": "SC", "sc": "SC", "scar": "SC", "georgia": "GA", "ga": "GA", "florida": "FL", "fla": "FL",
    "fl": "FL", "alabama": "AL", "ala": "AL", "mississippi": "MS", "miss": "MS", "louisiana": "LA", "la": "LA",
    "texas": "TX", "tex": "TX", "tx": "TX", "ohio": "OH", "oh": "OH", "michigan": "MI", "mich": "MI", "mi": "MI",
    "wisconsin": "WI", "wis": "WI", "wi": "WI", "illinois": "IL", "ill": "IL", "il": "IL", "indiana": "IN",
    "ind": "IN", "minnesota": "MN", "minn": "MN", "mn": "MN", "kentucky": "KY", "ky": "KY", "california": "CA",
    "cal": "CA", "calif": "CA", "oregon": "OR", "oreg": "OR", "ore": "OR", "washington": "WA", "wash": "WA",
    "wa": "WA", "alaska": "AK", "ak": "AK", "hawaii": "HI", "hi": "HI", "dc": "DC",
}
DITTO = "do"
NUMBER_STATES = {"ME", "NH", "MA", "RI", "CT", "NY", "NJ", "PA", "DE", "MD", "VA", "NC", "SC", "GA", "FL", "AL", "MS",
                 "LA", "TX", "OH", "MI", "WI", "IL", "IN", "MN", "KY", "CA", "OR", "WA", "AK", "HI", "DC"}


def state_cell(line: str) -> str | None:
    """"Maine" -> "ME", ". do ." -> "do", "N.H" -> "NH"; None when the cell is something else. A damaged state word
    is not guessed at: "Georgica" is a station on Long Island."""
    t = re.sub(r"[^A-Za-z]", "", line).lower()
    if not t or len(line.strip()) > 24:
        return None
    if t in ("do", "dot", "ditto", "ao", "da", "do1", "d0", "cio"):
        return DITTO
    if t in STATE_WORDS:
        return STATE_WORDS[t]
    return None


# ---------------------------------------------------------------------------------------------
# Cells
# ---------------------------------------------------------------------------------------------

HEADER_RE = re.compile(
    r"^(name\s+of\s+station|state\.?|locality\.?|approximate|positions?\.?\*?|lati\W*|tude\W*(north|west)?\W*|longi\W*|"
    r"north\W*|west\W*|latitude\W*|longitude\W*|report\W+united\W+states\W+life.?saving\W+service\W*|"
    r"life.?saving\W+districts\W+and\W+stations.*|districts\W+and\W+stations\W*|embracing.*|coasts?\W+of.*|"
    r"the\W+following\W+(is\W+)?a\W+list.*|list\W+of\W+life.?saving.*|continued\W*|\W*in\W+the\W+united\W+states\W*)$", re.I)
FOOTNOTE_RE = re.compile(r"^([a-g])\s+([A-Z][A-Za-z].*)$")
NUMTOK = re.compile(r"^\d{1,3}$")


@dataclass
class Cell:
    kind: str                       # text, state, num, bad
    text: str = ""
    state: str | None = None
    toks: list = field(default_factory=list)   # num: ints, or None for an unreadable token
    n: int = 0                      # index of the source line (for messages)


HEADER_PHRASES = ["nameofstation", "state", "locality", "approximateposition", "approximatepositions", "approximate",
                  "position", "latitude", "latitudenorth", "longitude", "longitudewest", "tude", "tudenorth", "tudewest",
                  "reportunitedstateslifesavingservice", "lifesavingdistrictsandstationsintheunitedstates"]


_HEADER_CACHE: dict[str, bool] = {}


def is_caps_header(line: str) -> bool:
    """A heading in capitals ("COAST BETWEEN DELAWARE AND CHESAPEAKE BAYS.", "CAROLINA."), or a column head the OCR
    has damaged ("Stale.", "Long! tude, west."): station names and localities are printed in mixed case, and a
    column head is the same few words on every page."""
    letters = re.sub(r"[^A-Za-z]", "", line)
    if len(letters) >= 4 and sum(ch.isupper() for ch in letters) >= 0.95 * len(letters):
        return True
    low = letters.lower()
    if low in ("long", "longi", "lati", "latit", "tude", "north", "west", "state", "stale", "staie"):
        return True
    if not 5 <= len(low) <= 40:
        return False
    if low not in _HEADER_CACHE:
        hit = False
        for h in HEADER_PHRASES:
            if abs(len(low) - len(h)) <= 3:
                sm = difflib.SequenceMatcher(None, low, h)
                if sm.quick_ratio() >= 0.85 and sm.ratio() >= 0.8:
                    hit = True
                    break
        _HEADER_CACHE[low] = hit
    return _HEADER_CACHE[low]


def is_numeric_line(line: str) -> bool:
    """A coordinate or a fragment of one: at most three short tokens, at least half of them holding a digit ("44 48 40",
    "6658 5(", "00 iSS 50", ".50"), and no word of three letters or more."""
    toks = line.split()
    if not toks or len(toks) > 3 or any(len(t) > 5 for t in toks):
        return False
    with_digit = sum(any(ch.isdigit() for ch in t) for t in toks)
    if with_digit * 2 < len(toks) or sum(ch.isalpha() for ch in line) > 4:
        return False
    return with_digit >= 1


def tokens_of(line: str) -> list:
    """The numbers on a numeric line: an int for a clean 1-3 digit token, None for one OCR has damaged
    (letters or brackets in it, four or more digits run together)."""
    out = []
    for tok in line.split():
        out.append(int(tok) if NUMTOK.match(tok) else None)
    return out


def classify(raw_lines: list[str]) -> tuple[list[Cell], list[tuple[str, str]], list[int]]:
    """Cells of a stretch of lines, and the footnotes it holds ([(letter, text)])."""
    cells: list[Cell] = []
    notes: list[tuple[str, str]] = []
    lines = [(i, re.sub(r"\s+", " ", ln).strip()) for i, ln in enumerate(raw_lines)]
    lines = [(i, ln) for i, ln in lines if ln]
    header_at = [k for k, (_, ln) in enumerate(lines) if re.match(r"^report\W+united\W+states\W+life", ln, re.I)]
    near_header = {k + d for k in header_at for d in range(-2, 3)}
    for k, (i, ln) in enumerate(lines):
        if HEADER_RE.match(ln) or is_caps_header(ln):
            continue
        if not re.search(r"[A-Za-z0-9]", ln):
            continue
        if re.fullmatch(r"\d{1,3}", ln) and k in near_header and (int(ln) > 125 or int(ln) < 18):
            continue                                # a page number beside the running head (never a degree)
        m = FOOTNOTE_RE.match(ln)
        if m and not is_numeric_line(ln) and state_cell(ln) is None:
            notes.append((m.group(1), m.group(2)))
            continue
        st = state_cell(ln)
        if st is not None:
            cells.append(Cell("state", ln, st, n=i))
        elif is_numeric_line(ln):
            cells.append(Cell("num", ln, toks=tokens_of(ln), n=i))
        elif len(re.sub(r"[^A-Za-z]", "", ln)) <= 1 or re.fullmatch(r"[OoQ0fSsrtIl1/\\'\"|!,. -]{1,12}", ln):
            continue                                # OCR dust: "O / //", "o / rt", "Off/", "Q 1 II"
        else:
            cells.append(Cell("text", ln, n=i))
    return cells, notes, []


def join_hyphenated(cells: list[Cell]) -> list[Cell]:
    """"Portsmouth Har-" ... "bor.": a cell that ends in a hyphen takes the next lower-case fragment (within the
    next six cells: the OCR may put the rest of a name after its row)."""
    out = list(cells)
    i = 0
    while i < len(out):
        c = out[i]
        if c.kind == "text" and re.search(r"[A-Za-z]-\s*$", c.text):
            for j in range(i + 1, min(i + 7, len(out))):
                d = out[j]
                if d.kind == "text" and re.match(r"^[a-z]", d.text) and len(d.text) <= 16:
                    c.text = re.sub(r"-\s*$", "", c.text) + d.text
                    del out[j]
                    break
        i += 1
    return out


# ---------------------------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------------------------

@dataclass
class Row:
    district: int | None
    name: str
    state: str | None
    locality: str | None = None
    lat: float | None = None
    lon: float | None = None
    lat_dms: tuple | None = None
    lon_dms: tuple | None = None
    clean: bool = False             # the block's counts agreed and both numbers read
    problem: str | None = None
    footnote: str | None = None
    block_k: int = 0
    pooled: bool = False
    state_inferred: bool = False


def clean_name(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[\s.,:;_\-'\"«»¬•|\\/*]+$", "", s).strip()           # dot leaders and OCR dust at the end
    s = re.sub(r"\s*\.{2,}.*$", "", s)
    s = re.sub(r"^[\W_]+", "", s)
    return s.strip()


def split_mark(raw: str) -> tuple[str, str | None]:
    """"Bolinas Bay b" -> ("Bolinas Bay", "b"); "Indian River Inlet®" -> ("Indian River Inlet", "*"): the footnote
    mark the table prints after a name (a letter, or a symbol the OCR reads for the first footnote) is taken off.
    A single letter after a space is a mark whatever letter the OCR made of it (b, t, J, l)."""
    s = re.sub(r"\s+", " ", raw).strip()
    mark = None
    m = re.search(r"[\s.,_\-\"'\u2018\u2019]+([A-Za-z])[\s.,_]*$", s)
    if m and re.search(r"[A-Za-z]{3}", s[:m.start(1)]):
        mark = m.group(1)
        s = s[:m.start(1)]
    elif re.search(r"[\u00ae\u00a9\u00ab\u00b0*\u2020\u2021\u00a7]", s):
        mark = "*"
        s = re.sub(r"[\u00ae\u00a9\u00ab\u00b0*\u2020\u2021\u00a7].*$", "", s)
    return clean_name(s), mark


def good_name(s: str) -> bool:
    """A station name as the table prints one: letters, a space, an apostrophe or hyphen; no digits."""
    return bool(re.fullmatch(r"[A-Z][A-Za-z'’]*(?:[ \-][A-Za-z][A-Za-z'’.]*)*", s)) and 3 <= len(s) <= 40


def dms_value(t: tuple) -> float | None:
    d, m, s = t
    if None in t or not (0 <= m <= 59 and 0 <= s <= 59):
        return None
    return round(d + m / 60 + s / 3600, 6)


def classify_triple(t: tuple, alaska: bool = False) -> str | None:
    """"lat" or "lon" by degrees: a station's latitude is under 50, its longitude 66 or more, so the two never
    meet. In a block that holds an Alaska station a latitude may be 50-72 (Nome 64) and a longitude 130 or more."""
    d = t[0]
    if d is None:
        return None
    if alaska and 50 <= d <= 72:
        return "lat"
    if 18 <= d <= 49:
        return "lat"
    if 66 <= d <= 125 or d >= 126:
        return "lon"
    return None


def triples_of(toks: list) -> list[tuple] | None:
    """Group a block's number tokens in threes; None when the count is not a multiple of three."""
    if len(toks) % 3:
        return None
    return [tuple(toks[i:i + 3]) for i in range(0, len(toks), 3)]


def pair_names_states(cur: list[Cell]) -> tuple[list[tuple[str, str | None]], str | None]:
    """The (name, state cell) pairs of a block's text and state cells, in order. When names and states come in
    two runs (or one pair at a time) the k-th name goes with the k-th state; when the counts differ but every state
    cell follows a name directly (name, state, name, state), a name with no state cell after it is a row whose
    state the OCR dropped. Returns (pairs, problem)."""
    last = max(i for i, c in enumerate(cur) if c.kind == "state")
    seq = [c for c in cur[:last + 1] if c.kind in ("text", "state")]
    names = [c for c in seq if c.kind == "text"]
    states = [c for c in seq if c.kind == "state"]
    if len(names) == len(states):
        return [(n.text, st.state) for n, st in zip(names, states)], None
    pairs: list[tuple[str, str | None]] = []
    for idx, c in enumerate(seq):
        if c.kind == "text":
            nxt = seq[idx + 1] if idx + 1 < len(seq) else None
            pairs.append((c.text, nxt.state if nxt is not None and nxt.kind == "state" else None))
        elif idx == 0 or seq[idx - 1].kind != "text":
            return [], f"{len(names)} names but {len(states)} states"      # a state cell with no name before it
    return pairs, None


def resolve_states(cells: list[str | None], prev_state: str | None) -> tuple[list[str | None], list[bool], str | None]:
    """State cells -> states: "do" repeats the state above; a missing cell (None) takes the state above when the next
    explicit state is the same or a "do", else stays None (unknown)."""
    out: list[str | None] = []
    inferred: list[bool] = []
    cur = prev_state
    for i, cell in enumerate(cells):
        if cell is None:
            nxt = next((c for c in cells[i + 1:] if c is not None), None)
            keep = cur is not None and (nxt == DITTO or nxt == cur or nxt is None)
            out.append(cur if keep else None)
            inferred.append(True)
        elif cell == DITTO:
            out.append(cur)
            inferred.append(False)
        else:
            cur = cell
            out.append(cell)
            inferred.append(False)
    return out, inferred, cur


def read_block(district: int | None, pairs: list[tuple[str, str | None]], pair_problem: str | None, locs: list[str],
               toks: list, prev_state: str | None) -> tuple[list[Row], str | None]:
    """One block -> rows (names as the OCR gave them: `split_mark` takes off a footnote mark). `prev_state` is the
    state a "do" cell at the top of the block repeats."""
    k = len(pairs)
    resolved, inferred, cur = resolve_states([st for _, st in pairs], prev_state)
    problem = pair_problem
    trip = triples_of(toks)
    coords: list[tuple[tuple | None, tuple | None]] = [(None, None)] * k
    if problem is None:
        if trip is None:
            problem = f"{len(toks)} number tokens, not a multiple of three"
        elif len(trip) != 2 * k:
            problem = f"{len(trip)} coordinates for {k} stations"
        else:
            kinds = [classify_triple(t, "AK" in resolved) for t in trip]
            lats = [t for t, kd in zip(trip, kinds) if kd == "lat"]
            lons = [t for t, kd in zip(trip, kinds) if kd == "lon"]
            if len(lats) != k or len(lons) != k:
                problem = f"{len(lats)} latitudes and {len(lons)} longitudes for {k} stations"
            else:
                coords = list(zip(lats, lons))
    rows: list[Row] = []
    for i in range(k):
        row = Row(district, pairs[i][0], resolved[i], block_k=k, state_inferred=inferred[i] and resolved[i] is not None)
        if len(locs) == k:
            row.locality = re.sub(r"[\s.]+$", "", locs[i])
        if problem:
            row.problem = problem
        else:
            la, lo = coords[i]
            row.lat_dms, row.lon_dms = la, lo
            row.lat, row.lon = dms_value(la), dms_value(lo)
            if row.lat is None or row.lon is None:
                row.problem = "a coordinate is damaged"
            else:
                row.lon = -row.lon
                row.clean = True
        rows.append(row)
    return rows, cur


def parse_blocks(district: int | None, cells: list[Cell], start_state: str | None = None) -> tuple[list[Row], list[str]]:
    """Rows of one district's stretch of text.

    A block is a run of cells that holds at least one state cell and ends where a text or state cell follows
    its numbers. Its text cells before the last state cell are the names, the ones after it the localities,
    whether the names and states alternate (name, state, name, state), come in two runs, or one by one."""
    rows: list[Row] = []
    problems: list[str] = []
    cur: list[Cell] = []
    cur_state = start_state

    def close() -> None:
        nonlocal cur, cur_state
        if any(c.kind == "state" for c in cur):
            last = max(i for i, c in enumerate(cur) if c.kind == "state")
            toks = [t for c in cur if c.kind == "num" for t in c.toks]
            locs = [c.text for c in cur[last + 1:] if c.kind == "text"]
            pairs, problem = pair_names_states(cur)
            if problem:
                # the rows are still listed (their names), without a position
                states = [c.state for c in cur if c.kind == "state"]
                names = [c.text for c in cur[:last] if c.kind == "text"]
                resolved, _inf, cur_state = resolve_states(states, cur_state)
                for n_ in names:
                    rows.append(Row(district, n_, None, problem=problem, block_k=len(states)))
            else:
                rs, cur_state = read_block(district, pairs, None, locs, toks, cur_state)
                rows.extend(rs)
        elif cur:
            problems.append(f"orphan cells: {[c.text for c in cur][:3]}")
        cur = []

    for c in cells:
        if c.kind in ("text", "state") and any(x.kind == "num" for x in cur):
            close()
        cur.append(c)
    close()
    return rows, problems


LOCALITY_START = re.compile(
    r"^(off|on|in|at|near|just|abreast|opposite|north|south|east|west|northeast|northwest|southeast|southwest|inside|outside|"
    r"about|between|beside|close|under|within|at the|the|a|an|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"[0-9£½¼¾|l]|\W)\b", re.I)
LOCALITY_WORD = re.compile(r"\b(miles?|mile|light|lights|lighthouse|entrance|harbor entrance|side|village|town of|channel|"
                           r"lake|river|creek|beach,|island,|point,|bay,|the town|shore|abreast)\b", re.I)


def looks_like_name(text: str) -> bool:
    """A station name as against a locality: a few capitalised words, no comma, no preposition or distance."""
    t = text.strip()
    if "," in t or len(t) > 32 or len(t.split()) > 4 or re.search(r"\d", t):
        return False
    if LOCALITY_START.match(t) and not re.match(r"^(North|South|East|West)\s+[A-Z]", t):
        return False
    if re.search(r"\b(miles?|mile|light|lights|lighthouse|entrance|side|village|shore|abreast|near|off)\b", t, re.I) \
            and not re.match(r"^(Point|Cape|Fort|Port)\b", t):
        return False
    return t[:1].isupper()


def parse_pooled(district: int | None, cells: list[Cell], start_state: str | None = None) -> list[Row] | None:
    """The whole district as four parallel columns: the name cells, the state cells, the latitudes and the
    longitudes, in the order the OCR gave them. Used when the blocks did not add up. Only an exact fit counts:
    as many names as states, as many latitudes and as many longitudes."""
    states = [c.state for c in cells if c.kind == "state"]
    names = [c.text for c in cells if c.kind == "text" and looks_like_name(c.text)]
    toks = [t for c in cells if c.kind == "num" for t in c.toks]
    n = len(states)
    trip = triples_of(toks)
    if n < 3 or trip is None or len(trip) != 2 * n or len(names) != n:
        return None
    resolved, cur = [], start_state
    for st in states:
        if st == DITTO:
            resolved.append(cur)
        else:
            cur = st
            resolved.append(st)
    kinds = [classify_triple(t, "AK" in resolved) for t in trip]
    lats = [t for t, kd in zip(trip, kinds) if kd == "lat"]
    lons = [t for t, kd in zip(trip, kinds) if kd == "lon"]
    if len(lats) != n or len(lons) != n:
        return None
    rows = []
    for i in range(n):
        row = Row(district, names[i], resolved[i], block_k=n)
        row.lat_dms, row.lon_dms = lats[i], lons[i]
        row.lat, row.lon = dms_value(lats[i]), dms_value(lons[i])
        if row.lat is None or row.lon is None:
            row.problem = "a coordinate is damaged"
        else:
            row.lon = -row.lon
            row.clean = True
            row.problem = None
        row.pooled = True
        rows.append(row)
    return rows


def parse_district(district: int | None, lines: list[str], start_state: str | None = None) -> tuple[list[Row], list[tuple[str, str]], list[str]]:
    """Rows of one district: read in blocks; when that leaves rows unclean, read the district as parallel columns and
    keep that if it fits exactly and reads more rows."""
    cells, notes, _ = classify(lines)
    cells = join_hyphenated(cells)
    rows, problems = parse_blocks(district, cells, start_state)
    if any(not r.clean for r in rows):
        pooled = parse_pooled(district, cells, start_state)
        if pooled and sum(r.clean for r in pooled) > sum(r.clean for r in rows):
            return pooled, notes, problems + ["read as parallel columns"]
    return rows, notes, problems


def find_tables(text_lines: list[str]) -> list[tuple[int, int]]:
    """Index of the station table in a report's lines: a "Life-saving districts and stations" heading (the OCR may
    spoil its first word) followed within 60 lines by "Name of station" and a First District heading."""
    starts = []
    for i, ln in enumerate(text_lines):
        if re.search(r"DISTRICTS\s+AND\s+STATIONS|LIST\s+OF\s+LIFE.?SAVING\s+DISTRICTS", ln, re.I):
            window = text_lines[i:i + 60]
            if any(re.search(r"Name\s+of\s+station", w, re.I) for w in window) and any(district_number(w) == 1 for w in window):
                starts.append(i)
    return [(s, 0) for s in starts[:1]]
