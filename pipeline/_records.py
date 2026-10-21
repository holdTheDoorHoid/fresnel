"""Helpers the US station-source fetchers share (DESIGN.md 2.3): the source-record builder
(3.8), a polite fetch that honours robots.txt and shares one rate limit per host with every other
process on this machine, text and coordinate parsers, and the extract writer that adds a credit line.

Python 3.12, standard library only.
"""
from __future__ import annotations

import fcntl
import html as htmllib
import json
import re
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib import robotparser
from urllib.parse import urlsplit

import _common as c

AI_AGENTS = ("claudebot", "anthropic-ai", "claude-web")
OUR_AGENT = "FresnelBot"
RETRY = {429, 500, 502, 503, 504}


class Blocked(c.FetchError):
    """robots.txt (or a block page) says no: skip the source, do not work around it."""


# ---------------------------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------------------------

def new_record(source: str, ident: str, name: str | None, *, url: str | None = None, country: str = "US",
               region: str | None = None, lat: float | None = None, lon: float | None = None,
               precision: str = "exact", kind: str = "lighthouse", **kw) -> dict:
    """A source record in the shape of DESIGN 3.8 (every key present, unknown values null).

    Keyword arguments set or update the nested parts: `structure`, `light`, `aton` update the
    default dict; `visit`, `stay`, `access`, `staffing` are optional keys (3.8 as extended for the
    US sources: only the keys a source actually knows are present)."""
    rec = {
        "key": f"{source}:{ident}", "url": url, "name": name, "other_names": [],
        "country": country, "region": region, "county": None,
        "lat": round(lat, 6) if isinstance(lat, (int, float)) else None,
        "lon": round(lon, 6) if isinstance(lon, (int, float)) else None,
        "precision": precision, "kind": kind, "kind_raw": None, "role": None,
        "status": None, "status_raw": None,
        "structure": {"type": None, "material": None, "built": None, "height_m": None, "status": None},
        "light": {"first_lit": None, "deactivated": None, "characteristic": None,
                  "focal_height_m": None, "range_nm": None, "fog_signal": None, "lens": None},
        "setting": None, "registers": [],
        "aton": {"uscg_llnr": None, "arlhs": None, "ccg_list_number": None, "nga": None},
        "agency": None, "ownership": None, "events": [], "photos": [], "links": [],
        "relations": {"replaces": [], "replaced_by": []}, "extra": {},
    }
    for k, v in kw.items():
        if k in ("structure", "light", "aton", "relations") and isinstance(v, dict):
            rec[k].update(v)
        else:
            rec[k] = v
    return rec


def write_extract(path: Path, *, source: str, title: str, url: str, license_text: str, credit: str,
                  records: list[dict], notes: dict | None = None, retrieved: str | None = None,
                  country: str | None = None) -> None:
    """data/sources/<source>.json with the credit line the site's Credits page prints.

    A source two fetchers share (LighthouseFriends and Rowlett: this one for the US, fetch_*_ca.py for Canada)
    passes `country`: the file keeps the other country's records and header, this country's records are
    replaced, and its notes go under `notes[<country>]`, so either fetcher can run first and the union is the
    same."""
    kept: list[dict] = []
    header: dict = {}
    if country and path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        kept = [r for r in old.get("records", []) if r.get("country") != country]
        header = {k: old.get(k) for k in ("title", "url", "license", "credit") if old.get(k)}
        merged = dict(old.get("notes") or {})
        merged[country.lower()] = notes or {}
        notes = merged
    elif country:
        notes = {country.lower(): notes or {}}
    c.write_source_json(path, source=source, title=header.get("title") or title, url=header.get("url") or url,
                        license_text=header.get("license") or license_text, records=kept + records, notes=notes,
                        retrieved=retrieved)
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for k, v in data.items():
        out[k] = v
        if k == "license":
            out["credit"] = header.get("credit") or credit
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------------------------
# Polite fetching: robots.txt, one request per 2 s per host across processes
# ---------------------------------------------------------------------------------------------

def _robots_path(host: str) -> Path:
    d = c.RAW_ROOT / "_robots"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{host}.txt"


def _locked_get(url: str, *, gap: float = c.MIN_INTERVAL_S, timeout: float = 120.0) -> tuple[int, bytes]:
    """One GET under the host's shared lock file (the same `_locks/web-<host>` bare-timestamp format
    research/fetch_text.py uses). Returns (status, body); HTTP errors are returned, not raised."""
    host = urlsplit(url).netloc.lower()
    lockdir = c.RAW_ROOT / "_locks"
    lockdir.mkdir(parents=True, exist_ok=True)
    with open(lockdir / ("web-" + re.sub(r"[^a-z0-9.]", "_", host)), "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            last = float((f.read() or "0").strip() or 0)
        except ValueError:
            last = 0.0
        wait = last + gap - time.time()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": c.USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            try:
                body = e.read()
            except Exception:  # noqa: BLE001
                body = b""
            return e.code, body
        finally:
            f.seek(0)
            f.truncate()
            f.write(str(time.time()))
            f.flush()


def robots_allows(url: str) -> bool:
    """True when robots.txt lets FresnelBot fetch `url`. The robots.txt is fetched once and cached
    under RAW_ROOT/_robots/<host>.txt. A host whose file names an AI crawler (ClaudeBot, anthropic-ai,
    Claude-Web) as disallowed is refused (DESIGN 2). 404 means no rules; 403 or an unreadable file
    with nothing cached means refuse."""
    parts = urlsplit(url)
    host = parts.netloc.lower()
    path = _robots_path(host)
    meta = path.with_suffix(".txt.json")
    if not path.exists():
        try:
            status, body = _locked_get(f"{parts.scheme}://{host}/robots.txt", timeout=30)
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError):
            raise Blocked(f"cannot read robots.txt of {host}; not fetching") from None
        path.write_bytes(body if status == 200 else b"")
        meta.write_text(json.dumps({"status": status}), encoding="utf-8")
    try:
        status = json.loads(meta.read_text(encoding="utf-8")).get("status", 200)
    except (OSError, ValueError):
        status = 200
    if status == 404 or status == 410:
        return True
    if status == 403 or status == 401:
        return False
    if status != 200:
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    rp = robotparser.RobotFileParser()
    rp.parse(text.splitlines())
    for agent in AI_AGENTS:
        if re.search(rf"(?im)^\s*user-agent:\s*{re.escape(agent)}\b", text) and not rp.can_fetch(agent, "/"):
            return False
    return rp.can_fetch(OUR_AGENT, url)


def polite_get(url: str, cache_path: Path, *, force: bool = False, retries: int = 4, timeout: float = 120.0,
               binary: bool = True) -> Path:
    """Cache `url` at `cache_path` (never fetched twice), robots-checked, rate-limited, retried on
    transient errors with exponential backoff. Raises Blocked when robots.txt forbids it."""
    if cache_path.exists() and not force:
        return cache_path
    if not robots_allows(url):
        raise Blocked(f"robots.txt forbids {url}")
    wait = 10.0
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            status, body = _locked_get(url, timeout=timeout)
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            last = c.FetchError(f"{type(e).__name__} fetching {url}: {e}")
        else:
            if status == 200:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = cache_path.with_suffix(cache_path.suffix + ".part")
                tmp.write_bytes(body)
                tmp.replace(cache_path)
                return cache_path
            last = c.FetchError(f"HTTP {status} from {urlsplit(url).netloc} for {url}: {body[:200]!r}")
            if status not in RETRY:
                raise last
        if attempt < retries:
            c.log(f"  {last}; retrying in {wait:.0f} s")
            time.sleep(wait)
            wait *= 2
    raise last or c.FetchError(f"could not fetch {url}")


# ---------------------------------------------------------------------------------------------
# Text and number parsers
# ---------------------------------------------------------------------------------------------

def clean_text(s: str | None) -> str:
    """HTML to one line of plain text."""
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def year_in(s: str | None, lo: int = 1500, hi: int = 2100) -> int | None:
    m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", s or "")
    if m and lo <= int(m.group(1)) <= hi:
        return int(m.group(1))
    return None


def dms(deg: float, minutes: float = 0.0, seconds: float = 0.0, hemi: str | None = None) -> float:
    v = abs(deg) + minutes / 60.0 + seconds / 3600.0
    if hemi in ("S", "W") or deg < 0:
        v = -v
    return v


def state_of(place: str | None) -> str | None:
    """", ME" at the end of an LHF place string."""
    m = re.search(r",\s*([A-Z]{2})\s*$", place or "")
    return m.group(1) if m else None


# ---------------------------------------------------------------------------------------------
# A small .xlsx reader (zip of XML; no third-party library)
# ---------------------------------------------------------------------------------------------

def _col_index(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):  # type: ignore[union-attr]
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx_rows(path: Path, sheet: str = "xl/worksheets/sheet1.xml"):
    """Yield each row of the first worksheet as a list of strings ('' for an empty cell). Shared strings
    are read once (the NRHP workbook's are 18 MB), the sheet is streamed."""
    import zipfile
    import xml.etree.ElementTree as ET
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as z:
        strings: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            with z.open("xl/sharedStrings.xml") as f:
                for _ev, el in ET.iterparse(f, events=("end",)):
                    if el.tag == ns + "si":
                        strings.append("".join(t.text or "" for t in el.iter(ns + "t")))
                        el.clear()
        with z.open(sheet) as f:
            for _ev, row in ET.iterparse(f, events=("end",)):
                if row.tag != ns + "row":
                    continue
                cells: dict[int, str] = {}
                for cell in row.findall(ns + "c"):
                    ref = cell.get("r") or ""
                    v = cell.find(ns + "v")
                    t = cell.get("t")
                    if t == "inlineStr":
                        val = "".join(x.text or "" for x in cell.iter(ns + "t"))
                    elif v is None or v.text is None:
                        val = ""
                    elif t == "s":
                        val = strings[int(v.text)]
                    else:
                        val = v.text
                    cells[_col_index(ref) if ref else len(cells)] = val
                row.clear()
                if cells:
                    yield [cells.get(i, "") for i in range(max(cells) + 1)]


def excel_date(serial: str | float | None) -> str | None:
    """An Excel serial day number (1900 system) as YYYY-MM-DD, else None."""
    import datetime as dt
    try:
        n = float(serial)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if n < 1:
        return None
    return (dt.date(1899, 12, 30) + dt.timedelta(days=int(n))).isoformat()
