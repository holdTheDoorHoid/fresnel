"""Shared helpers for Fresnel's source fetchers (DESIGN.md section 2).

Python 3.12, standard library only: the pipeline runs in GitHub Actions with no installs.

Conventions every fetcher follows:

- One honest User-Agent (USER_AGENT) for every request. No browser impersonation, ever.
- At most one request every 2 s per host (RateLimiter, shared per process).
- Raw responses are cached under RAW_ROOT/<source>/ so a re-run never fetches anything twice.
  RAW_ROOT is the environment variable FRESNEL_RAW_ROOT when it is set; otherwise, in a git
  worktree, the main checkout's data/raw/ (so every agent's worktree shares one cache, as
  DESIGN.md section 6 asks); otherwise <repo>/data/raw/. data/raw/ is git-ignored.
- Transient server errors (429, 502, 503, 504, timeouts) are retried with exponential backoff,
  as the public APIs ask, a few times and then given up on loudly.
- Source extracts (DESIGN.md 3.1, data/sources/<source>.json) are written with records sorted
  by key, so a re-run on the same cache writes the same bytes.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

USER_AGENT = "FresnelBot/0.1 (+https://github.com/holdTheDoorHoid/fresnel)"
REPO = Path(__file__).resolve().parent.parent
MIN_INTERVAL_S = 2.0
RETRY_STATUSES = {429, 500, 502, 503, 504}


def _main_checkout(repo: Path) -> Path | None:
    """The main working tree when `repo` is a git worktree (its .git is a file that points into
    <main>/.git/worktrees/<name>), else None."""
    dot_git = repo / ".git"
    if not dot_git.is_file():
        return None
    try:
        line = dot_git.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not line.startswith("gitdir:"):
        return None
    gitdir = Path(line.split(":", 1)[1].strip())
    if not gitdir.is_absolute():
        gitdir = (repo / gitdir).resolve()
    # <main>/.git/worktrees/<name>  ->  <main>
    if gitdir.parent.name == "worktrees" and gitdir.parent.parent.name == ".git":
        return gitdir.parent.parent.parent
    return None


def raw_root() -> Path:
    env = os.environ.get("FRESNEL_RAW_ROOT")
    if env:
        return Path(env)
    main = _main_checkout(REPO)
    return (main or REPO) / "data" / "raw"


RAW_ROOT = raw_root()


def today() -> str:
    return date.today().isoformat()


def raw_dir(source: str) -> Path:
    d = RAW_ROOT / source
    d.mkdir(parents=True, exist_ok=True)
    return d


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


class RateLimiter:
    """Keeps requests to one host at least `min_interval_s` apart."""

    def __init__(self, min_interval_s: float = MIN_INTERVAL_S) -> None:
        self.min_interval_s = min_interval_s
        self._last: dict[str, float] = {}

    def wait(self, url: str) -> None:
        host = urlsplit(url).netloc.lower()
        last = self._last.get(host)
        if last is not None:
            remaining = self.min_interval_s - (time.monotonic() - last)
            if remaining > 0:
                time.sleep(remaining)
        self._last[host] = time.monotonic()


LIMITER = RateLimiter()


class FetchError(RuntimeError):
    pass


def http_request(url: str, *, data: bytes | None = None, headers: dict | None = None,
                 timeout: float = 120.0, retries: int = 4, backoff_s: float = 10.0) -> bytes:
    """GET (or POST when `data` is given) with our User-Agent, spaced per host, retrying
    transient errors with exponential backoff (10 s, 20 s, 40 s, 80 s by default)."""
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    wait = backoff_s
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        LIMITER.wait(url)
        req = urllib.request.Request(url, data=data, headers=hdrs, method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read()
            except Exception:  # noqa: BLE001 - best effort, for the log
                pass
            last_err = FetchError(f"HTTP {e.code} from {urlsplit(url).netloc}: {body[:300]!r}")
            if e.code not in RETRY_STATUSES:
                raise last_err from e
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            last_err = FetchError(f"{type(e).__name__} from {urlsplit(url).netloc}: {e}")
        if attempt < retries:
            log(f"  {last_err}; retrying in {wait:.0f} s")
            time.sleep(wait)
            wait *= 2
    raise last_err or FetchError(f"could not fetch {url}")


def cache_key(*parts: str) -> str:
    """A short stable file name for a request (a query's text, an endpoint)."""
    h = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return h[:20]


def fetch_cached(url: str, cache_path: Path, *, data: bytes | None = None, headers: dict | None = None,
                 timeout: float = 120.0, force: bool = False, retries: int = 4) -> Path:
    """Download `url` to `cache_path` unless it is already there. Returns the path."""
    if cache_path.exists() and not force:
        return cache_path
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    body = http_request(url, data=data, headers=headers, timeout=timeout, retries=retries)
    tmp = cache_path.with_suffix(cache_path.suffix + ".part")
    tmp.write_bytes(body)
    tmp.replace(cache_path)
    return cache_path


def write_source_json(path: Path, *, source: str, title: str, url: str, license_text: str,
                      records: list[dict], notes: dict | None = None, retrieved: str | None = None) -> None:
    """Write a source extract (DESIGN.md 3.1/3.2): header plus records sorted by key."""
    payload = {
        "source": source,
        "title": title,
        "url": url,
        "retrieved": retrieved or today(),
        "license": license_text,
    }
    if notes:
        payload["notes"] = notes
    payload["records"] = sorted(records, key=lambda r: r["key"])
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(".json.part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def retrieved_date(*paths: Path) -> str:
    """The day the oldest of these cache files was written (the extract's 'retrieved' date), so
    re-running a fetcher on an old cache does not claim the data is from today."""
    times = [p.stat().st_mtime for p in paths if p.exists()]
    if not times:
        return today()
    return date.fromtimestamp(min(times)).isoformat()


def ft_to_m(feet: float) -> float:
    return round(feet * 0.3048, 2)
