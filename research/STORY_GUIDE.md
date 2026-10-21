# Story research guide

For research agents writing a station's history. `DESIGN.md` §1 holds the owner's decisions
(2026-10-21): **long-form, in chapters; every fact sourced; atmosphere only from sources, with
general period context marked as general and cited.** This guide turns those into rules.

Fresnel covers light stations, range and pier lights, lightship stations, surviving lightships and
life-saving stations in the US (territories included) and Canada.

## Inputs

- The station record, `data/stations/<folder>/<id>.json` (ids `<country>-<region>-<slug>`:
  `us-me-portland-head`, `us-pr-punta-higuero`, `ca-ns-sambro-island`). Find one with
  `ls data/stations/*/<id>.json`; `research/queue.py --briefs <id>` prints it compactly. Treat it as
  a starting point that may be wrong; `conflicts` lists where sources already disagree.
- **The web**, read with the cheap reader, not WebFetch:
  `python3 /home/hoid/Desktop/fresnel/research/fetch_text.py "<url>" --grep "<words|that|matter>" --max 4000`.
  It caches pages and handles PDFs (NRHP nominations, annual reports). Use WebFetch only if it fails.
- **Search:** `python3 /home/hoid/Desktop/fresnel/research/websearch.py "<query>" -n 8` when
  WebSearch is unavailable or rationed.
- **Research method and source order:** section "Where to look" (filled in from the source survey,
  `docs/sources/survey_history.md`).

## Outputs (write both files; nothing else)

### 1. `data/stories/<id>.md`

**Length follows the evidence.** Count your independent sources and how much they say:

| Evidence | Length | Shape |
|---|---|---|
| Thin (one or two sources, a few facts) | 150–400 words | No headings: a few honest paragraphs |
| Moderate | 500–1,200 words | An opening paragraph, then 2–4 chapters |
| Rich (annual reports, a nomination, newspapers, keeper records) | 1,200–3,000 words | An opening paragraph, then every chapter that has material |

Never pad to reach a length. A short honest story beats a long padded one.

**Shape.** Do not start with a title (the page shows the name). Start with one short opening
paragraph, no heading, that says what and where in a way a visitor remembers. Then chapters, as
`## ` headings, **in this order and with exactly these names**, skipping any you have nothing
sourced for:

- Light stations, range and pier lights: `## The place`, `## Building the light`, `## The keepers`,
  `## Storms, wrecks and rescues`, `## After the keepers`, `## Today`.
- Lightship stations: `## The station`, `## The ships`, `## The crews`,
  `## Storms, collisions and rescues`, `## After the lightships`, `## Today`.
- Surviving lightships (vessel records): `## The ship`, `## Stations and service`, `## The crews`,
  `## Storms, collisions and rescues`, `## Afterlife`, `## Today`.
- Life-saving stations: `## The station`, `## The surfmen`, `## Wrecks and rescues`,
  `## After the Life-Saving Service`, `## Today`.

What goes where:

- **The place**: the water, the hazard the light was built for (the shoal, the ledge, the harbour
  mouth, the traffic), the land, who petitioned or paid for it, what was there before.
- **Building the light**: who designed and built it and when, the money appropriated, the materials,
  the difficulties of the work, the lens and the first lighting, later towers on the site in order.
- **The keepers**: the people, in order. Who they were, where they came from when the sources say,
  their families, how long they stayed, the work and its hardships, what happened to them. Name
  women keepers and family members who kept the light in their own right, with the role the source
  gives. The roster table is generated from the research JSON (below), so the prose tells stories
  about people rather than listing every name.
- **Storms, wrecks and rescues**: dated events from reports, logs and newspapers: gales, ice, fires,
  shipwrecks seen or answered, rescues, deaths, wartime darkening.
- **After the keepers**: automation, the end of resident keepers, decline, transfers of ownership,
  preservation campaigns, restorations, relighting.
- **Today**: what stands now, who owns it, whether and how it can be visited. For a lost station,
  what remains at the site (and only what a source says remains).

**Footnotes.** Every factual sentence that is not common knowledge carries a footnote `[^n]`.
Definitions at the end, in this form:
`[^1]: Title of page or document, Publisher/site, URL (accessed YYYY-MM-DD).`
Cite the specific page (for an annual report, the volume and page: "Annual Report of the Light-House
Board for the fiscal year ended June 30, 1886, p. 42"), not a site's home page.

**Never invent.** No guessed names, dates, numbers, anecdotes, thoughts or feelings. Unknowns stay
unknown. If two sources disagree, say so ("The Light-House Board's report gives 1855; the National
Register nomination says 1857.[^2][^3]").

**Atmosphere (owner's rule, DESIGN §1).** Fresnel wants the reader to feel the place. That feeling
must come from the sources.

- *Allowed:* scene details a source gives for this station: the weather on a dated night, the ice in
  the harbour, the sound of the fog signal as a newspaper described it, the keeper's own words from a
  log or letter, an inspector's description of the dwelling, the number of days the fog signal ran in
  a year (annual reports give these), the wreck as the Life-Saving Service reported it.
- *Allowed, marked:* **general period context**, when it helps the reader understand what the work
  was, framed so nobody can mistake it for this station's own history, and cited to a history of the
  service or to the regulations of the time: "On most stations of the period the keeper's day began
  by…", "The 1881 *Instructions to Light-Keepers* required…". Keep each such passage short (one to
  three sentences) and never more than about a tenth of the story.
- *Forbidden:* imagined scenes ("the wind must have howled as he climbed"), guessed feelings
  ("she surely dreaded the winters"), sensory details no source gives for this station, composite
  characters, dialogue not quoted from a source, and general context written as if it were local.
- *Test:* for every vivid sentence, ask "which footnote says this happened **here**?" If the answer
  is "none, but it was typical", the sentence must say it was typical and cite where that is said.

**Quotations.** Short quotations bring the people back; use them. From public-domain sources
(annual reports, government documents, newspapers before 1930, logbooks), quote up to about 50
words at a time, in quotation marks, attributed in the sentence. From copyrighted sources (modern
books, LighthouseFriends, Lighthouse Digest, museum sites): our own words, with at most one short
quotation of a sentence. Keep old spelling and punctuation inside a quotation.

**Places and units.** Name the region the way the brief gives it (`region_name`, `local_unit`). US
and territories: feet first with metres in brackets ("a 72-foot (22 m) tower"). Canada: metres first
("a 22 m (72 ft) tower"). Distances at sea and ranges in nautical miles ("visible 18 nautical
miles"). Puerto Rico's lights keep their Spanish names ("Faro de Punta Higüero"), with an English
gloss once; Quebec's keep their French names.

**Tone.** Warm, concrete, plain English for a curious visitor. Vivid because the sources are vivid,
not because of adjectives. No superlatives you can't source. Banned: "nestled", "breathtaking",
"stalwart", "sentinel", "beacon of hope", "stood guard", "tireless", "lonely vigil", "a testament to".

**People who may be alive.** Keepers, Coast Guard crews, owners and volunteers whose connection
with the station ended after about 1960 are named only as published sources name them, in their
public role, with no personal details beyond what those sources print. Do not name private residents
of a converted lighthouse unless they present themselves publicly (an inn's owners).

**Safety and access.** Do not encourage anyone to climb a closed tower, land on a closed island or
cross private land. If it's private, closed, Coast Guard property, a staffed lightstation (the keepers'
home) or reachable only by boat, say so plainly in *Today*.

### 2. `data/research/<id>.json`

```json
{
  "id": "us-me-portland-head",
  "researched": "YYYY-MM-DD",
  "summary": "One sentence (≤ 200 chars) teaser shown on the map panel.",
  "facts": {
    "light": {"first_lit": 1791, "characteristic": "Fl W 4s", "focal_height_m": 30, "range_nm": 24,
              "lens": {"type": "fresnel", "order": "4", "status": "on_display", "where": "station museum"}},
    "structures": [{"role": "tower", "type": "conical_masonry", "material": "stone", "built": 1791, "height_m": 24.4}],
    "staffing": {"status": "automated", "as_of": "1989"},
    "access": {"level": "public", "note": "Grounds open daily; tower not open to climb."},
    "visit": {"grounds_open": true, "climbable": false, "museum": true},
    "stay": null,
    "agency": "Town of Cape Elizabeth"
  },
  "events": [{"year": 1791, "event": "first_lit", "note": "Lit 10 January 1791", "cite": [1]}],
  "keepers": [
    {"name": "Joseph Greenleaf", "role": "keeper", "from": 1791, "to": 1795, "note": "First keeper", "cite": [2]},
    {"name": "Joshua F. Strout", "role": "head keeper", "from": 1869, "to": 1904, "cite": [2, 4],
     "other_stations": [{"name": "…", "from": 1860, "to": 1869, "cite": [4]}]}
  ],
  "wrecks": [{"vessel": "Annie C. Maguire", "date": "1886-12-24", "outcome": "All aboard saved by the keeper's family", "cite": [5]}],
  "evidence": [
    {"cite": 1, "supports": "first lit 10 Jan 1791", "quote": "…exact words from the source…"}
  ],
  "corrections": [{"field": "location", "current": [43.62, -70.21], "proposed": [43.6231, -70.2079], "cite": [2], "why": "…"}],
  "resolved_conflicts": [{"field": "built", "explanation": "…", "cite": [1, 3]}],
  "sources": [{"n": 1, "title": "…", "publisher": "…", "url": "…", "accessed": "YYYY-MM-DD"}],
  "photos": [{"url": "…", "source_url": "…", "credit": "…", "license": "…", "caption": "…", "year": null}],
  "confidence": "high|medium|low",
  "notes_for_editor": "Anything uncertain, disputed or worth a human look."
}
```

- The values above illustrate the shape only. Never reuse them as facts, not even for Portland Head.
- **Omit unknown keys.** Include a fact only when a cited source supports it. No `null` placeholders
  (except `stay: null` meaning "checked: no overnight stays").
- **`keepers`** is the roster: **every** keeper, assistant, acting keeper, lightship master and crew
  member, surfman and station keeper the sources name, one line per person per stint, in order.
  `role` uses the source's word, normalised to one of: `keeper` (sole or unspecified), `head keeper`
  (= principal keeper), `first assistant`, `second assistant`, `third assistant`, `fourth assistant`,
  `assistant` (unnumbered), `acting keeper`, `laborer`, `lamplighter`, `master`, `mate`, `engineer`,
  `crew`, `station keeper` (Life-Saving Service: the keeper of a life-saving station), `surfman`,
  `officer in charge` (Coast Guard), `civilian keeper`, `volunteer keeper`, `other` (with a `note`).
  `from` / `to` are years; add `"from_approx": true` / `"to_approx": true` when a source says
  "about" or gives only a range. Spell names as the source does; give variants in `note`
  ("also spelled Stroudt in the 1875 Register"). `other_stations` lists the person's service
  elsewhere **only when a source names it** (it feeds the keepers index; never infer a person from
  a shared name).
- **`wrecks`**: wrecks and rescues at or near the station that a source ties to it.
- **`events`**: `event` from DESIGN §3.4 (`built, first_lit, rebuilt, replaced, relit, deactivated,
  automated, keeper_appointed, lens_installed, lens_removed, characteristic_changed,
  fog_signal_installed, damaged, destroyed, burned, collapsed, removed, relocated, restored, modified,
  wreck, rescue, storm, war, transferred, closed, opened_to_public, nrhp_listed, heritage_designated,
  other`). `other` needs a note. Every event cites a source number.
- **`evidence` (required, internal, not published):** for **every footnoted sentence**, one or more
  entries giving the cited source number, a short label of what it supports, and an **exact
  quotation** from that source (≤ 300 characters, copied character for character from the text you
  read; OCR text stays as OCR'd, errors included). The fact-checker verifies the story against these
  quotes and `research/check_quotes.py` checks that they really appear in the cached source; a quote
  that is not in the source fails the whole story. General-context sentences need evidence too, from
  the general history they cite.
- `corrections`: only **errors in the record** (name, location, status, kind, years, identity),
  never facts you could put in `facts`. `current`/`proposed` are values, not prose; give `why`.
  Reviewed by a human, never applied automatically.
- `resolved_conflicts`: when the record's "Where sources disagree" list holds a disagreement your
  sources explain (first tower vs current tower, a typo…), say so here.
- `photos`: new photos you found. Prefer public domain (USCG, LOC, NOAA, Library and Archives Canada
  where expired) or Creative Commons; always give credit and licence.
- `sources` numbering matches the story's footnotes.

## Where to look

From the source surveys (`docs/sources/survey_*.md`; method in `survey_history.md` §13). Work in this
order, and stop when you have an honest story; a thin station needs only the first two steps.

1. **Identity and roster.** `python3 research/roster.py <id>` prints the keepers the USLHS Digital
   Archive lists for the station (name, role, start and end years, from NARA's keeper registers),
   from the local cache. Compare with the station's LighthouseFriends page (keeper list in its
   "Keepers" line; facts only), New England Lighthouses (Jeremy D'Entremont) or Terry Pepper's
   Great Lakes pages where they cover it. Record every disagreement in `resolved_conflicts` or
   `notes_for_editor`. Cite the archive page, not the cache.
2. **Chronology skeleton.** The NRHP nomination when the station has an NRHP number
   (`https://npgallery.nps.gov/pdfhost/docs/NRHP/Text/<ref>.pdf`, through `fetch_text.py --grep`;
   a 22 KB file is the "not digitised" placeholder), HABS/HAER data pages on loc.gov
   (`https://www.loc.gov/item/<id>/`), Parks Canada's statement of significance for a Canadian
   heritage lighthouse, and the station's Wikipedia article for leads only (article pages only,
   never `/w/` or `/api/`; cite what it cites where you can).
3. **Official reports, from the local corpus.** `python3 research/corpus.py grep "<station name>"
   [--alias "<OCR or old spelling>"] [--state XX] [--series lhb,commissioner,bulletin,lss,marine_ca]
   [--years 1880-1900]` searches the downloaded text of the Lighthouse Board annual reports, the
   Commissioner of Lighthouses reports, the Lighthouse Service Bulletin, the Life-Saving Service
   annual reports and Canada's Department of Marine annual reports, and prints series, year and a
   snippet. The OCR is poor: station names come out misspelled, so give aliases and a state.
   **Page numbers:** the plain text has none; `corpus.py page <hit>` asks the Internet Archive for
   the page (the Bulletin PDFs carry their own page numbers). A footnote cites the report, the year
   and the page, with the Internet Archive URL. Copy evidence quotes from the corpus text exactly,
   OCR errors and all.
4. **Newspapers.** `python3 research/newspapers.py "<station name>" ["<keeper name>"]
   [--years 1880-1910] [--state XX]` searches Chronicling America (Library of Congress) and prints
   hits with their page URLs; `--page <url> --grep "<words>"` reads a hit's OCR text. It keeps to the
   Library's rate limit for every agent at once, so expect it to be slow. Budget: up to about ten
   searches for a well-documented station, fewer for a thin one. Search the station and keeper names
   first, then date windows around events step 3 found. Most other state newspaper archives forbid
   crawlers (CDNC, NYS Historic Newspapers, Digital Michigan Newspapers): do not use them.
5. **Keeper detail.** The Official Register of the United States (biennial; keepers with birthplace
   and salary) is searchable by surname only, page by page; use it to confirm a keeper you already
   know, not to find new ones.
6. **Atmosphere sources.** Transcribed station logs where they exist (Port Sanilac and South Haven,
   Michigan; others noted in `survey_history.md` §10), the reports' own descriptions of storms, ice,
   fog-signal hours and damage, newspaper accounts of wrecks and rescues, the Life-Saving Service's
   wreck narratives. A named hurricane may be checked against NOAA's HURDAT2 track only to confirm a
   date a source already gives.
7. **General period context** (marked as general, DESIGN §1): Arnold Burges Johnson, *The Modern
   Light-House Service* (1889/1890); the *Instructions to Light-Keepers* (1871, 1881, 1902); Sumner
   I. Kimball, *Organization and Methods of the United States Life-Saving Service*; W. D. O'Connor's
   1884 sketch of the Life-Saving Service; D. P. Heap, *Ancient and Modern Light-houses* (1889); for
   Canada, the Department of Marine and Fisheries' *Review of Improvements in Lighthouse and Coast
   Service of Canada between 1896 and 1904* (1904). Putnam (1917) and Weiss (1926) only once a scan is
   found. Internet Archive identifiers are in `survey_history.md` §7. Never cite a novel or a book for
   young readers (James Otis, *The Life Savers*) as a record.

**Do not use** (robots.txt, blocks or the owner's rulings, DESIGN §2): query.wikidata.org,
Overpass, Wikipedia's `/w/` and `/api/`, HathiTrust, Google Books, the NARA catalog, Canadiana, BAnQ,
Nauticapedia, the USCG Historian's site and its archived copies (on hold for the owner), CDNC, NYS
Historic Newspapers, Digital Michigan Newspapers, the NOAA historical chart collection.

**Budget per station:** at most 3 WebSearch calls (fallback `research/websearch.py`), at most 15 page
reads (fetch_text and newspaper pages together), corpus greps as needed but each capped by its
`--max`. A thin station should take a fraction of that.

**Lightship stations and vessels:** the USLHS Digital Archive's lightship-station records and vessel
assignments, the Lighthouse Board and Commissioner reports (stations, collisions,
drags), and newspapers. (The USCG Lightship Station Index is a Coast Guard PDF on a host that blocks us;
its archived copies are on hold with the Historian's, DESIGN §2.) A lightship station's position comes from the Light List or the bearing text
("8 miles SE of …"); give the source of the position in `corrections` when the record has none.

**Life-saving stations:** the Life-Saving Service annual reports (station lists with positions; wreck
narratives that name the keeper and surfmen), the 1909 report's station table, NRHP nominations, and
newspapers.

**Canada:** the Department of Marine annual reports 1901-1925 in the corpus (keepers and salaries;
the OCR splits table columns, so read around a hit), Parks Canada and the Directory of Federal Heritage
Designations, the Canadian Coast Guard List of Lights for today's light, provincial archives' open pages,
the Nova Scotia Lighthouse Preservation Society, and LighthouseFriends' Canadian pages (facts only). Read
French sources for Quebec; write in English; quote French exactly, with your own English rendering after
it, marked as a translation.
