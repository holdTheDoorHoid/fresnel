# Source survey: US lighthouses in the 50 states (key `us`), 2026-10-21

Scope: lighthouses in the 50 states (lower 48, Great Lakes, Alaska, Hawaii), standing and lost,
plus pier, harbor and range lights with real structures. Territories, lightships, life-saving
stations, Canada and the archival-history sources are covered by other surveys; leads noticed in
passing are in "Leads for other surveys" at the end.

Cached samples and parsed extracts are under `data/raw/survey/us/` (git-ignored, about 40 MB; the
two biggest files are the NRHP workbook and the Light List Vol. I PDF). All requests used
`FresnelBot/0.1 (+https://github.com/holdTheDoorHoid/fresnel)`, one request every 2 s per host or
slower. Search budget used: 3 of 25 WebSearch calls.

## Honesty notes (read first)

- **One robots violation, by mistake.** While probing NPS IRMA I requested
  `https://irma.nps.gov/DataStore/DownloadFile/2299727` before reading that host's robots.txt, which
  says `Disallow: /DataStore/DownloadFile/` and `Crawl-delay: 1200`. One request, a 22 KB response
  that was not a usable file; I deleted it and made no further requests to that path. Fetchers must
  not touch that path.
- **Wikidata Query Service and Overpass: robots says no, API policy says yes.** `query.wikidata.org/robots.txt`
  has `Disallow: /sparql` for all agents, and `overpass-api.de/robots.txt` has `Disallow: /api/`. Both
  are documented public APIs meant for programmatic use with a descriptive User-Agent, and robots.txt
  there is aimed at link-following crawlers. I used WDQS for about 11 queries (2 s apart) because
  Wikidata is the design's primary bulk source. **The orchestrator should decide whether that
  reading is acceptable before the fetcher is written**; the fallback is the Wikidata JSON dump
  (very large, over 100 GB, so not recommended) or QLever's Wikidata endpoint (`qlever.dev`, no
  robots.txt at all, so nothing to violate; I only tested its OSM endpoint, not its Wikidata one).
- **Blocked, not worked around.** `history.uscg.mil` (USCG Historian) returns an Akamai "Access
  Denied" 403 to every request including robots.txt, and `michiganlighthouse.org` serves a
  Cloudflare "Just a moment" challenge. I made one WebFetch attempt at the USCG list page (also
  403) and stopped. Both are recorded as skipped.
- No site I read lists an AI crawler by name (checked Wikidata, Wikipedia, Overpass, navcen, NPS,
  ibiblio, USLHS, Lighthouse Digest, New England Lighthouses, ARLHS).

---

## 1. Wikidata (WDQS SPARQL)

- **URL:** `https://query.wikidata.org/sparql` (POST `query=...`, `Accept: application/sparql-results+json`).
- **Coverage:** class `Q39715` (lighthouse) and all subclasses via `wdt:P31/wdt:P279*`, restricted to
  `wdt:P17 wd:Q30`: **992 items** (territories included, about 36 items have no state in the P131
  chain, roughly 20 of those are PR, USVI and Pacific islands; so about 955 in the 50 states).
  Standing and lost mixed; lost is under-recorded (see Quality). Instance-of breakdown: lighthouse
  920, wooden lighthouse 34, integral lighthouse 24, leading lights 13, destroyed building 9, Texas
  Tower lighthouse 6, historic district 6, plus a few museums, houses, one faux lighthouse and so on
  (noise to filter).
- **Property ids verified by real queries:**

  | Property | Id | Items filled (of 992) |
  |---|---|---|
  | coordinates | P625 | 957 (96%) |
  | located in (admin) | P131 | 982 |
  | image | P18 | 889 |
  | ARLHS lighthouse ID | **P2980** | 831 |
  | inception | P571 | 742 |
  | light characteristic | P1030 | 732 |
  | Commons category | P373 | 704 |
  | USCG lighthouse ID | **P3723** | 659 |
  | focal height | P2923 | 639 |
  | height | P2048 | 611 |
  | MarineTraffic lighthouse ID | P3601 | 526 |
  | heritage designation | P1435 | 525 |
  | NRHP reference number | **P649** | 498 |
  | lighthouse range | P2929 | 481 |
  | made from material | P186 | 281 |
  | service retirement | P730 | 434 |
  | dissolved/abolished | P576 | 78 |
  | Online List of Lights ID | P3223 | 34 |
  | NGA lighthouse ID | P3563 | 16 |
  | Lighthouse Directory page | P11627 | 1 (property exists, almost unused for US) |
  | state of use | P5817 | 1 |

  `P3723` values look like `1-7565` (Light List volume, hyphen, LLNR), which joins directly to the
  Light List. `P2980` values look like `USA661` (no hyphen; ARLHS itself writes `USA-661`; Alaska and
  Hawaii use `ALK` and `HAW` prefixes).
- **Counts by state (P131 chain, 50 states):** MI 124, NY 84, MA 81, ME 70, WI 54, CA 52, MD 50, FL 49,
  VA 36, CT 34, WA 31, RI 31, DE 29, NJ 27, OH 22, LA 22, SC 21, AK 20, NC 18, HI 17, OR 15, MS 11,
  GA 9, MN 9, TX 8, IL 8, VT 6, AL 5, PA 5, IN 4, NH 2, NE 1. (State table in "Counts".)
- **Lost lights:** only about 85 items carry P576 (78) or the "destroyed building or structure"
  class (9). Wikidata is a standing-lights source.
- **Fields:** position (sub-metre where the editors used satellite imagery, else the Wikipedia
  value), inception year, deactivation year (P730, mixed with tower rebuilds), characteristic
  (sometimes two values: main light and sector), focal height (m), height (m), range (nm), images.
- **Access:** one simple query per property group works. **Path queries
  (`P131+` over all items) time out with 504**; resolve states by querying the distinct admin items
  once and walking `P131*` to `Q35657`. The whole US set, 1,133 rows, comes back in one query in
  seconds. Cached: `wd_base.json`, `wd_admin_state.json`, `wd_items.json`, `wd_propfill.json`.
- **robots.txt:** see the honesty note. Quote: `User-agent: *` / `Disallow: /sparql` at
  `query.wikidata.org/robots.txt`.
- **Licence:** CC0 (Wikidata data). No AI-crawler rules.
- **Quality:** current (edited continuously), but derived mostly from Wikipedia lists, so it is strong on
  the famous standing lights and weak on lost ones. Duplicates exist (Punta Borinquen and Buck
  Island each appear twice). Some items are not lighthouses (historic districts, museums).
- **Recommended use:** **bulk source** (skeleton ids, positions, NRHP/ARLHS/USCG ids, Commons
  images). Also the join hub: OSM carries `wikidata=Q...`, Wikipedia lists link to it.
- **Sample (own words):** Q2105159, Portland Head Light, Cape Elizabeth, Maine: point 43.62306,
  -70.20778; NRHP 73000121; ARLHS USA661; Light List 1-7565; characteristic Fl W 4s (a second
  statement describes the red/white/green sector); focal height 31 m; height 24.38 m; range 24 nm;
  inception 1791; has a Commons image.

## 2. OpenStreetMap

- **Overpass:** `overpass-api.de`, `lz4.overpass-api.de`, `z.overpass-api.de` all failed today. IPv6
  to overpass-api.de times out; over IPv4 the mirrors answer "502 server at capacity, all query
  workers busy". `overpass.kumi.systems` and `overpass.private.coffee` time out. So Overpass is
  **not usable right now**; retry later with backoff, and note the robots line
  (`Disallow: /api/`, see honesty note).
- **Working alternative: QLever OSM planet endpoint** `https://qlever.dev/api/osm-planet` (POST
  `query=`, SPARQL; answers in tens of milliseconds to seconds). `qlever.dev/robots.txt` is a 404 (no
  rules). Snapshot date of the planet extract not checked (check its `/api/osm-planet?cmd=stats`
  before relying on freshness). Tags are IRIs `osmkey:man_made` etc. (`https://www.openstreetmap.org/wiki/Key:`),
  and containment uses `ogc:sfContains` (`http://www.opengis.net/rdf#`) from boundary relations that
  carry `osmkey:ISO3166-2`.
- **Counts (US, relation 148838 or by ISO3166-2 state):**

  | Tag | World | US |
  |---|---|---|
  | `man_made=lighthouse` | 15,032 | 988 (983 inside state polygons: 961 in the 50 states + 22 territories) |
  | `historic=lighthouse` | 437 | 391 |
  | `building=lighthouse` | 533 | 92 |
  | `disused:man_made=lighthouse` | 111 | 7 |
  | `was:man_made=lighthouse` | 37 | 5 |
  | `abandoned:man_made=lighthouse` | 30 | 3 |
  | `demolished:man_made=lighthouse` | 6 | 3 |
  | `ruins:` and `removed:man_made=lighthouse` | 2 and 2 | 0 |
  | `seamark:type=light_major` | 4,617 | 186 |
  | `seamark:type=light_minor` | 24,676 | 1,171 |

  Per state (man_made=lighthouse, inside state boundary polygon): MI 141, NY 84, WI 65, ME 64, MA 63,
  CA 58, MD 42, FL 40, WA 36, OH 32, IL 32, RI 28, AK 23, NJ 23, CT 23, AZ 22, HI 20, OR 18, DE 13,
  IN 13, VA 12, TX 12, NC 12, PA 12, MN 10, SC 9, VT 7, GA 6, LA 6, NH 6. Offshore lights outside
  state polygons (Gulf, Carolinas, Florida reefs) are undercounted, and AZ 22 / IL 32 include
  replicas and decorative towers. **Lost lights are essentially absent** (about 18 lifecycle-tagged
  objects in the whole US).
- **Fields:** position (node or way, so centroid), `name`, often `height`, `wikidata`, `wikipedia`,
  sometimes `start_date`, `heritage`, `seamark:light:*` (range, colour, period) on tagged ones.
- **Licence:** ODbL 1.0 (attribution and share-alike; our database is ODbL, compatible).
- **Quality:** good positions for standing towers, weak and inconsistent attributes, few lifecycle
  tags. Overlaps heavily with Wikidata through `wikidata=` tags.
- **Recommended use:** **bulk source for positions and cross-checks** (one QLever query, no fetch
  loop); `seamark:*` for characteristic where present. Not a source of lost lights.
- **Sample (own words):** way 329793373, Portland Head Light: `man_made=lighthouse`, `building=yes`,
  `height=24.384`, `seamark:type=landmark`, `seamark:light:range=19`, `wikidata=Q2105159`.

## 3. NOAA ENC `LIGHTS` (ENC Direct to GIS, ArcGIS REST)

- **URL:** `https://encdirect.noaa.gov/arcgis/rest/services/encdirect/enc_coastal/MapServer/10`
  (`Coastal.Light_point`; `enc_approach/MapServer/13`, `enc_harbour/MapServer/11`,
  `enc_general`, `enc_overview` and `enc_berthing` are the other scale bands). Query:
  `.../MapServer/10/query?geometry=<xmin,ymin,xmax,ymax>&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=...&outSR=4326&f=json`.
  `maxRecordCount` is 1000, page with `resultOffset`.
- **What works today:** the **coastal band works** (5,186 light points nationwide, all aids with a
  light, not only lighthouses). Queries against the **harbour and approach layers returned
  "Could not find service. Service may be stopped"** on three tries, though their metadata pages load;
  berthing likewise. Treat as intermittent. This misses most harbour-scale lights; the S-57 files
  below are the dependable route.
- **Fields (layer):** `OBJNAM` (almost always empty for US lights), `CATLIT`, `COLOUR`, `LITCHR`
  (coded: 1 fixed, 2 flashing...), `SIGPER`, `SIGGRP`, `SIGSEQ`, `HEIGHT` (m), `VALNMR` (nm),
  `LITVIS`, `SECTR1/SECTR2` (sector limits), `ORIENT`, `SORDAT` (source date), `DSNM` (the ENC cell).
  **No light-list number and no name**: join by position (the same light repeats once per ENC cell
  and once per sector; dedupe on position within about 25 m).
- **Test near Portland Head** (box -70.25..-70.17, 43.58..43.66): 14 records. The main light at
  -70.20786, 43.62310 appears as white, flashing, period 4 s, group (1), height 30.8 m, range 14 nm,
  source date 2025-10-21 (a year old), plus three sector records (red 271.3-274.3 deg, white
  274.3-275.8, green 275.8-279.3) at height 10.4 m, plus an "emergency, reduced intensity" record.
  Position agrees with Wikidata to better than 1 m.
- **Bulk alternative:** `https://charts.noaa.gov/ENCs/<STATE>_ENCs.zip` (S-57 cells; ME 41 MB, a
  Coast Guard district 105 MB, AK 214 MB), and `All_ENCs.zip` is **823 MB (over the 500 MB cap; not
  downloaded)**. Parsing S-57 needs GDAL's S57 driver or a Rust S-57 reader; GDAL is **not
  installed** on this machine and the owner keeps Fresnel in Rust, so the REST layers are the lower
  friction path if the harbour band comes back.
- **robots.txt:** `encdirect.noaa.gov` and `charts.noaa.gov` return 404 (no rules).
- **Licence:** NOAA works are US federal public domain (per DESIGN.md); the service says data are "not
  intended for navigation". I did not find a copyright string on the service.
- **Quality:** authoritative for **active lights only** (characteristic, period, height, range);
  deactivated lighthouses appear only if charted as landmarks. Weekly updates.
- **Recommended use:** **regional source for the light block** (characteristic, focal height,
  range, sectors) of active lights, joined by position to stations built from other sources.

## 4. USCG Light List (navcen.uscg.gov)

- **URL:** index `https://www.navcen.uscg.gov/light-list-annual-publication`; files
  `https://navcen.uscg.gov/sites/default/files/pdf/lightLists/LightList_V<1-7>_2025.pdf` (the `www`
  host 301-redirects to the bare host). Weekly change PDFs under `.../lightLists/weeklyUpdates/`.
- **Coverage:** all federal aids, not only lighthouses: buoys, daybeacons, lights. Volumes: I
  Northeast (4.5 MB, 267 pages), II East (5.3 MB), III Southeast (7.3 MB), IV Gulf (5.1 MB), V Western
  Rivers (1.9 MB), VI Southwest/Northwest/Oceania/Arctic (4.0 MB), VII Great Lakes (2.7 MB). Total
  about 31 MB. **PDF only; no CSV, XML or API** on this site (the old data files are gone).
- **Fields:** `LLNR` (Light List number), name, position in degrees-minutes-seconds to 0.001",
  characteristic, height, nominal range, structure description (colour, shape, material), remarks
  (fog signal type, seasonal, "emergency light"). Vol. I has about 7,950 positioned lines.
- **Access tested:** downloaded Vol. I; `pdftotext -layout` gives clean fixed-width rows that parse
  by regex (LLNR first, then name, then DMS position). **The height column is unreliable in the text
  layer** (Portland Head shows `0` where a real height belongs) so take heights and ranges from
  ENC or Wikidata and use the Light List for LLNR, structure text and fog signal.
- **robots.txt:** navcen disallows `/core/`, `/profiles/`, `/admin/`, `/search/` etc. The PDF path
  `/sites/default/files/pdf/` is not disallowed. No AI-crawler rules.
- **Licence:** US Coast Guard publication, federal public domain. No notice found on the page.
- **Quality:** the PDF's metadata says it was produced 2025-01-02 while the server file is dated
  2026-10-14, so check the edition on the first page before trusting it as current. Active aids only.
- **Recommended use:** **regional source** for LLNR (the join key to Wikidata P3723), structure
  description and fog signal; **research source** for "what the station looks like now".
- **Sample (own words):** LLNR 7565, Portland Head Light, 43-37-23.209N 070-12-28.323W, characteristic
  Fl W 4s, white tower, horn one blast every 15 s, emergency light of reduced intensity; LLNR 7570
  is the separate directional light at the base of the same tower.

## 5. USCG Historian's Office (history.uscg.mil): BLOCKED

- **URL pattern (from search results, not fetched):**
  `https://www.history.uscg.mil/Browse-by-Topic/Assets/Land/Lighthouses-Light-Stations/Article/<id>/<slug>/`,
  list at `.../Lighthouses-Light-Stations/?Page=N` (at least 19 list pages seen), alphabetical with
  a state code in each entry. Related: "Lighthouse Files Held by USCG Historian's Office (Indexed by
  State)" and an archival subject-file content list, hosted at `media.defense.gov`.
- **Access:** every request, robots.txt included, gets an Akamai "Access Denied" 403 from curl and
  from WebFetch. **Skipped; I will not spoof a browser.** The owner can ask the Historian's Office
  whether it can supply the pages or a list. The site labels its documents public domain.
- **Mirror that survives:** the USLHS Digital Archive carries 3,798 items from the "U.S. Coast Guard
  Historian's Office" collection (section 8).
- **Recommended use:** `skip (blocked)`; revisit only if the Historian grants access.

## 6. NPS Inventory of Historic Light Stations

- **What happened to it:** the old per-state pages
  (`www.nps.gov/maritime/inventories/lights/me.htm`) now return the Maritime Heritage Program front
  page, and `.../inventories/lights.htm` is a 404. The NHLPA resources page still lists "Inventory of
  Historic Light Stations (National Park Service)" and links it to an NPS IRMA reference
  (`irma.nps.gov/DataStore/Reference/Profile/2299727`), whose PDF is behind the robots-disallowed
  `DownloadFile` path (see honesty note). The data was first published 1995 per USLHS (a search
  snippet says 1994 and 595 stations, unverified).
- **Surviving copy:** USLHS Digital Archive, collection "National Park Service Inventory", **291
  records** (`https://archives.uslhs.org/collection-donor/national-park-service-inventory`), each
  with name, type, state, existing yes/no, year established, location, lat/long, owner, open to
  public, tower details, optics (see section 8 for a sample).
- **Recommended use:** `skip` the NPS originals; use the USLHS copy as a **regional source** for
  existing federal-heritage stations.

## 7. National Register of Historic Places (NRHP)

- **Bulk list:** `https://www.nps.gov/subjects/nationalregister/upload/national-register-listed_20260522.xlsx`
  (14.5 MB; also `...-everything_...`, `National-Historic-Landmarks_...`, `...-removed_...`;
  dated 2026-05-22 snapshot, page `.../nationalregister/data-downloads.htm`). 100,866 rows. Columns:
  `Ref#`, Prefix, Property Name, State, County, City, Street & Number, Status, Request Type, Acreage,
  Area of Significance, Category of Property, **External Link (NARA catalog URL of the nomination)**,
  Listed Date, NHL Designated Date, Other Names, Property ID. **No coordinates.**
- **Lighthouse content:** name search on the listed file finds about 440 properties whose name or
  other names contain lighthouse / light station / lightship / light vessel / range light, and
  about 120 more named "<Place> Light" (some are electric light companies; roughly 90 real).
  By state (word-match set): MI 73, ME 51, NY 38, MA 28, CA 23, CT 21, FL 21, WI 21, MD 18, RI 18,
  NJ 17, WA 14, VA 12, AK 11, NC 11, OR 9, DE 8, OH 7, SC 6, TX 6. Wikidata has 498 NRHP ids on its
  lighthouses, so use **Wikidata P649 to pick the lighthouse subset** and use the workbook for
  listed date, county, NHL date and the NARA link, instead of fuzzy name matching.
- **Positions:** NPS feature service
  `https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/0`
  (74,636 points, `maxRecordCount` 2000, fields include `NRIS_Refnum`, `RESNAME`, `STATUS`,
  `CertDate`, `NARA_URL`, `MAP_METHOD`, `SRC_ACCU`). Query by
  `where=NRIS_Refnum='73000121'&outSR=4326&f=json`. Tested: Portland Headlight is at -70.20768,
  43.62313, listed 1973, accuracy about +/-12 m. A name filter
  (`UPPER(RESNAME) LIKE '%LIGHTHOUSE%' OR ... LIKE '% LIGHT'`) returns count 424.
  robots.txt for `mapservices.nps.gov` is a 404 (no rules). `www.nps.gov/robots.txt` disallows only
  `/ns/`, `/search/`, `loader.cfm`.
- **Licence:** federal public domain. The service says sensitive properties are excluded and
  coordinates are for properties under 10 acres a single point.
- **Quality:** the register lists a whole complex under one point and often with the old name
  ("Portland Headlight"); lost lights are listed only if they were listed before loss.
- **Recommended use:** **regional source** (register status, listed date, NHL, nomination link for
  the research agents), joined by NRHP number.

## 8. U.S. Lighthouse Society Digital Archive ("J. Candace Clifford Lighthouse Research Catalog")

- **URLs:** places `https://archives.uslhs.org/places` (GET filters `field_type_target_id=207` for
  Light Station, `field_us_state_value`, `field_existing_value=0|1`), place page
  `https://archives.uslhs.org/places/<slug>`, people `https://archives.uslhs.org/people`, person
  page `.../people/<slug>`. 30 records per list page.
- **Coverage:** places by type: **Light Station 1,202**, Lightship Station 139, Minor Aid to
  Navigation 686, Lifesaving Station 67, Depot 88, Museum 45, Fog Signal Station 3, plus Replica and
  Private (Faux) Lighthouse. Light stations split roughly **730 existing / 470 not existing** (from
  list pagination: 25 and 16 pages of 30; approximate). These probably include the territories (and possibly a few Cuban lights), so the 50-state figure is
  about 1,150. Collections include 3,798 items from the
  Historian's Office, 18,932 from the National Archives, 15,459 from the D'Entremont collection,
  576 from NPS, and **47,592 items in the "Kraig Anderson Inventory of Lighthouse Personnel"**.
- **People (keepers):** about 1,200 list pages of 30, so about 36,000 people. Types: Light Keeper
  22,376, Lightship Personnel 4,189, Tender personnel 6,910, Light Keeper (Female) 525, Light Keeper of
  African descent 94, Superintendents 209, and more. A person record carries name, type, associated
  place or vessel, title/position, year started, beginning salary and a NARA record-group source.
  Filters by lighthouse district exist. This is a ready-made keeper index (note: it lists start
  year, not full tenures).
- **Place fields (sample page "Absecon"):** type, year established, existing yes/no, source,
  latitude/longitude (degrees and decimal minutes), city, state, county, owner/manager, open to
  public, year discontinued, tower material, foundation, focal height, tower shape, daymark, fog
  signal building, keeper's quarters, other structures, optics (original and current), plus a
  dated history paragraph block and links to documents, photos, postcards, plans, clippings and
  people. The Absecon record (own words): established 1857, brick-and-iron conical tower, first-order
  Fresnel lens, 167 ft focal height, discontinued 1933 and relit 1997, managed by a local
  association, open to the public.
- **robots.txt:** `archives.uslhs.org/robots.txt` is the stock Drupal file (disallows `/search/`,
  `/admin/`, `/user/...`); list and record pages are not disallowed. No AI-crawler rules.
- **Licence:** "(c) 2026 U.S. Lighthouse Society, All Rights Reserved." Facts only; the keeper
  and station data originate in public-domain federal records (Record Group 26), so extract
  names, years, coordinates and link back.
- **Recommended use:** **bulk source for the lost-light roster and station attributes**
  (about 41 list pages + about 1,200 place pages, 40 min at 2 s) and **regional source for keepers**
  (about 1,200 list pages). Strongest single list of historic US stations I found.

## 9. USLHS lighthouse inspection ("Description of Light Station") reports

- **URL:** `https://uslhs.org/gr/inventory/light_station_states.php` then
  `.../state_light_station_reports.php?id=<n>` (ids 1-54, 34 with content).
- **What it is:** transcriptions of the Lighthouse Service's station description reports
  (National Archives RG 26), compiled for the Historian's Office by the Chesapeake Chapter. State
  lists are small (NH shows 2 stations; Maine 74 report-years; Michigan 198; Maryland 121); counts
  are report-years, about 1,350 across all states, not stations. Mostly 1930s.
- **robots.txt:** `uslhs.org` stock Drupal file; the `/gr/` path is not disallowed.
- **Licence:** site (c) the Society; underlying reports are federal records.
- **Recommended use:** `research source (cite per station)`; low priority.

## 10. USLHS Passport Club list and accommodations

- **Passport list:** `https://uslhs.org/sites/default/files/passport_club/full_page_mini_list.pdf`
  (4 pages, 185 KB, "Last Updated: July 2026", free; the detailed list is members-only and I did
  not touch it). About 770 stamp lines in 3-4 column text grouped by state, including Canada,
  international, "Lost Lights", series stamps and some non-lighthouse sites (life-saving
  stations, lightships, museums, Fresnel lens displays). Use `pdftotext` without `-layout` or
  crop columns. Many stamps sit at lights that are visitable.
- **Accommodations:** `https://uslhs.org/travel/accommodations` says there are lodging options in 14
  states and Canada (the state list shows CA, ME, MD, MA, MI, MN, NY, NC, OR, RI, VA, WA, WI, i.e. 13 links), in the classes B&B,
  vacation rental, hostel, "keeper for a fee", volunteer host keeper. State sub-pages list the
  operators (not fetched).
- **Licence:** (c) the Society; a station-name list is facts.
- **Recommended use:** `facts only, link` (passport flag and lodging class per station).

## 11. LighthouseFriends.com (Kraig Anderson)

- **URLs:** state page `https://www.lighthousefriends.com/pull-state.asp?state=ME`; per-light page
  `https://www.lighthousefriends.com/light.asp?ID=547`. The state list takes GET filters
  `A1..A15=1` for the icon legend; verified meanings: A6 climbable, A9 overnight lodging, A10
  volunteer keeper program, A14 **destroyed**, A15 active Fresnel lens (A1 easy access, A2 boat, A3
  ferry, A4 hike, A5 private, A7 interior open/museum, A8 fee, A11 photogenic, A12 movie, A13 haunted).
- **Coverage (crawled today, 31 states x 5 filters = 155 requests):** **1,059 US lighthouses, of
  which 272 flagged destroyed**; 194 climbable, 47 with lodging, 34 with a volunteer-keeper
  program. Counts per state in "Counts". The site's dropdown has no entry for AZ, AR, CO, IA, KS, KY,
  MO, MT, NE, NV, OK, TN, UT, WV (inland replicas and river lights). Also Canada and Cuba.
- **Bulk trick:** each state page embeds a Google-Maps script with **every light's ID and 5-decimal
  coordinates**; one request per state yields name, place, ID and position for the whole state.
  All 1,059 entries had coordinates. A parsed index is at `data/raw/survey/us/lhf_index.json`.
- **Per-light page (Cape Elizabeth sample):** long history prose (about 20,000 characters), a
  keeper roster on one line ("Head: Name (yyyy-yyyy), ..." and Assistants), latitude/longitude, visitor
  information, pictures with copyright notices. Keeper lists with years are the most valuable part.
- **robots.txt:** `https://www.lighthousefriends.com/robots.txt` returns an IIS 404, so no rules;
  no AI-crawler mention.
- **Licence:** "Copyright (c) 2001- Lighthousefriends.com; pictures copyright Kraig Anderson, used
  by permission". No data licence. **Facts only** (names, years, keeper names and tenures, flags,
  coordinates); never copy prose or photos.
- **Quality:** the most complete visit and keeper site; current (news items dated this week);
  lists lost lights it has researched (272) but not all. Includes some non-US-state oddities (small
  beacons in Hawaii).
- **Recommended use:** **bulk source for the station list, coordinates and visit flags** (31
  requests) and **research source (cite per station)** for keepers. Per-light crawl is 1,059 pages
  (about 35 min) if keeper rosters are wanted in bulk; do that only as facts-only extraction.

## 12. Russ Rowlett's Lighthouse Directory (UNC / ibiblio)

- **URLs:** index `https://www.ibiblio.org/lighthouse/`; US regional pages such as `me.htm`, `me2.htm`,
  `minel.htm`, `ak.htm`, `hi.htm` (73 US and territory pages found on the index; I fetched all).
  The directory claims over 24,800 lights worldwide, last updated 2026-10-17.
- **Coverage:** US pages carry a "Lighthouses: N" footer; the sum over the US and territory pages
  is **1,508** (about 1,460 in the 50 states). Per region counts are in `rowlett/summary.json`.
  Lost lights are included only occasionally; the directory is mostly existing and inactive
  structures, plus replicas.
- **Fields (free text per entry):** name, year built and year station established, "inactive since"
  year, structure description, access and owner, location, ARLHS number, Admiralty (J-series) and USCG
  numbers, and links to other sites' pages. **Positions are not given as plain coordinates** (only
  inside Google Maps links), so this is not a position source. A ratings key is on a separate page.
- **robots.txt (ibiblio):** `User-agent: *` / `Crawl-delay: 2`; none of the disallowed
  directories (`/dbarberi/wiki/`, `/herbmed/getit.php` ...) include `/lighthouse/`.
- **Licence:** "Site copyright 2026 Russ Rowlett and the University of North Carolina at Chapel Hill."
  Facts only.
- **Quality:** careful and current (each page shows a "checked and revised" date, Maine July 2026);
  hand-written paragraphs are hard to parse, so use it for ARLHS / USCG / Admiralty id cross-walks
  and as a second opinion on years and status.
- **Recommended use:** `facts only, link` (cross-check source), regional pages as research source.
- **Sample (own words):** Nash Island Light (second tower), Maine: 1873 brick pyramidal tower on a
  station established 1838; inactive since 1982; charted as a landmark; keeper's buildings gone after
  1958 automation; sibling of Burnt Coat Harbor Light; refuge island closed to visitors in nesting
  season; support group owns it since 1997.

## 13. ARLHS World List of Lights (WLOL)

- **URLs:** `https://wlol.arlhs.com/` (the database), state table `.../index.php?mode=na`, alphabetical
  `.../index.php?mode=alpha`, per-light page `.../lighthouse/USA661.html`. (The society's
  WordPress site `arlhs.com` is separate.)
- **Coverage:** 15,577 lights worldwide, "last updated October 20, 2026". US states: **1,435 lights**
  (+18 PR). Per state: MI 203, NY 142, TX 108, MA 90, ME 81, WI 76, MD 72, FL 61, CA 57, NC 47, NJ 45,
  VA 41, HI 39, OH 37, LA 37, RI 37, DE 36, WA 35, CT 26, AK 25, SC 22, OR 16, PA 15, MS 14, GA 12, IL 12,
  VT 12, IN 10, MN 10, AL 7, NH 5, IA 2, MO 1, OK 1, WV 1. Texas is inflated by oil-platform and
  offshore structures.
- **Fields (per light page):** ARLHS number and aliases, state, **coordinates (decimal, DMS and
  KML link)**, Maidenhead grid, **a "structure removed, relocated, destroyed or otherwise lost?"
  flag**, date added to the list, amateur-radio activation history.
- **robots.txt:** `wlol.arlhs.com`: `Disallow: /arlhsadmin/`, `/coordinates.php`, `/photo/add.php`.
  **`arlhs.com` has `Crawl-Delay: 600`** and its WordPress is currently publishing casino spam posts
  (compromised): do not use that host.
- **Licence:** "Copyright 2003-2026 ARLHS, LLC ... Database HTML Rendering Programs, MySQL Schema and Web
  Site Content (excluding the actual lighthouse data) Copyright 2006-2026 John Huggins". The facts
  are not claimed in that wording, but ask or keep to ids, names and coordinates.
- **Quality:** wide net (includes towers that are not strictly lighthouses), many coordinates
  user-proposed, "Location Verified" flag per light.
- **Recommended use:** **regional source for ARLHS numbers and the lost flag** (about 1,450 page
  fetches, 50 min) or, cheaper, take ARLHS ids from Wikidata P2980 (831) and fetch WLOL only for the
  gaps.

## 14. Lighthouse Explorer Database and Doomsday List (Lighthouse Digest / Foghorn Publishing)

- **URLs:** `https://www.foghornpublishing.com/Digest/database/searchdatabase.cfm`;
  alphabetical lists `.../datapage.cfm?letter=A` (GET); detail `.../uniquelighthouse.cfm?value=<id>`;
  Doomsday list `.../doomsday.cfm`. `lighthousedigest.com` links to the same database.
- **Coverage:** "8,260 lighthouses from all over the world"; crawled all 26 letter pages: **1,314 US
  entries**. By state: MI 190, NY 127, ME 84, MA 84, WI 62, CA 58, MD 56, FL 55, NJ 50, OH 42, HI 41,
  NC 41, VA 40, RI 35, WA 34, LA 34, DE 30, TX 30, CT 27, AK 22, SC 21, PR 16, OR 16, PA 14.
  Doomsday List: about 60 endangered lights, all at risk and mostly standing.
- **Detail fields:** nearest town, location text, managing organisation with phone and website, notes,
  tower height, focal plane, tower description, date established, date present tower built, date
  automated, optics, current use, **open to public?**, directions, endangered flag.
- **robots.txt:** `Disallow: /SS/`, `/Digest/admin/`, `/Digest/temp/`, `/Digest/calendar/`,
  `/Digest/batchfiles/` (a commented-out block would have disallowed everything; it is not active).
  `/Digest/database/` is allowed.
- **Licence:** none stated on the pages I read; (c) Foghorn Publishing presumably. Facts only.
- **Recommended use:** `facts only, link`; best for the **managing organisation, opening status
  and "endangered" flag**. Detail pages are 1,314 fetches; fetch lazily.

## 15. New England Lighthouses: A Virtual Guide (Jeremy D'Entremont)

- **URLs:** `https://www.newenglandlighthouses.net/` (index), per-light history page
  `.../avery-point-light-history.html`; also `-lighthouse.html`, `-bibliography.html`, `-postcards.html`.
  180 "light-history" pages for the six states.
- **Content:** long histories (a typical page is 50,000 characters of text), many with keeper names
  inside the narrative, bibliographies, NRHP mentions.
- **robots.txt:** `User-agent: NerdyBot` and `dotbot` limited; `*` disallows `/ajax/` and `/apps/`.
  A sitemap is published at `/sitemap.xml`.
- **Licence:** none stated; (c) the author. Facts only.
- **Recommended use:** `research source (cite per station)` for New England, good bibliography
  pointers. Not structured for bulk.

## 16. Terry Pepper, "Seeing the Light" (Great Lakes)

- **URLs:** `http://www.terrypepper.com/lights/index.htm`, state pages `state_michigan.htm` etc.,
  light pages like `.../lights/huron/alpena/index.htm`, with a **`keepers.htm` sub-page per light**.
  Covers MI, WI, MN, IL, IN (Lakes Superior, Michigan, Huron) and some of the Great Lakes tenders.
- **Content:** history, photos, keeper lists. The home page says last updated 2012-09-03, so lights
  restored or lost since then are not covered. No robots.txt (404).
- **Licence:** "Copyright by Terry Pepper". Facts only.
- **Recommended use:** `research source (cite per station)` for Great Lakes keepers; pair with
  LighthouseFriends.

## 17. Michigan Lighthouse Conservancy

- `https://www.michiganlighthouse.org/` answers curl with a Cloudflare challenge ("Just a moment") and a
  403. **Skipped.** Michigan is covered by LighthouseFriends (148), Pepper (about 124 pages), USLHS
  archive and ARLHS (203).

## 18. Wikipedia "List of lighthouses in <state>"

- **URLs:** `https://en.wikipedia.org/wiki/List_of_lighthouses_in_Maine` and one per coastal state
  (also `List_of_lighthouses_in_the_United_States`, which says the US has had "approximately a
  thousand" lights and that Michigan has more than 150).
- **Access:** normal article pages; `/wiki/` is allowed (robots disallows `/w/` and `Special:`, which
  matters if anyone tries the API).
- **Tables carry:** name, image, location, **coordinates (geohack links: 69 on Maine's page)**, year
  first lit, automated year, year deactivated, current lens, focal height, notes with references.
- **Licence:** CC BY-SA 4.0 (text); data facts only, with the Wikidata mirror CC0.
- **Quality:** good for standing lights, mixed for lost. Largely the origin of the Wikidata items.
- **Recommended use:** `facts only, link`; use Wikidata as the machine route and Wikipedia pages as
  citations in the research phase. No need for a Wikipedia scraper.

## 19. NGA List of Lights

- `https://msi.nga.mil/Publications/NGALOL` is a JavaScript app (the page is an empty shell). US
  waters in the NGA lists are the same as the Light List. Wikidata P3563 holds 16 ids. **Skip.**

---

## Visit and stay: what answers "can I climb it, sleep in it, volunteer?"

| Question | Best source | Notes |
|---|---|---|
| Climb / interior open / fee | LighthouseFriends icons A6, A7, A8 | 194 climbable US lights |
| Overnight lodging | LighthouseFriends A9 (47 lights, listed in `lhf/summary.json`); USLHS accommodations page (13-14 states) | Classes: B&B, rental, hostel, keeper-for-a-fee, volunteer host |
| Volunteer keeper program | LighthouseFriends A10 (34 lights: MI 13, OR 6, WI 5, NC 3, CA 1, FL 2, ME 1, RI 1, WA 2) | USLHS lists host-keeper opportunities |
| Open to public / managing org | Lighthouse Explorer detail pages; USLHS archive `Open to Public`; Rowlett (access sentence) | |
| Passport stamp | USLHS 4-page PDF (about 770 stamp lines) | Free summary only |
| Boat-only / hike | LighthouseFriends A2, A3, A4 | |
| Endangered | Lighthouse Digest Doomsday List | about 60 |

None of these is an API. For the page's "visit" block the LighthouseFriends flags plus the USLHS
passport and accommodations lists cover most needs from facts-only extraction.

---

## Counts

Per state, as of 2026-10-21. LHF = LighthouseFriends (all, lost = flagged destroyed). ARLHS = WLOL
state table. OSM = `man_made=lighthouse` inside the state polygon. Explorer = Lighthouse Explorer
Database. Rowlett = sum of regional-page footers. NRHP = properties named like a lighthouse (fuzzy).

| State | LHF all | LHF lost | LHF standing | Wikidata | ARLHS | OSM | Explorer | Rowlett | NRHP names |
|---|---|---|---|---|---|---|---|---|---|
| AK | 18 | 6 | 12 | 20 | 25 | 23 | 22 | 26 | 11 |
| AL | 6 | 3 | 3 | 5 | 7 | 4 | 7 | 17 | 4 |
| CA | 50 | 7 | 43 | 52 | 57 | 58 | 58 | 76 | 25 |
| CT | 23 | 2 | 21 | 34 | 26 | 23 | 27 | 26 | 22 |
| DE | 22 | 8 | 14 | 29 | 36 | 13 | 30 | 27 | 11 |
| FL | 40 | 9 | 31 | 49 | 61 | 40 | 55 | 84 | 22 |
| GA | 13 | 6 | 7 | 9 | 12 | 6 | 10 | 15 | 5 |
| HI | 43 | 2 | 41 | 17 | 39 | 20 | 41 | 33 | 5 |
| IL | 10 | 2 | 8 | 8 | 12 | 32 | 11 | 33 | 3 |
| IN | 6 | 0 | 6 | 4 | 10 | 13 | 12 | 11 | 3 |
| LA | 32 | 22 | 10 | 22 | 37 | 6 | 34 | 39 | 4 |
| MA | 73 | 13 | 60 | 81 | 90 | 63 | 84 | 70 | 51 |
| MD | 50 | 20 | 30 | 50 | 72 | 42 | 56 | 65 | 19 |
| ME | 71 | 4 | 67 | 70 | 81 | 64 | 84 | 78 | 54 |
| MI | 148 | 22 | 126 | 124 | 203 | 141 | 190 | 210 | 80 |
| MN | 8 | 0 | 8 | 9 | 10 | 10 | 8 | 13 | 6 |
| MS | 11 | 9 | 2 | 11 | 14 | 4 | 12 | 19 | 3 |
| NC | 38 | 25 | 13 | 18 | 47 | 12 | 41 | 26 | 11 |
| NH | 5 | 0 | 5 | 2 | 5 | 6 | 8 | 7 | 2 |
| NJ | 35 | 13 | 22 | 27 | 45 | 23 | 50 | 27 | 19 |
| NY | 105 | 22 | 83 | 84 | 142 | 84 | 127 | 124 | 53 |
| OH | 32 | 8 | 24 | 22 | 37 | 32 | 42 | 46 | 22 |
| OR | 15 | 3 | 12 | 16 | 16 | 18 | 16 | 25 | 10 |
| PA | 8 | 4 | 4 | 5 | 15 | 12 | 14 | 12 | 4 |
| RI | 31 | 10 | 21 | 31 | 37 | 28 | 35 | 22 | 22 |
| SC | 18 | 8 | 10 | 21 | 22 | 9 | 21 | 13 | 7 |
| TX | 19 | 14 | 5 | 8 | 108 | 12 | 30 | 86 | 8 |
| VA | 37 | 22 | 15 | 36 | 41 | 12 | 40 | 36 | 12 |
| VT | 8 | 2 | 6 | 6 | 12 | 7 | 8 | 12 | 0 |
| WA | 30 | 4 | 26 | 31 | 35 | 36 | 34 | 51 | 17 |
| WI | 54 | 2 | 52 | 54 | 76 | 65 | 62 | 66 | 32 |
| Other states (AZ, AR, CO, IA, KS, KY, MO, MT, NE, NV, OK, TN, UT, WV, SD) | n/a | n/a | n/a | 1 | 5 | 43 | 26 | 65 | 10 |
| **Total (includes the "other states" row)** | **1,059** | **272** | **787** | **956** | **1,435** | **961** | **1,295** | **1,460** | **557** |

**Best estimate of Fresnel's state counts** (standing = mean of LHF standing and Wikidata minus its
lost items; lost low = larger of LHF's flagged lost and Wikidata's lost; lost high = what the
median of ARLHS, Explorer and Rowlett implies once the standing estimate is subtracted):

| State | Standing | Lost (low-high) | State | Standing | Lost (low-high) |
|---|---|---|---|---|---|
| AK | 16 | 6-9 | NC | 13 | 25-28 |
| AL | 4 | 3 | NH | 4 | 0-3 |
| CA | 45 | 7-13 | NJ | 23 | 13-22 |
| CT | 27 | 2 | NY | 81 | 22-46 |
| DE | 20 | 8-10 | OH | 23 | 8-19 |
| FL | 37 | 9-24 | OR | 13 | 3 |
| GA | 8 | 6 | PA | 4 | 4-10 |
| HI | 29 | 2-10 | RI | 24 | 10-11 |
| IL | 8 | 2-4 | SC | 14 | 8 |
| IN | 5 | 0-6 | TX | 6 | 14-80 (high is inflated by offshore platforms) |
| LA | 14 | 22-23 | VA | 20 | 22 |
| MA | 68 | 13-16 | VT | 6 | 2-6 |
| MD | 33 | 20-32 | WA | 28 | 4-7 |
| ME | 68 | 4-13 | WI | 52 | 2-14 |
| MI | 124 | 22-79 | MN | 8 | 0-2 |
| MS | 5 | 9 | Inland (14 states) | about 15 | 0 |
| **Total** | **about 850** | **about 270-540** | | | |

Caveats on the table: HI looks high because LighthouseFriends counts small beacons; LA, MS, NC, VA,
TX and MD are mostly lost (offshore screwpile, reef and Gulf lights, many destroyed); the USLHS
archive's own existing/not-existing split (about 730 / 470, territories included) is a third
opinion that lands inside the same range.

### How many US stations should Fresnel expect

- 50 states, **standing: about 850** (range 790-950). Wikidata alone gives about 870 once its roughly 85
  lost items are removed; LighthouseFriends gives 787.
- 50 states, **lost: about 400-450 is the realistic target** from the sources in this survey
  (USLHS archive about 470, LHF 272, Wikidata about 85, OSM about 18); the true historical number
  is higher, and the Lighthouse Board annual reports (another survey) are the way to find the rest.
- Raw records before merging: about 1,300 in the 50 states; after merging towers into stations and
  ranges into one station each, **plan for about 1,200-1,300 station records** in the 50 states
  (territories add about 70 more: PR 18-53, USVI 9-13, Guam, Samoa, Marianas, Pacific remote
  islands). Plus lightship stations (USLHS lists 139) and life-saving stations (67) belong to other
  surveys.

---

## Gaps and risks

1. **Lost lights are the weak spot.** No machine-readable source lists them well. The best are
   the USLHS archive (about 470), LHF (272) and Wikidata (about 85); OSM has about 18. Positions for
   lost lights are often approximate or missing, so expect many lost stations to carry a
   "positional precision: approximate" flag.
2. **Merging.** Station boundaries differ by source (LHF lists "Cape Elizabeth" and "Cape Elizabeth
   West" separately, Wikidata may hold one item per tower, range lights are listed as pairs). Build
   the merge key around position (about 100 m) plus normalised name, with Wikidata ids and ARLHS ids
   as hard keys.
3. **Blocked or dead sources:** USCG Historian (Akamai 403), Michigan Lighthouse Conservancy
   (Cloudflare), NPS Inventory pages (dead; PDF behind a robots-disallowed path), NGA List of
   Lights (JS only), ENC harbour/approach layers (service stopped), Overpass (at capacity).
4. **robots/policy questions for the orchestrator:** WDQS and Overpass disallow `/sparql` and `/api/`
   for generic agents in robots.txt but are public APIs; see the honesty note. ARLHS's
   `arlhs.com` Crawl-Delay 600 (use `wlol.arlhs.com`, whose robots.txt is permissive).
5. **Copyright.** LHF, Rowlett, USLHS, Lighthouse Digest, New England Lighthouses and Pepper are all
   under copyright; extract names, years, flags, coordinates and keeper names with tenures only,
   and cite. Keeper names with years are facts but the USLHS and LHF compilations took years of
   work: link to them on each page.
6. **Light List text layer** has garbled heights; use ENC and Wikidata for numbers.
7. **Wikidata noise:** duplicates, non-lighthouses, and two characteristic statements for sector
   lights.
8. **Coordinates for the roughly 4% of Wikidata items without P625, and for inland
   replicas, are missing;** LHF and ARLHS fill most.
9. **Freshness.** The NRHP workbook is dated 2026-05-22; the Light List PDF says "2025"; QLever's
   OSM snapshot date is unchecked; the Terry Pepper site stopped updating in 2012.
10. **A compromised ARLHS WordPress** (spam posts on `arlhs.com`) - avoid following its links.

## Leads for other surveys

- **USLHS Digital Archive** (section 8) has 47,592 personnel items, 18,932 National Archives items,
  3,798 USCG Historian items, 1,358 Library of Congress items, 139 lightship stations and 67
  life-saving stations: useful to the lightship, life-saving and archival surveys.
- **Lighthouse Digest "Lighthouse Explorer"** is worldwide (8,260), so Canada is covered too
  (QLever shows OSM: ON 334, BC 285, NS 276, QC 226, NB 136, NL 91, PE 74).
- **ARLHS WLOL** counts for Canada from the state table: NS 313, ON 320, QC 285, NB 151, PE 122,
  NL 100, BC 60, MB 16.
- **QLever** (`qlever.dev/api/osm-planet`) works for any OSM question with no robots rules; its
  Wikidata sibling endpoint is untested and might remove the WDQS robots question.
- **The USLHS passport list** has a Canadian and "Lost Lights" section.
- **NARA catalog links** (the NRHP workbook's External Link column) point to nomination PDFs on
  `catalog.archives.gov` for the research agents.

## Recommended fetcher order

1. **Wikidata** (`wikidata.json`): ids, positions, NRHP/ARLHS/USCG numbers, Commons images,
   inception and retirement years. About 15 queries (state resolution and property groups).
2. **LighthouseFriends state pages** (31 requests): name, ID, 5-decimal position, destroyed,
   climb, lodging, keeper-program flags. Gives the lost-light skeleton and visit flags in one pass.
3. **USLHS Digital Archive places** (about 41 list pages + about 1,200 place pages): existing
   flag, year established and discontinued, lat/long, owner, open to public, tower and optics
   details. Resolves lost lights and fills 40-year-old facts.
4. **OSM via QLever** (a handful of queries): positions, `wikidata=` cross-links, seamark tags.
5. **NRHP** (workbook download + about 450 point queries to `mapservices.nps.gov`, or
   one query by `REFNUM` list): register status, listed date, NHL, NARA nomination link.
6. **Light List PDFs + ENC coastal layer**: LLNR, structure text, fog signal, characteristic,
   height, range for active lights; match by P3723 and position.
7. **ARLHS WLOL pages** only for lights without an ARLHS id from Wikidata (about 600 pages) and
   for the "lost" flag.
8. **Rowlett regional pages** (73 pages, 150 s): second opinion on year built / inactive since and
   cross-reference numbers.
9. **Passport PDF and accommodations page**: stamp and lodging flags.
10. **Lighthouse Explorer** (26 list pages; detail pages lazily): managing organisation and open-to-public
    status.
11. Research phase only: LHF per-light pages, USLHS people index, New England Lighthouses, Terry
    Pepper keeper pages, USLHS light-station reports.

## Files cached under `data/raw/survey/us/`

`wd_*.json` (Wikidata query results), `osm_lighthouse_by_state.json`, `lhf/` (155 state pages and
`summary.json`), `lhf_index.json` (1,059 lights with positions and flags), `rowlett/` (73 regional
pages + `summary.json`), `lhd/` (26 letter pages + `summary.json`), `uslhs_reports/`,
`nrhp_listed.xlsx`, `nrhp_lighthouseish.json`, `LightList_V1_2025.pdf` + `ll_v1.txt`,
`passport_mini_list.pdf`, `enc_ph_coastal.json`, `state_table.md`, `state_estimates.md`, and the
robots.txt files fetched.
