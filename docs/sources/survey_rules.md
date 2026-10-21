# Source survey rules (2026-10-21)

For the agents surveying Fresnel's sources. Read `~/Desktop/fresnel/DESIGN.md` first (sections 1–3):
it says what Fresnel covers and how stations, structures, lights, keepers, lightships and
life-saving stations are modelled.

## What a survey is for

Two later jobs depend on it:

1. **Fetchers** that build the station list (bulk or per-region sources with positions).
2. **Research agents** that write long-form, footnoted histories of each station and its keepers
   (sources they can cite, and how to search them cheaply).

So for every source, say plainly what it gives, how to get it by machine, and whether we may use it.

## Output

Write `~/Desktop/fresnel/docs/sources/survey_<key>.md` (your key is in your task). Any downloads,
samples or cached pages go under `~/Desktop/fresnel/data/raw/survey/<key>/` (git-ignored). Write
nothing else in the repo. Do not commit; the orchestrator commits your survey.

For **each source**, one section with:

- **Name and URL** (the exact page or endpoint, not a home page).
- **Coverage**: what it lists, which regions, standing / lost / both, how many entries (count them
  where it is cheap; say "estimated" otherwise).
- **Fields**: position (and how precise), years (built, first lit, deactivated), structure, height,
  lens, characteristic, keepers (names, years), photos, prose.
- **Access**: bulk download / API / one HTML table / per-station pages / PDF / JS-only. The exact
  query or URL pattern that works, tested. Size of a bulk download.
- **robots.txt**: fetched and read. Quote the relevant lines. If it disallows AI crawlers by name
  (ClaudeBot, anthropic-ai, Claude-Web, GPTBot-style lists that include Anthropic agents) or
  disallows the paths we need, say so: we skip it.
- **Licence**: the exact words, with where they appear. "None stated" if none.
- **Quality**: how current, known errors, overlaps with other sources (is it copied from another?).
- **Recommended use**: `bulk source` / `regional source` / `research source (cite per station)` /
  `facts only, link` / `skip (why)`.
- One **sample record**, a few fields, written in our own words (never paste their prose).

End with **counts** (stations per region where you can get them), **gaps and risks**, and a short
**recommendation** for the order to build fetchers in.

## Manners

- At most one request every 2 s per host. User-Agent:
  `FresnelBot/0.1 (+https://github.com/holdTheDoorHoid/fresnel)`.
- Never automate around a CAPTCHA, a login or a Cloudflare challenge: note it and move on.
- No bulk download over ~500 MB without saying why in the survey (disk is shared; 58 GB free).
- Budget: about 25 WebSearch calls in total. Prefer fetching known URLs (curl, or
  `python3 ~/Desktop/fresnel/research/fetch_text.py "<url>" --grep "<words>" --max 4000`, a
  cached text reader that also handles PDFs) over searching. If WebSearch is unavailable, use
  `python3 ~/Desktop/fresnel/research/websearch.py "<query>" -n 8`.
- Facts only from copyrighted sites; never copy their text into the survey beyond a few words.
- Never contact anyone, sign up for anything or submit any form.
