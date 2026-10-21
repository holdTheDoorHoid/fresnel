#!/usr/bin/env python3
"""Shared polite-HTTP layer for the Fresnel research tools (roster, corpus, newspapers).

What it enforces (DESIGN.md section 2):

- the honest User-Agent;
- one request per `gap` seconds per site (request start to request start, and at least 0.5 s idle between
  one request's end and the next one's start), across every process on this machine (an fcntl lock per
  site under <raw root>/_locks/, in the same bare-timestamp format as research/fetch_text.py, so the two
  share a host's rate limit);
- robots.txt for every host (cached under <raw root>/_robots/), with `*` and `$` patterns and the longest
  match winning; a host whose robots.txt names ClaudeBot / anthropic-ai / Claude-Web as disallowed is
  skipped and the skip is recorded in <raw root>/_robots/skipped.json; a 403 on robots.txt counts as
  "everything disallowed"; if robots.txt cannot be read at all and nothing is cached, the request is
  refused instead of guessed;
- every redirect hop is a separate, throttled, robots-checked request;
- back-off: timeouts and 5xx retry with growing pauses; 429/503 also set a cooldown in the shared lock
  state so every other process stops too. A cooldown longer than `max_cooldown_wait` raises
  RateLimited instead of sleeping for an hour.

The cache root is $FRESNEL_RAW_ROOT, default <repo>/data/raw (git-ignored).
Python 3.12 standard library only.
"""
import fcntl
import http.client
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "FresnelBot/0.1 (+https://github.com/holdTheDoorHoid/fresnel)"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_AGENTS = ("claudebot", "anthropic-ai", "claude-web")
OUR_AGENT = "fresnelbot"

# Hosts that are one site for rate-limit and robots purposes, and the gap each site needs.
# (Download nodes of archive.org share archive.org's lock; tile.loc.gov shares www.loc.gov's.)
SITE_GAPS = {"loc.gov": 5.0}
ROBOTS_HOST = {"archive.org": "archive.org"}
DEFAULT_GAP = 2.0
MARGIN = 0.05  # seconds added to every gap, so clock jitter never makes two requests land inside it


def raw_root():
    return os.environ.get("FRESNEL_RAW_ROOT") or os.path.join(REPO, "data", "raw")


def lock_dir():
    return os.path.join(raw_root(), "_locks")


def site_key(host):
    """Collapse a hostname to the site whose lock and robots.txt govern it."""
    host = host.lower().split(":")[0]
    for dom in ("archive.org", "loc.gov"):
        if host == dom or host.endswith("." + dom):
            return dom
    return host


def site_gap(host):
    return SITE_GAPS.get(site_key(host), DEFAULT_GAP)



def read_text(path, errors="strict"):
    with open(path, encoding="utf-8", errors=errors) as fh:
        return fh.read()


def read_bytes(path, n=None):
    with open(path, "rb") as fh:
        return fh.read() if n is None else fh.read(n)


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj, **kw):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, **kw)


class PoliteError(Exception):
    pass


class Blocked(PoliteError):
    """robots.txt (or an AI-crawler rule) forbids this request."""


class RateLimited(PoliteError):
    """The site told us to slow down for longer than we are willing to wait in-process."""

    def __init__(self, msg, retry_at=None):
        super().__init__(msg)
        self.retry_at = retry_at


class NetworkError(PoliteError):
    """Timeouts / connection errors / 5xx that survived every retry."""


class Response:
    def __init__(self, status, headers, body, url):
        self.status, self.headers, self.body, self.url = status, headers, body, url

    @property
    def ok(self):
        return 200 <= self.status < 300

    def text(self, encoding="utf-8"):
        return (self.body or b"").decode(encoding, "replace")


# --------------------------------------------------------------------------------------------------
# Rate limiting across processes
# --------------------------------------------------------------------------------------------------

class Throttle:
    """Context manager: hold the site's lock, wait until the site may be hit again, and on exit stamp
    the time the request finished. `name` is the lock file stem ("web-<site>")."""

    def __init__(self, name, gap=DEFAULT_GAP, per_minute=None, clock=time.time, sleep=time.sleep,
                 lockdir=None, max_cooldown_wait=180.0, idle=0.5):
        self.name, self.gap, self.per_minute = name, float(gap), per_minute
        self.idle = float(idle)
        self.start = 0.0
        self.clock, self.sleep = clock, sleep
        self.lockdir = lockdir or lock_dir()
        self.max_cooldown_wait = max_cooldown_wait
        self.f = None
        self.waited = 0.0

    # sidecar JSON: {"hits": [timestamps in the last minute], "cooldown_until": ts, "strikes": n}
    @property
    def _side_path(self):
        return os.path.join(self.lockdir, self.name + ".json")

    def _read_side(self):
        try:
            return read_json(self._side_path)
        except (OSError, ValueError):
            return {}

    def _write_side(self, d):
        tmp = self._side_path + ".tmp%d" % os.getpid()
        with open(tmp, "w") as fh:
            json.dump(d, fh)
        os.replace(tmp, self._side_path)

    def __enter__(self):
        os.makedirs(self.lockdir, exist_ok=True)
        self.f = open(os.path.join(self.lockdir, self.name), "a+")
        fcntl.flock(self.f, fcntl.LOCK_EX)
        try:
            self.f.seek(0)
            try:
                last = float((self.f.read() or "0").strip() or 0)
            except ValueError:
                last = 0.0
            side = self._read_side()
            now = self.clock()
            until = last + self.gap + MARGIN
            cooldown = float(side.get("cooldown_until", 0) or 0)
            if cooldown > now:
                if cooldown - now > self.max_cooldown_wait:
                    raise RateLimited(
                        "%s asked us to back off until %s; try again after that"
                        % (self.name, time.strftime("%H:%M:%S", time.localtime(cooldown))), cooldown)
                until = max(until, cooldown)
            if self.per_minute:
                hits = sorted(t for t in side.get("hits", []) if t > now - 60)
                if len(hits) >= self.per_minute:
                    until = max(until, hits[-self.per_minute] + 60.0 + 0.5)
            wait = until - now
            if wait > 0:
                self.waited = wait
                self.sleep(wait)
            self.start = self.clock()
        except BaseException:
            self.f.close()
            self.f = None
            raise
        return self

    def __exit__(self, *exc):
        try:
            now = self.clock()
            # The next request may start `gap` s after this one started and `idle` s after it ended, whichever
            # is later. The lock file holds the timestamp T such that "T + gap" is that moment (the format
            # research/fetch_text.py reads), so the two tools share one rate limit.
            stamp = max(self.start, now - self.gap + self.idle)
            self.f.seek(0)
            self.f.truncate()
            self.f.write("%.3f" % stamp)
            self.f.flush()
            if self.per_minute:
                side = self._read_side()
                side["hits"] = [t for t in side.get("hits", []) if t > now - 60] + [now]
                self._write_side(side)
        finally:
            fcntl.flock(self.f, fcntl.LOCK_UN)
            self.f.close()
            self.f = None

    def set_cooldown(self, seconds):
        """Record that the site told us to stop for `seconds` (shared with every process). Must be called
        while the lock is held or from a context that does not hold it (it locks briefly itself)."""
        side = self._read_side()
        side["strikes"] = int(side.get("strikes", 0)) + 1
        side["cooldown_until"] = self.clock() + seconds
        self._write_side(side)

    def clear_strikes(self):
        side = self._read_side()
        if side.get("strikes"):
            side["strikes"] = 0
            self._write_side(side)

    def strikes(self):
        return int(self._read_side().get("strikes", 0))


# --------------------------------------------------------------------------------------------------
# robots.txt
# --------------------------------------------------------------------------------------------------

def parse_robots(text):
    """-> list of (agents: [lowercase tokens], rules: [(allow: bool, pattern)]) groups."""
    groups, agents, rules, in_rules = [], [], [], False
    for raw in (text or "").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = (s.strip() for s in line.split(":", 1))
        field = field.lower()
        if field == "user-agent":
            if in_rules:
                groups.append((agents, rules))
                agents, rules, in_rules = [], [], False
            agents.append(value.lower())
        elif field in ("allow", "disallow"):
            in_rules = True
            if value or field == "allow":
                rules.append((field == "allow", value))
            elif field == "disallow":
                rules.append((True, "/"))  # "Disallow:" (empty) allows everything
    if agents:
        groups.append((agents, rules))
    return groups


def _pattern_regex(pat):
    anchored = pat.endswith("$")
    if anchored:
        pat = pat[:-1]
    rx = "".join(".*" if c == "*" else re.escape(c) for c in pat)
    return re.compile("^" + rx + ("$" if anchored else ""))


def rules_for(groups, agent=OUR_AGENT):
    """The rules that apply to `agent`: its own group if there is one, else the `*` group."""
    own = [r for ag, r in groups if any(a and a in agent for a in ag if a != "*")]
    if own:
        return [x for r in own for x in r]
    return [x for ag, r in groups if "*" in ag for x in r]


def path_allowed(rules, path):
    """Longest matching pattern wins; on a tie Allow beats Disallow; no match means allowed."""
    best_len, allowed = -1, True
    for allow, pat in rules:
        if not pat:
            continue
        if _pattern_regex(pat).match(path):
            n = len(pat.rstrip("$"))
            if n > best_len or (n == best_len and allow):
                best_len, allowed = n, allow
    return allowed


def ai_blocked(groups):
    """True when a group naming one of Anthropic's crawlers carries a real Disallow."""
    for ag, rules in groups:
        if any(a in AI_AGENTS for a in ag) and any((not allow) and pat for allow, pat in rules):
            return True
    return False


def _robots_dir():
    return os.path.join(raw_root(), "_robots")


def record_skip(site, reason):
    os.makedirs(_robots_dir(), exist_ok=True)
    path = os.path.join(_robots_dir(), "skipped.json")
    try:
        d = read_json(path)
    except (OSError, ValueError):
        d = {}
    if site not in d:
        d[site] = {"reason": reason, "when": time.strftime("%Y-%m-%d %H:%M:%S")}
        write_json(path, d, indent=1)


_ROBOTS_MEMO = {}


def robots_groups(scheme, host, ttl=7 * 86400, fetcher=None):
    """Parsed robots.txt for the site `host` belongs to (cached on disk and in memory)."""
    site = "archive.org" if site_key(host) == "archive.org" else host.lower().split(":")[0]  # one robots.txt per host
    memo = _ROBOTS_MEMO.get((raw_root(), site))
    if memo is not None:
        return memo
    os.makedirs(_robots_dir(), exist_ok=True)
    path = os.path.join(_robots_dir(), site + ".txt")
    meta_path = path + ".json"
    fresh = os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl
    text = None
    if fresh:
        text = read_text(path)
    else:
        url = "%s://%s/robots.txt" % (scheme, ROBOTS_HOST.get(site, host))
        try:
            r = (fetcher or get)(url, robots=False, retries=1, timeout=25)
        except PoliteError:
            if os.path.exists(path):  # stale copy beats guessing
                text = read_text(path)
            else:
                raise Blocked("robots.txt for %s could not be read and nothing is cached; not guessing" % site)
        else:
            if r.status in (404, 410):
                text = ""
            elif r.status in (401, 403):
                text = "User-agent: *\nDisallow: /\n"
                record_skip(site, "robots.txt answered HTTP %d (treated as disallow-all)" % r.status)
            elif r.ok:
                text = r.text()
            else:
                if os.path.exists(path):
                    text = read_text(path)
                else:
                    raise Blocked("robots.txt for %s answered HTTP %d; not guessing" % (site, r.status))
            with open(path, "w") as fh:
                fh.write(text)
            write_json(meta_path, {"status": r.status, "fetched": time.strftime("%Y-%m-%d %H:%M:%S"), "url": url})
    groups = parse_robots(text)
    if ai_blocked(groups):
        record_skip(site, "robots.txt names an Anthropic crawler as disallowed")
    _ROBOTS_MEMO[(raw_root(), site)] = groups
    return groups


def check_robots(url):
    u = urllib.parse.urlsplit(url)
    groups = robots_groups(u.scheme or "https", u.netloc)
    site = "archive.org" if site_key(u.netloc) == "archive.org" else u.netloc.lower()
    if ai_blocked(groups):
        raise Blocked("%s: robots.txt names AI/Claude crawlers as disallowed; skipped (DESIGN.md section 2)" % site)
    path = u.path or "/"
    if u.query:
        path += "?" + u.query
    if not path_allowed(rules_for(groups), path):
        raise Blocked("%s: robots.txt disallows %s" % (site, path))


# --------------------------------------------------------------------------------------------------
# GET with throttling, robots, redirects and back-off
# --------------------------------------------------------------------------------------------------

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _retry_after(headers, default):
    v = headers.get("retry-after") if headers else None
    if v:
        try:
            return min(float(v), 3600.0)
        except ValueError:
            pass
    return default


def get(url, *, timeout=40, retries=3, gap=None, per_minute=None, headers=None, dest=None, robots=True,
        max_redirects=5, backoff=(5.0, 20.0, 60.0), max_cooldown_wait=180.0, clock=time.time,
        sleep=time.sleep, opener=None, log=None):
    """One polite GET. Returns Response(status, headers, body, final_url). 404/410 and other 4xx are
    returned, not raised (the caller decides); 429/503 set a shared cooldown and retry; timeouts and 5xx
    retry with back-off and then raise NetworkError. With `dest`, the body is streamed to that path
    (via dest + '.part') and Response.body is None."""
    opener = opener or _OPENER
    hdrs = {"User-Agent": UA, "Accept": "*/*"}
    hdrs.update(headers or {})
    cur = url
    hops = 0
    attempt = 0
    while True:
        u = urllib.parse.urlsplit(cur)
        if u.scheme not in ("http", "https"):
            raise PoliteError("unsupported URL: " + cur)
        if robots:
            check_robots(cur)
        key = site_key(u.netloc)
        g = gap if gap is not None else site_gap(u.netloc)
        th = Throttle("web-" + re.sub(r"[^a-z0-9.]", "_", key), gap=g, per_minute=per_minute, clock=clock,
                      sleep=sleep, max_cooldown_wait=max_cooldown_wait)
        err = None
        resp = None
        with th:
            try:
                req = urllib.request.Request(cur, headers=hdrs)
                try:
                    r = opener.open(req, timeout=timeout)
                    status, rh = r.status, {k.lower(): v for k, v in r.headers.items()}
                    body = None
                    if dest:
                        os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
                        with open(dest + ".part", "wb") as out:
                            while True:
                                chunk = r.read(262144)
                                if not chunk:
                                    break
                                out.write(chunk)
                        os.replace(dest + ".part", dest)
                    else:
                        body = r.read()
                    r.close()
                except urllib.error.HTTPError as e:
                    status, rh = e.code, {k.lower(): v for k, v in e.headers.items()}
                    body = None if dest else e.read()
                resp = Response(status, rh, body, cur)
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError,
                    http.client.HTTPException) as e:
                err = e
                if dest and os.path.exists(dest + ".part"):
                    os.remove(dest + ".part")  # a cut-off download must not be mistaken for a whole file
            if resp is not None and resp.status in (429, 503):
                strikes = th.strikes()
                pause = _retry_after(resp.headers, min(60.0 * (2 ** strikes), 3600.0))
                th.set_cooldown(pause)
                if log:
                    log("HTTP %d from %s; cooling down %.0f s" % (resp.status, key, pause))
            elif resp is not None and resp.status < 500:
                th.clear_strikes()
        if resp is not None and resp.status in (301, 302, 303, 307, 308):
            loc = resp.headers.get("location")
            if not loc:
                return resp
            hops += 1
            if hops > max_redirects:
                raise PoliteError("too many redirects from " + url)
            cur = urllib.parse.urljoin(cur, loc)
            continue
        retryable = err is not None or (resp is not None and (resp.status in (429, 503) or resp.status >= 500))
        if not retryable:
            return resp
        if attempt >= retries:
            if err is not None:
                raise NetworkError("%s: %s" % (cur, err))
            if resp.status in (429, 503):
                raise RateLimited("%s answered HTTP %d" % (key, resp.status))
            return resp
        pause = backoff[min(attempt, len(backoff) - 1)]
        if log:
            log("retry %d for %s after %s" % (attempt + 1, cur, err or ("HTTP %d" % resp.status)))
        attempt += 1
        sleep(pause)


def cached_get(url, cache_path, **kw):
    """get() with a file cache: returns (bytes, from_cache). Only 200 responses are cached."""
    if os.path.exists(cache_path):
        return read_bytes(cache_path), True
    r = get(url, **kw)
    if r.status != 200:
        raise PoliteError("HTTP %d for %s" % (r.status, url))
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    tmp = cache_path + ".tmp%d" % os.getpid()
    with open(tmp, "wb") as fh:
        fh.write(r.body)
    os.replace(tmp, cache_path)
    return r.body, False
