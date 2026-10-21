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
| Writer | Pilot first: the same handful of stations researched once and written by **both Haiku and Sonnet**, shown to the owner side by side; the owner picks the writer for the big run. Then batches, as in Firefinder. |
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
- **Skipped because robots.txt names Anthropic's crawlers** (ClaudeBot, anthropic-ai, Claude-Web):
  BAnQ numérique, Nauticapedia. Canadiana disallows the same names, and its `/search` and `/file`
  paths for every agent, so it is skipped too. The owner may overrule (in Firefinder the owner kept a
  source whose robots.txt named AI crawlers).
- **Retired pages through the Wayback Machine: allowed.** A page its publisher has taken down (the
  NPS light-station inventory, old Tripod sites) may be read from the Internet Archive and cited with
  both the original URL and the archive URL.
- **Live but blocked pages through the Wayback Machine: OWNER'S CALL, on hold.** The USCG Historian's
  site (public-domain federal histories: station pages with keeper lists, the Lightship Station Index)
  answers 403 to our requests. The territories survey read 292 archived copies of its pages. Until the
  owner decides, no fetcher is built on them and no story cites them.
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
  people/<id>.json          one record per keeper or crew member in the keepers index (3.6)
  stories/<id>.md           the researched long-form story with footnotes (section 5)
  research/<id>.json        that research's facts, events, keepers, evidence, sources, fact-check
  photos_manifest.json      mirror output (as in Firefinder); files served from fresnel-photos
  raw/                      crawl cache, git-ignored
  vocab.json                controlled vocabularies (3.4)
  merge_report.json         pipeline/merge.py's review file (3.9); committed
```

Built so far: `sources/`, `stations/`, `merge_report.json`, `vocab.json`. `vessels/`, `people/`,
`stories/`, `research/` and `photos_manifest.json` come with later rounds; the site already renders
a story and a keepers roster when they exist (`web/fixtures/` has one of each).

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
- `staffing`: `automated` with `as_of` when a source dates the automation; otherwise `unknown`
  (the staffed Canadian lightstations need their own list: a later source, 2.2).
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
  in a chosen year.
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
shown on the station page and feeds `data/people/<id>.json`, one page per person, listing every
station they served and linking the stories that mention them.

- **Never join two people by name alone.** Two roster lines become one person only when a source
  connects them (a transfer "from Portland Head to Cape Elizabeth", the same birth date, a family
  history that follows one person through both stations). Same name, no link: two people, and the
  pages say "possibly the same person as…" when the years and places fit.
- Family keepers (spouses, children who kept the light) are listed in their own right, with the role
  the source gives ("acting keeper", "assistant", "kept the light after her husband's death").
- **Living people:** keepers, owners and volunteers who may be alive (roughly anyone whose service
  ended after 1960) are named only as published sources name them, in their public role, with no
  personal details beyond what those sources print. Private residents of converted lighthouses are
  not named unless they present themselves publicly (an inn's owners).

**Roster shape** (`data/research/<id>.json` → `keepers`, rendered as the station page's Keepers
table; `research/STORY_GUIDE.md` has the research rules):

```json
"keepers": [
  {"name": "Joseph Greenleaf", "role": "keeper", "from": 1791, "to": 1795, "note": "First keeper", "cite": [2]},
  {"name": "Joshua F. Strout", "role": "head keeper", "from": 1869, "to": 1904, "cite": [2, 4],
   "from_approx": false, "other_stations": [{"name": "…", "from": 1860, "to": 1869, "cite": [4]}]}
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
- `person`, `other_stations`: for the keepers index (later).

`pipeline/validate.py` rejects a roster line without a name, with a malformed year, or citing a
number the file's sources do not have. `pipeline/build_site_data.py` copies the roster and the
research sources into `s/<id>.json` as `keepers` and `research_sources`.

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
`wikidata` (an OSM element's `wikidata=` tag).

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

First run (2026-10-21): 1,779 stations shown (1,127 US, 652 Canada), 3 hidden (decorative), 1,017
held by both sources (760 joined through an OSM `wikidata=` tag), 376 Wikidata only, 390 OSM only;
1,099 records not shown (701 likely minor beacons, 327 with no name, 39 station buildings with no
station near, 32 seamark lights).

### 3.10 What the site loads (`pipeline/build_site_data.py` → `web/public/data/`)

- `stations.geojson`: every visible station as a point (5 dp), short properties (the legend is in
  `meta.json` → `format`): `i` id, `n` name, `r` region, `cc` country when not the US, `c` county, `k`
  kind, `s` status, `v` verification, `a` access level (when known), `sf` staffed / volunteer, `bo` 1
  boat only, `cl` 1 climbable, `sy` 1 somewhere to stay, `tr` 1 tribal land, `rg` 1 on a register, `o`
  other names "|"-joined, `y0` first year lit (or built), `y1` year the light went out or the station
  was lost, `st` 1 has a story.
- `s/<id>.json`: the canonical record, plus `story_html`, `chapters` (`[{id, title}]` from the story's
  `## ` headings, `pipeline/story_md.py`), `keepers`, `research_sources` and `research` when they
  exist.
- `meta.json`: counts (by status, kind, region, country, country and kind, verification), the regions
  in listing order (states and DC, then the territories, then Canada), the sources with licence,
  credit line, retrieved date and how many stations each supplies, build date, `fixtures`.
- `redirects.json`: `{redirects: {old id: new id}}` for retired stations.

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
  one-sentence summary labelled as built from the record); **Keepers** (the roster table, 3.6);
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
- **Not built yet**: the "lights lit per year" view, a mini-map on station pages, the keepers index,
  vessels, guide and lessons.
- **Commands** (in `web/`): `npm run data:fixtures` (sample data) or `npm run data` (the real
  stations), `npm run dev -- --port 5194 --strictPort`, `npm run check`, `npm test`, `npm run build`.
  `.github/workflows/pages.yml` runs the pipeline tests, `validate.py`, `build_site_data.py
  --fallback-fixtures --strict`, the website checks, tests and build, and deploys to Pages.

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
