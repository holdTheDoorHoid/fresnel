# Source survey: US territories, lightships, life-saving stations (`territories_lightships_lss`)

Surveyed 2026-10-21 by one agent, following `docs/sources/survey_rules.md` and DESIGN.md sections 1-3.
Caches and samples: `data/raw/survey/territories_lightships_lss/` (about 15 MB, git-ignored).
Searches used: 9 of about 25. Every URL below was fetched during this survey unless it says "not fetched".

**Read this first (blockers that change the plan):**

1. **The USCG Historian's site and its PDF host are closed to us.** `www.history.uscg.mil` and
   `media.defense.gov` answer every request, even `robots.txt`, with an Akamai "Access Denied" 403 for our
   User-Agent and for WebFetch. We did not try to get around it. That site holds the best lightship, lighthouse
   keeper and life-saving-station material in the public domain. **Everything from it that we have came through
   Internet Archive Wayback copies** (see sources L1, S2). The owner should decide whether to ask the Historian's
   office for access or a data file (outreach is the owner's to send).
2. **Wikidata and OSM go through QLever, per the orchestrator's note.** `query.wikidata.org/robots.txt` says
   `Disallow: /sparql`; `www.wikidata.org` and `en.wikipedia.org` say `Disallow: /w/` (which contains `api.php`);
   `overpass-api.de` says `Disallow: /api/`. So all SPARQL and OSM counts below come from
   `https://qlever.dev/api/wikidata` and `https://qlever.dev/api/osm-planet` (`qlever.dev/robots.txt` is 404, no
   rules; queries saved in `qlever/`). **Disclosures (nothing was sent to `query.wikidata.org` or `overpass-api.de`):**
   (a) before the note arrived I sent three bounding-box queries to two public Overpass **mirrors**
   (`overpass.private.coffee`, `overpass.kumi.systems`; neither has a robots.txt); all timed out with no data, and I
   did not redo them; (b) I made one `en.wikipedia.org/w/api.php?action=parse` call (the lightship list wikitext)
   before reading the `/w/` rule; (c) one `loc.gov/pictures/search` call (disallowed there), whose result I deleted
   and replaced with the allowed `loc.gov/collections/` endpoint. Wikidata `Special:EntityData/Q....json` and
   Wikipedia `/wiki/` pages are allowed and worked. QLever limits seen: a label scan over all of Wikidata timed out
   (429), one label-regex query returned 502, and the OSM name-regex query took 100 s; keep fetcher queries narrow.
3. **Wikidata and OSM are thin for lightship stations and life-saving stations** (numbers in L8 and S9). Territory
   lighthouses are well covered in Wikidata (25 items) except Guam and American Samoa.
4. **No source gives coordinates for lightship stations.** Positions have to be built (see "Links to light stations").
5. **The biggest life-saving-station list (USLSSHA, 582 sites) has no usable coordinates** and its terms of
   service forbid copying material. Facts only, geocoded elsewhere.

---

## Part 1. US territories

Scope found: Puerto Rico (16 historic lights), US Virgin Islands (4 or 5), Guam (2 historic plus modern
harbour lights), American Samoa (3 or 4), Northern Mariana Islands (2), minor outlying islands (Navassa, Howland,
Baker, Midway). About **30 to 40 candidate stations**, of which roughly **28 pass the DESIGN 3.4 test** (a real
structure with a history). The rest are modern skeleton towers and pile beacons that the Light List carries.

### T1. Wikipedia lists (seed list)

- **URLs:** `https://en.wikipedia.org/wiki/List_of_lighthouses_in_Puerto_Rico`;
  `https://en.wikipedia.org/wiki/List_of_lighthouses_in_the_United_States_territories` (the pages for the Virgin
  Islands, Guam, American Samoa and the Northern Marianas all redirect to this one list);
  `https://en.wikipedia.org/wiki/Navassa_Island_Light`. Cached in `wp/`.
- **Coverage:** PR table has **16 rows** (11 shown Active, 4 Inactive, 1 Destroyed). The territories table has
  **14 rows**: Virgin Islands 4 (Buck Island, Fort Louise Augusta, Hams Bluff, Savana Island), Guam 5 (Apra Outer
  Harbor range front and rear, Glass Breakwater, Orote Point, Ritidian Point), American Samoa 4 (Aunu'u,
  Breakers Point, Pago Pago range front and rear), Northern Marianas 1 (Garapan, the 1934 Japanese lighthouse).
  Navassa is its own article.
- **Fields:** name, municipality, established year, tower and focal height, current status, condition (PR);
  coordinates, year built, year deactivated, focal height, NGA and Admiralty numbers (territories).
- **Access:** HTML tables, parse with the `<table>` rows. Wikidata ids of the lists: Q6351262, Q42377180.
  The PR table rows carry no article links (no per-light articles), so there are no QIDs to follow from it.
- **robots.txt:** `/wiki/` allowed (`Disallow: /w/` covers only the API; see blocker 2).
- **Licence:** Wikipedia text is CC BY-SA 4.0 (site footer). We take facts only.
- **Quality:** the PR table disagrees with itself in places (Culebrita is "Active" and "In ruins"; the 1886 tower
  is a ruin but the Light List still carries an Isla Culebrita Light). Dates are "first lit in the present tower".
- **Recommended use:** `regional source` (seed names and statuses; do not trust status without the Light List).
- **Sample (own words):** Punta Tuna Light, Maunabo, first lit 1892, 15 m tower, focal plane 34 m, active,
  restored for visitors, hurricane damage from Maria noted.

### T2. NPS Inventory of Historic Light Stations (retired web pages, Wayback copies)

- **URLs:** live `www.nps.gov/maritime/inventories/lights/pr.htm` now redirects to the Maritime Heritage landing
  page. Wayback copies fetched: `https://web.archive.org/web/20170416133547id_/https://www.nps.gov/maritime/inventories/lights/pr.htm`
  and `.../20150306044728id_/http://www.nps.gov:80/maritime/inventories/lights/vi.htm`. Cached in `nps_inv/`.
  The CDX list of every archived state page is `cdx_nps_lights.txt`. (No archived pages for AS, GU, MP.)
- **Coverage:** PR **16** entries (adds Cabras Island Light 1902, "no longer extant"; lists Point Borinquen as 1920
  and Point Jiguero/Higuero as 1922, the rebuilt towers). VI: **Hams Bluff only**. Year = year first lit in the
  existing tower. Located by text only ("Southeast of Pole Ojea on Cape Rojo"), no coordinates.
- **robots.txt:** `www.nps.gov`: `Disallow: /ns/`, `/search/`, `/loader.cfm` (no AI crawler named). Wayback has no robots.txt (404).
- **Licence:** US government work, public domain.
- **Quality:** 2014-2017 vintage. The successor data set is the IRMA DataStore reference profile
  `https://irma.nps.gov/DataStore/Reference/Profile/2299727` ("Inventory of Historic Light Stations"). Its robots.txt
  says `Disallow: /DataStore/DownloadFile/` and `Crawl-delay: 1`, so **the downloadable file is off limits to us**;
  the profile page itself is allowed. Skip the download, use the Wayback pages.
- **Recommended use:** `research source` (confirms the PR list of 16; names Cabras).
- **Sample:** Cabras Island Light, first lit 1902 (Wikipedia says 1908), not standing.

### T3. NRHP "Lighthouse System of Puerto Rico TR" (NPGallery) and HAER (Library of Congress)

- **NPGallery URL pattern:** `https://npgallery.nps.gov/AssetDetail/NRIS/<8-digit NRIS id>`; each page links
  `https://npgallery.nps.gov/GetAsset/<guid>` (the nomination PDF, plus a HAER PDF where one exists).
  Cached in `npg/` (Culebrita nomination and HAER PDF tested; the 5.8 MB HAER PDF is OCR text, readable).
- **Tested NRIS ids (13 lights and the dwelling):** 77001546 Arecibo; 77001549 Guanica; 77001551 Vieques (Punta
  Mulas; NPGallery wrongly files it under Isabela municipio); 81000685 Los Morrillos de Cabo Rojo; 81000686 Culebrita;
  81000687 Punta de las Figuras; 81000688 Punta Tuna; 81000689 Mona; 81000690 Caja de Muertos; 81000691 Faro del
  Puerto de Ponce (Cardona); 81000692 Cabezas de San Juan; 81000693 Morro; 81000694 Superintendent of Lighthouses'
  Dwelling. Listed 1977 (AD) and 22 Oct 1981. Punta Higuero (**81000560**) and Punta Borinquen (**81000559**) are NRHP
  too (ids from Wikidata, T6); Puerto Ferro has no NRHP number in Wikidata (HAER PR-45 exists).
- **Fields:** significance, architect (José M. Sanz for Guánica and Vieques), periods, significant years, and a long
  narrative form that usually carries construction dates and the 1898-1903 US takeover.
- **robots.txt:** `npgallery.nps.gov/robots.txt` returns 404 (no rules). Be gentle anyway: pages are 30 KB, PDFs up to several MB.
- **Library of Congress HAER (allowed, `Crawl-Delay: 5`):**
  `https://www.loc.gov/collections/historic-american-buildings-landscapes-and-engineering-records/?q=lighthouse+puerto+rico&fo=json&c=50`
  returned **20 items**: HAER **PR-32 to PR-47 (`pr0032` to `pr0047`) are the Spanish-era system**: 15 lights (Tuna,
  Cabo Rojo, Punta Mulas, Ponce/Cardona, Caja de Muertos, Borinquen, Arecibo, Figuras, Cabezas de San Juan, Guánica,
  Culebrita, Higuero, Puerto Ferro, Morro, Mona) plus the superintendent's dwelling. Each has measured drawings,
  photographs and written history; the JSON has a `latlong` field. Item URL: `https://www.loc.gov/item/pr0035/`.
  Do not use `loc.gov/pictures/search` (disallowed).
- **Licence:** NRHP forms and HAER are US government records, public domain; some photographs credit others.
- **Quality:** best primary-source base for the 16 Spanish-era lights. Typed or scanned (OCR is rough).
- **Recommended use:** `research source (cite per station)` and a check on `built` years.
- **Sample:** HAER PR-42, Isla Culebrita Light, drawings and photos, with a 1980 survey text; NRIS 81000686 lists
  significant year 1886.

### T4. Rowlett's Lighthouse Directory (territory pages)

- **URLs (the directory moved from unc.edu to ibiblio; old `unc.edu/~rowlett/lighthouse/*.htm` is 404):**
  `https://www.ibiblio.org/lighthouse/pr.htm`, `vi.htm`, `gu.htm`, `asm.htm`, `mnp.htm`, `umi.htm`, `nvi.htm`
  (Navassa), index `https://www.ibiblio.org/lighthouse/`. Cached in `rowlett/`.
- **Coverage:** PR page with ARLHS numbers PUR-001 to about PUR-024 (the 16 historic lights plus modern jetty and
  range lights); VI 3 entries (VIR-001, -002, -005, -006 seen); Guam 2; American Samoa 1; Northern Marianas 2 (Ushi
  Point, Garapan); minor outlying islands (Howland "Amelia Earhart" light 1937; Sand Island, Midway; Baker); Navassa 1 (NAV-001).
  Includes lost lights (Guánica collapsed after 1950). Index says the directory has "more than 24,800" lights; last update 17 Oct 2026.
- **Fields:** year (station and present tower), focal plane, characteristic, tower description, owner and site manager, Admiralty, USCG and NGA numbers, ARLHS number, links to photos.
- **robots.txt (`www.ibiblio.org/robots.txt`):** `User-agent: *`, `Crawl-delay: 2`, disallows only unrelated directories; no `/lighthouse/` rule, no AI crawler named.
- **Licence:** page footer: "All material in The Lighthouse Directory is copyright 2026 by Russ Rowlett and the University of North Carolina at Chapel Hill", copying portions allowed "for personal use and study", all other rights reserved; do not copy pages to another site. **Facts only, credit and link, per DESIGN.**
- **Quality:** best single current gazetteer with ARLHS numbers. Hand-edited, pages carry some errors (see L5).
- **Recommended use:** `facts only, link` (ARLHS ids, focal heights, lost-light notes).
- **Sample:** Punta Higuero (Rincon), station established 1892, present concrete tower 1922, focal plane 27 m, occulting white 4 s.

### T5. USCG Light List 2025 (current aids; PDF)

- **URLs:** `https://www.navcen.uscg.gov/sites/default/files/pdf/lightLists/LightList_V3_2025.pdf` (7.3 MB, covers
  Puerto Rico and the US Virgin Islands) and `..._V6_2025.pdf` (4.0 MB, Southwest, Northwest, **Oceania** and Arctic:
  Guam, American Samoa, Northern Marianas, Pacific islands). Landing page `https://www.navcen.uscg.gov/light-list-annual-publication`.
  Cached in `lightlist/` (PDF and `pdftotext -layout` text; PDFs dated 14 Oct 2026).
- **Fields (tested on the text):** LLNR number, name, position in degrees-minutes-thousandths, characteristic
  (`Fl W 15s`), height, range, structure text, remarks. In PR/VI it names the historic lights with their 5-digit
  numbers (Punta Borinquen 30715, Arecibo 30720, Puerto San Juan 30735, Cabo San Juan 31155, Punta Mulas 31530,
  Isla Culebrita 31685, Savana Island 31690, Punta Tuna 31800, Isla Caja de Muertos 31925, Isla de Cardona 31950,
  Cabo Rojo 32290, Isla de Mona 32295, Punta Higuero 32400, Buck Island 32565). Guam and Samoa lights are in V6
  (Ritidian Point 30660, Breakers Point 30185, Pago Pago range 30190 and 30195).
- **robots.txt:** `navcen.uscg.gov` robots is the standard Drupal file (disallows `/core/`, `/profiles/` and similar); the PDFs are not blocked; no AI crawler named.
- **Licence:** US government work, public domain.
- **Quality:** current and authoritative for **active** lights only; no history.
- **Recommended use:** `bulk source` for active-light characteristic, position and LLNR (all districts; the other agents will use all seven volumes).
- **Sample:** Cabo San Juan Light, LLNR 31155, 18-22-53.5 N, `Fl W 15s`, 80-ft class light on a cylindrical tower fronting a white building.

### T6. Wikidata (CC0), via QLever

- **Endpoint (tested):** `POST https://qlever.dev/api/wikidata`, form field `query=`, header
  `Accept: application/sparql-results+json`, explicit `PREFIX wd: wdt: wikibase: rdfs:` lines. The territory query
  (`qlever/q_territories.rq`, result `qlever/territories.json`, 12 KB, 2.5 s) takes instances of `lighthouse` (Q39715,
  with subclasses) whose country (P17) or located-in chain (P131+) is PR, VI, GU, MP, AS or UM, with P625, P571, P649 (NRHP) and P2980 (ARLHS).
- **Result: 25 items.** PR **17** (Arecibo, Caja de Muertos, Cape San Juan, Cardona, Culebrita, El Morro, Los Morrillos, Guánica, Isla Cabras, Mona,
  Puerto Ferro, two Punta Borinquen items (Q109232559 and Q7260508, a duplicate to merge), Punta Higüero, Punta Mulas, Punta Tuna, Punta de las Figuras);
  VI **4** (Buck Island twice, Hams Bluff, Savana Island); minor outlying islands **3** (Navassa Island Light Q6982191; Baker Island Day Beacon; "Aeronautic Lighthouse" at Wake, Q122675246);
  Northern Marianas **1** (Japanese Lighthouse, Garapan, Q15229363). **Guam, American Samoa: none** under the lighthouse class (the Wikipedia list covers them; check other classes such as `beacon` before concluding they are absent).
  Missing from Wikidata under this class: Fort Louise Augusta (VI), the Guam and Samoa lights, and Ushi Point (Northern Marianas).
- **Fields:** all 25 have coordinates; inception year on 15; **NRHP reference number on 16** (this fills the gap in T3: Punta Borinquen **81000559**, Punta Higüero **81000560**, Hams Bluff 100004382, Japanese Lighthouse 74002224); **ARLHS number on 22** (PUR001 to PUR022, VIR001, VIR002, MAI001, BAK001, NAV001). Positions are given to better than 1 m and can be treated as `exact` after a map check.
- **Also tested:** `https://www.wikidata.org/wiki/Special:EntityData/Q6982191.json` (Navassa Island Light) for the full item: coordinates (18.39738, -75.01284), inception 1917, height 162 ft (P2048), focal height (P2923), P131 Navassa Island (Q25359), an image.
- **Licence:** CC0. **Recommended use:** `bulk source` for ids, coordinates, NRHP and ARLHS numbers; years need the other sources (10 of 25 items have no inception date).

### T7. OpenStreetMap, via QLever

- **Endpoint (tested):** `POST https://qlever.dev/api/osm-planet` with prefixes `osmkey: <https://www.openstreetmap.org/wiki/Key:>`,
  `geo: <http://www.opengis.net/ont/geosparql#>`. Query `?x osmkey:man_made "lighthouse" . ?x geo:hasGeometry/geo:asWKT ?wkt . OPTIONAL { ?x osmkey:name ?name }`
  returned **15,032 lighthouse objects worldwide** in 5 s (4.4 MB; `qlever/osm_lh.json`). Filtering by bounding box on the client side gives, for the territories:
  **Puerto Rico 14 + Mona 1** (all named "Faro de ..."; the node named "Faro de Punta Los Morrillos" at 18.482, -66.699 is the **Arecibo** light, a name error), **US Virgin Islands 2** (Hams Bluff; a "Buck Island Signal Light" node on St. Croix), **Northern Marianas 1**, **American Samoa 1** (Breakers Point), **Navassa 1**, **Guam 0**, Wake 1 (unnamed).
- **Fields:** tags only as mapped (`name`, sometimes `wikidata`, `start_date`); geometry for towers and buildings. No history. ODbL; credit and share-alike for the derived database.
- **Recommended use:** `regional source` for positions where Wikidata lacks them; not a list authority.

### T8. Spanish-language and Spanish-archive sources (for the Spanish-era chapters)

- **Oficina Estatal de Conservación Histórica (OECH) booklet "El sistema de faros de Puerto Rico"** (Luis A.
  Gutiérrez-Negrón and Arleen Pabón-Charneco). The OECH page is gone; a hobbyist mirror with one page per light
  (Aguadilla, Arecibo, Arroyo, Cabo Rojo, Culebrita, Fajardo, Guánica, Mona, Maunabo, Ponce, Rincón, San Juan, Vieques)
  survives at `https://web.archive.org/web/20090204151526/http://farosdepur.tripod.com/trasfondo_de_nuestros_faros.htm`
  (fetched, 17 KB, Spanish prose, ISO-8859 encoding). Rights unclear (OECH text on a personal site); `research source`, cite OECH.
- **Nuria Hinarejos Martín, Revista de Indias 2021, DOI 10.3989/revindias.2021.022** on the first Spanish coastal
  lighting plan of Puerto Rico (1869 plan; sources in the Archivo Histórico Nacional). The journal host
  `revistadeindias.revistas.csic.es` fails TLS verification from this machine (certificate chain incomplete), so it was
  not fetched; I did not bypass verification. Fetch later from DOAJ or by DOI. Journal is open access (licence unchecked).
- **Norma Castaldi, *Los faros de Puerto Rico* (ICP, 2013)**: book, cite only.
- **Archivo Histórico Nacional (Spain), Ministerio de Ultramar files, via PARES** (`pares.mcu.es`, robots 404): plans,
  regulations for keepers (torreros), the 1897 revision. Search interface; `research source`, not machine-friendly.
- **Enciclopedia de Puerto Rico** (`enciclopediapr.org`, article ref 08072205): copyrighted prose; link only.
- **Fideicomiso de Conservación / Para la Naturaleza** (Culebrita restoration), **FEMA** project notes for Cabezas de San Juan: today's status, news.
- **There is no "Autoridad de Conservación de Faros"** in anything I found; OECH (Law 183 of 2000) is the state preservation office and does not run the lights.
- **Proclamation (Roosevelt) 1903** transferring the Spanish lights: `https://en.wikisource.org/wiki/Proclamation%20(Roosevelt)` (public domain).

### T9. Others checked

- **LighthouseFriends** (`www.lighthousefriends.com`, `robots.txt` is 404, so no rules): home and maps pages fetched; the
  state menu is script-driven, so I could not confirm territory pages. The US-bulk survey should test `light.asp?ID=` pages for PR/VI.
- **ARLHS World List of Lights** (`wlol.arlhs.com/lighthouse/PUR16.html`, not fetched): search result says the list data is
  copyright ARLHS; use only the ARLHS *number* as an identifier, with credit.
- **USLHS Digital Archive** (`archives.uslhs.org`) has 1,202 "Light Station" places; territory coverage not tested (see L2 for the site's rules).

**Link to light stations (Part 1):** these are the light stations. Nearby life-saving stations: only San Juan appears (USCG
index, one entry; USLSSHA PR=1, AS=1, HI=3).

**Counts (Part 1):** PR 16 historic (+ Cabras lost); VI 4 to 5; Guam 2 historic + 3 modern; AS 3 to 4; CNMI 2; outlying 3 to 4. Candidate total about 35 before scope filtering.

---

## Part 2. Lightships

**Counts:** stations: USCG index **116 entries** (about 108 true stations, 2 "wreck of" markers, plus 8 WWI Navy "approach"
stations on the last page); USLHS archive **139** place records (many name variants and 2 depots); after de-duplication
expect **about 125 to 135 distinct stations**. Vessels: **118 numbered hulls (LV-1 to LV-118)** plus about 24 letter-coded
pre-1867 ships (A to Z) plus the 1950s WLV hulls (189, 196, 604, 605, 612, 613): **about 140 to 150 vessels**. Survivors:
**about 16 US-built hulls** are preserved, derelict or private (table in L5).

### L1. USCG Historian's Office, "U.S. Lightship Station Assignments" (Lightship Station Index; PDF)

- **URL:** `https://media.defense.gov/2020/Sep/28/2002507200/-1/-1/0/LIGHTSHIP_STATION_INDEX.PDF` (403 for us; see blocker 1).
  **Tested copy:** `https://web.archive.org/web/20240712200159id_/https://media.defense.gov/2020/Sep/28/2002507200/-1/-1/0/LIGHTSHIP_STATION_INDEX.PDF`
  (741 KB, 54 pages, text layer; cached `LIGHTSHIP_STATION_INDEX.pdf`, `lsi.txt`). Wayback also holds copies from 2020, 2021 and 2024-11.
- **Coverage:** **116 stations** listed alphabetically (Ambrose Channel 1823-1967 through York Spit), standing and lost, all coasts and the
  Great Lakes. About 410 vessel-assignment lines; **113 distinct LV numbers (LV-1 to LV-118, gaps at 26, 27, 36, 92, 104)**,
  37 WAL aliases, 6 WLV numbers, and quoted early names/letters. Page 52-54: WWI Navy patrol vessels on "approach" stations.
- **Fields:** station name, start and end year, a "Location & historical notes" paragraph, and the list of vessels with
  years (for example Nantucket Shoals 1854-1983, with LV-11, LV1, LV-54, LV-58, LV-66, LV-85, LV-106, LV-117, LV-112,
  WLV-196, WLV-612, WLV-613 and a 1942-45 gap). **No coordinates.** Location text gives a state and **a distance and bearing
  from a named lighthouse in about two-thirds of entries** (for example "6.2 miles and 097 degrees from the Sandy Hook
  Lighthouse"); 53 entries say the station was **"replaced by"** something (a lighthouse, the Ambrose Light Tower, a buoy).
- **Access:** one PDF; `pdftotext -layout` gives clean text. Entry header regex: `^<Name>, <start>-<end>$`, then
  `Location & historical notes:`, then `Lightships assigned:` and `YYYY-YYYY: LV-n / WAL-n` lines.
- **robots.txt:** `media.defense.gov/robots.txt` is itself 403 (unreadable). Wayback has none.
- **Licence:** US government work; document credits Doug Bingham (Lightship Sailors Association historian) and Willard Flint. Public domain as a USCG publication.
- **Quality:** the authoritative list, built on Flint's 1989 *Lightships and Lightship Stations of the U.S. Government*. WAL numbers can
  disagree with other sources (LV-83 is WAL-508 here and in the NMA table, WAL-513 on Rowlett).
- **Recommended use:** **bulk source** for lightship stations and vessel assignments. Build `lightship_station` records from it.
- **Sample:** Ambrose Channel station, 1823-1967 (called Sandy Hook until 1908), 6.2 miles at 097 degrees from the Sandy Hook Light;
  vessels LV-16, LV-48, LV-51, LV-87, LV-111, then WLV-613 (1952-67); replaced by the Ambrose Light Tower.

### L2. U.S. Lighthouse Society Digital Archive (Research Catalog)

- **URLs:** category listing `https://archives.uslhs.org/type-place/lightship-station` (+ `?page=1`..`3`, 4 pages, 35 per page);
  place pages `https://archives.uslhs.org/places/<slug>-lightship-station`; vessels `https://archives.uslhs.org/vessels` (18 pages). Cached in `uslhs/`.
- **Coverage:** category counts shown on every page: Lightship Station **139**, Lifesaving Station **67**, House of refuge **1**, Light Station **1,202**,
  Depot 88, Minor Aid to Navigation 686, Museum 45, Replica 13, Fog Signal Station 3; vessels about 170 listed (tenders and other). It also hosts the
  "Kraig Anderson Inventory of Lighthouse Personnel" (47,592 records; the keepers index lead for other agents) and a Jeremy D'Entremont collection (15,459 items).
- **Fields (lightship station page):** name, alternate names, state, year established and discontinued, location phrase, **vessel assignments as
  structured rows** (vessel, start, end), comment, entry date; a "Light list data" tab. **No latitude/longitude on the two stations sampled**
  (Ambrose Channel, Diamond Shoal); the House of Refuge page *did* carry DMS lat/lon (27 11' 58" N), so lighthouse and house-of-refuge pages may.
- **Access:** server-rendered Drupal HTML, 10 to 35 items per list page, `?page=N`. Place URL slugs are predictable.
- **robots.txt (quoted):** `User-agent: *` ... `Disallow: /search/`, `/admin/`, `/user/login`, `/node/add/`, `/core/`, `/profiles/`. `/places/`, `/type-place/` and `/vessels` are not listed. No AI crawler is named.
- **Licence:** none stated on the pages sampled except "(c) 2026 U.S. Lighthouse Society, All Rights Reserved". Facts only, credit and link. Some records credit donors (USCG Historian's Office, Data Created by Society, Gary Riemenschneider for light-list data).
- **Quality:** station list partly derived from the USCG index (collection tag "U.S. Coast Guard Historian's Office"), but it **adds stations the PDF lacks**
  (Dry Tortugas, Pensacola, Cape Charles, Grosse Pointe, Kewaunee, Shovelful Shoal, Vidal Shoal, Rattlesnake Shoal, Weehawken) and spells names differently
  (Frying Pan Shoals, Hooper Strait, Limekiln Crossing). Years can differ (Ambrose Channel 1908-1967 here, 1823-1967 in the USCG index).
- **Recommended use:** `regional source` / research source; second opinion on stations, state, year, and a home for lifesaving-station and house-of-refuge places with coordinates where present.
- **Sample:** Diamond Shoal station (also called Cape Hatteras), North Carolina, 1897-1966, vessels LV-69, LV-71, LV-72, LV-105, LV-114, WLV-189.

### L3. Wikipedia "List of lightships of the United States" (vessel table)

- **URL:** `https://en.wikipedia.org/wiki/List_of_lightships_of_the_United_States` (wikitext cached as `wp_lightships_list.json`; HTML `/wiki/` also allowed). Category: `https://en.wikipedia.org/wiki/Category:Lightships_of_the_United_States` (22 pages, cached `wp/cat_lightships_us.html`).
- **Coverage:** **113 vessel rows**: lettered ships A-Z (note A: names assigned in 1938), LV-1 to LV-118, WLV-604/605/612/613. Columns: designation, start and end year (with "c." flags), stations with years, fate. Individual articles for the museum ships.
- **Access:** one `wikitable`; rows split on `|-`. The vessel cell is `Lightship ''LV-nn''`.
- **Licence:** CC BY-SA 4.0. Facts only.
- **Quality:** built from Flint's *A History of U.S. Lightships*; **fates are stale in places** (LV-79 Barnegat "museum in Philadelphia" while Rowlett reports it derelict in Camden NJ).
- **Recommended use:** `regional source` for vessel-to-station-and-fate; cross-check with L1, L4, L5.
- **Sample:** WLV-604 Columbia, station Columbia River 1951-79, now a museum in Astoria, Oregon.

### L4. Naval Marine Archive, "U.S.C.G. Light Vessels (LV, WAL)" table

- **URL:** `https://navalmarinearchive.com/sbh/smallships/wal.html` (57 KB; cached `nma/wal.html`).
- **Coverage:** **118 rows**, USLHB LV number, USCG WAL number, **original station**, shipbuilder and place, tons, delivery date, disposition (13 rows say museum or restaurant). Last updated 16 Feb 2016.
- **robots.txt (quoted):** disallows `/agm/`, `/build2021/`, `/cgi-bin/`, `/ims/`, `/media`, `/member_pages/`, `/collections/data/`, `/research/data/`; blocks Amazonbot, MJ12bot, PetalBot, meta-externalagent. `/sbh/` allowed; no Claude/Anthropic rule.
- **Licence:** "Copyright 2026 Naval Marine Archive"; table of facts. Facts only.
- **Quality:** useful builder and year facts, older than the others, and its "museum" statuses date from the 1960s-70s (LV-84, LV-107 shown as restaurants).
- **Recommended use:** `facts only, link` (builder, place, delivery date, original station).
- **Sample:** LV-118 (WAL-539), built by Rice Brothers, East Boothbay, delivered Sept 1938 for Cornfield Point, museum at Lewes DE from 1973.

### L5. Surviving lightships: Rowlett's checklist, plus NPS and museum pages

- **URL:** `https://www.ibiblio.org/lighthouse/lightships.htm` (50 KB; cached `rowlett/lightships.htm`). World checklist of 127 vessels; US section "Deactivated and Restored".
- **US survivors per Rowlett (13):** LV-83 Swiftsure (under restoration), LV-87 Ambrose, LV-101 Portsmouth, LV-103 Huron, LV-107 Winter Quarter, LV-112 Nantucket,
  LV-115 Frying Pan, LV-116 Chesapeake, LV-118 Overfalls, WLV-604 Columbia, WLV-605 Relief, WLV-612 Nantucket I, WLV-613 Nantucket II. Also LV-76 and LV-114 mentioned,
  LV-79 Barnegat rotting at Camden NJ, LV-106 and LV-109 beached in Suriname, WLV-196 Umatilla, and "recently scrapped" ones.
  NMA adds LV-76 museum at Vancouver BC (1987; a US-built hull now in Canada, for the Canada agent).
- **Conflicts to resolve per vessel:** Wikipedia says LV-79 is a museum, Rowlett says derelict; WAL-513 vs WAL-508 for LV-83; LV-84 and LV-107 were floating restaurants in the NMA table. **Every berth needs a current check** against the museum's own site.
- **Licence / robots:** same as T4 (all rights reserved; facts and credit).
- **NPS side:** the retired NPS page `.../maritime/ref/landmarks/lightships.htm` now redirects to the Maritime Heritage landing page; the successor is IRMA profile 2193569 "Lightships in the U.S." (download disallowed). Several lightships are National Historic Landmarks; status per vessel via Wikipedia infoboxes or Wikidata P1435, not checked here.
- **Recommended use:** `facts only, link`; build `lightship` (surviving vessel) records from Rowlett's list, with Wikipedia articles as the verification pass.

### L6. Flint's histories; Lightship Sailors Association; US Lightship Museum

- **Willard Flint, *A History of U.S. Lightships*** (USCG Historian, 1993): `http://www.uscg.mil/history/articles/Lightships.pdf` (about 9 MB). Wayback CDX shows captures from 2008 to 2011, but **playback returned HTTP 500 twice**
  (2008 and 2011 copies); retry later or from a different capture. **Flint, *Lightships and Lightship Stations of the U.S. Government* (1989)** and the "Reference Notes" were not found online; the station index (L1) is derived from the 1989 book. Public domain if located.
- **Lightship Sailors Association:** no website found in two searches; its historian (Doug Bingham) compiled L1. Contact is the owner's call.
- **US Lightship Museum (Boston, LV-112)** and the museums at Baltimore, Lewes, Astoria, Seattle, Port Huron, Portsmouth, Oakland: per-vessel histories; not fetched.
- **Secondary:** Morgan MacKenzie, *American Lightships, 1820-1983* (East Carolina University MA thesis, 2011, open access, 224 pages; construction and archaeology, no station gazetteer).

### L7. Positions for lightship stations

- **Light Lists on archive.org** carry the lat/lon of each light vessel: `lightlistatlant00servgoog` (1893), `lightlistatlant01servgoog` (1900),
  `lightlist00unkngoog` (1947, Great Lakes), `lightlistpacific00unit` (1988), 1986 volumes. Full text: `https://archive.org/download/<id>/<id>_djvu.txt`
  (archive.org robots disallows only `/control/` and `/report/`; search via `advancedsearch.php`, tested). Research source; needs a per-station search.
- **Where a station was replaced by a lighthouse or tower** (53 cases in L1), the station's position is the structure's.
- **Modern successors** (large navigational buoys and light towers: Ambrose, Diamond Shoal, Frying Pan, Columbia River, Nantucket Shoals) are in the current Light List (T5 pattern, other volumes).
- **Otherwise** compute from the L1 bearing and distance from the named lighthouse (miles not specified as statute or nautical; mark `precision: approx`).

### L8. Wikidata and OSM for lightships (QLever)

- **Wikidata (CC0):** class `lightvessel` is **Q831515** (`qlever/q_lv.rq`, `qlever/lv.json`): **134 items worldwide, about 20 are US vessels**, and almost all are survivors or famous wrecks:
  Barnegat (Q4861475, NRHP 79002317, coordinates still at Philadelphia, stale), Portsmouth (Q7890709, 89001080), Swiftsure (Q7656131, 75001852), Ambrose LV-87 (Q7890707, 84002758),
  Chesapeake (Q7892539, 80000349), Columbia (Q7892541, 89002463), Frying Pan (Q588285, 98001615), Huron (Q7892543, 76001974), Nantucket LV-112 (Q2270033, 89002464),
  Overfalls (Q7892547, 89000006), Relief WLV-605 (Q7892546, 89002462), Lightship No. 114 (Q6546566, 90000777), plus the sunk ships Diamond Shoal LV-71 (Q5270918, NRHP 15000541),
  LV-117 (Q7892542), Buffalo LV-82 (Q33189299), and the items for WLV-612 (Q33189313) and several bare hull numbers (LV17, LV83, LV86, LV94).
  Fields: coordinates (berth), NRHP number. **Wikidata has no class of lightship *station***; I did not find those items.
  **Recommended use:** `bulk source` for the survivors' berth coordinates and NRHP/NHL numbers; join to Rowlett (L5) by hull number.
- **OSM:** `seamark:type=light_vessel` or `ship=lightship` (and named historic ships) returns 26 objects worldwide; the US ones are Relief (Oakland), Portsmouth, Frying Pan (Hudson River Park, NYC),
  Columbia (Astoria), Nantucket LV-112 (East Boston), Barnegat (Camden NJ, matching Rowlett's "derelict"), Huron (Port Huron). Seven US vessels with berth geometry; `regional source`.

### Links to light stations (Part 2)

- L1 location text names the nearest lighthouse with distance and bearing for most stations; 53 entries say which lighthouse or tower replaced the station.
- L2 pages hold a state and "Light list data". Use L1 names to attach each station to a `us-<state>-<slug>` light station (fuzzy, then reviewed).
- Examples of a lightship station replaced by a lighthouse: Eel Grass Shoal (Latimer Reef), Northwest Passage (Northwest Passage Lighthouse), Hoopers Straight (Hooper Island Light).

---

## Part 3. Life-saving stations (US)

**Counts:**

- **1909 USLSS annual report:** **281 stations**: 1st (ME, NH) 14; 2nd (MA) 32; 3rd (RI, Fishers Island) 9; 4th (Long Island) 33; 5th (NJ) 42;
  6th (Cape Henlopen to Cape Charles) 19; 7th (Cape Henry to Cape Fear) 34; 8th (SC, GA, east FL) 10; 9th (Gulf) 8; 10th (Erie, Ontario, Louisville) 12;
  11th (Huron, Superior) 18; 12th (Michigan) 31; 13th (Pacific) 19. The federal Service was never much larger than this; it merged into the Coast Guard in 1915.
- **USLSSHA "Station Sites":** **582 site records** (all eras including Coast Guard stations), by state: AK 6, AL 2, AS 1, CA 28, CT 2, DC 1, DE 8, FL 38,
  GA 3, HI 3, IL 7, IN 1, KY 2, LA 6, MA 51, MD 14, ME 23, MI 61, MN 3, MS 3, NC 44, NH 5, NJ 69, NV 1, NY 66, OH 11, OR 24, PA 3, PR 1, RI 11, SC 4, TX 17, VA 26, VT 1, WA 19, WI 17. Plus **about 843 station-building records**.
- **USCG Historian "Historic Lifesaving & Other Shore Stations":** about **420 to 450 station names** (index snapshot 2020; names only, ME 16, NH 6, VT 1, MA about 51, RI 10, CT 3, NY about 53, NJ about 49, PA 2, DE 6, MD 10, DC 1, VA 20, NC about 32, SC 3, GA 2, FL 29, PR 1, AL 1, MS 2, LA 2, TX 11, CA 20, OR 12, WA 13, AK 4, HI 2, OH 6, KY 1, MI about 48, IN 1, IL 6, WI 12, MN 1 — approximate because the page is hand-edited).
- **Florida Houses of Refuge:** **10** (Bethel Creek/Indian River, Gilbert's Bar, Orange Grove, New Inlet, Biscayne Bay; then Smith's Creek/Bulow, Mosquito Lagoon, Chester Shoal, Cape Malabar, Indian River Inlet); only Gilbert's Bar survives.
- **Massachusetts Humane Society:** no consolidated list found. Counts from histories: 18 lifeboat stations by 1845; 78 lifeboats and 92 boathouses and huts by 1871. Use the Society's own reports and the USLSS reports of the 1870s (not verified).

### S1. USLSSHA "Station Sites" and "Station Buildings"

- **URLs:** `https://uslife-savingservice.org/station-sites-search/` (list, 10 per page, 59 pages, "total_rows 582" in the embedded FacetWP config);
  `https://uslife-savingservice.org/station-sites/<slug>/`; sitemaps `.../station_sites-sitemap.xml` (583 URLs) and `.../station_buildings-sitemap.xml` (844 URLs). Cached in repo `data/raw/...` root (`usls_*`).
- **Fields (site page):** name, town, state, also-known-as, year established (often "1855?"), active range, year closed, "original site location" flag,
  **designation number** (the Coast Guard station number, e.g. 124 for Absecon), notes that cite "USLSS Annual Reports" and "USCG Historian's Website", the list of buildings and whether each survives.
  Building page: built year, designer, condition, current use, survives or not.
- **Coordinates: unusable.** The embedded map data has `lat` and `lng` values of 0, 4, 7, 357, 800 (corrupted); the page only embeds a Google map query for the *town*. Geocode from the town plus other sources.
- **robots.txt (quoted):** `User-agent: *` / `Disallow:` (nothing disallowed), Yoast sitemap listed. No AI crawler named.
- **Licence / terms:** footer "© U.S. Life-Saving Service Heritage Association, All Rights Reserved". **Terms of Service (`/terms-of-service/`) say you must not republish, reproduce, copy or redistribute material from the site.** Facts only (names, towns, years, designation numbers), no prose, with credit and link; the owner may want to ask permission (outreach notes are the owner's to send).
- **Quality:** a volunteer registry; years carry "?" marks; includes later Coast Guard stations (Active: Yes). Not copied from the USCG pages but cites them.
- **Recommended use:** `bulk source` for the station list (facts only) and the best state-by-state count. Table of 582 above.
- **Sample:** Absecon Station Site, Atlantic City NJ, established 1855 (uncertain), active to 1917, closed 1922, designation 124, 1896 station house survives as a children's hospital facility.

### S2. USCG Historian station histories (Wayback copies; public domain)

- **URLs:** station index (names, by state) `https://www.history.uscg.mil/Browse-by-Topic/Assets/Land/Stations-Units/` (403 live); **tested Wayback copy**
  `https://web.archive.org/web/20200807100704id_/https://www.history.uscg.mil/Browse-by-Topic/Assets/Land/Stations-Units/` (cached `uscg_stations_index.html`).
  Station articles `.../Stations-Units/Article/<id>/station-<name>-<state>/`; **292 distinct station articles are archived** (`cdx_uscg_stations.txt` lists them: NY 41,
  NJ 38, MI 34, MA 30, NC 29, ME 15, VA 12, CA 8, WI 8, WA/FL/OR 7 each, DE/TX 6, six Houses of Refuge...). Tested article:
  `https://web.archive.org/web/20221203230316id_/https://www.history.uscg.mil/Browse-by-Topic/Assets/Land/Stations-Units/Article/2562304/station-absecon-new-jersey/` (cached `uscg_absecon.html`, 568 KB mostly menus).
- **Fields (Absecon):** USLSS station number and district, Coast Guard station number, **location text with latitude and longitude in degrees-minutes-seconds in 1878 and again in 1915**, date of land conveyance, year station built, fate, remarks on land titles, **keeper list with appointment and departure dates** (a keepers-index source), photo credits, sources (an unpublished "Register of the Stations and Keepers of the U.S. Life-Saving Service", c. 1977, and Shanks, York and Shanks, *The U.S. Life-Saving Service*, 1996).
- **Access:** Wayback `id_` fetch of each URL listed by CDX; 7 s per page; Wayback rate-limits (429 and 504 seen when running several lookups close together).
- **robots.txt:** live site 403 (unreadable); Wayback no rules.
- **Licence:** US government work, public domain (individual photographs credit donors).
- **Quality:** the richest per-station source with coordinates and keepers; the live site has more articles than Wayback saw (captures 2019-2024).
- **Recommended use:** `research source (cite per station)` and `regional source` for coordinates and keepers, if we get live access it becomes a **bulk source** for ~450 stations.
- **Sample:** Station Absecon, New Jersey: USLSS station 28 in the Fourth District (the report numbering differs by year), CG station 124, built 1872 at Chelsea, 2.75 miles southwest of Absecon Inlet, about 39-20-45 N / 74-27-27 W in 1878, keepers from 1872 (Rose, Eldridge, Blackman, Galskill, Steelman, Parker, Riley), given to GSA in 1955.

### S3. USLSS annual reports (Internet Archive full text; public domain)

- **Search:** `https://archive.org/advancedsearch.php?q=title%3A%28annual+report+life-saving+service%29+AND+mediatype%3Atexts&fl[]=identifier&fl[]=title&fl[]=year&rows=60&output=json` returned **18 items**
  (1876, 1877, 1878, 1883-1885, 1888, 1889, 1891, 1893, 1896, 1899, 1902, 1903, 1909 ...). Full text: `https://archive.org/download/<identifier>/<identifier>_djvu.txt`.
  Tested: `annualreportofun00unit_2` (FY1909, 1.5 MB text, 139,000 lines, cached `ia/uslss_1909_djvu.txt`). Another volume I tried (1878) timed out at 120 s.
- **What a report holds:** list of stations by district with counts (above); a **station location table** with station name, district, a **location phrase relative to a lighthouse** ("5.5 miles north of Absecon light"), and **latitude and longitude** in degrees-minutes-seconds (OCR rows
  for about 145 stations recovered by a simple regex; a proper table parser is needed); crew and keeper lists; and the **wreck-by-wreck narrative** (vessels, casualties, rescues) that the stories need (DESIGN section 1).
- **robots.txt:** `archive.org` disallows only `/control/` and `/report/`. **Licence:** public domain (1876-1914). The Historian's page also lists these volumes as PDFs (not reachable).
- **Quality:** OCR is readable; table columns are split across lines. 13 districts by 1909.
- **Recommended use:** `bulk source` for the 1909 or 1914 snapshot (station list, district, coordinates), and `research source` for wrecks and rescues.
- **Sample:** 1909 table row (own reading): Atlantic City, Fifth District, at Absecon light, 39-22-00 N / 74-24-50 W.

### S4. Wikipedia "List of United States Coast Guard stations"

- **URL:** `https://en.wikipedia.org/wiki/List_of_United_States_Coast_Guard_stations` (1.7 MB HTML; cached `wp/List_of_USCG_stations.html`).
- **Coverage:** **412 rows** in per-state tables (NY 49, MA 40, NJ 43, NC 33, MI 42, FL 29, ME 20, VA 20, CA 20 ...). Columns: station, location, opened, closed, "Life-Saving Station?", LSS number, LSS district, CG station number.
- **Quality:** partial and uneven: many "Unknown" cells and merged rows (rowspans), so counting "Yes" by regex is unreliable (about 73 flagged).
- **Licence:** CC BY-SA 4.0. **Recommended use:** `regional source` / cross-check of district and station numbers only.

### S5. USLHS Digital Archive: Lifesaving Station and House of Refuge places

- **URLs:** `https://archives.uslhs.org/type-place/lifesaving-station` (**67** places, 2 pages); `.../type-place/house-refuge` (1: Gilbert's Bar);
  sample `https://archives.uslhs.org/places/gilberts-bar-house-refuge` (cached `uslhs_gilberts.html`). Rules as L2.
- **Fields:** type, year established, existing yes/no, owner, open to public, lat/lon (DMS) on the house-of-refuge page, county, comment, photos.
- **Recommended use:** `facts only, link` for survivors and a few positions. The 67 is a fraction of the stations, so not a bulk source.

### S6. Houses of Refuge (Florida)

- **Sources:** `https://en.wikipedia.org/wiki/Houses_of_Refuge_in_Florida` (not fetched; named by search); USCG Historian pages for Gilbert's Bar
  (`.../Article/2650172/gilberts-bar-house-of-refuge-florida/`), Cape Malabar, Chester Shoal, Indian River, Mosquito Lagoon, Orange Grove (six archived); USLHS (above);
  Palm Beach County and Broward County history articles; the Florida Historical Quarterly. Sizes and years: first five built 1876 by Albert Blaisdell about 25 miles apart, five more 1885-86; keepers lived on the first floor.
- **Count:** 10; only Gilbert's Bar (Hutchinson Island, Martin County) survives, as a museum.
- **Recommended use:** `research source`; list the ten by hand from the USCG pages.

### S7. Massachusetts Humane Society stations

- **Finding:** no list online that I could find. Facts from histories (NPS Cape Cod pages, Scituate and Orleans historical societies, Wikipedia "Massachusetts Humane Society"): first hut 1787 at Scituate's Third Cliff; first lifeboat station Cohasset 1807; six Cape Cod huts early 1800s; 18 stations by 1845; 78 lifeboats and 92 boathouses and huts by 1871; the Society kept equipment until 1946. Federal stations at the nine Cape Cod sites came 1872.
- **Recommended use:** model as a small set of `life_saving_station` records only where a named station exists in a source; treat huts as events on nearby stations. Needs a research pass in the Society's annual reports and the 1870s USLSS reports.

### S8. NRHP and HABS/HAER for life-saving stations

- **NRHP Multiple Property Submission** "U.S. Government Lifesaving Stations, Houses of Refuge, and pre-1950 U.S. Coast Guard Lifeboat Stations" (nationwide, Coast Guard sponsored; recent listings include Old Coast Guard Station Manasquan Inlet, May 2021) and the older **"Lifesaving Stations of Maine"** MPS. Cover documents and individual nominations on NPGallery (`npgallery.nps.gov/AssetDetail/NRIS/<id>`, no robots rules); I did not find a full property list.
- **Wikipedia category** `Category:Life-Saving_Service_stations_on_the_National_Register_of_Historic_Places` lists 18 articles; `Category:Life-Saving_Service_stations` has 24.
- **Better path:** filter the NPS National Register dataset (bulk, other agent) for names matching "Life[- ]Saving|Lifesaving|Coast Guard Station|House of Refuge" to get NRIS ids and coordinates.
- **HABS/HAER (LoC)** phrase search `"life saving station"` returned **11 records** (e.g. Caffey's Inlet NC, Cape Lookout NC, Avalon NJ, Vermilion MI); more under "life-saving" and "lifesaving".
- **NPS Inventory of Historic Life-Saving Stations** (retired pages; Wayback copies by state, for 17 states: CA, CT, DE, FL, IL, MA, MD, ME, MI, NC, NJ, NY, OR, RI, VA, WA, WI) lists only surviving, visitable stations (North Carolina: 4: Caffey's Inlet, Chicamacomico, Kitty Hawk, Ocracoke). `research source` for "can I visit", with owner and current use.
- **NARA Record Group 26 logbooks:** station logbooks for the Cleveland, Jacksonville, Norfolk and New Orleans districts 1874-1942 (finding aid on `archives.gov/atlanta`, not fetched).

### S9. Wikidata and OSM for life-saving stations (QLever)

- **Wikidata (CC0):** no single class. Items with an NRHP number (P649) and a label matching life-saving / lifesaving / House of Refuge / lifeboat / Coast Guard Station
  (`qlever/q_lss.rq`) give **45 items, 43 with coordinates** (e.g. Amagansett, Avalon, Bodie Island, Caffey's Inlet, Chicamacomico, Fort Hancock, Gilbert's Bar, Humboldt Bay, Indian River, Kitty Hawk,
  Klipsan Beach, Nahant, North Manitou, Old Harbor, Point Allerton, Point Reyes, Quogue, Racine Harbor, Squan Beach, West Quoddy), including the two MPS items (**Lifesaving Stations of Maine MPS, NRHP 64500263**;
  **U.S. Government Lifesaving Stations, Houses of Refuge, and pre-1950 U.S. Coast Guard Lifeboat Stations MPS, NRHP 64501177**: the number to search NPGallery for the full property list).
  Class `lifeboat station` (**Q11997323**), US only: **23 items, all with coordinates**. A wider label-only query across all US items returned a 502; not repeated.
  **Wikidata holds about 45 of roughly 280 to 580 stations**, so it is a coordinate and NRHP-id source for the listed ones, not a list.
- **OSM:** no consistent tag. A name search (`osmkey:name` matching "Life Saving Station", "Lifesaving Station", "House of Refuge", "Lifeboat Station") found 398 objects worldwide, **about 100 in the US, of which roughly 50 to 60 are genuine stations**
  (the rest are churches called "House of Refuge", parking lots, cemeteries); e.g. Indian River, Nahant, Klipsan Beach, Sullivan's Island, Thunder Bay Island, Wood Island, Elberta, Jupiter Inlet, Gilbert's Bar, Biscayne House of Refuge.
  The query took 100 s: run it once, cache the result. `regional source` for coordinates after a name match.

### Links to light stations (Part 3)

- 1909 report location table: every station's distance and bearing from a named light (e.g. Atlantic City "at Absecon light"). Parse the phrase `<n> miles <direction> of <Name> light`.
- USCG station pages: coordinates in 1878 and 1915 and place names; match to light stations by distance.
- USLSSHA: town and state only (join by town to a light station in the same town, then check).
- Several stations shared a site with a lighthouse (Racine Harbor, Sandy Hook); the NRHP names them together.

---

## Counts (summary)

| Item | Count | Source |
|---|---|---|
| PR historic lights | 16 (+ Cabras lost); Wikidata 17 items, OSM 15 | T1, T2, T3, T6, T7 (HAER PR-32..47 = 15 lights + dwelling) |
| USVI / Guam / AS / CNMI / outlying | 4-5 / 2 historic (+3) / 3-4 / 2 / 3-4 | T1, T4 |
| Lightship stations | 116 (USCG), 139 (USLHS), ~125-135 distinct | L1, L2 |
| Lightship vessels | 113 numbered LV + lettered + WLV; ~140-150 | L1, L3, L4 |
| Surviving US lightships | ~16 (13 per Rowlett); Wikidata ~20 US vessel items, OSM 7 berths | L5, L8 |
| LSS stations 1909 | 281 | S3 |
| LSS sites ever (USLSSHA) | 582 (+843 buildings) | S1 |
| USCG Historian station names | ~420-450 (292 archived articles) | S2 |
| Houses of Refuge (FL) | 10 | S6 |
| Territory lights in Wikidata / OSM | 25 / 20 | T6, T7 |
| LSS items in Wikidata / OSM | ~45 NRHP + 23 lifeboat-station class / ~50-60 genuine | S9 |

## Gaps and risks

- **USCG Historian access** (blocker 1). The Wayback route works but is slow, partial (292 of ~450 articles), rate-limited (429, 500, 504 seen) and about four years behind.
- **Lightship station coordinates** are not published anywhere I found; they will be `approx` or hand-built from Light Lists.
- **Lightship survivor berths** conflict between sources. Check each vessel.
- **USLSSHA terms** forbid copying; use names, towns and years only, credit and link, and decide whether to ask permission.
- **Wikidata and OSM are thin for lightship stations and life-saving stations** (no station class; about 45 NRHP life-saving items; OSM names are noisy). They help with coordinates, not with the list. QLever is rate-limited and sometimes returns 429 or 502 on broad queries.
- **Spanish-era detail** (keepers, torreros) is in archives (AHN) and in a journal article that failed TLS; expect thin keeper rosters for PR before 1900.
- **IRMA** download files are off limits (robots); NPS inventories only via Wayback.
- **Scope calls for the owner:** modern pile beacons in Guam and Samoa (excluded by DESIGN 1), the Howland "Earhart Light" memorial daybeacon (a real aid to navigation from 1937, now a ruin?), and whether Navassa (US-administered, claimed by Haiti) counts as a US territory for this site; DESIGN names minor outlying islands "if any lights are found there".

## Recommended fetcher order

1. **`uscg_lightship_station_index`** (L1): one Wayback PDF, parse 116 stations and ~410 vessel lines; also extract the "from the X Lighthouse" and "replaced by" links.
2. **`light_list_territories`** (T5): Light List volumes III and VI for active PR, VI, Guam, AS, CNMI lights; the same fetcher handles all seven volumes for the other agents.
3. **`territories_seed`** (T1, T2, T3, T4): hand-curated list of about 35 candidates joined by name to Light List LLNR, NRIS ids, HAER item ids and ARLHS numbers.
4. **`uslhs_archive`** (L2, S5): category pages and place pages for lightship stations, lifesaving stations, houses of refuge (about 4 + 2 + 1 list pages, a few hundred place pages; 2 s apart).
5. **`lightship_vessels`** (L3, L4, L5): Wikipedia table plus NMA table plus Rowlett survivors, joined by hull number; flag conflicts.
6. **`uslssha_sites`** (S1): the 583-URL sitemap or 59 list pages; facts only.
7. **`uslss_annual_reports`** (S3): download 1909 and the last report, parse the station-location table (name, district, light-relative phrase, lat/lon).
8. **`uscg_historian_stations`** (S2): via Wayback now (292 articles), via the live site if access is granted; keepers and coordinates.
9. **Wikidata** (T6, L8, S9) and **OSM** (T7, L8, S9) through QLever with narrow queries (`qlever/*.rq` are tested starting points; the OSM name-regex query takes ~100 s, run once and cache); NRHP dataset filter (S8) for coordinates.
10. Research-only (no fetcher): NPGallery and LoC HAER/HABS per station, Spanish and AHN material, Flint's histories, Humane Society records.

## Cached files (all under `data/raw/survey/territories_lightships_lss/`)

`robots_*.txt` (every host); `lsi.txt` and `LIGHTSHIP_STATION_INDEX.pdf`; `wp_lightships_list.json`, `wp/*.html`; `nps_inv/`;
`npg/`, `npg_77001549.html`; `loc_habshaer_pr.json`, `loc_habs_lss.json`; `rowlett/`; `lightlist/` (V3, V6 PDF and text);
`uslhs/`; `usls_*`; `uscg_stations_index.html`, `uscg_absecon.html`, `cdx_*.txt`; `ia/uslss_1909_djvu.txt`, `ia_*.json`;
`nma/wal.html`; `farosdepur_trasfondo.html`; `wd_Q6982191.json`; `qlever/` (queries `*.rq` and results `territories.json`, `lv.json`, `lss_nrhp.json`, `lifeboat_us.json`, `osm_lh.json`, `osm_lv.json`, `osm_lss.json`).
