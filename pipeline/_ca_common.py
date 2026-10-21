"""Helpers shared by the Canadian source fetchers (DESIGN.md section 2): polite fetching that
honours robots.txt and shares its per-host clock with every other Fresnel process, the survey's
cached pages as a fallback cache, and a few text helpers.

- **One clock per host across processes.** `polite_get` takes the file lock
  `RAW_ROOT/_locks/web-<host>` (the same lock and timestamp format research/fetch_text.py uses)
  and waits until `interval` seconds have passed since the last request any Fresnel process made to
  that host. Two agents crawling one site at once therefore still send one request every 2 s.
- **robots.txt is read and obeyed** (`Robots.check`). A host whose robots.txt disallows the path
  for us (user agent `FresnelBot`, else `*`) raises `Blocked`; one that names Anthropic's crawlers
  (ClaudeBot, anthropic-ai, Claude-Web) with `Disallow: /` raises `Skipped`, as DESIGN section 2
  rules. A 4xx robots.txt (none) allows everything, as RFC 9309 says. The answer is cached in
  `RAW_ROOT/_robots/<host>.txt` (+ `.txt.json`) beside the other agents'.
- **`cached_get`** returns a page from its cache file, else from the survey's cache
  (`RAW_ROOT/survey/canada/...`, read in place of fetching again), else fetches it politely.
- Python 3.12, standard library only.
"""
from __future__ import annotations

import fcntl
import html
import json
import re
import shutil
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit

import _common as c

SURVEY = c.RAW_ROOT / "survey" / "canada"
LOCK_DIR = c.RAW_ROOT / "_locks"
ROBOTS_DIR = c.RAW_ROOT / "_robots"
AI_AGENTS = ("claudebot", "anthropic-ai", "claude-web")
AGENT_TOKEN = "FresnelBot"


class Blocked(c.FetchError):
    """robots.txt disallows this path for us."""


class Skipped(c.FetchError):
    """robots.txt names Anthropic's crawlers as disallowed: the source is skipped (DESIGN section 2)."""


def _lock_path(host: str) -> Path:
    return LOCK_DIR / ("web-" + re.sub(r"[^a-z0-9.]", "_", host.lower()))


def request(url: str, *, interval: float = c.MIN_INTERVAL_S, timeout: float = 90.0, data: bytes | None = None,
            headers: dict | None = None, retries: int = 3, backoff_s: float = 15.0) -> tuple[int, bytes]:
    """GET (or POST) one URL: (status, body). 2xx/3xx bodies come back; a 4xx comes back as its
    status (the caller decides); 429/5xx/timeouts are retried with exponential backoff, then raise."""
    host = urlsplit(url).netloc.lower()
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    hdrs = {"User-Agent": c.USER_AGENT, "Accept": "text/html,application/pdf,application/json,*/*"}
    if headers:
        hdrs.update(headers)
    wait_s = backoff_s
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        status, body = 0, b""
        with open(_lock_path(host), "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            try:
                last = float((f.read() or "0").strip() or 0)
            except ValueError:
                last = 0.0
            pause = last + interval - time.time()
            if pause > 0:
                time.sleep(pause)
            req = urllib.request.Request(url, data=data, headers=hdrs, method="POST" if data else "GET")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status, body = resp.status, resp.read()
            except urllib.error.HTTPError as e:
                status = e.code
                try:
                    body = e.read()
                except Exception:  # noqa: BLE001 - best effort
                    body = b""
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                last_err = c.FetchError(f"{type(e).__name__} from {host}: {e}")
            finally:
                f.seek(0)
                f.truncate()
                f.write(str(time.time()))
                f.flush()
        if status and status not in c.RETRY_STATUSES:
            return status, body
        if status:
            last_err = c.FetchError(f"HTTP {status} from {host}")
        if attempt < retries:
            c.log(f"  {last_err}; retrying in {wait_s:.0f} s")
            time.sleep(wait_s)
            wait_s *= 2
    raise last_err or c.FetchError(f"could not fetch {url}")


class Robots:
    """robots.txt for each host, fetched once (cached under RAW_ROOT/_robots)."""

    def __init__(self) -> None:
        self._parsers: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._ai_blocked: dict[str, bool] = {}

    def _load(self, scheme: str, host: str) -> None:
        if host in self._parsers:
            return
        ROBOTS_DIR.mkdir(parents=True, exist_ok=True)
        cache = ROBOTS_DIR / f"{host}.txt"
        text: str | None = None
        if cache.exists():
            text = cache.read_text(encoding="utf-8", errors="replace")
        else:
            for legacy in (SURVEY / "robots" / f"{host}.txt", SURVEY / "robots" / f"{host.removeprefix('www.')}.txt"):
                if legacy.exists():
                    text = legacy.read_text(encoding="utf-8", errors="replace")
                    break
        if text is None:
            status, body = request(f"{scheme}://{host}/robots.txt", interval=c.MIN_INTERVAL_S)
            text = body.decode("utf-8", errors="replace") if status < 400 else ""
            cache.write_text(text, encoding="utf-8")
            cache.with_name(cache.name + ".json").write_text(json.dumps({
                "status": status, "fetched": time.strftime("%Y-%m-%d %H:%M:%S"),
                "url": f"{scheme}://{host}/robots.txt"}), encoding="utf-8")
        if re.match(r"\s*<", text):  # an HTML error page served with a 200: there is no robots.txt
            text = ""
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(text.splitlines())
        self._parsers[host] = rp
        self._ai_blocked[host] = ai_crawlers_blocked(text)

    def check(self, url: str) -> float | None:
        """Raise Blocked / Skipped when robots.txt forbids the URL; else the host's crawl delay or None."""
        parts = urlsplit(url)
        host = parts.netloc.lower()
        self._load(parts.scheme or "https", host)
        if self._ai_blocked[host]:
            raise Skipped(f"{host}: robots.txt disallows Anthropic's crawlers by name; source skipped (DESIGN section 2)")
        rp = self._parsers[host]
        if not rp.can_fetch(AGENT_TOKEN, url):
            raise Blocked(f"{host}: robots.txt disallows {parts.path or '/'}")
        delay = rp.crawl_delay(AGENT_TOKEN)
        return float(delay) if delay else None


def ai_crawlers_blocked(robots_text: str) -> bool:
    """True when a `User-agent:` group naming ClaudeBot, anthropic-ai or Claude-Web has `Disallow: /`."""
    agents: list[str] = []
    in_rules = False
    for raw in robots_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = (s.strip() for s in line.split(":", 1))
        field = field.lower()
        if field == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(value.lower())
        else:
            in_rules = True
            if field == "disallow" and value == "/" and any(a in AI_AGENTS for a in agents):
                return True
    return False


ROBOTS = Robots()


def polite_get(url: str, *, interval: float = c.MIN_INTERVAL_S, **kw) -> bytes:
    """robots.txt-checked GET; raises FetchError on any non-2xx answer."""
    delay = ROBOTS.check(url)
    status, body = request(url, interval=max(interval, delay or 0), **kw)
    if not 200 <= status < 300:
        raise c.FetchError(f"HTTP {status} from {urlsplit(url).netloc} for {url}")
    return body


def cached_get(url: str, cache: Path, *legacy: Path, interval: float = c.MIN_INTERVAL_S, refresh: bool = False,
               **kw) -> bytes:
    """The page at `url` from `cache`; else from the first existing `legacy` path (the survey's
    cache, copied into `cache`); else fetched politely and cached."""
    if cache.exists() and not refresh:
        return cache.read_bytes()
    if not refresh:
        for old in legacy:
            if old.exists():
                cache.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(old, cache)
                return cache.read_bytes()
    body = polite_get(url, interval=interval, **kw)
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_suffix(cache.suffix + ".part")
    tmp.write_bytes(body)
    tmp.replace(cache)
    return body


# ---------------------------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------------------------

TAG_RE = re.compile(r"<[^>]+>")


def decode(body: bytes, *encodings: str) -> str:
    """Decode a page: the first encoding that works (UTF-8 first unless told otherwise)."""
    for enc in encodings or ("utf-8", "cp1252"):
        try:
            return body.decode(enc)
        except UnicodeDecodeError:
            continue
    return body.decode("cp1252", errors="replace")


def text_of(fragment: str) -> str:
    """HTML to one line of text: line breaks become spaces, entities are decoded."""
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>", " ", fragment)
    s = html.unescape(TAG_RE.sub("", s)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def dms_to_deg(deg: str | float, minutes: str | float = 0, seconds: str | float = 0, hemisphere: str | None = None) -> float:
    """Degrees, minutes, seconds to decimal degrees (6 places); S and W give negatives."""
    value = abs(float(deg)) + float(minutes) / 60 + float(seconds) / 3600
    if hemisphere and hemisphere.upper() in ("S", "W"):
        value = -value
    return round(value, 6)
