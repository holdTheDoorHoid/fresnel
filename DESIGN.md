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

The source survey (2026-10-21, `docs/sources/survey_*.md`) fills this table. Leads to check:

| Kind | Leads |
|---|---|
| Open, bulk | Wikidata (CC0; ~990 US and ~490 Canadian lighthouses, ~500 with NRHP ids), OpenStreetMap `man_made=lighthouse` (ODbL), NOAA ENC `LIGHTS` objects (public domain: characteristic, period, height, range of active lights), the USCG Light List, the Canadian Coast Guard List of Lights, the NPS National Register dataset, Parks Canada's heritage lighthouses (Heritage Lighthouse Protection Act), the Canadian Register of Historic Places |
| Public-domain history | USCG Historian's Office station histories and lightship lists; the NPS Maritime Heritage Program's inventory of historic light stations; the Lighthouse Board (1852–1910) and Commissioner of Lighthouses (1911–39) annual reports and the Lighthouse Service Bulletin (HathiTrust / Google Books / Internet Archive); the US Life-Saving Service annual reports (1876–1914, wreck-by-wreck); NRHP nomination forms (NPGallery); HABS/HAER (Library of Congress); Chronicling America; NARA RG 26 keeper registers (M1373 and later) |
| Canadian history | Department of Marine and Fisheries / Marine annual reports in the Sessional Papers (Canadiana; they list keepers and salaries), Library and Archives Canada, provincial archives, the Nova Scotia Lighthouse Preservation Society, BAnQ and the RPCQ for Quebec |
| Community sites (facts only) | LighthouseFriends.com (histories and keeper lists), Russ Rowlett's Lighthouse Directory (worldwide, lost lights included, ARLHS numbers), Lighthouse Digest (the Doomsday List of endangered lights), the US Lighthouse Society (passport stamps, rentals, keeper programs), regional conservancies and Friends groups |
| Wrecks | NOAA's wrecks and obstructions data (AWOIS and ENC `WRECKS`), public domain; the Life-Saving Service reports for the rescues |
| Charts | NOAA Office of Coast Survey Historical Map & Chart Collection; NOAA's current chart display service (both public domain); Canadian historical charts if licensable |

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
```

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
- `ownership`, `access.level`, `verification`: as in Firefinder.
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

### 3.7 Wrecks

A wreck layer from NOAA's public-domain wreck data, near each station within a set radius, shown on
the map and listed on the page ("Recorded wrecks within 5 nm"). The stories' rescue accounts are
events (`wreck`, `rescue`) with sources. Positions of wrecks are shown as NOAA publishes them.

---

## 4. Site

Same stack and look as Firefinder (Vite + TypeScript + MapLibre; prerendered static pages per
station; GitHub Pages via Actions; `pipeline/validate.py` gates the build), with Fresnel's own name,
palette and icons. Pages: map (`/`), station pages (`/s/<id>/`), keepers index (`/keepers/`,
`/k/<person-id>/`), vessels (`/v/<id>/`), lens and tower guide (`/guide/`), lessons (`/learn/`),
"can't place yet" lists, credits and about. The light at night and the range ring are built like
Firefinder's view from the cab (Rust → WebAssembly where terrain matters, otherwise TypeScript).

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
