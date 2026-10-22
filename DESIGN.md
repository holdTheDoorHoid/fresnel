# Fresnel — design

Fresnel is the sister site to [Firefinder](https://holdthedoorhoid.github.io/firefinder/). It puts
every lighthouse in the United States (its territories included) and Canada on one modern map,
standing or lost, together with the lightships, the pier, harbor and range lights, and the
life-saving stations that stood beside them. Each station gets a page: practical information first
(can I visit, climb, stay), then a long, sourced history of the place and the people who kept the
light.

Firefinder's pages tell what a lookout was. Fresnel's go further. They tell who lived at the light,
what the place was like, what the weather and the wrecks were, and what the work was, in as much
detail as the record allows and never more.

The project is named for the Fresnel lens, the stack of glass prisms at the heart of nearly every
lighthouse, the way Firefinder is named for the sighting table in every lookout cab.

This file is **authoritative**. Agents read it before touching code or data. Decisions marked
DECIDED came from the owner's interview on 2026-10-21. Do not change them without asking. Where a
rule is "as in Firefinder", Firefinder's `DESIGN.md` (`~/Desktop/firefinder/DESIGN.md`) has the
worked-out detail, and Fresnel follows it unless this file says otherwise.

---

## 1. Decisions (DECIDED 2026-10-21)

| Topic | Decision |
|---|---|
| Name | **Fresnel**. Repo `holdTheDoorHoid/fresnel`, site `holdthedoorhoid.github.io/fresnel/`. Firefinder and Fresnel link to each other ("Sister site"). |
| Geography | The **United States** (lower 48, Alaska, Hawaii, the Great Lakes), the **US territories** (Puerto Rico, the US Virgin Islands, Guam, the Northern Mariana Islands, American Samoa, and the minor outlying islands if any lights are found there), and **all of Canada**. Standing and lost. The data model carries `country` + `region` as in Firefinder, so more countries can come later without rework. |
| Scope | **Light stations** (lighthouses, standing or lost), **lightships** (each station where one was moored, plus the surviving vessels), **pier, harbor and range lights** that have a real structure and a history, and **life-saving stations** (the US Life-Saving Service and its Canadian counterparts, and the historic Coast Guard boathouses that inherited them). **Not** modern automated beacons (steel poles, skeleton towers, buoys) with no keeper history, except as a light's current successor noted on its page; **not** decorative "lighthouses" that never served as an aid to navigation. Detail: 3.4. |
| Audience | Balanced, in layers, as in Firefinder: a clean map for anyone; each page puts visit / climb / stay / access first and the history below. |
| Stories | **Long-form, in chapters.** Length follows the evidence: about 800–3,000 words for a well-documented light, shorter (down to ~150) when the sources are thin. A short honest story beats a padded one. Chapters, used when there is something to put in them: *The place*, *Building the light*, *The keepers* (with a roster of names, roles and years), *Storms, wrecks and rescues*, *After the keepers*, *Today*. Sources include the Lighthouse Board and Commissioner of Lighthouses annual reports, keeper registers, the Life-Saving Service annual reports, historic-register nominations and old newspapers. Every factual sentence is footnoted. Detail: section 5 and `research/STORY_GUIDE.md`. |
| Atmosphere | **Sourced scenes plus marked context.** Every detail of a scene (the weather that night, the sound of the fog signal, a keeper's words) comes from a source: logbooks, letters, inspectors' reports, newspaper accounts, weather and wreck records, short quotations in their own words. General passages about the period (what trimming a wick in the 1870s involved, life aboard a lightship) are allowed **only** when framed as general ("On most stations of the period…") and cited to a history of the service. They are **never** presented as having happened at this station. Nothing is invented: no imagined scenes, no guessed feelings, no composite characters. |
| Writer | Pilot first: the same handful of stations researched once and written by **both Haiku and Sonnet**, shown to the owner side by side; the owner picks the writer for the big run. Then batches, as in Firefinder. **Owner decided 2026-10-21 after the pilot (`research/PILOT.md`): the mix.** Sonnet researches and writes the roughly 300 best-documented stations (`research/queue.py --tier sonnet`), Haiku the rest; each model fact-checks its own stories. The big run goes in multi-agent workflows, back to back until the owner says stop, pausing near 90% of the weekly allowance. The pilot's seven Sonnet stories are published. |
| Publishing | **Public from day one.** Thin or unchecked entries show a visible **Unverified** badge. |
| Photos | **Same as Firefinder**: mirror photos from every source, hobbyist and registry sites included, **with credit and a takedown note**, served from a separate public repo `holdTheDoorHoid/fresnel-photos`. The owner chose this; do not relitigate. |
| Features | (a) **The light at night**: the light seen from a ship's deck at sea, flashing in its real characteristic, at a distance the visitor chooses, plus a map ring showing how far out it could be seen (worked out from its focal height and its recorded range); lost lights use their recorded height and characteristic. (b) **Keepers index**: a page for each keeper, linked across every station they served. (c) **Wrecks and rescues**: a map layer of recorded wrecks near each light (NOAA) with the rescues the stories mention. (d) **Old charts and then-and-now**: a historical nautical-chart overlay, a timeline on each page, and a "lights lit per year" slider. By default (told the owner): a **lens and tower-type guide** (Fresnel orders, screwpile, caisson, skeletal iron, conical masonry…) linking to surviving examples, and a **"fix your position" lesson** (bearings on two lights, crossed on the chart), the sailor's version of Firefinder's smoke-spotting lesson. |
| Registry data | As in Firefinder: use **facts** (position, dates, heights, characteristics, keeper names and years, register numbers) from all-rights-reserved sites (LighthouseFriends, the Lighthouse Directory, Lighthouse Digest and others), with credit and a link on every page. Write our own prose; never copy their text. Partnership / permission notes are drafted in `docs/outreach/` (git-ignored) for the **owner** to send; never send them ourselves. |
| Access | Exact location for every site. Private residences, Coast Guard property closed to the public, island stations reachable only by boat, tribal land and **staffed Canadian lightstations** (the keepers' home and workplace) get a prominent access label. Warn, don't hide. |
| Contributing | GitHub only: a "Suggest an edit" button on each page opens a pre-filled GitHub issue. |
| Checklist | Visited / climbed / stayed / want-to-go, saved in the browser (localStorage) with export/import. No accounts, nothing collected. |
| License | Code GPL-3.0; database ODbL 1.0; our prose CC BY-SA 4.0; photos keep their own rights. |

---

## 2. Sources

Crawl politely: at most one request every 2 s per host, an honest User-Agent
(`FresnelBot/0.1 (+https://github.com/holdTheDoorHoid/fresnel)`), honour robots.txt (a site whose
robots.txt names AI or Claude crawlers as disallowed is skipped, and the skip is recorded). Cache raw
responses under `data/raw/` (git-ignored) so nothing is fetched twice. Never automate around a
CAPTCHA or a Cloudflare challenge.

Endpoint rulings (orchestrator, 2026-10-21, from the surveys):

- **Wikidata and OpenStreetMap through QLever.** `query.wikidata.org/robots.txt` disallows `/sparql`
  and `overpass-api.de/robots.txt` disallows `/api/` for all agents, so neither is used. QLever
  (University of Freiburg; no robots.txt) serves the same data: `https://qlever.dev/api/wikidata`
  (SPARQL; explicit `PREFIX` lines needed) and `https://qlever.dev/api/osm-planet`. Per-entity JSON
  at `https://www.wikidata.org/wiki/Special:EntityData/<Q>.json` is allowed by wikidata.org's robots.txt.
- **Wikipedia: article pages only** (`/wiki/<Title>`). Its robots.txt disallows `/w/` (the Action API)
  and `/api/` (REST) for all agents; Firefinder follows the same rule.
- **robots.txt that names Anthropic's crawlers** (ClaudeBot, anthropic-ai, Claude-Web): BAnQ numérique
  and Nauticapedia are **used by the owner's decision (2026-10-21)**, told of the ban: politely, at low
  volume, keeping to each site's rules for all other agents (`*`); `research/polite.py` lists them in
  `OWNER_ALLOWED_DESPITE_AI_RULES`. Canadiana stays out: it disallows `/search` and `/file` for every agent.
- **Retired pages through the Wayback Machine: allowed.** A page its publisher has taken down (the
  NPS light-station inventory, old Tripod sites) may be read from the Internet Archive and cited with
  both the original URL and the archive URL.
- **The USCG Historian's pages through the Wayback Machine: allowed (owner, 2026-10-21).** The site
  (public-domain federal histories: station pages with keeper lists, the Lightship Station Index) answers
  403 to our requests; its Internet Archive copies may be read and cited, every footnote giving both the
  original address and the archive copy.
- **Skipped as blocked:** USCG Historian (`history.uscg.mil`, Akamai 403 to everything), the Michigan
  Lighthouse Conservancy, PEI Island Newspapers, Maritime History of the Great Lakes (Cloudflare
  challenges), Library and Archives Canada search and the New Brunswick archives (robots.txt), NPS IRMA
  `/DataStore/DownloadFile/` (robots.txt).

The source survey (2026-10-21, `docs/sources/survey_*.md`) fills this table. Leads to check:

| Kind | Leads |
|---|---|
| Open, bulk | Wikidata (CC0; ~990 US and ~490 Canadian lighthouses, ~500 with NRHP ids; LighthouseFriends suggests Canada has ~740 standing and ~390 lost, so Wikidata holds less than half), OpenStreetMap `man_made=lighthouse` (ODbL), NOAA ENC `LIGHTS` objects (public domain: characteristic, period, height, range of active lights), the USCG Light List, the Canadian Coast Guard List of Lights, the NPS National Register dataset, Parks Canada's heritage lighthouses (Heritage Lighthouse Protection Act), the Canadian Register of Historic Places |
| Public-domain history | USCG Historian's Office station histories and lightship lists; the NPS Maritime Heritage Program's inventory of historic light stations; the Lighthouse Board (1852–1910) and Commissioner of Lighthouses (1911–39) annual reports and the Lighthouse Service Bulletin (HathiTrust / Google Books / Internet Archive); the US Life-Saving Service annual reports (1876–1914, wreck-by-wreck); NRHP nomination forms (NPGallery); HABS/HAER (Library of Congress); Chronicling America; NARA RG 26 keeper registers (M1373 and later) |
| Canadian history | Department of Marine and Fisheries / Marine annual reports in the Sessional Papers (Canadiana; they list keepers and salaries), Library and Archives Canada, provincial archives, the Nova Scotia Lighthouse Preservation Society, BAnQ and the RPCQ for Quebec |
| Community sites (facts only) | LighthouseFriends.com (histories and keeper lists), Russ Rowlett's Lighthouse Directory (worldwide, lost lights included, ARLHS numbers), Lighthouse Digest (the Doomsday List of endangered lights), the US Lighthouse Society (passport stamps, rentals, keeper programs), regional conservancies and Friends groups |
| Wrecks | NOAA's wrecks and obstructions data (AWOIS and ENC `WRECKS`), public domain; the Life-Saving Service reports for the rescues |
| Charts | NOAA Office of Coast Survey Historical Map & Chart Collection; NOAA's current chart display service (both public domain); Canadian historical charts if licensable |

### 2.1 The fetchers built so far (scaffold, 2026-10-21)

Two open bulk sources, each a script that writes one committed extract, `data/sources/<source>.json`
(3.8). Both go through QLever, per the rulings above. Neither runs in CI: the extracts and the
stations are committed, and are refreshed by hand (2.2).

- **`pipeline/fetch_wikidata.py`** → `data/sources/wikidata.json` (CC0). QLever's Wikidata endpoint
  times out on one query with many `OPTIONAL` value-node patterns, so the fetcher makes one small
  query per selection and one per property over all the selected items (`VALUES`), about 50 queries
  in all, each cached under `$FRESNEL_RAW_ROOT/wikidata/` by a hash of its text. QLever sometimes
  sends its whole answer twice in one response; the reader keeps the first complete JSON document.
  - *Selection* (class and property ids checked against live answers on 2026-10-21): instance of
    lighthouse `Q39715` or any subclass (`P31/P279*`), with country (`P17`) the US `Q30`, Canada `Q16`
    or a territory's own item, or located (`P131+`) in a territory; light station `Q27193297`;
    lightvessel `Q831515` (the surviving vessels, at their berths; `kind: lightship`); lightvessel
    station `Q109662605`; lifeboat station `Q11997323` (Wikidata's class for the Life-Saving Service
    stations); coast guard station `Q31407679` only when it has an NRHP number or a heritage
    designation (the historic stations, never air stations); and any NRHP-listed item whose English
    label says Life-Saving / Lifesaving / Life Saving / Lifeboat Station, House of Refuge or Coast
    Guard Station / Boathouse. NRHP cover documents ("Light Stations of Maine MPS") are skipped.
  - *Fields*: English label (the French label kept as another name for a Canadian station, the
    Spanish one in Puerto Rico; elsewhere those labels are translations and are left out), aliases,
    coordinates `P625`, classes `P31`, region and county by walking `P131` up four levels (the region
    from the first ISO 3166-2 code `P300` or territory item, the county from the nearest place whose
    class is a US county or county-equivalent, a Louisiana parish, an Alaska borough or census area, a
    Puerto Rico municipio, or a Canadian census division; most Canadian items name only their
    province), inception `P571` (→ a structure's `built`), service entry `P729` (`first_lit`), service
    retirement `P730` (`deactivated`), dissolved/demolished `P576`, state of use `P5817`, height
    `P2048`, focal height `P2923`, range `P2929` (with colour `P462`), elevation `P2044` (all through
    `p:`/`psv:` to read the unit: feet, metres, nautical and statute miles and kilometres were all
    found), characteristic `P1030` (when there are several, the one in Light List form with a period
    wins: "Fl W 4s" over "FF WRG (secteurs)"), NRHP `P649`, ARLHS `P2980`, USCG Light List number
    `P3723` ("1-7565": volume and LLNR), Canadian Coast Guard List of Lights number `P3920`, NGA
    `P3563`, Canadian Register `P477`, Heritage Lighthouse of Canada `P3211`, Federal Heritage
    Buildings `P3197`, the Nova Scotia (`P909`) and PEI (`P763`) registers, heritage designation
    `P1435` (with start time `P580`, → `nrhp_listed` / `heritage_designated` events), Lighthouse
    Directory page `P11627`, image `P18`, Commons category `P373`, website `P856`, material `P186`,
    operator `P137`, owner `P127`, replaces / replaced by `P1365` / `P1366`, significant event `P793`
    with point in time `P585` (automatization → `automated`, relocation, demolition...), and the
    English, French and Spanish Wikipedia articles.
  - *Status claims*: the destroyed / demolished / former-entity classes → `lost`; ruins → `ruins`;
    replica → `replica`; inactive lighthouse, or a service retirement → `inactive`. `P576` does not
    say whether the light was discontinued or the tower taken down (on lighthouse items it is most
    often a loss, Cape Henlopen 1926; sometimes an older tower of a light that still stands, Cape
    Hatteras 1871), so it makes no claim: the record is marked `possibly_lost` and the merge decides
    (3.9). The faux lighthouse and aerial lighthouse classes (and two beacon classes) are kept with
    `extra.out_of_scope`, which the merge turns into `hidden`.
  - *2026-10-21 run*: 1,558 items selected, 1,501 written (1,026 US, 475 Canada), 56 skipped with
    no coordinates and one with no region.
- **`pipeline/fetch_osm.py`** → `data/sources/osm.json` (ODbL). Three queries on QLever's OSM planet
  endpoint: every element inside the boundary relation of the United States (148838), Canada
  (1428125), Puerto Rico, the US Virgin Islands, Guam, the Northern Marianas, American Samoa or the
  Minor Outlying Islands (a country's relation reaches over its territorial sea, so reef and shoal
  lights are inside) tagged `man_made=lighthouse`, `building=lighthouse`, `historic=lighthouse`,
  the lifecycle forms `disused:` / `was:` / `abandoned:` / `demolished:` / `razed:` / `removed:` /
  `destroyed:` / `ruins:man_made=lighthouse`, or `seamark:type=light_major` / `light_vessel`; then
  every tag of each, and its geometry (a way's position is the mean of its outline). The region is
  the territory's own relation, else the point's region from the Census Bureau's state boundaries
  (US, waters included) or Natural Earth's admin-1 polygons (Canada, the Minor Outlying Islands),
  probing outward up to 60 km for a light on a rock the coastline leaves out (`regions.RegionLookup`).
  - *Readings* (module docstring has the full table): kind from the name (Range / Front / Rear, pier,
    pierhead, breakwater, jetty, mole) or `seamark:light:category`; `harbor_light` for a
    `man_made=lighthouse` that is a `seamark:type=light_minor` and whose name does not call it a
    lighthouse; status from the lifecycle forms, `ruins`, `disused=yes`, `seamark:status`, and
    `active` for a lighthouse carrying seamark light tags; the characteristic written in Light List
    form from `seamark:light:character`, `:group`, `:colour`, `:period` ("Fl(2) W 10s"; sector
    lights give their first sector, the others kept), focal height, range and fog signal.
  - *Flags the merge reads*: `enrich_only` (a `light_major` with no lighthouse tag: a light on a
    pole, a skeleton tower, or a separate light node beside a mapped tower; it may add its light to a
    station, never start one, as DESIGN section 1 excludes modern beacons); `minor_beacon_suspect`
    (a fixme saying "beacon": 787 of Canada's elements are NRCan CanVec imports marked "could be a
    beacon with a light"; an unnamed `light_minor`; or a name that is a numbered aid, "Light 147",
    "Daybeacon", "Aid to Navigation"; each only without a Wikidata, NRHP or heritage link);
    `decorative_hint` (miniature golf, shop, restaurant and similar tags, or "replica" in the name,
    on an element with no seamark light, Wikidata link or register).
  - *2026-10-21 run*: 2,813 elements, 2,807 written (1,309 US, 1,498 Canada); 1,173 have no name.
- **Raw cache**: `$FRESNEL_RAW_ROOT`, else, in a git worktree, the main checkout's `data/raw/` (so
  every agent's worktree shares one cache), else `<repo>/data/raw/` (`pipeline/_common.py`). The
  boundary files (`census/states.geojson`, `natural_earth/...admin_1...geojson`, public domain) are
  fetched there once.

### 2.2 Refreshing, and adding a source

```
python3 pipeline/fetch_wikidata.py --refresh   # ask QLever again (otherwise the cache answers)
python3 pipeline/fetch_osm.py --refresh
python3 pipeline/merge.py                      # writes data/stations/ and data/merge_report.json
python3 pipeline/validate.py
python3 pipeline/build_site_data.py            # web/public/data/, for npm run dev / build
```

A new source is a fetcher that writes `data/sources/<id>.json` in the record shape of 3.8. The
merge picks it up with no code change (it ranks after Wikidata and OSM in every field, then
alphabetically); give it its place in `merge.SOURCE_ORDER` and `merge.PRECEDENCE` when it should
outrank them for some field (NOAA ENC for the charted light, the USCG and CCG lists for the light
list numbers, a staffed-lightstation list for `staffing`).

### 2.3 Canadian sources (2026-10-21, branch `agent/sources-ca`)

Six more extracts, each from its own fetcher in `pipeline/` with tests (`pipeline/test_fetch_*.py`). The
fetchers share `pipeline/_ca_common.py`: robots.txt is read and obeyed for every host (a host that
names Anthropic's crawlers is skipped, `Skipped`; a disallowed path raises `Blocked`), requests keep one
clock per host **across processes** (the lock files `data/raw/_locks/web-<host>`, the same ones
`research/fetch_text.py` uses, so two agents on one site still send one request every 2 s), and the
survey's cached pages (`data/raw/survey/canada/`) are read in place of fetching again. The extracts are
committed; none runs in CI. Order is the survey's; each source is a row.

| Source id | Fetcher | Licence and use | What it supplies |
|---|---|---|---|
| `parks_canada_hl` | `fetch_parks_canada_hl.py` | Open Government Licence - Canada (the Directory of Federal Heritage Designations CSV, open.canada.ca, 20 s crawl delay); Parks Canada's page: facts only | 115 designated heritage lighthouses (114 with a position from the page's map markup): designation date (a `heritage_designated` event), Heritage Lighthouse register entry and link to the statement of significance, custodian, build year, height, material. `extra.standing`: the Act protects standing lighthouses only |
| `ccg_list_of_lights` | `fetch_ccg_list_of_lights.py` | (c) His Majesty the King in Right of Canada, Canadian Coast Guard, 2026; no open licence: facts only, credit and link | The List of Lights, Buoys and Fog Signals (114 HTML sections, 5 volumes): characteristic, focal height, range, fog signal, structure height, list number (letter of the volume + number: `N1`, `A456`, `I563`, `P435`, `T50`) and Admiralty number, position to 0.1". Of 4,482 lit fixed aids only the 60 clear lighthouses (light stations; major lights), 7 the Lighthouse Directory lists with a lantern and no Lighthouse Friends page, and the 844 within 150 m of a station in the other extracts are kept (911 records); buoys and the 3,571 small beacons with no station near are counted in the header and dropped. Only a clear lighthouse may start a station |
| `lighthousefriends` | `fetch_lighthousefriends_ca.py` (`fetch_canada()`; the US fetcher shares the source id and the file: the writer keeps records of the other country) | All rights reserved: facts only (names, positions, flags), credit and link | The eight provincial index pages: 1,148 lights (744 standing, 404 destroyed), each with its GPS position, community and the site's visit flags (boat required, private, open for climbing, interior open, lodging, keeper programme). No station page is read; the URL on every record is the citation |
| `rowlett` | `fetch_rowlett.py` (same arrangement as above for the file) | (c) 2026 Russ Rowlett and UNC: facts only | 39 regional pages, 1,278 entries: years (tower, station established), status (active, inactive, lost `#`, replica), focal plane, structure height and material, owner, access wording ("Site open, tower closed", "Accessible only by boat"), and the numbers that join the others (ARLHS, CCG list, Admiralty, NGA, the Lighthouse Friends id in the anchor). No positions: a record joins a station by an identifier or a unique name |
| `ca_staffed_lightstations` | `fetch_ca_staffed_lightstations.py` (curated) | Facts from Senate, Coast Guard and DFO publications and news reports, each linked on the record | The 51 lightstations the sources name as staffed (BC 27, NL 23, Machias Seal Island) with `staffing`, the access label and note, and evidence. 49 staffed; Carmanah Point and Pachena Point `automated` since 31 July 2024 (the newer source wins). 44 stations rest only on the Coast Guard's April 2010 list (`check`) |
| `ca_lightships_lifesaving` | `fetch_ca_lightships_lifesaving.py` (curated) | Facts compiled from open and public-domain sources, each linked | Canadian lightship stations and life-saving stations the sources name: Lower Traverse, Lurcher Shoal, Red Island Reef, Manicouagan Shoal; the lightship years of White Island Reef and Prince Shoal; the Sable Island Humane Establishment; the federal lifeboat stations of 1882-89. Positions only where a source gives one (3 of 21); the others are written without one and are the leads list |

Findings from the build: the Directory has no coordinates and the CCG list has no names that match the
other sources, so **identifiers do the joining** (3.9). Wikidata's coordinates are sometimes kilometres out
(Cape St. James 18.8 km, Sisters Islets 10.3 km): the same light then appeared twice, and curation merges
them. There is no Sambro lightship (Sambro is a lighthouse).

### 2.4 United States sources, second round (2026-10-21, branch `agent/sources-us`)

Eight more extracts, each from its own fetcher in `pipeline/` with tests (`pipeline/test_fetch_*.py`). The
fetchers share `pipeline/_records.py` (the record builder; a polite, robots-obeying `polite_get` with the one
clock per host that 2.3 describes; the xlsx reader; the writer). **A shared extract keeps the other country's
records**: `lighthousefriends.json` and `rowlett.json` hold Canada's records (2.3) and the United States'
(`write_extract(..., country="US")` replaces only the US ones), so either fetcher can run alone. Every
request is sent as `FresnelBot/0.1 (+https://github.com/holdTheDoorHoid/fresnel)`; none runs in CI; the
extracts are committed. Facts only from every copyrighted site: a name, a year, a flag, a number, a position
and a link per station, never prose or pictures. Order is the order they were built; the merge reads them in
`SOURCE_ORDER` (3.9).

| Source id | Fetcher | Licence and use | What it supplies |
|---|---|---|---|
| `lighthousefriends` | `fetch_lighthousefriends.py` (US half of the file 2.3 describes) | All rights reserved, (c) Kraig Anderson: facts only, credit and link | 32 state index pages (Puerto Rico is one) read as a marker list plus seven icon-filter passes (`all`, `destroyed`, `climb`, `lodging`, `keeperprog`, `private`, `boat`): 1,076 lights, each with its 5-decimal position, community and id (`extra.xref` `lhf:<id>`, which Rowlett's links also carry). Destroyed gives status `lost`; the flags give `visit` (climbable, boat only), `stay` (rental, keeper programme) and `access` (private); a light with no flag gets nothing, never a false. No per-light page is read |
| `uslhs` | `fetch_uslhs.py` (reads the cache the corpus agent crawls, `$RAW/uslhs/places.json`; never crawls) | (c) U.S. Lighthouse Society: facts only, link to each place's page | The Digital Archive's 2,299 places -> 2,139 records: 1,195 light stations, 134 lightship stations and 67 life-saving stations (3 and none of them with a position: they join an existing station by name, else wait as leads), 13 replicas, 681 minor aids and 48 private (faux) lighthouses (join-only; the faux ones carry a `decorative_hint`). Years, existing/lost, owner, optic, material, open to public; positions to 0.1 minute (`approximate`), 1,140 of them; 43 positions dropped (`plausible_position`: 0,0 placeholders, coordinates not on Earth, outside the bounding box of the state the record is filed under, or more than 15 km from it and nearer another). Ranks below Wikidata, OSM and LHF for location (it put Split Rock 23 km off) |
| `nrhp` | `fetch_nrhp.py` | US federal public domain (NPS) | The workbook (reference number, name, other names, state, county, listed and NHL dates, nomination link) joined to the NPS point service by number: 577 properties (every number Wikidata carries on a station, the lighthouse and life-saving multiple-property listings, and names that say lighthouse, lightship, range light, life-saving station, house of refuge, Coast Guard station). `registers[]` with `listed`, `nhl`, `nomination`; positions are the service's batch-derived points (`approximate`). A district is station-level, a boundary increase never starts a station; a point outside the bounding box of its state (2 of the 577: Great Beds, NJ, at 44.09 N) is dropped and said (`extra.position_dropped`) |
| `enc` | `fetch_enc.py` | US federal public domain (NOAA); not for navigation | NOAA ENC Direct light points, six chart bands, clustered (25 m) and kept only within 200 m of another source's record: 1,058 lights with the characteristic in Light List form (`Fl(2) W 6s`), focal height and nominal range. No names: position-only enrichment (`enrich_only`). The service drops bands at times (2026-10-21: the approach and harbour bands answered \"Could not find service\" and are partly read from cached pages; `notes.bands_missing` says which) |
| `uscg_light_list` | `fetch_uscg_light_list.py` | US federal public domain (USCG) | Light List volumes I-VII (2025 edition; `pdftotext -layout`, token-offset columns): 2,054 lights that can be a station (their number is one Wikidata carries, or another source lies within 300 m) with number `vol-LLNR`, name, position to 0.001\", characteristic, range, structure and remarks. Enrichment and the hard key for joins |
| `rowlett` | `fetch_rowlett_us.py` (US half of the file 2.3 describes) | (c) Russ Rowlett and UNC: facts only, credit and link | 73 regional pages, 1,697 US entries: years (tower, station established), status word, focal plane, the ARLHS, Light List and Admiralty numbers and the LHF id in the anchor. No positions: a record joins a station by number, else by a unique name in its state. Bracketed entries (fog signals, other buildings) are join-only |
| `uslhs_passport` | `fetch_uslhs_passport.py` | (c) U.S. Lighthouse Society: facts only, link | The Passport Club stamp list (PDF, July 2026; 622 stations) -> `visit.passport_stamp`, and the accommodations pages (57 stations) -> `stay` type and the operator's site. No contact names or numbers. Position-less: joins by name within its state; ranks first for `visit` and `stay` |
| `territories` | `fetch_territories.py` | Facts only: Wikipedia's list of territorial lighthouses (CC BY-SA) for the seed lights; Library of Congress HAER records (public domain) | 22 records for Guam, American Samoa, the Virgin Islands, Howland Island and Puerto Rico, where Wikidata and OSM are thin: 7 seed lights (the ones that pass DESIGN section 1) and 15 HAER PR-32..47 records, which only add the HAER number and link to the station they join. Guam had no station before this; the posts with no dated history are left out and named in the extract |

Findings from the build: the Society's archive and Rowlett carry no usable positions for most lightship and
life-saving stations, so those join by name or wait as leads (3.9); LighthouseFriends's and OpenStreetMap's
positions for a handful of lights are tens of kilometres out (Six Mile Point Range), as are Wikidata's
(Ship Shoal, Cape Fear, Point Stuart) and the Society's (Oswego, Split Rock, Race Point): the decisions are in
`pipeline/record_joins.py`, with their reasons in `docs/sources/review_2026-10-us.md`.

---

## 3. Data model

As in Firefinder (`data/sources/<source>.json` normalized extracts → `pipeline/merge.py` →
canonical records → `pipeline/build_site_data.py` → the site), with lighthouse fields.

### 3.1 Files

```
data/
  sources/<source>.json     normalized extract from one source; committed
  stations/<dir>/<id>.json  one canonical record per station (3.2); the source of truth.
                            <dir> is the state or territory code for a US station (me/, pr/),
                            <country>-<region> for any other country (ca-ns/), as in Firefinder
  vessels/<id>.json         one record per lightship vessel (3.5)
  people/<id>.json          one record per keeper or crew member in the keepers index (3.6); id = the archive's person slug
  rosters/<dir>/<id>.json   the U.S. Lighthouse Society archive's roster for each US station that has one (3.6)
  people_report.json        counts from pipeline/build_people.py: people, withheld by reason, matches. Never a name
  stories/<id>.md           the researched long-form story with footnotes (section 5)
  research/<id>.json        that research's facts, events, keepers, evidence, sources, fact-check
  photos_manifest.json      mirror output (as in Firefinder); files served from fresnel-photos
  raw/                      crawl cache, git-ignored
  vocab.json                controlled vocabularies (3.4)
  curation_ca.json          Canada's explicit review decisions, each with a reason (3.9)
  merge_report.json         pipeline/merge.py's review file (3.9); committed
```

Built so far: `sources/`, `stations/`, `merge_report.json`, `vocab.json`, and (3.6) `people/`, `rosters/` and
`people_report.json`. `vessels/`, `stories/`, `research/` and `photos_manifest.json` come with later
rounds; the site already renders a story and a keepers roster when they exist (`web/fixtures/` has one of
each).

### 3.2 Canonical station (`data/stations/<dir>/<id>.json`)

`id` = `<country>-<region>-<slug>` (`us-me-portland-head`, `us-pr-punta-higuero`,
`ca-ns-sambro-island`), with `-2`, `-3`… for same-name stations in one region. **Ids never change
once published** (they are URLs and checklist keys); two records that turn out to be one station
retire one id with `merged_into`, as in Firefinder.

**A station is the named light at a place**, not a single tower. Most light stations had several
towers over time (a first tower of 1803 replaced in 1870, a third in 1932). They are one station with
a list of `structures`, as long as the light stayed at essentially the same place and kept its
identity. A light moved to a different headland, or a new station with its own name, is a new
station, linked from the old one (`succeeded_by` / `preceded_by`). A range is one station with a
front and a rear structure. Cape Hatteras, moved 2,900 ft inland in 1999, is one station with a
`relocated` event.

Rulings (orchestrator, 2026-10-21, from the first build's open questions):

- **Twin lights are one station** with two tower structures (Navesink Twin Lights; Cape Ann Light
  Station's twin towers on Thacher Island; Chatham's former pair), because they were one station with
  one set of keepers.
- **Successive lights at clearly separate sites with their own established names are separate
  stations**, linked with `preceded_by` / `succeeded_by`: Old Point Loma (1855, on the ridge, now a
  museum) and New Point Loma (1891, at the shore) are two stations. A rebuild at essentially the same
  spot under the same name stays one station.
- **Scale copies of a specific historic light are `replica`**, linked to the original (`related`,
  relation `replica_of`). The Lake Havasu lights in Arizona (one-third-scale copies of named lights)
  are shown as replicas; that they also mark the lake for boaters goes in a note. A decorative
  "lighthouse" that copies no particular light and never served as an aid stays hidden.

```json
{
  "id": "us-me-portland-head",
  "name": "Portland Head Light",
  "other_names": [],
  "country": "US", "region": "ME", "county": "Cumberland",
  "water": "Gulf of Maine",
  "setting": "coast",
  "kind": "lighthouse",
  "location": {"lat": 43.6231, "lon": -70.2079, "precision": "exact", "from": "wikidata"},
  "status": "active",
  "structures": [
    {"role": "tower", "type": "conical_masonry", "material": "stone", "built": 1791,
     "height_m": 24.4, "status": "standing", "note": null, "from": "uscg"}
  ],
  "light": {
    "first_lit": 1791, "deactivated": null,
    "lens": {"type": "fresnel", "order": "4", "status": "on_display", "where": "museum on the station"},
    "characteristic": "Fl W 4s", "focal_height_m": 30, "range_nm": 24,
    "fog_signal": "horn", "from": "enc"
  },
  "registers": [{"register": "NRHP", "number": "73000121", "url": "..."}],
  "aton": {"uscg_llnr": "...", "arlhs": "USA-650", "ccg_list_number": null},
  "agency": "Town of Cape Elizabeth",
  "ownership": "local",
  "access": {"level": "public", "note": null},
  "staffing": {"status": "automated", "as_of": "1989"},
  "visit": {"grounds_open": true, "climbable": false, "museum": true, "tours": null,
            "boat_only": false, "passport_stamp": null, "note": null},
  "stay": null,
  "events": [{"year": 1791, "event": "first_lit", "note": null, "from": "uscg"}],
  "keepers_count": null,
  "related": [{"id": "us-me-...", "relation": "life_saving_station_nearby"}],
  "photos": [], "links": [], "sources": [], "conflicts": [],
  "verification": "unverified", "locked": [],
  "hidden": false, "hidden_reason": null,
  "updated": "2026-10-21"
}
```

`stay` (when someone can sleep there: rental, inn or B&B, hostel, volunteer keeper program):
`{"type": "rental|inn|hostel|keeper_program", "provider": "...", "url": "...", "season": "...",
"note": "...", "checked": "YYYY-MM-DD"}`.

As built (2026-10-21), the merge also writes:

- `status_note`: text beside the status, or null ("Wikidata gives an end date (1926) without saying
  whether the light was discontinued or the tower taken down... It may be gone.").
- `structures[]`: one entry per structure the records describe, oldest first (front before rear for
  a range), each with `name` (the record's name when the station has more than one structure, else
  null), and `location` `{lat, lon}` when it stands more than 25 m from the station's pin (a rear
  range light, an older tower up the hill). `role` is `tower` unless a record says otherwise
  (`front_range`, `rear_range`, `dwelling` for a keeper's house, `fog_signal`, `oil_house`,
  `boathouse`, `other`); a life-saving station's building is `other`. A structure's `status` is
  `standing` when OpenStreetMap maps it today, else what the sources claim, else `standing` when the
  station is lit or out but standing, else `unknown`.
- `light.from`: the source of the characteristic (or of the first-lit year when there is none).
  `light.lens` is null until a source gives it. A lightship and a lightship station have a `light`
  but no `structures`; a life-saving station has structures but no `light`.
- `sources[]`: `{source, key, part, fields}`: `part` names the structure the record describes (the
  key of the first record of that structure) or `station` for a record that describes the whole
  station (a light-station or historic-district item, the item for a whole range); `fields` lists
  what the record supplied. The merge's memory reads `key` and `part` back on the next run.
- `related[]`: `{id, relation, name}`, relations from `vocab.relation`: `preceded_by` /
  `succeeded_by` (Wikidata's replaces / replaced by between two stations), and
  `life_saving_station_nearby` / `light_station_nearby` (within 1.5 km, both ways).
- `staffing`: `automated` with `as_of` when a source dates the automation; otherwise `unknown`. A
  Canadian lightstation on the staffed list (2.3) is `staffed` with `as_of` the year of its newest
  evidence, plus `basis` (what it rests on), `check` (true when only the April 2010 list names it: a
  research agent must confirm it before a page says "staffed" now) and `evidence` (label, url, date). Its
  `access` is `restricted` with the note "Staffed lightstation: the keepers' home and workplace. Visit
  only where the station welcomes visitors, and never land uninvited."; Carmanah Point and Pachena Point
  (`automated`, 2024) carry the Coast Guard's safety note instead.
- `aton.admiralty` (Canada): the Admiralty number (`H3680`), from the Coast Guard list, the Directory or
  an OpenStreetMap `seamark:light:reference`. `visit` and `stay` take Lighthouse Friends' flags (boat only,
  climbable, lodging, keeper programme) and the Directory's wording; `access.level` is `private` for a
  private flag, `closed` for "site closed" with nothing open, `public` only where the Directory says the
  site and tower are open or Lighthouse Friends says it is climbable.
- `visit.museum`: true when Wikidata classes the item as a museum; `stay`: an inn when it classes it
  as a bed and breakfast. Every other `visit` and `access` value stays null / unknown until a source
  says so (OpenStreetMap's `access=*` describes the structure, not the grounds, so it is kept only
  as `access.note`, as in Firefinder).
- `conflicts[]`: `{field, values[{source, value}], distance_m?, note}` for `status` (lit against out,
  or gone against mapped today), `location` (records of one structure more than 500 m apart),
  `first_year` (first years 2 or more apart), `light.characteristic`, `light.focal_height_m` (more
  than 3 m apart) and `light.first_lit` (a service entry after the retirement: perhaps relit; then
  neither is shown as the first lighting).
- `verification`: `facts` when two independent sources place the station within 500 m of its pin and
  no status conflict stands; otherwise `unverified`; `researched` / `verified` are never downgraded.

### 3.3 Countries, regions, units

As in Firefinder (`pipeline/regions.py`, mirrored in `web/src/lib/regions.ts`), with the US
territories added as regions of `US`: `PR`, `VI`, `GU`, `MP`, `AS` (and `UM` if needed). Folders:
the bare code for a US state or territory (`me/`, `pr/`), `<country>-<region>` otherwise (`ca-ns/`).
Local units in `county` (US counties, boroughs, parishes, Puerto Rico's municipios; Canadian units as
their source writes them).

**Units:** heights and elevations as in Firefinder: feet first with metres alongside in the US and
its territories, metres first with feet alongside in Canada. Data is always metres. **Ranges and
distances at sea are nautical miles** everywhere (with km alongside), because that is how lights are
charted.

### 3.4 Vocabularies (`data/vocab.json`)

- `kind`: `lighthouse` (a light station whose light is on a tower or on its building), `range_lights`
  (a front and rear pair aligned to mark a channel), `pier_light` (pierhead or breakwater light),
  `harbor_light` (a small harbor or river light that is not a full station but has a structure and a
  history), `lightship_station` (a place at sea where lightships were moored), `lightship` (a
  surviving vessel, shown at its berth; 3.5), `life_saving_station`.
- `setting`: `coast`, `island`, `offshore` (on a shoal or reef, out of sight of land or nearly),
  `bay`, `river`, `great_lakes`, `harbor`, `pier`.
- `structures[].type`: `conical_masonry` (brick or stone tower), `cast_iron` (plate or cast-iron
  tower), `skeletal` (open iron or steel framework), `screwpile`, `caisson` (sparkplug), `crib`
  (timber or concrete crib in a lake), `integral` (lantern on the keeper's dwelling: schoolhouse,
  Cape Cod), `wood_frame`, `concrete`, `texas_tower` (offshore platform), `other`. `role`: `tower`,
  `dwelling`, `fog_signal`, `oil_house`, `boathouse`, `front_range`, `rear_range`, `other`.
- `status` (of a station): `active` (still an aid to navigation, any agency or private), `inactive`
  (standing, light out), `lost` (gone: demolished, burned, washed away, collapsed), `ruins`,
  `relocated` (the structure now stands elsewhere; `events` record from and to), `replica` (a copy of
  a specific historic light, linked to it), `unknown`. A structure's own `status`: `standing`,
  `lost`, `ruins`, `relocated`, `unknown`.
- `light.lens.status`: `in_place`, `on_display` (with `where`), `lost`, `unknown`.
- `light.characteristic`: the Light List / IALA abbreviation as charted (`Fl W 6s`, `Fl(2) R 10s`,
  `Oc W 4s`, `Iso G 6s`, `Q R`, `Mo(A) W 8s`, `Al Fl W R 30s`, `F W`). Historical characteristics are
  events (`characteristic_changed`) with a note, so the light at night can show the light as it was
  in a chosen year. Such an event gives the pattern from that year on in `characteristic` (else its
  note is read: "Fl W 4s", "changed to Fl W 4s", "from F W to Fl W 4s"), and may give the one before
  in `previous_characteristic` and that era's `focal_height_m` and `range_nm` (4.1).
- `staffing.status`: `staffed` (keepers live there now), `automated` (with `as_of`), `volunteer`
  (resident volunteer or caretaker keepers), `unstaffed`, `unknown`.
- `ownership`, `access.level`, `verification`: as in Firefinder (`ownership` adds `provincial` and
  `nonprofit`: many lights belong to a province or a preservation society).
- Also in `data/vocab.json` (2026-10-21): `structure_material` (`brick`, `stone`, `wood`, `concrete`,
  `cast_iron`, `iron`, `steel`, `aluminium`, `fiberglass`, `tabby`, `mixed`), `lens_type`,
  `lens_order`, `stay_type`, `relation` and `link_kind`. `pipeline/validate.py` checks every value of
  every station against these lists, and `web/src/lib/vocab.ts` gives each its words.
- `events[].event`: `built`, `first_lit`, `rebuilt`, `replaced`, `relit`, `deactivated`,
  `automated`, `keeper_appointed` (prefer the roster), `lens_installed`, `lens_removed`,
  `characteristic_changed`, `fog_signal_installed`, `damaged`, `destroyed`, `burned`, `collapsed`,
  `removed`, `relocated`, `restored`, `modified`, `wreck` (a wreck at or near the station),
  `rescue`, `storm`, `war` (wartime darkening, use or damage), `transferred` (ownership), `closed`,
  `opened_to_public`, `nrhp_listed`, `heritage_designated` (Canada; note the register), `other`
  (needs a note). Every event cites its source.

### 3.5 Lightships

A **lightship station** (Nantucket Shoals, Diamond Shoals, Ambrose, Lurcher Shoal…) is a map entry like any
station, at its charted position, with the vessels that served it by years. A **vessel** has its own
record (`data/vessels/<id>.json`, id from its hull number: `lv-112`, `wal-534`, Canadian names
slugged) with its career (stations and years), its fate, and, if it survives, its berth. A
surviving vessel is also on the map at its berth (`kind: lightship`). The keepers index covers
lightship crews the same way as keepers.

### 3.6 Keepers index

The research for each station records a **roster**: every keeper, assistant and (on lightships)
master and crew member the sources name, with role and years and a cite for each line. The roster is
shown on the station page and feeds the keepers index: one page per person (`/k/<person-id>/`), listing
every station they served and linking the stories that mention them, and a searchable index of
them (`/keepers/`).

**Where the names come from (built 2026-10-21).** Until research has checked a station, its roster is the
**U.S. Lighthouse Society's Digital Archive's** (`archives.uslhs.org`, "All Rights Reserved": facts only, a
credit and a link on every page): "Keepers listed by the U.S. Lighthouse Society's Digital Archive, from the
National Archives' keeper registers". The corpus crawl (`research/roster.py crawl`, 2 s per request) holds 2,160
rosters of 43,999 lines naming **24,355 people**. A roster line carries the archive's own person record (the slug of
its `/people/<slug>` page, `william-robertson`, `charles-h-davis-0`), so one record seen at several places is one
person without anyone reading a person page: the 24,355 pages would take 14 hours at 2 s each, and they would
add only salary, source and birth and death years, none of which the index needs. That one slug is one person is checked against the archive itself: the 34 person pages in the cache list exactly the stints that the rosters group under their slug (`ArchiveGroundTruthTest`). `pipeline/build_people.py`
turns the cache into the committed files below; it fetches nothing.

- **Never join two people by name alone.** Two roster lines become one person only when a source connects them.
  With the archive that is its own record: lines naming the same record are one person's stints, and two
  records with the same name are two people (the archive itself files a "Thorwald Hansen" and a "Thorwald
  Hansen-0"). Where two records share a name and their years and region fit one career (the later one begins
  within 6 years of the earlier one ending, in one state or within 150 km; no overlap of more than a year; each
  side has at most 3 such candidates, else the name is too common to say anything), each page may say
  "**possibly the same person as…**" with a link, and **nothing more**: the stints are never merged. Of the
  published people 22 carry such a hint (11 pairs). A record whose stints overlap by 2 years or more at places
  100 km or more apart (`check: far_overlap`) gets a plain note that the archive's record may hold two people.
- **Research rosters join a person only on a source.** In `data/research/<id>.json` a roster line may carry
  `person` (the archive person slug, from `research/roster.py --json`: the line is that record's stint) and
  `other_stations` (service elsewhere, each `{name, id?, role?, from, to, cite}` with a **cite**, the connecting
  source). A line that names a published archive record replaces that person's overlapping archive stint at
  the station (the research is the checked version of it) and adds its `other_stations`. A line with
  `other_stations` and no `person` makes a person only the research names (`<station id>--<name slug>`), who is
  never joined to an archive record of the same name. A line with neither stays a row in the station's table.
  A `person` the archive does not know is left unlinked with a warning; one the rule withholds is never made a
  page. The pipeline keeps `person` on a research line only when that person has a page.
- Family keepers (spouses, children who kept the light) are listed in their own right, with the role
  the source gives ("acting keeper", "assistant", "kept the light after her husband's death").
- **Living people (DECIDED, the owner's 1950/1960 line).** Keepers, owners and volunteers who may be alive
  (roughly anyone whose service ended after 1960) are named only as published sources name them, in their
  public role, with no personal details beyond what those sources print. Private residents of converted
  lighthouses are not named unless they present themselves publicly (an inn's owners). In the keepers index
  that is a rule with no judgment in it (`keepers.withhold_reason`): **a person any of whose recorded stints
  begins in 1950 or later, or ends after 1960, or who has no year at all, has no person page and no index
  entry.** A stint with no end year is read as lasting 30 years, so one that began in 1931 or later is withheld
  (a career that long was the longest usual). The archive's spans are read as printed ("1950s-" begins in
  1950; "at least 1950-1951" begins in 1950). The decision is for the whole person, so a keeper who served 1935
  to 1962 is out. Such people stay **only as lines in the roster tables of the stations**, exactly as the
  archive prints them (name, role, years). The archive's race and sex fields are never read, stored or shown;
  roles as printed ("acting keeper", "USCG") are fine. As built: of 24,355 archive people **16,884 have a page and
  7,471 are withheld** (counted once, by the first rule a stint breaks: 6,879 begin in 1950 or later, 158 end after
  1960, 321 have an open end that began in 1931 or later, 113 have no year). `validate.py` fails the build if a person with a file breaks the rule, and
  `test_keepers.py` checks the committed files too.

**Files.** `data/people/<person-id>.json` (16,884 as built):

```json
{"id": "thorwald-hansen-0", "name": "Thorwald Hansen", "source": "uslhs",
 "archive": "https://archives.uslhs.org/people/thorwald-hansen-0",
 "stints": [
  {"place": "round-island-ms", "place_name": "Round Island MS", "state": "MS", "role": "first assistant",
   "span": "1909-1911", "from": 1909, "to": 1911}],
 "possibly": ["thorwald-hansen"]}
```

`place` is the archive's place slug, `span` the years as printed, `from` / `to` the years read from it (with
`from_approx` / `to_approx` for "at least"), `role` the normalised role, `role_raw` the archive's heading when it
is not one of its standard seven ("Machinist"), `check` the far-overlap note. `data/rosters/<dir>/<station
id>.json` (958 stations) holds, for each US station, the roster of each archive place it shows, every line as
printed with its `person` slug **whether or not that person has a page**, and `match`, how the place was
matched. `data/people_report.json` holds counts, never a name. A run on the same cache writes the same bytes
and deletes files of people the rule now withholds.

**Which archive place is which station.** First the merge's own join: a station whose `sources` hold
`uslhs:<nid>` shows that place's roster (950 stations; the merge matched name and position, and the doubtful
ones were reviewed, `docs/sources/review_2026-10-us.md`); a range's front and rear are two places on one
station. Then, for a station with no archive record at all, `research/roster.py`'s own match (name and position),
accepted only when it is **by name and position within 1 km**, the place is claimed by no station's merge key
and no other station is matched to it (8 stations). The fallback's weaker matches ("by name only, WARNING: its
USLHS position is 790 km from the station's") are refused: they would put one light's keepers on another
(Pigeon Point 2, Table Bluff, Sabine Bank twice). Lightship stations have no archive rosters.

**What the pages say.** A station page shows its **checked** research roster when it has one (marked "Checked",
each line with its sources) and a one-line note that the archive lists N lines too; otherwise the archive's
roster, marked "Not yet checked", with the archive's sentence, the archive place linked, and the credit again
under Sources and credits. Each name with a person page links to it. A person's page lists the stints in order
with the station (linked, or the archive's place with a link when the station is not on the map), the role,
the years as printed and the source of each stint, the "possibly the same person as" block, the written histories of the stations they served at (and whether the
history's text names them), and the credit. A story is linked only through a station where the person is listed,
never because its text contains their name: finding "Strout" in another station's story would be joining by
name. Details in 4.2.

**Roster shape** (`data/research/<id>.json` → `keepers`, rendered as the station page's Keepers
table; `research/STORY_GUIDE.md` has the research rules):

```json
"keepers": [
  {"name": "Joseph Greenleaf", "role": "keeper", "from": 1791, "to": 1795, "note": "First keeper", "cite": [2],
   "person": "joseph-k-greenleaf"},
  {"name": "Joshua F. Strout", "role": "head keeper", "from": 1869, "to": 1904, "cite": [2, 4],
   "from_approx": false, "other_stations": [{"name": "…", "id": "us-me-…", "from": 1860, "to": 1869, "cite": [4]}]}
]
```

- `name` (required): as the source spells it.
- `role`: the source's word, normalised as the story guide lists (`keeper`, `head keeper`, `first
  assistant`, ..., `station keeper`, `surfman`, `master`, `crew`); text or null.
- `from`, `to`: a year, or a `"YYYY"` / `"YYYY-MM-DD"` string, or null; `from_approx` /
  `to_approx` true when the source gives only an approximate year (the page writes "c. 1880").
- `note`: text or null.
- `cite` (required): one or more numbers of the research file's own `sources[].n`; the page links
  each to that source, listed under Sources and credits.
- `person` (optional): the archive person slug this line is the stint of. `other_stations` (optional): service
  elsewhere with a `cite` for each; `id` when the station is on the map (else the name stays text).

`pipeline/validate.py` rejects a roster line without a name, with a malformed year, citing a
number the file's sources do not have, with a `person` that is not a slug, or an `other_stations` entry
without a name or a cite. `pipeline/build_site_data.py` copies the roster and the
research sources into `s/<id>.json` as `keepers` and `research_sources`.

**Canada.** The archive covers the United States only, so the index has no Canadian keepers yet and says so.
Canadian keepers come from the stations' researched stories (research-only people, joined by `other_stations`
with a cite), never from name matching. A research roster on any station, Canadian or American, appears in
the index through the rules above.

**Refreshing.** `python3 pipeline/build_people.py` after the archive cache is rebuilt
(`research/roster.py crawl` then `build`) or the stations change (`--check` prints the report and writes
nothing). The site build reads only the committed files, so CI needs no cache.

### 3.7 Wrecks

A wreck layer from NOAA's public-domain wreck data, near each station within a set radius, shown on
the map and listed on the page ("Recorded wrecks within 5 nm"). The stories' rescue accounts are
events (`wreck`, `rescue`) with sources. Positions of wrecks are shown as NOAA publishes them.

### 3.8 Source records (`data/sources/<source>.json`)

`{"source", "title", "url", "retrieved", "license", "notes", "records": [...]}`, records sorted by
key. Each record, as in Firefinder with lighthouse fields:

```json
{
  "key": "wikidata:Q2105159", "url": "...", "name": "Portland Head Light", "other_names": [],
  "country": "US", "region": "ME", "county": "Cumberland", "lat": 43.623056, "lon": -70.207778,
  "precision": "exact", "kind": "lighthouse", "kind_raw": "lighthouse", "role": null,
  "status": null, "status_raw": null,
  "structure": {"type": "conical_masonry", "material": "stone", "built": 1791, "height_m": 24.38, "status": null},
  "light": {"first_lit": 1791, "deactivated": null, "characteristic": "Fl W 4s",
            "focal_height_m": 31.0, "range_nm": 24.0, "fog_signal": null, "lens": null},
  "setting": null, "registers": [{"register": "NRHP", "number": "73000121", "url": "..."}],
  "aton": {"uscg_llnr": "1-7565", "arlhs": "USA661", "ccg_list_number": null, "nga": null},
  "agency": null, "ownership": null, "events": [], "photos": [], "links": [],
  "relations": {"replaces": [], "replaced_by": []},
  "extra": {}
}
```

`status` is the record's own claim in the station vocabulary, or null for none. `role` is the
structure the record describes (`front_range`, `rear_range`, `dwelling`) or null. Unknown values
are null, never `""`. Coordinates WGS84, west negative; all lengths in metres, ranges in nautical
miles. `extra` carries the source's own words and the flags the merge reads: `station_level`,
`out_of_scope`, `possibly_lost`, `enrich_only`, `minor_beacon_suspect`, `decorative_hint`,
`wikidata` (an OSM element's `wikidata=` tag). The US sources of 2.4 add: optional `visit`, `stay` and
`access` blocks on a record (only what the source states, never a false for a missing flag; the merge
fills the station's from the first source in `PRECEDENCE`, passport and LighthouseFriends first for
`visit` and `stay`); register entries with `listed`, `nhl` and `nomination` beside `number` and `url`;
`extra.xref` (identifiers of another source that name the same light: `lhf:<id>`), `quiet_unmatched`
(a record that joins a station or is not worth listing: ENC, the Light List, minor aids), `secondary` (a
Light List entry for a directional, sector or emergency light of a station: it ranks after the main light
for the charted fields) and `position_dropped` (the position a fetcher refused, and why).

### 3.9 Merge (`pipeline/merge.py`)

As in Firefinder: canonical files are the source of truth; the merge **adds and refreshes, never
deletes**; **ids never change** (two stations found to be one retire one id with `merged_into`, and
the site redirects its address); fields in `locked` are never overwritten; a re-run with unchanged
inputs writes nothing (a file is rewritten only when more than `updated` changed, and the review
file describes the merged state, not the run). The module docstring has every rule; in short:

- **Stations and structures.** Records join *stations*, and within a station *parts*, one per
  structure; each part becomes a `structures` entry. Two records of one source in one station are
  two structures (successive towers: "Old Cape Henry Light" and "Cape Henry Light"), unless they
  carry the same name word for word within 150 m (a duplicate, or an OSM node and its building). A
  light-station or historic-district item describes the whole station and joins it without being
  a structure.
- **Matching**, sources in the order Wikidata, OSM (others after, alphabetically), records by key,
  and the records that may start a station before those that may not (so those always see every
  station, and a first run equals a run with memory): (1) memory (`sources[].key` / `part`); (2) an
  OSM element's `wikidata=` tag, to the station holding that item within 10 km (Wikidata's
  coordinates for some offshore lights are kilometres out; farther tags are listed); (3) place and
  name: same country and kind group (lights; lightships; lightship stations; life-saving stations
  never join each other), names agreeing strongly (>= 0.85) within 1 km, partly (>= 0.5) or with
  one side unnamed within 250 m, or anything but opposites within 60 m; a second record of a
  source already in the station needs a strong name. Names compare without the words for the kind
  (Light, Lighthouse, Light Station, Phare de, Faro de, Life-Saving Station...), with St / Pt / Is /
  Hbr expanded and accents folded; Old / New / Original are dropped from the core, so "Old X"
  scores 0.95 against "X"; North / South, East / West, Upper / Lower, Front / Rear, Inner / Outer,
  High / Low, Big / Little and different numbers are opposites (0.2, never joined). (4) Else a new
  station, when the record may start one.
- **Records that never start a station** (they may only join one, within 300 m with a strong name
  or 150 m otherwise, and are listed in the report's `not_shown` when they join none): OSM's
  `enrich_only` and `minor_beacon_suspect` elements, records with no name, register listings that
  cover several stations ("Apostle Islands Lighthouses"), and **station buildings**: a name ending
  in a building word (Keeper's Quarters, Oil House, Fog Signal Building, Visitor Center...), or an
  OSM element tagged only `historic=lighthouse` with no light word in its name (OSM marks every
  building of a historic light station so: "Rainshed", "Tram Way"). A station building joins the
  nearest light station within 300 m as a structure (`dwelling`, `fog_signal`, `oil_house`,
  `boathouse` or `other`); a Wikidata keeper's-house item with no light station near starts one.
- **Range lights.** A station with only a front range light and one with only a rear light, of the
  same base name in one region within 3 km and with no other candidate, become one `range_lights`
  station named "<base> Range Lights", its pin on the front light. When Wikidata also has an item
  for the whole range, that item becomes the station and the halves its two structures. Groups with
  two fronts or two rears (Craighill Channel's upper and lower ranges) and lone halves are left
  apart and listed (`range_lights.ambiguous` / `unpaired`).
- **Status** (`station_status`): `replica` when a source says so; `lost` (or `ruins`) when every
  tower is lost (or ruins) and no current map shows one; `active` when OSM shows the light lit
  (seamark light tags), else when Wikidata gives a characteristic and no retirement; `inactive` when
  a source says the light is out; but a Wikidata end date (`possibly_lost`) with no OSM element
  mapping the structure today gives `unknown` with a `status_note` that it may be gone, and is
  listed (`possibly_lost`). Station buildings do not decide the status. OSM wins over Wikidata when
  they disagree on lit or out, with a conflict recorded.
- **Field precedence** (first source with a value wins): name, region, county, kind, structure
  facts (type, material, built, height), light dates, light list numbers, agency, ownership:
  Wikidata > OSM; location and the light as charted (characteristic, focal height, range, fog
  signal): OSM > Wikidata. The name prefers one without Old / New / Original. Registers, events
  (by year and event), photos and links are unions.
- **Out of scope** (kept, `hidden: true` with the reason): a station whose records are all
  `out_of_scope` (Wikidata's faux lighthouse and aerial lighthouse classes). Decorative suspects the
  data does not settle are **not hidden**; the report lists them.
- **Ids**: `<country>-<region>-<slug>`, the slug from the name without "Light", "Lighthouse",
  "Light Station", a leading "Phare de" / "Faro de" ("Faro de Punta Higüero" → `us-pr-punta-higuero`);
  a life-saving station keeps its words (`us-nc-kitty-hawk-life-saving-station`); same-name
  stations in a region are numbered `-2`, `-3` north to south.
- **`data/merge_report.json`** (committed; a human reads it): counts by country, region, kind,
  status, verification and source mix; `hidden`; `range_lights` (paired, ambiguous, unpaired);
  `successive_structures` (stations with more than one tower); `same_source_stations` (two starting
  records of one source in one station); `wikidata_tag_elsewhere`; `possibly_lost`;
  `decorative_suspects` (decorative tags, inland OSM-only lights with no charted light or register,
  or an OSM-only light sharing its name with a registered station elsewhere: Lake Havasu's replicas);
  `possible_duplicates` (two stations of one kind group within 150 m); `related`; `not_shown`.

- **Canada (`pipeline/merge_ca.py`, called from a few marked places in `merge.py`).**
  - *Identifiers join records.* A record that shares a Heritage Lighthouse id, Coast Guard list number,
    Admiralty number, ARLHS number or Lighthouse Friends id with a station already built joins it (within
    5 km when it has a position). Keys that point at two stations are left alone and listed in the run's
    output. A record with no position (the Directory, the staffed list) joins by an identifier, else by a
    unique name in its province; the rest are listed as not shown. After both passes, and again after
    curation, every record that joined nothing gets one more try, so the order of two records of one pass
    never decides a join (a second run changes no file).
  - *Who may start a station.* A record needs a name and a position. A Coast Guard List aid that is not a
    clear lighthouse never starts one. Everything else follows the rules above.
  - *Names and ranges.* For a Canadian record only real opposites (North / South, Front / Rear) keep two
    lights apart on name; a name with nothing in common within 60 m still joins (the Coast Guard's "Toronto
    East Entrance Outer" is Mimico's lighthouse). A possessive `'s` is not the abbreviation of South. A
    rear light joins the station that holds its front even when the same source supplied the front.
    A Wikidata item with no label (`Q135261059`) has no name.
  - *Precedence* (`PRECEDENCE`, ranks inserted by `merge_ca.register`): the Coast Guard list leads the
    charted light (characteristic, heights, range, fog signal); position is OpenStreetMap, the Coast Guard
    list, the heritage lighthouses, Lighthouse Friends, then Wikidata; names Wikidata, OpenStreetMap, the
    heritage designation, Lighthouse Friends, the Coast Guard list, the Directory.
  - *Status.* A designated heritage lighthouse counts as standing. Where the historic structure is gone
    (Lighthouse Friends) and the Coast Guard list still shows a light, the status is `lost` with a note that
    a modern aid took its place.
  - *Curation* (`data/curation_ca.json`; every entry needs a reason; the decisions are in
    `docs/sources/review_2026-10-ca.md`): `rekind`, `join`, `apart`, `hide` (by id, or by record key before
    the station has an id), `rename` (display name only) and `merge_stations` (retires one id with
    `merged_into`; the file stays).
  - *The review file* has a `canada` section (counts by province, status, kind, staffing and access; the
    staffed list and the stations that rest only on the 2010 list; unplaced Directory entries; stations the
    Coast Guard list started; curation entries). What a run did (joins by kind, ambiguous identifiers) is
    printed, not saved.

- **United States, second round (`merge.py`, rules for `country == "US"` records only; Canada's output is
  unchanged).**
  - *Hard keys.* An NRHP number, an ARLHS number, a Light List number (`vol-LLNR`: Wikidata's P3723 and the
    Light List agree on the form) or an `xref` (`lhf:<id>`, which Rowlett's links carry) joins a record to the
    station that holds the same key, within 10 km when both have a position, and in the same state unless the
    key is an NRHP number (a register lists a vessel where it is moored, and a district can cross a state line;
    a Light List or ARLHS number copied into another state's entry is not trusted).
  - *Position-less records* (Rowlett, the passport list, most of the Society's lightship and life-saving
    stations) join by a hard key, else by a name that is strong and unique in their state; the rest wait in the
    extract and show in the report's `not_shown`. Such a record never starts a structure of its own: it
    describes the station as a whole.
  - *A unique namesake a few kilometres off* (a vanished tower pinned far from the station by one source) joins
    when exactly one station of the state and kind has the same name within 10 km. The joins are printed by
    the run, not saved: what a run did differs when it has memory.
  - *Who may start a station.* A record with a name and a position, unless it is enrichment: ENC points, Light
    List entries, HAER records, the Society's minor aids and private (faux) lighthouses and the register's
    batch-derived points (`limited`) join a station and give it facts, never a structure. A scale copy
    (status `replica`, or "(Replica)" in the name) is its own station, joined to an original only on the spot,
    by a hard key or by a decision.
  - *Status.* A Wikidata, ENC or Light List entry is a weak sign that a light is lit: any explicit "inactive"
    or "lost" beats it. A status from a record with no position (Rowlett's) counts only when nothing with a
    position speaks, and is never listed as a conflict.
  - *Fields.* `visit`, `stay` and `access` come from the first source that states them (passport list and
    LighthouseFriends first); the charted light from ENC, then the Light List, then OSM; a register adds an
    entry (`listed`, `nhl`, `nomination`) and an event; location prefers OSM, Wikidata, LighthouseFriends, then
    the Society, whose points are rounded and sometimes wrong.
  - *Decisions* (`pipeline/record_joins.py`, generated from the review in `docs/sources/review_2026-10-us.md`,
    every entry with its reason): records sent to a station (a station id, a record key, or `new:<id>`, which
    starts a station of that id: Old Point Loma), positions found wrong, records kept apart, names, statuses,
    hidden stations, scale copies (`replica_of`) and successive lights (`preceded_by`). Pinned records wait until
    everything else is placed and go in key order; a station whose every record is sent elsewhere is retired
    (`merged_into`, file kept); an id that matches no station is listed under `related.decisions`. The
    DESIGN 3.2 rulings (twin lights one station; Old and New Point Loma two linked stations; scale copies
    `replica`) are applied this way.
  - *Second runs.* Records that joined nothing are tried again after the pins and the range pairing (by hard
    key, then by position and name), so neither the order two records of a pass arrive in nor a run with
    memory decides a join; a run on its own output writes nothing, and the review file is byte for byte the
    same.

First run (2026-10-21): 1,779 stations shown (1,127 US, 652 Canada), 3 hidden (decorative), 1,017
held by both sources (760 joined through an OSM `wikidata=` tag), 376 Wikidata only, 390 OSM only;
1,099 records not shown (701 likely minor beacons, 327 with no name, 39 station buildings with no
station near, 32 seamark lights).

Canada run (2026-10-21, the first build merged again with the six sources of 2.3 and `data/curation_ca.json`):
1,193 Canadian stations shown (652 before; 628 new, 617 of them started by Lighthouse Friends), 74 hidden
(67 of them small modern harbor lights that only OpenStreetMap or the Coast Guard list mention), 16
Canadian ids retired with `merged_into`. By province BC 75, MB 18, NB 137, NL 149, NS 256, NU 10, ON 237,
PE 59, QC 252; by status 697 active, 133 inactive, 301 lost, 16 replica, 1 ruins, 45 unknown. 49 stations
are staffed (44 of them resting only on the 2010 list), 2 destaffed in 2024. A second run changes no file.

United States run (2026-10-21, the build merged again with the eight sources of 2.4, `data/curation_ca.json`
and the decisions of `pipeline/record_joins.py`, reviewed in `docs/sources/review_2026-10-us.md`): 1,432 US
stations shown (1,082 of them already published, 350 new: the Society's archive started 164, LighthouseFriends
162, the NRHP 12, the territories 4, and Wikidata or OpenStreetMap records the decisions moved 8), 20 hidden
(decorative, or in Canada), 26 ids retired with `merged_into`. By status 556 active, 319 inactive, 363 lost, 39
replica, 5 ruins, 150 unknown; by kind 1,121 lighthouses, 158 range lights, 79 pier lights, 52 life-saving
stations, 17 lightships, 4 lightship stations, 1 harbor light. Guam has 2 stations (it had none). The review's
three lists: 50 possible duplicate pairs to 0, 56 possibly lost to 0, 40 decorative suspects to 0 (the Canadian
stations in them are `agent/sources-ca`'s). Not placed: 967 Society places (629 minor aids, 130 lightship
stations, 57 life-saving stations and 117 light stations with no position and no unique name in their state, 33
private (faux) lighthouses), 1,159 Light List and 283 ENC entries with no station near, 645 Rowlett and 115
passport entries that match no station by number or unique name. A second run changes no file and the review
file is byte for byte the same.

### 3.10 What the site loads (`pipeline/build_site_data.py` → `web/public/data/`)

- `stations.geojson`: every visible station as a point (5 dp), short properties (the legend is in
  `meta.json` → `format`): `i` id, `n` name, `r` region, `cc` country when not the US, `c` county, `k`
  kind, `s` status, `v` verification, `a` access level (when known), `sf` staffed / volunteer, `bo` 1
  boat only, `cl` 1 climbable, `sy` 1 somewhere to stay, `tr` 1 tribal land, `rg` 1 on a register, `o`
  other names "|"-joined, `y0` first year lit (or built), `y1` year the light went out or the station
  was lost, `st` 1 has a story, `fh` the light's focal height in metres and `rn` its charted range in
  nautical miles (when recorded; for the map's range rings, 4.1).
- `s/<id>.json`: the canonical record, plus `story_html`, `chapters` (`[{id, title}]` from the story's
  `## ` headings, `pipeline/story_md.py`), `keepers`, `research_sources` and `research` when they
  exist.
- `meta.json`: counts (by status, kind, region, country, country and kind, verification), the regions
  in listing order (states and DC, then the territories, then Canada), the sources with licence,
  credit line, retrieved date and how many stations each supplies, build date, `fixtures`.
- `redirects.json`: `{redirects: {old id: new id}}` for retired stations.
- `s/<id>.json` also carries `archive_roster` (`{count, places: [{name, url, count, lines?}]}`) for a station the
  archive has a roster for: the lines as printed with `person` only where that person has a page, and **no
  lines** when a checked research roster exists (just the count and the place links). A research line's
  `person` is kept only when that person has a page.
- `k/`: the keepers index (`pipeline/keepers.py`, 3.6, 4.2). `index.json` (the manifest: totals, people at more
  than one place, people left out, counts by surname initial, state and role), `stations.json` (the stations a
  person served at, for the station filter), `i/<L>.json` (the search index, one file per surname initial,
  `other.json` for a non-letter; a row is `[id, name, first year, last year, regions, role numbers, station
  numbers]`) and `p/<L>.json` (each person's page data, **read by the prerender and then deleted**: it is not
  published).

---

## 4. Site

Same stack as Firefinder (Vite + TypeScript + MapLibre GL; prerendered static pages per station;
GitHub Pages via Actions; `pipeline/validate.py` gates the build), with Fresnel's own name, palette
and icons. `web/` was copied from Firefinder's and adapted; nothing is imported across the repos.
Pages planned: map (`/`), station pages (`/s/<id>/`), keepers index (`/keepers/`, `/k/<person-id>/`),
vessels (`/v/<id>/`), lens and tower guide (`/guide/`), lessons (`/learn/`), credits and about. The
light at night and the range ring are built like Firefinder's view from the cab (Rust → WebAssembly
where terrain matters, otherwise TypeScript).

**Built (scaffold, 2026-10-21):**

- **Look.** Deep navy header band, lamp amber for lit lights, foam-white pages; a night chart in
  dark mode (prefers-color-scheme plus a light / dark / auto toggle, `fresnel.theme`). Fonts
  bundled with the site (Atkinson Hyperlegible Next, Newsreader). Fresnel-lens logo and favicon.
- **Markers: the shape alone says the status**, colour only repeats it: active, a lit lamp
  (amber sunburst); inactive, a solid unlit silhouette; ruins, a broken stump; **lost, a dashed
  ring with a cross, drawn under every standing station**; moved, the silhouette with an arrow;
  replica, a double outline; unknown, a ring with a question mark. The silhouette says the kind (a
  tower for lights, a ship for lightships and lightship stations, a house for life-saving
  stations).
- **Map** (`/`): all stations, clustered; a **Key** button and panel always on the map (not only in
  the filters); filters by status, kind, country and region, verification, access and staffing,
  climbable, stay, checklist marks; search by name, other names and region; a side panel with the
  facts and a link to the page; deep links (`?s=<id>` selects a station); a count that says what it
  counts; "Go to" jumps (lower 48, Great Lakes, Alaska across the 180th meridian, Hawaii and the
  Pacific territories, Puerto Rico and the Virgin Islands, Canada...). Base map OpenFreeMap
  (keyless), imperial and metric scales.
- **Station page** (`/s/<id>/`): name, kind, status badge (the map's symbol and its words),
  **Unverified** badge; practical first (**Visit, climb and stay**, with a prominent access label for
  private, closed, permission or tribal land, restricted, boat-only and staffed lightstations: "a
  working lightstation, the keepers' home and workplace"; warn, don't hide); a facts card (the light
  with its characteristic read in plain words, "Fl W 4s: one white flash every 4 seconds"; focal
  height; range in nautical miles with km; lens; fog signal; structures with roles, types, materials,
  years and their own status; registers; light list numbers); a timeline; **History** (the story with
  an "In this history" chapter list and footnotes, or a plain line that none is written yet and a
  one-sentence summary labelled as built from the record); **Keepers** (the checked research roster when there is one, else the archive's, each name with a page linked, 3.6);
  photos with credits; where sources disagree; sources and credits (every source of the record with
  its credit line and licence, every link, the research sources); Suggest an edit (a pre-filled
  GitHub issue form, `.github/ISSUE_TEMPLATE/edit.yml`, on holdTheDoorHoid/fresnel); the checklist.
- **Checklist**: visited / climbed / stayed / want to go, in `localStorage` (`fresnel.checklist.v1`)
  with export and import as JSON; a retired id's marks move to the station that took it.
- **Units** (3.3): feet first in the US and its territories, metres first in Canada; nautical miles
  with km for ranges. Region names in full ("Puerto Rico", "Nova Scotia, Canada");
  `web/src/lib/regions.ts` mirrors `pipeline/regions.py`, and a test checks they agree.
- **About** (`/about/`), **Credits** (`/credits/`: every source from `meta.json` with licence, credit
  line and counts; map, software and font credits), a 404 page, a sitemap, redirect pages for
  retired ids. "Sister site: Firefinder" in the header and on About.
- **Extension points**: the station page is an ordered list of section renderers (`SECTIONS` in
  `web/src/render/station.ts`), map layers are `OVERLAYS` in `web/src/map/layers.ts` and map
  controls are in `web/src/map/controls.ts`, so the light at night, wrecks and old charts are one
  addition each.
- **Not built yet**: the "lights lit per year" view, a general mini-map on station pages (the light at
  night has its own, 4.1), vessels, guide and lessons. (The keepers index is 4.2.)
- **Commands** (in `web/`): `npm run data:fixtures` (sample data) or `npm run data` (the real
  stations), `npm run dev -- --port 5194 --strictPort`, `npm run check`, `npm test`, `npm run build`.
  `.github/workflows/pages.yml` runs the pipeline tests, `validate.py`, `build_site_data.py
  --fallback-fixtures --strict`, the website checks, tests and build, and deploys to Pages.

### 4.1 The light at night (built 2026-10-21)

Feature (a) of section 1: the light as it looks from a boat at night, in its real pattern and
colour, at a distance the visitor chooses, with the ring of how far out it could be seen. Plain
TypeScript and a 2D canvas (no terrain is needed at sea). A guide, not a navigation aid: the page
says so once, plainly.

**What the visitor sees.** On every station page with a light, a section *The light at night*,
after the facts:

- A tag naming the era shown ("Today, as charted", "As it was when last lit (the light went out in
  1931)", "From 1883 to 1958"), the characteristic in plain words, and a caution when sources disagree
  on the pattern or the focal height, with a choice between them (about half of the 49 focal-height
  disagreements are one figure written in feet as metres; the page says so).
- The night scene: sky, stars, sea, horizon and the light, flashing in its pattern and colour, with
  its reflection on the water when it is bright. Controls: the distance (a slider, 0.5 nmi to well past
  the farthest it could be seen; it starts at a typical approach, 60 % of the visible range, between
  1 and 10 nmi), the eye height (1, 3, 6, 15, 30 m: kayak, small boat's deck (the default), fishing
  boat's wheelhouse, ship's bridge, large ship's bridge; feet first in the US), the visibility (very
  clear 20 nmi, normal 10 nmi, haze 3 nmi, fog 0.5 nmi), a 7× binocular view, Play / Pause; where the
  record has them, the year (era), which light (front / rear, a passing light), which sector, which
  source's pattern or height. Under it, a live sentence says what the scene shows ("From 25 nmi (46 km)
  away ... the light is below your horizon ... Nothing of it can be seen."). The scene labels a light
  that is too faint to see, below the horizon, in a dark sector, or drawn without a recorded height or
  brightness, instead of quietly drawing or hiding it.
- The **strip diagram** of one period, for everyone: lit spans in the light's colour, darkness in
  night blue, drawn to scale with seconds marked (short periods repeat, paler, to show the rhythm),
  one strip per sector colour or light; a playhead moves along it in step with the scene. Without a
  recorded period the strip has no time scale and says so.
- *Recorded, and drawn by convention*: every duration that is a convention, in words; *Not recorded*:
  what is missing (pattern, focal height, range) and what that stops the page from working out.
- *How far out it can be seen* from a small boat's deck and from a ship's bridge, which limit applies
  (the horizon or the brightness), and a mini-map (MapLibre, loaded only when it scrolls into view)
  with the ring for the chosen eye height and visibility and a dotted ring at the chosen distance.
- *How this view is worked out*: the assumptions below, in plain words, with this light's numbers.
- On the map: an optional layer, **Light ranges** (a chip in the status bar; `&reach=<eye m>` in the
  URL), a ring round every light the filters show, so several together show how the lights covered a
  coast; amber for lights lit today, grey and dashed for lights out, lost or of unknown status, as last
  recorded. The map's side panel has the reach from a small boat's deck in one line.

**Reading the characteristic** (`web/src/lib/characteristic.ts`). IALA / USCG Light List / CCG
notation: F, Fl, LFl, Oc, Iso, Q, VQ, UQ, IQ, IVQ, IUQ, Mo(X), F Fl, groups `(2)` and composite groups
`(2+1)`, `Gp`, `Q(6)+LFl`, `Al` alternating colours, colours W R G Y Bu Or (several letters without
`Al` are sectors), the period. And the forms the records really use: dots, commas, `FL`, `FI` (a
capital i), `L Fl`, `Alt`, `QF` (old "quick flashing"), "4 sec", minutes; `FF` (French *feu fixe*);
words ("fixed white varied by a flash every 90 seconds", "flashing W 2.5s", "5 s R flash", "28 s on,
2 s off", "Alternating R and G 24 s (R 12s, G 12s)", "Fl alternately R and W, interval between Fl
10s", "continuous revolving W with a 90 s interval", "Feu fixe d'alignement"); sector clauses ("R
sector", "with two R sectors", "R sector 045° to 135°", "dark sector", "obscured from 158° to 318°",
"avec F W (secteur)"); several lights in one record ("F R (rear); F W (front)", "F G (along range
line)<br>Fl W 4s (passing light)"); dates and eras ("F W (original); Fl W ... (current)", "F R
(initially F W)", "F W (1901)", "(c1965)", "(as of 1941)"); notes kept as notes (an emergency light,
"visible on range line only"); and two artefacts of an upstream "red" → "R" replacement ("obscuR",
"Ruced"). Every decision is said in words on the page (`FF` read as feu fixe; a period with no unit
read as seconds; a fixed light given a period drawn steady, with a warning; `Al WR 10s` with no type
word drawn as alternating flashes, as most US and Canadian alternating lights are rotating beacons).
Anything else is left unread and shown as the source writes it. **On 2026-10-21: 1,141 of the 1,148
stations with a characteristic are read** (243 of 248 distinct strings); the 7 left are not patterns
("inactive" ×2, "R" ×2, "decorative light", "current decorative light") or alternating with one
colour ("Al W 10s"). One read pattern cannot be drawn: "Fl(6) W 1s" (six flashes do not fit in one
second; the page says the record may be miswritten). `web/test/characteristic.test.ts` reads every
real string in `data/stations/` and fails if that list changes.

**Durations by convention** (`web/src/lib/pattern.ts`, within IALA R0110's limits and the Light
List's rates): flash 0.5 s (a quarter of the period when that is shorter); 1 s between the flashes of
a group of two, 1.5 s for three or more, twice that between the parts of a composite group, the dark
after the group at least three times the gap (scaled down to fit a short period); long flash 2 s;
occulting eclipse a quarter of the period, at most 2 s (1 s eclipses with 1 s of light in a group);
isophase half and half; quick 60 a minute (the US Light List rate; IALA 50 to 79), very quick 120,
ultra-quick 160, each flash 0.3 of its cycle; interrupted quick: quick flashes for three quarters of
the period; Morse short 0.5 s, long 1.5 s, 0.5 s between; fixed-and-flashing: the steady light at 40 %;
alternating colours evenly spaced (or as recorded), one colour per part of a composite group; no
period: one is chosen only to show the rhythm (5 s for a flash) and the strip has no time scale; no
colour: drawn white, said. A duration the record gives is used as given.

**Physics** (`web/src/lib/sighting.ts`):

- *Geographic range* D = 2.08 × (√H + √h) nmi (H focal height, h eye height, metres; standard
  refraction, the Light List's and Bowditch's factor). The scene's vertical angles use the same
  refraction, as a sphere of effective radius R' = (2.08 × 1852)² / 2 ≈ 7,420 km: the light's angle
  above the eye's horizontal is (H − h)/d − d/2R', the horizon's dip √(2h/R'), so the light meets the
  horizon exactly at D. Within 0.3 nmi of D it is "dipping".
- *Luminous range*: Allard's law, E = I·T^d / d², with T = 0.05^(1/V) per nmi (Koschmieder's 5 %
  contrast, V the meteorological visibility), and the threshold implied by the charted range: a light
  of nominal range Rn is just visible at Rn when V = 10 nmi (IALA's definition of nominal range). So
  brightness over threshold = (Rn/d)² × 0.05^(d/V − Rn/10). The intensity and the threshold (0.2 µlux)
  cancel. The charted `range_nm` is taken as the nominal range.
- *Visible range* = the smaller of the two; it is the ring on both maps.
- *Loom*: shown for a light whose charted range is 18 nmi or more, below the horizon but within its
  luminous range (bright enough, only the horizon in the way), fading from the horizon distance to the
  luminous range, pulsing with the flashes. A sketch, labelled.
- *The picture*: a moonless night; naked-eye view 40° wide, binoculars 7° (a 7×50 marine glass);
  brightness drawn on a logarithmic scale (core and glow grow with log₁₀ of the brightness over
  threshold), with a haze or fog halo. A screen cannot show glare, so the page says a near light looks
  dimmer than in life and a faint one plainer.

**Missing data.** No pattern: the scene shows where the light would be, labelled, and the ranges.
No focal height: no horizon limit; the light is drawn on the horizon line, labelled, and the range is
"if the horizon does not hide it first". No charted range: no brightness; it is drawn at a middling
brightness, labelled, and the range is the horizon "however bright it is". Neither: distance, eye and
weather controls are hidden, and the scene shows the pattern only. Nothing at all: one sentence and an
invitation to suggest an edit. Life-saving stations have no section.

**Past lights** (`web/src/lib/light-history.ts`). Eras come from `characteristic_changed` events
(3.4), else from dates and era words in the characteristic itself, else one era: today, as charted;
or, for a light that is out or gone, *as it was when last lit*; or, for status unknown, *as last
recorded (whether it is still lit is not known)*. An era uses its own height and range where
recorded; an earlier era borrows today's focal height (said on the page) but never today's range, so
its brightness is "not recorded" unless the event gives it. On 2026-10-21 no station has a
`characteristic_changed` event yet; three have eras written into the characteristic (Marcus Hook
Range, Craighill Channel Upper Range Front, Fishing Battery), and the sample
station `us-me-example-head` has two events, to exercise the year selector.

**Motion and accessibility.** The scene plays by itself only when the visitor has not asked for
reduced motion and the light comes on no more than three times in any second; otherwise it shows a
still frame and the strip, with Play. Pause is always there; the scene stops when off screen or in a
hidden tab. The canvas is decorative (`aria-hidden`); the live sentence (`role=status`) and the strip
(an SVG with a title listing every phase) carry the same information. The scene is dark in both
themes (it is night); the page around it follows the theme.

**Limits, for later.** Sector bearings are rarely recorded (the visitor picks the sector);
`fetch_osm.py` keeps only an OSM light's first sector in the station record, so OSM sector lights
read as single-colour lights. The rings ignore land (headlands, hills, the light's arc of
visibility). Range lights show one light at a time, not the pair in line. Old ranges in some records
may be geographic rather than nominal; nothing marks them.

**Files.** `web/src/lib/characteristic.ts` (reading), `pattern.ts` (timing), `sighting.ts` (physics,
eye heights, visibility, rings), `light-history.ts` (eras); `web/src/render/night.ts` (the section and
the live sentence), `render/strip.ts` (the strip); `web/src/ui/night.ts` (scene and controls),
`ui/night-map.ts` (mini-map); `web/src/map/reach.ts` (map layer and control). Tests:
`web/test/characteristic.test.ts`, `web/test/night.test.ts`.

### 4.2 The keepers index (built 2026-10-21)

Feature (b) of section 1. The data and the rules are 3.6; this is what the site does with them.

- **`/keepers/`** (header link "Keepers"). The page is prerendered: the counts, a plain explanation (where the
  names come from, that two people are never joined by name, what "possibly the same person as" means, who is
  left out and why, that Canada has no keepers here yet), the form's frame and the A to Z letters with their
  counts. The script then loads the index **lazily, one file per surname initial** (up to 109 KB, 33 KB
  gzipped; 1.1 MB in all, 0.35 MB gzipped): a typed name reads the chunk of each word's initial (a surname
  is one of them); a single word searches surnames beginning with it, with a link to **search first names
  too** (reads every chunk); a letter reads one chunk; a state, role or station filter without a name reads
  every chunk (about 0.35 MB gzipped, once). The station filter's list (`k/stations.json`, 14 KB gzipped) is read
  when the field is focused. Search by name (every typed word must begin a word of the name), filter by state or
  territory, role and station (a text field with a list; a name two stations share also shows its id), counts
  ("N people found; showing the first 100"), **Show more**; the search is kept in the address
  (`?q=strout&state=ME&role=head keeper&station=us-me-portland-head&l=S&all=1`) so it can be shared. Without
  JavaScript the form stays hidden and a notice says so; every station page still lists its keepers, linked.
  The logic is `web/src/lib/people.ts` (pure, tested, and tested against `pipeline/keepers.py` for the name
  folding and the letters); the DOM is `src/pages/keepers.ts`.
- **`/k/<person-id>/`**, prerendered like a station page (`person.html`, 16,884 pages, 8 to 27 KB each, median
  8.7 KB or 3 KB gzipped; the prerender takes about 15 s for all 19,500 pages). Header: the name, "Listed at 3 places in Maine and New
  Hampshire, 1861–1878." Sections: **Where they served** (a table: station, role, years as printed, source of
  each stint: "Archive" with the archive place linked, or "Checked" with the research source numbers linked to
  the station's list), **Possibly the same person** (only when there is a hint), **In the histories** (the
  stations' written histories where they served, adding "The history mentions the name “Jane Doe”" only when
  the history's text contains it: whole-name match, never part of a longer name; a common name may be another
  person, so it says "the name"), **Sources and credits** (the archive's sentence, the archive's
  own person page linked, "two records with the same name are never joined", the credit line), and **Suggest a
  correction** (the edit form on GitHub, filled in). A stint at a place not on the map names the archive's place
  with a link and says "Not linked to a station page". The page never shows a race or sex, and a sample (fixture)
  person's page is `noindex` and left out of the sitemap.
- **Station pages** show the archive's roster as 3.6 says; the section appears for a lightship station too when it
  has one. A station with neither roster says so plainly and offers "Tell us".
- **Sitemap and prerender.** `scripts/prerender.ts` writes the index page's body and one page per person from
  `dist/data/k/p/<L>.json`, deletes those files, and adds every non-sample person to `sitemap.xml` (19,513
  addresses in all, well under the 50,000 limit). `person.html` and `keepers/index.html` are Vite entries.
- **Size.** The built site is 260 MB (keeper pages 153 MB, station pages 89 MB, the data 15 MB); the largest
  station page (Cape Ann, 200 lines of keepers) is 125 KB, 17 KB gzipped.
- Tests: `web/test/people.test.ts` (names, search logic, the pages from the fixtures: grouping, hints, research
  joins, the cut-off, escaping), `pipeline/test_keepers.py` (the rules and the committed files);
  `web/fixtures/people`, `rosters` and `people_report.json` are invented people at the invented stations.

---

## 5. Stories

Written by research agents following `research/STORY_GUIDE.md` (to be written from Firefinder's
guide after the source survey, with the decisions above). What differs from Firefinder:

- **Chapters with headings** (`## The place`, `## Building the light`, `## The keepers`,
  `## Storms, wrecks and rescues`, `## After the keepers`, `## Today`), used only when there is
  sourced material for them; a thin story may be one or two chapters.
- **The keepers chapter** tells the people: who they were, where they came from when the sources say,
  how long they stayed, what happened to them there. The roster table is generated from the research
  JSON, not written by hand in the prose.
- **Atmosphere** follows section 1 exactly: sourced scene details, and general period context only
  when marked as general and cited.
- **Evidence quotes** for every footnoted sentence, machine-checked against cached sources, as in
  Firefinder (`check_quotes.py`).
- **Tone:** warm, concrete, plain English; vivid because the sources are vivid, not because of
  adjectives. No "nestled", no "breathtaking", no "stalwart sentinel", no "beacon of hope".

---

## 6. Process

- Agents work in their own worktrees (`~/Desktop/fresnel-wt/<name>`, branch `agent/<name>`); the
  orchestrator merges to `main` and pushes. Never commit `data/raw/`.
- Subagents: Opus for hard engineering, Sonnet for routine work and research; story batches use the
  writer the owner picks after the pilot.
- Firefinder's pipeline and web code are the starting point: copy and adapt, do not import across
  repos (the two sites must build independently).
