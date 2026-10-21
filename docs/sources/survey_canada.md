# Source survey: Canada (key `canada`), 2026-10-21

Scope: lighthouses (standing and lost), range / pier / harbour lights with a structure, lightships,
lifesaving stations, and the Canadian historical sources research agents will cite. Raw samples and
caches are under `data/raw/survey/canada/` (git-ignored, about 66 MB). All requests used the
`FresnelBot/0.1` User-Agent, at most one request per 2 s per host (20 s on open.canada.ca, 10 s on
sites that ask for it). About 14 of the 25 WebSearch calls were used.

## Read this first: rule deviations and hard skips

1. **Endpoints I used before the orchestrator's note, and what replaced them.** The orchestrator
   ruled mid-survey that `query.wikidata.org/sparql` and Overpass (overpass-api.de and mirrors) are not
   to be used, because their robots.txt disallows those paths (`https://query.wikidata.org/robots.txt`:
   `User-agent: *` / `Disallow: /sparql`). **I had already used both**: about 9 WDQS queries and
   5 Overpass requests on `overpass.kumi.systems` (plus 1 on `overpass.private.coffee`). I then
   re-ran the key counts on **QLever** (`https://qlever.dev/api/wikidata`, `https://qlever.dev/api/osm-planet`;
   `qlever.dev/robots.txt` is a 404, i.e. none) and they **agree exactly**: Wikidata 488 Canadian
   lighthouse items with the identical province split (NS 122, NL 67, NB 59, PE 59, QC 57, ON 52,
   BC 48, MB 15, 9 unassigned), and OpenStreetMap 1,485 `man_made=lighthouse` objects in Canada
   (relation 1428125). QLever answers are cached in `data/raw/survey/canada/qlever/`. **Fetchers
   must use QLever for Wikidata and OSM.** The earlier WDQS/Overpass extracts are kept only as
   cross-checks.
   **Not covered by that ruling, still open:** I also used the MediaWiki Action API
   (`en|fr.wikipedia.org/w/api.php`, about 22 calls). The Wikipedia/Wikidata robots files list
   `Disallow: /w/` for `*` (exceptions only for `/w/load.php?`, `mobileview` and the REST doc) and
   `Disallow: /wiki/Special:`. If the same reading applies, the Wikipedia list tables (1.8) should be
   fetched some other way or dropped. They are the lowest-value source here, so dropping them costs
   little.
2. **Skipped because robots.txt names Claude/Anthropic crawlers** (recorded, nothing fetched beyond
   robots.txt):
   - Canadiana: `https://www.canadiana.ca/robots.txt` has `User-agent: anthropic-ai`, `ClaudeBot`
     and `Claude-Web`, each `Disallow: /`; header says "Policy: block AI training and retrieval
     crawlers". This is where the Sessional Papers and the 1864 Admiralty List of Lights live.
   - BAnQ numérique: `https://numerique.banq.qc.ca/robots.txt` has `# Anthropic` /
     `User-agent: ClaudeBot` / `Disallow: /`.
   - Nauticapedia (BC marine history, keeper sequences): `https://www.nauticapedia.ca/robots.txt`
     has `User-agent: ClaudeBot` / `Disallow: /` (and `CCBot`).
3. **Skipped because the path is disallowed or challenged:**
   - Library and Archives Canada collection search: `recherche-collection-search.bac-lac.gc.ca/robots.txt`
     is `User-agent: *` / `Disallow: /`, with only Googlebot allowed.
   - Provincial Archives of New Brunswick: `archives.gnb.ca/robots.txt` disallows `/Search/`,
     `/text/`, `/digitized-documents/`, `/documents/`, `/photos/` for `*`.
   - Island Newspapers (PEI, `islandnewspapers.ca`) and Maritime History of the Great Lakes
     (`images.maritimehistoryofthegreatlakes.ca`): both answered with a Cloudflare "Just a moment"
     challenge. Not circumvented.
   - Memorial University digital collections (`collections.mun.ca`): the TLS certificate fails
     verification. I made one unverified GET of its robots.txt only to diagnose it; nothing else.
4. **Overpass behaviour (for the record).** Country-wide `area[ISO3166-1=CA]` queries were slow or
   timed out on the public mirrors (`overpass.private.coffee` timed out; `overpass.kumi.systems`
   answered the first query in about 3 minutes, then timed out or returned 504 on follow-ups). I
   stopped there. The lifecycle tag forms were counted afterwards on QLever (see 1.7).

---

## 1. Station lists and registers

### 1.1 Canadian Coast Guard List of Lights, Buoys and Fog Signals (current, 2026 edition)

- **URL:** `https://www.notmar.gc.ca/list-livre-en.php` (index, French `list-livre-fr.php`).
  Complete volumes: `https://www.notmar.gc.ca/publications/list-lights/<vol>/<vol>volumee.pdf`
  with `<vol>` = `newfoundland/nlvolumee`, `atl/atlvolumee`, `inland-waters/iwvolumee`,
  `pac/pacvolumee`, `arc/arcvolumee`. Per-section HTML: `.../list-lights/atl/atl163-en.php`; PDF:
  `.../atl/ATL163e.pdf`. Dataset descriptions: `https://e-navigation.canada.ca/gn/description/eng/<uuid>`
  (Atlantic `1449a2d2-ba89-4868-b606-931b7624c216`, NL `c4233f87-19e3-45ad-8a36-e1a4b0c2670b`).
- **Coverage:** every aid to navigation the Coast Guard approves: lighthouses, skeleton towers,
  range lights, light buoys, beacons, fog signals. **Active aids only**: no lost or deactivated
  lights. Five volumes: Newfoundland and Labrador (154 pp), Atlantic incl. the St. Lawrence to
  Montréal (329 pp), Inland Waters west of Montréal (200 pp), Pacific (154 pp), Arctic incl. Hudson
  Bay, Mackenzie River and Great Slave Lake (74 pp). Sections are corrected monthly (latest
  corrections stamped 09/2026). Roughly 2,000 entries carry an international (Admiralty, `H####` or
  `G####`) number, i.e. lit fixed structures; most are small skeleton towers. DFO says the country
  has "more than 750 lighthouses and long range lights" (see 1.5).
- **Fields:** list number (Atlantic and NL regional numbering, e.g. `A-247`, `N14`, `P435` appear as
  Wikidata P3920), Admiralty number, name, position to 0.1 arc-second, characteristic, colour,
  period, focal height (m), nominal range (nm), structure description with height, seasonality,
  fog signal and remarks. No years, no keepers, no prose.
- **Access:** the HTML sections are clean tables (`<table class="wb-tables ...">`, one `<tr>` per
  aid, buoys in `<em>`, fixed lights carry an `H` number in italics under the list number). Tested:
  `atl163-en.php` parses to 83 rows (49 non-italic). PDFs convert with `pdftotext -layout` (all five
  volumes: 32 MB of PDFs, 25 MB of text, cached in `data/raw/survey/canada/ccg/vols/`). One request
  per section HTML is about 190 requests for everything; or 5 PDFs.
- **robots.txt (`https://www.notmar.gc.ca/robots.txt`):** `User-agent: *` / `Disallow: /zip-publication-en.php`
  / `Disallow: /zip-publication-fr.php` / `Disallow: /tmp/`. Nothing we need is blocked. The
  `e-navigation.canada.ca` host has no robots.txt (404).
- **Licence:** the front matter says "© His Majesty the King in Right of Canada, as represented by
  the Canadian Coast Guard, 2026" (Cat. No. D16-5E-PDF). No open licence is stated on the volume or
  on the e-Navigation dataset page; Canada.ca "Terms and conditions" is linked in the footer. We
  take facts (position, characteristic, height, range) with credit. Confirm the Canada.ca
  reproduction terms before publishing the database commercially.
- **Quality:** authoritative and current for active lights; coordinates are surveyed; descriptions
  are terse. Contains no heritage or lost lights. The DFO page notes issues were skipped 2016–2021 in
  the monthly PDF series, but the 2026 volumes are current.
- **Recommended use:** **bulk source** for the `light` block (characteristic, focal height, range,
  fog signal) and position of every active aid. Also the cross-key for Admiralty numbers.
- **Sample:** Cape Race, NL: list no. 1, Admiralty H0444, 46°39'30.9"N 53°04'25.0"W, flashing white
  every 7.5 s, focal height 51.8 m, range 27 nm, white cylindrical tower with red upper part, 20.7 m
  tall, fog horn, operates year round.

### 1.2 Parks Canada: Heritage lighthouses of Canada (Heritage Lighthouse Protection Act)

- **URL:** `https://www.pc.gc.ca/en/lhn-nhs/pp-hl` (French: `.../fr/lhn-nhs/pp-hl`); detail pages
  `https://www.pc.gc.ca/apps/dfhd/page_hl_eng.aspx?id=<DFHD identifier>`.
- **Coverage:** the designated heritage lighthouses, standing only. **115** at 2026-03-31 (DFHD
  count); the page says "more than 100". By province (DFHD): NS 26, BC 21, ON 18, NL 16, PE 13,
  QC 11, NB 8, MB 2.
- **Fields:** official name, community and province, designation year, a one-paragraph description
  (year built, height, form), and, in the page's table markup, **a WKT point per lighthouse**
  (`data-geometry="POINT (-123.29151 48.87338)"`, 5 decimal places). 114 detail links on one page.
- **Access:** one HTML page, 150 KB, whole list server-rendered (client-side pagination only).
  Cached as `data/raw/survey/canada/pc_hl.html`.
- **robots.txt:** `https://www.pc.gc.ca/robots.txt` returns 404 (none).
- **Licence:** none stated on the page; Government of Canada content under Canada.ca terms. The
  statements of significance are also in the Open Government Licence dataset (1.3).
- **Quality:** authoritative for designation; the HLPA petition process (348 petitions in 2010–12
  by the one press summary I saw) is not published as a list, only the designations.
- **Recommended use:** **regional source** (heritage register) for status, designation year and
  exact position of 115 lights; key = DFHD identifier (= Wikidata P3211).
- **Sample:** Active Pass Lighthouse, Mayne Island BC, designated 2013, built 1969, 13.7 m concrete
  "apple core" tower, position 48.87338 N, 123.29151 W.

### 1.3 Directory of Federal Heritage Designations (open.canada.ca) with statements of significance

- **URL:** dataset `https://open.canada.ca/data/dataset/49d5ba7d-d860-40d9-9183-892979e4acbe`;
  CSV `.../resource/682d1e12-26dd-4d30-bb40-f04658502bcd/download/dataset-of-federal-heritage-designations-as-of-march-31-2026.csv`
  (13.7 MB; French `.../7c2ec7b9-2b70-402d-91f0-e1cac3fd4e50/...`; XLSX also offered).
- **Coverage:** 3,889 federal designations (National Historic Sites, Persons, Events, Federal
  Heritage Buildings, Heritage Railway Stations, **Heritage Lighthouses**). Lighthouse-related rows:
  **115** Heritage Lighthouse of Canada (the `Heritage Lighthouse Number` column is filled),
  13 National Historic Sites named for lighthouses (e.g. Cape Race, Cape Spear, Cape Pine, Pointe-au-Père,
  Île Verte, Cap-des-Rosiers, Point Clark, Mississauga Point, Triple Island, Fisgard, Point Atkinson,
  Miscou Island), about 60 FHBRO lighthouse buildings (Recognized or Classified), and one National
  Historic Event ("Construction of the Sambro Island Lighthouse"). Also **Sable Island Humane
  Establishment (1801–1958)**, National Historic Event 2021-04-28, id 16352: the only federal
  designation I found for lifesaving. No lightships.
- **Fields:** identifier, name, other names, designation type and statute, designation date, research
  report numbers, a "Highlight" line, the full statement of significance (description, heritage value,
  character-defining elements), commemorative inscription, address, local area, province, custodian,
  construction start/end dates, associated persons/architect/builder, Heritage Lighthouse Number,
  FHRO number. No coordinates (use 1.2 for those).
- **Access:** one CSV download (cp1252-encoded; the file starts with a title line fused to the
  header, so find `Identifier,Designation name` and parse from there). A lighthouse subset
  (metadata only) is in `data/raw/survey/canada/opencanada/dfhd_lighthouse_subset.json`.
- **robots.txt (`https://open.canada.ca/robots.txt`):** `User-agent: *` / `Crawl-delay: 20`, then
  disallows for `/core/`, `/libraries/`, `/modules/`, `/profiles/`, `/scripts/`, `/sites/`,
  `/themes/` and some files. The CKAN API (`/data/api/3/action/...`) and `/data/dataset/.../download/`
  are not disallowed; **honour the 20 s delay**.
- **Licence:** `ca-ogl-lgo`, "Open Government Licence - Canada" (CKAN `license_id` and
  `license_title`). Attribution is required; text may be reused, so statements of significance can be
  quoted with a link.
- **Quality:** modified 2026-10-04; authoritative for designations; the page also lists lighthouses
  the Heritage Lighthouse Protection Act protects, not every historic light.
- **Recommended use:** **bulk source** (heritage status + citable statements of significance) and
  **research source** for the 130 or so designated stations.
- **Sample:** Fisgard Lighthouse, Colwood BC: Heritage Lighthouse number 168, designated 2013-05-23,
  custodian Parks Canada, built 1859–61; also a National Historic Site.

### 1.4 Canadian Register of Historic Places (historicplaces.ca)

- **URL:** per place `https://www.historicplaces.ca/en/rep-reg/place-lieu.aspx?id=<n>` (`/fr/` for French).
- **Coverage:** federal, provincial and municipal listings; the ids for lighthouses come from
  Wikidata P477 (195 Canadian lighthouse items carry one) and from the federal CSV. Whole-register
  size not counted.
- **Fields (in `<meta>` tags on each page):** `PlaceLatitude`, `PlaceLongitude`, `CommonName`,
  `PlaceNames`, `ConstructionDate` (as a range), `Description` (the statement of significance),
  `HeritageValue`, `CharacterDefiningElements`, `Location`, `PlacePrimaryImage`, `ProvinceId`,
  `JurisdictionId`, `PurposeTypeId` (126 appears on a light tower). Tested id 13042.
- **Access:** per-id pages work (52 KB each). **The search results URL I tried
  (`results-resultats.aspx?q=lighthouse`) returned HTTP 500**; discover ids from Wikidata and the
  federal CSV instead, or find the working search-parameter form before building a fetcher.
- **robots.txt:** 404 (none).
- **Licence:** none stated on the page; the federal statements are Open Government Licence. Provincial
  and municipal statements are the authorities' own; treat as facts + link.
- **Recommended use:** **research source (cite per station)** and a coordinate / construction-date check.
- **Sample:** Cape St. Mary's Light Tower, St. Bride's NL, position 46.82305 N 54.19601 W, built
  1859–60, Recognized Federal Heritage Building, octagonal tapered tower later given a concrete shell.

### 1.5 DFO "Lighthouses" pages (staffed, surplus, transferred)

- **URLs:** `https://dfo-mpo.gc.ca/otw-am/lighthouses-phares/index-eng.html`;
  `.../canada-eng.html` (types, staffed, surplus); `.../publications/lightstationsnl-lespharestnl-eng.html`
  (Newfoundland and Labrador, with a 5.9 MB PDF); `https://dfo-mpo.gc.ca/rp-bi/lh-ph-eng.htm`
  (Alternate Use Study, Surplus Lighthouses, final report March 2011, appendix of divested lights).
- **Coverage/facts:** "more than 750 lighthouses and long range lights"; lighthouses in every
  province except Alberta and Saskatchewan; "over 100 lighthouses" transferred to individuals,
  communities and municipalities with Parks Canada. NL: 55 major lightstations, 23 staffed. The
  2011 study gives examples of divested lights (privately owned and publicly owned) but not a full list.
- **robots.txt (`https://dfo-mpo.gc.ca/robots.txt`):** `User-agent: *` / `Disallow: */_baks/`,
  `*/_mm/`, `*/_notes/`, `/CSSP-PCCSM/`, `/fm-gp/`. Our paths are fine.
- **Licence:** Government of Canada web content (terms on the footer link); facts only.
- **Recommended use:** `facts only, link` for staffing and transfer context; the surplus study is a
  **research source** for divested lights. No machine-readable list of transferred lights found
  (gap).

### 1.6 Wikidata (CC0)

- **Endpoint to use:** QLever, `POST https://qlever.dev/api/wikidata` with `query=<url-encoded SPARQL>`
  and explicit `PREFIX wd: wdt: rdfs:` lines (tested: the province count below returned in one
  request, HTTP 200, `application/sparql-results+json`). The original extract was made on
  `query.wikidata.org/sparql` before the orchestrator's note (see the top of this file); the
  QLever province counts are identical. Canadian lighthouse items: `?l wdt:P31/wdt:P279* wd:Q39715 ;
  wdt:P17 wd:Q16`. Province from `wdt:P131+` to an item of class `Q11828004`. On WDQS heavy
  GROUP_CONCAT queries returned HTTP 500; plain triple-pattern queries (split into three) worked.
  The per-item property queries have not been re-run on QLever; they use the same patterns.
- **Coverage:** **488 items**, almost all standing: NS 122, NL 67, NB 59, PE 59, QC 57, ON 52,
  BC 48, MB 15, no province (9, three without coordinates). 4 items have a dissolved date. By P31:
  lighthouse 476, leading lights 20, replica 6, integral lighthouse 3, faux lighthouse 2, light
  station 1 (an item can carry several). **No Yukon, NWT, Nunavut, Alberta or Saskatchewan items.**
  **No Canadian lightvessel items and no Canadian lifesaving stations** (`Q831515` lightvessel
  and `Q11997323` lifeboat station return nothing useful for Canada).
- **Fields and coverage of identifiers (of 488):** coordinates 470, English label 471, French label
  267, inception 265, height (P2048) 188, enwiki article 112, frwiki article 129, **ARLHS id
  (P2980) 231**, **Canadian Coast Guard Lighthouse ID (P3920) 207** (values like `P435`, `N14`, `A-247`),
  **Heritage Lighthouse of Canada ID (P3211) 112** (= DFHD identifier), **Canadian Register of
  Historic Places ID (P477) 195**, NGA lighthouse ID (P3563) 181, Quebec cultural heritage directory
  (P633) 19, Lighthouse Directory page (P11627) 1. Ontario Heritage Act (P4120) and Heritage NL
  (P933) exist as properties but were not tested.
- **Access:** SPARQL on QLever (not WDQS). A 488-row WDQS-made dump
  with all of the above is cached at `data/raw/survey/canada/wikidata/ca_part_a.json` (+ `_b` province,
  `_c` types). Size under 1 MB.
- **Licence:** CC0 1.0 (Wikidata data).
- **Quality:** good identifiers, thin on lost lights and on Quebec (57 items vs about 140 standing
  Quebec lights in other sources); many items lack an English label (17).
- **Recommended use:** **bulk source for ids and cross-links**, not for counts. Its identifier set
  (ARLHS, CCG, HLPA, CRHP, NGA) is the cheapest way to join the other sources.
- **Sample:** "Cape St. Mary's light": CCG id N14, Heritage Lighthouse id 14954, CRHP id 13042,
  ARLHS CAN-721.

### 1.7 OpenStreetMap (ODbL)

- **Endpoint to use:** QLever OSM, `POST https://qlever.dev/api/osm-planet`, query
  `osmrel:1428125 ogc:sfContains ?o . ?o osmkey:man_made "lighthouse"` (prefixes
  `osmkey: <https://www.openstreetmap.org/wiki/Key:>`, `osmrel: <https://www.openstreetmap.org/relation/>`,
  `ogc: <http://www.opengis.net/rdf#>`). A count returned in 140 ms: **1,485**. Counts of tag forms
  in Canada on QLever (cached `qlever/osm_forms_ca.json`): `seamark:type=light_minor` 575,
  `light_major` 182, `building=lighthouse` 13, `man_made=lighthouse` with `disused=yes` 3,
  `historic=lighthouse` 1, `amenity=lifeboat_station` 1; **zero** for `disused:man_made`,
  `abandoned:man_made`, `was:man_made`, `ruins:man_made` and `seamark:type=light_float`. So OSM holds
  almost no lost lights or lightships in Canada.
- **How the 1,485-object extract was made:** before the orchestrator's note, on
  `https://overpass.kumi.systems/api/interpreter` (Overpass query for the same tag; data timestamp
  2026-10-21T13:45Z; 506 KB cached as `osm/ca_lighthouse.json`, used for the tag statistics below).
  The QLever count matches it exactly.
- **Coverage:** **1,485 objects** (1,315 nodes, 170 ways) tagged `man_made=lighthouse` in Canada.
  Quality is very uneven: 1,126 carry a `source` that is an NRCan CanVec import; **787 carry
  `fixme=could be a beacon with a light`**. Only 356 have `name` (609 have `name` or `seamark:name`);
  **182 have `wikidata`**, 83 `wikipedia`, 393 `seamark:light:reference` (the Admiralty number),
  538 `seamark:type` (light_minor 317, light_major 167, landmark 49), `seamark:light:character` 418,
  `:period` 309, `:height` 413, `:range` 314, `:colour` 418. 39 objects are north of 60°N.
- **Licence:** ODbL 1.0 (compatible with our database licence; attribution + share-alike).
- **Recommended use:** **cross-check and fallback coordinates**; use the 182 Wikidata-linked and the
  393 Admiralty-numbered objects. Fetch via **QLever** (include `osmkey:name`, `wikidata`,
  `seamark:light:*` columns). Geofabrik per-province PBFs are a heavier alternative (e.g.
  `https://download.geofabrik.de/north-america/canada/nova-scotia-latest.osm.pbf` is 99 MB; the whole
  Canada file is 6.5 GB, over our limit).
- **Sample:** a node named "Long Point Lighthouse": Wikidata Q6673078, Admiralty ref H 0640, flashing,
  5 s period, light height 101, range 16.

### 1.8 Wikipedia lists (CC BY-SA 4.0, facts only)

- **URLs (English):** the hub `https://en.wikipedia.org/wiki/List_of_lighthouses_in_Canada`, and
  provincial tables `List_of_lighthouses_in_<British_Columbia|Manitoba|Newfoundland_and_Labrador|New_Brunswick|Ontario|Prince_Edward_Island>`.
  Nova Scotia and Quebec are redirects to the hub (unstructured bullet lists). French:
  `fr.wikipedia.org/wiki/Liste_des_phares_au_Québec` (about 33 lines, stub),
  `Liste_des_phares_au_Canada`, `Liste_des_phares_de_la_Colombie-Britannique`,
  `Liste_des_phares_de_l'Île-du-Prince-Édouard` (stubs).
- **Coverage / counts (table rows):** BC about 44, MB about 25, NL about 108, NB about 100, ON about 58,
  PE about 60. Columns vary (BC/NL/ON/PE: name, image, water body, region, location, built, notes;
  NB and MB add class of light, focal height, ARLHS/NGA, Admiralty/CCG, range). Coordinates: present in
  NB, ON, PE, MB; absent in NL; BC has a map template with lat/long. Categories are small
  (`Category:Lighthouses in <province>`: BC 22, MB 4, NB 34, NL 46, NS 18, ON 25, PE 25, QC 6).
  No lost lights to speak of; no lightships (no Canadian lightship category exists).
- **Access:** `action=parse&prop=text|wikitext` (see the robots warning). Cached in `wikipedia/`.
- **Licence:** CC BY-SA 4.0 (en.wikipedia.org footer standard); we use facts only.
- **Recommended use:** **skip as a bulk source** (Wikidata + the community sites cover it better);
  `facts only, link` for the few articles with real histories (Cape Spear, Sambro, Fisgard…).

### 1.9 Lighthouse Friends (lighthousefriends.com), Canadian pages

- **Index URLs (tested):** `https://www.lighthousefriends.com/pull-state.asp?state=<BC|MB|NB|NF|NS|ON|PE|PQ>`
  (GET form; the site's own state selector). Station pages: `.../light.asp?ID=<n>`.
- **Coverage (counts of index entries, standing + destroyed together):** **1,148** =
  BC 62, MB 12, NB 136, NL 140, NS 260, ON 234, PE 65, QC 239. **Destroyed** (the site's own filter
  `A14=1`, verified identical to the "destroyed" colour class): BC 15, MB 2, NB 56, NL 58, NS 93,
  ON 79, PE 4, QC 97 = **404 lost, 744 standing** (replicas count as standing). 236 names are range
  lights or front/rear pairs. Territories: none.
- **Access flags from the same filters (A2 boat, A5 private, A6 climb, A7 interior open, A9 lodging,
  A10 keeper programme):** Canada-wide 23 climbable (NS 12, QC 10, PE 8, ON 4, NB 3, NL 3), 59
  interior-open, **21 with lodging** (QC 8, NL 3, NB 2, NS 2, ON 2, PE 2; including Cape Anguille,
  Cape Bauld, Fort Amherst, Cape d'Or, Port Bickerton, West Point PE, Île Verte, Pointe des Monts,
  Pot à l'Eau-de-Vie, Cap Chat, McKay Island ON, Flowerpot Island ON), **2 keeper programmes**
  (Swallowtail NB, Cabot Head ON), 58 private, 244 boat-required. Saved in
  `lhfriends/lhf_access_flags.json`.
- **Fields on a station page (tested IDs 2022, 1333):** latitude and longitude (6 decimals), a
  history, a **keeper list with years** and the references used (often "Annual Report of the
  Department of Marine and Fisheries, various years"), directions, tower height and lens notes.
  The index is a list of name + community + thumbnail.
- **Access notes:** pages are served without a charset and need **windows-1252** decoding. Index
  pages are 25–220 KB; station pages about 25 KB; about 1,150 station fetches at 2 s each is about
  40 minutes.
- **robots.txt:** `https://www.lighthousefriends.com/robots.txt` returns the IIS 404 page (none).
- **Licence:** footer "Copyright © 2001- Lighthousefriends.com"; photos by named owners. Facts only,
  credit and link on every page (per DESIGN.md); never copy text.
- **Quality:** the most complete Canadian source for lost lights and keeper lists; the author visited
  most of the sites. Coordinates are GPS fixes (good). The destroyed flag is by site, not by
  structure, so a station with a replacement tower can be flagged either way.
- **Recommended use:** **bulk source** for the station list (standing + lost), keepers and access
  flags; **research source (cite per station)**.
- **Sample:** Annapolis (NS): position 44.744333 N, 65.519944 W; first keeper listed in 1889 and
  successive keepers named to 1923 (names and years only), all citing the Marine and Fisheries
  annual reports.

### 1.10 Russ Rowlett's Lighthouse Directory (ibiblio.org/lighthouse)

- **URLs:** index `https://www.ibiblio.org/lighthouse/`; Canadian regional pages (all fetched,
  cached in `ibiblio/`): `ab sk mb bcn bcs bcv nbe nbn nbs lab nfln nfle nflw nscbe nscbw nse nsnw nss
  nsbf pei peiw ongb onno onnw onso onse onsw onlh qcc qce qcn qcs qcsw qcw nwt nvt` (each
  `.htm`). 39 pages, 3.9 MB.
- **Coverage (the page footer "Lighthouses: n" summed):** BC 76, MB 26, NB 101, NL 99, NS 192,
  PE 63, ON 244, QC 219, NWT 29, Nunavut and northern Québec 25, AB 3, SK 1 = **1,078**. Includes
  historic lights that are gone ("replaced by a buoy", "demolished"); the NS page says "roughly 170".
  Several pages were "checked and revised" in June 2026.
- **Fields:** one paragraph per light: name, years in service, water body and county, a short
  history, and identifiers **ARLHS CAN-nnnn, CCG list number, Admiralty H number, NGA number**.
  No coordinates in the text (a map link per entry), no keepers. 
- **Access:** one HTML page per region (50–100 KB, static HTML, UTF-8).
- **robots.txt (`https://www.ibiblio.org/robots.txt`):** `User-agent: *` / `Crawl-delay: 2` and
  disallows for unrelated project directories only.
- **Licence:** "Site copyright 2026 Russ Rowlett and the University of North Carolina at Chapel
  Hill" (page footer). Facts + ARLHS ids only, with credit and link.
- **Quality:** the best id crosswalk (it gives the Admiralty and CCG numbers that join to the CCG
  List and Wikidata P3920/P2980). NWT and Nunavut pages are mostly small river/lake beacons and
  need manual vetting before counting as lighthouses.
- **Recommended use:** **bulk source for identifiers + years in service**, and `facts only, link`.
- **Sample:** Port Maitland (NS), 1884–1945, Bay of Fundy side of Yarmouth County; the old light stood
  on the west breakwater; ARLHS CAN-1211, CCG A-247, Admiralty H3840, NGA 10776.

### 1.11 Lighthouse Digest database (lighthousedigest.com / foghornpublishing.com)

- **URLs (tested):** list by letter `https://www.lighthousedigest.com/Digest/database/datapage.cfm?letter=S`
  (284 KB, 743 entries, 150 in Canada); detail
  `https://www.lighthousedigest.com/Digest/database/uniquelighthouse.cfm?value=383` (Sambro Island
  Light, 11 KB). Doomsday List: `http://www.foghornpublishing.com/Digest/database/doomsday.cfm`.
- **Coverage:** "8260 lighthouses from all over the world" (page text); Canadian share about 20%
  from the S page. Name, location (city, province, country), organisation, height, built,
  directions and a keepers text field. The province search form is POST (not used).
- **robots.txt (`https://www.lighthousedigest.com/robots.txt`):** `User-agent: *` / `Disallow: /SS/`,
  `/Digest/admin/`, `/Digest/temp/`, `/Digest/calendar/`, `/Digest/batchfiles/`.
- **Licence:** none stated; site content is Foghorn Publishing's. Facts only with credit.
- **Recommended use:** `facts only, link` and **research source** (keepers). 26 letter pages plus
  detail pages (about 1,600 Canadian) are a second-priority fetch after Friends + Directory.

### 1.12 Regional lists with visit and access detail

| Source | URL | What it gives | Robots / licence | Use |
|---|---|---|---|---|
| **Nova Scotia Lighthouse Preservation Society** | `https://www.nslps.com/about-ns-lighthouses/lighthouse-lists` | one table of **about 190 NS lights, standing and lost**, with county, region, **position in DMS** and a category per light: visit (16 parsed), photo-op (66), remote (46), **lost (51 parsed)**, museum (4), lightship; plus "NS Lighthouses under HLPA" (25 named) and *The Lightkeeper* back-issues (research PDFs) | robots 404; footer "© 2026 Nova Scotia Lighthouse Preservation Society"; no licence page text found | bulk source for NS access categories; facts only, link |
| **PEI Lighthouse Society** | `https://peilighthousesociety.ca/index.php/history/lighthouses/<name>` | 7 detailed histories (West Point, Victoria Seaport, East Point, Point Prim, Wood Islands, Panmure Island, Cape Bear), lists of open, public, range and private lights | Joomla robots (admin paths only) | regional source; facts only |
| **Route des phares / Corporation des gestionnaires des phares de l'estuaire et du golfe Saint-Laurent** | `https://routedesphares.qc.ca/phares/` (sitemap `wp-sitemap-posts-page-1.xml`) | about 47 eastern-Quebec lights: municipality, built year, height, manager, access (e.g. by boat from the Isle-Verte wharf), visit and lodging notes; bulletins *Amis des phares* (PDFs, 2015–2021, `wp-content/uploads/2024/08/…`) | robots: `Disallow: /wp-admin/` only; © the Corporation | regional source (visit/stay); bulletins are **research sources** |
| **Répertoire du patrimoine culturel du Québec (RPCQ)** | `https://www.patrimoine-culturel.gouv.qc.ca/rpcq/detail.do?methode=consulter&id=<n>&type=bien` | Quebec heritage records: name, other names, region, municipality, date, theme, status (municipal citation, classification) and linked structures; the Pointe-à-la-Renommée record is tied to an "Inventaire des phares du Québec (2009 – 2010)" | robots 404; text © Gouvernement du Québec, images "©" per photo; page served behind Imperva/Incapsula scripts (one page fetched fine) | research source (cite per station) |
| **Heritage NL, Ontario Heritage Trust (Ontario Heritage Act Register P4120), Saskatchewan** | `heritage.nf.ca`, `heritagetrust.on.ca` | provincial registers; not tested. The Ontario Heritage Trust robots disallows GPTBot, Google-Extended and PerplexityBot, not Anthropic by name | – | not tested; low priority |
| **Nova Scotia Archives, Lighthouses of Nova Scotia** | `https://archives.novascotia.ca/lighthouses/` (items `.../archives/?ID=<n>`) | archival **photo database** by county (Department of Transport albums, Clara Dennis) with dated, referenced captions | no robots (the host serves an HTML redirect); © Nova Scotia Archives (use protocols) | research source / photo lead; permission needed before mirroring |
| **Canadian Lighthouses of Lake Superior**; Beach Canal Lighthouse Group; Nottawasaga Lighthouse Preservation Society | web (not fetched) | Ontario preservation groups; local histories, volunteer-run | – | leads only |

### 1.13 Wayback of the Coast Guard "Usque ad mare" lights page

`https://bac-lac.wayback.archive-it.org/web/20071114190341/http:/www.ccg-gcc.gc.ca/usque-ad-mare/lights_e.htm`
(a Library and Archives Canada web archive of a 2007 Coast Guard history page, not fetched). The
LAC archive-it host may have its own robots rules; check before use.

---

## 2. Staffed lightstations ("keepers' home" label)

Newest sources found (nothing in a single official list):

- **British Columbia: 25 staffed** since 31 July 2024, when the Coast Guard ended keeper functions at
  **Carmanah Point and Pachena Point** for geotechnical safety reasons
  (`https://www.canada.ca/en/canadian-coast-guard/news/2024/07/canadian-coast-guard-to-cease-light-keeper-functions-at-carmanah-point-and-pachena-point-light-stations-due-to-safety-concerns.html`,
  cached). The baseline list of 27 is **Appendix 4 of the 2011 Senate report "Seeing the Light"**
  (CCG data, April 2010): Addenbroke Island, Boat Bluff, Bonilla Island, Cape Beale, Cape Mudge,
  Cape Scott, Carmanah Point, Chatham Point, Chrome Island, Dryad Point, Egg Island, Entrance Island,
  Estevan Point, Green Island, Ivory Island, Langara Island, Lennard Island, McInnes Island, Merry
  Island, Nootka, Pachena Point, Pine Island, Pulteney Point, Quatsino, Scarlett Point, Trial Island,
  Triple Island (4 staff, 28-day rotation). Subtract the two closed in 2024. A January 2025 article
  names Cape Beale as still staffed.
- **Newfoundland and Labrador: 23 staffed** (2010 list, same Appendix 5; still 23 in the DFO October
  2017 figure and in a May 2024 newsletter): Bell Island, Cape Anguille, Cape Bonavista, Cape Norman,
  Cape Race, Cape Ray, Cape St. Mary's, Fort Amherst, Fort Point, Fortune Head, Fox Point, Green
  Island (Fortune Bay), Green Island (Trinity Bay), Lamaline, Long Point, New Ferolle Peninsula,
  Northwest Head, Pass Island, Powles Head, Puffin Island, Red Bay, St. Shotts, Tides Cove Point.
  Rotation lengths vary (7, 14 or 28 days; three single-keeper posts). The DFO NL page
  (`.../lightstationsnl-lespharestnl-eng.html`) confirms "23 staffed" of 55 major lightstations.
- **New Brunswick: Machias Seal Island, 1.** The 2011 report says four lightkeepers stay on the
  island ("no plans to remove") as the one Maritimes exception; the island is claimed by both
  Canada and the United States. Its 2026 staffing was not confirmed beyond the 2017/2024 "1 in NB".
- National total: 51 (DFO, October 2017), 49 after the 2024 BC change (January 2025 article).
- **Limits:** no source after January 2025; the NL list is the 2010 one. Treat as
  `staffing.status = staffed, as_of 2010/2024` and note the source on each record. The Senate PDF
  (`https://sencanada.ca/content/sen/committee/411/pofo/rep/rep02oct11-e.pdf`, 2.2 MB; sencanada.ca
  robots empty) is cached with its text in `staffed/`.

## 3. Visit and stay (Canada)

- **Lodging in a keeper's house or tower** (LighthouseFriends lodging filter plus the web search):
  Cape Anguille Lighthouse Inn (NL, duplex keeper's house, Registered Heritage Structure 2003), Île
  Verte (QC, two houses with eight rooms, boat access), Pointe des Monts (QC, keeper's quarters),
  Pot à l'Eau-de-Vie / Brandy Pot (QC), Cap d'Espoir, Cap Chat, Cap au Saumon, Pointe de l'Ouest,
  Cap de Rabast (QC, all in the Route des phares list), West Point (PE, tower and inn), Cape d'Or and
  Port Bickerton (NS), Green's Point (NB), Campbellton Range Rear (NB), McKay Island and Flowerpot
  Island (ON), Fort Amherst and Cape Bauld (NL). Fisgard (BC) has Parks Canada oTENTik tents on the
  fort grounds, not in the lighthouse.
- **Keeper programmes (volunteer):** LighthouseFriends marks Swallowtail (NB) and Cabot Head (ON). No
  Canadian programme list found.
- **Climbable:** 23 on LighthouseFriends (NS 12, QC 10, PE 8, ON 4, NB 3, NL 3: PE's Point Prim is
  among them). Always check season.
- **Access labels** (boat only, private, staffed) come from the same filters (58 private, 244
  boat-required) and from the Coast Guard's staffed lists above.

## 4. Lightships and lifesaving stations

- **Lightships (no registry or Wikidata coverage).** Sources found: the Lights Lists of the 1860s–1900s
  (Canadiana, blocked; the Admiralty List of Lights corrected to January 1864 is
  `canadiana.ca/view/oocihm.36126`), the 1901–1925 Marine reports on the Internet Archive (section 6),
  Jean Cloutier's article on floating lights of the St. Lawrence (Sémaphore PDF, 3 pages, cached),
  Archives Canada's *C.G. Lightship Lurcher* fonds, For Posterity's Sake (`forposterityssake.ca`, RCN
  history site, Lurcher lightship page), and the Polson Iron Works page for Lightship 14. From these:
  - **Lurcher Shoal** (off Yarmouth NS), lightships from about 1904–06 (No. 14), replaced 1951,
    1959 (No. 2), 1960 (No. 4, ex-*Cataraqui*), automatic buoy from 1969.
  - **Traverse / Lower Traverse (St. Lawrence)**: first vessel *Brilliant* in 1830–31; later vessels
    from 1875; sunk in a collision in October 1887; replaced by a spar buoy in 1904.
  - **Red Island Reef** (from 1871; Lightship No. 3 from 1923 to 1961), **White Island Reef** (1893 on;
    Nos. 5, 20, 23), **Prince Shoal** (No. 7, 1906–56, then a "pilier" in 1964), **Manicouagan Shoal**,
    **Anticosti East Point**, a vessel near Île aux Coudres, and Lake St-Pierre (three lightships
    from 1816/1828).
  - **BC: Sandheads** (Fraser River): lighthouse built 1880, replaced by a lightship in 1913 (via Wikipedia).
  - The 1896 Dominion list shows 13 lightships; the NFB caption of 1955 credits the Department of
    Transport with eight on both coasts. **Estimated 15 to 25 Canadian lightship stations over time,
    about 30 vessels**; no complete list located, and **none is a Sambro lightship** (Sambro is a
    lighthouse).
- **Lifesaving.** Wikidata has no Canadian entries. Sources: Parks Canada's Sable Island Humane
  Establishment (1801–1958; federal designation, 2021; "first permanent government-sponsored coastal
  rescue organisation" in the northwest Atlantic; the release says about 40 humane stations by the
  mid-20th century) at `https://www.canada.ca/en/parks-canada/news/2021/12/the-sable-island-humane-establishment.html`;
  a secondary transcript of the 1885–86 federal lifeboat programme on
  `navalmarinearchive.com/research/docs/life_saving_stations.html`: twelve boats, two on Sable
  Island and one each at Devil's Island, Duncan's Cove, Yarmouth and Scatarie (NS) and Cobourg,
  Collingwood, Goderich, Port Stanley, Toronto and Pelee Island (ON); the first station opened at
  Port Stanley, 25 June 1885. Federal role was thin: only five stations were maintained federally
  (same source). British Columbia (for example the Bamfield station) is **not** covered by anything I
  retrieved and is from background knowledge only. **Estimate: 10 to 40 sites, poorly documented;
  plan for an owner-supplied list.**

## 5. Historical sources for research agents

| Source | Reachable? | Notes |
|---|---|---|
| **Sessional Papers / Marine annual reports on Canadiana** | **No: robots names Claude/Anthropic.** Skipped. | The authoritative set, 1868 on. |
| **Internet Archive, "Report of the Department of Marine and Fisheries (Marine)" 1901–1925** | **Yes.** Machine search `https://archive.org/advancedsearch.php?q=title:("Department of Marine and Fisheries")…&output=json` returns 56 items. Full text `https://archive.org/download/<id>/<id>_djvu.txt`. | Tested `1901v35i9p21_0025` (716 KB text). "Sambro" appears 11 times; the report contains **"List of Lightkeepers, Stations, &c" (p. 121)** with names, dates of appointment and salaries, but the OCR splits the columns into separate blocks (names, stations, dates, "$" amounts), so rows must be rebuilt from hOCR or by hand. Identifier pattern `<year>v<vol>i<no>p<paper>_<id>`; supplements `supplementtoannu<year>cana`. archive.org robots: `Disallow: /control/`, `/report/` only. Licence: public domain (Crown copyright expired), IA terms. |
| **Internet Archive, "Sessional papers of the Dominion of Canada" volumes** | Yes, patchy (1867, 1880, 1883, 1899, 1901, 1907–08, 1909, 1915, 1917…). | e.g. `sessionalpaperso1671cana` (v.16, 1883). |
| **DFO Library scans** (`https://waves-vagues.dfo-mpo.gc.ca/library-bibliotheque/<id>.pdf`) | **Yes** for the one known: `40758606_1871.pdf` ("(4th) Annual Report, Department of Fisheries (1871)", 547 pp, 17 MB, with an OCR text layer, 3.6 MB of text; mentions Sambro's Daboll fog trumpet). | The ids are not sequential; locate others through the Federal Science Libraries catalogue. robots 404. |
| **publications.gc.ca (Depository Services)** | Yes, but the PDFs found are the **Fisheries** parts: `MA1-<year>-eng.pdf` (1868–1883), `Fs1-<year>-eng.pdf` (1884–1891), `MA1-1-<year>-eng.pdf` (1892–1928). Tested `MA1-1875-eng.pdf` = "Supplement No. 4 … Commissioner of Fisheries". | The Marine volumes' catalogue records were not found. `publications.gc.ca/robots.txt` disallows only the search pages. |
| **Library and Archives Canada** | **No** (`Disallow: /`). | Keeper personnel files exist but cannot be crawled; leads for the owner. |
| **BAnQ numérique** | **No** (names ClaudeBot). | |
| **Nova Scotia Archives** | Yes (photos, finding aids). | Rights: ask first. |
| **Provincial Archives of New Brunswick** | Search / text pages disallowed. | |
| **Island Newspapers (PEI)**, **Maritime History of the Great Lakes** | Cloudflare challenge, skipped. | |
| **Sémaphore (UQAR) repository** `https://semaphore.uqar.ca/` | **Yes.** robots: `Crawl-delay: 10`, `Disallow: /cgi/`. | Open PDFs on Quebec lights: floating lights, *Les gardiens de phares*, *Les premiers phares du Saint-Laurent*, Rocher-Maudit keepers. Tested `2868/1/Des phares flottants sur le Saint-Laurent.pdf` (3 pp). |
| **Érudit** (Magazine Gaspésie, *Continuité*, *Cap-aux-Diamants*) | Reachable: robots `Crawl-delay: 10`, `Disallow:` empty. | Many French articles on named lights (Cap-Blanc keepers 1874–1965, Cap-Gaspé). |
| **Route des phares bulletins** | Yes. | See 1.12. |
| **Race Rocks (racerocks.ca)**, **Lighthouse Digest keeper fields**, **LighthouseFriends keeper lists** | Yes. | Keeper rosters with years (BC, ON, NS); disagree in places (Race Rocks 1866 vs 1867). |
| **Books** (not machine-readable) | – | Graham, *Keepers of the Light* (1985) and *Lights of the Inside Passage* (1986), for BC keepers. |
| **HathiTrust / Google Books** | HathiTrust's robots.txt request returned HTTP 403; Google not reviewed. Not tested. | |

Quick test result requested: **one known station and year** is reachable: Sambro Island, 1901
Marine report via the Internet Archive (full text, OCR), and Sambro in 1871 via the DFO library PDF.

## 6. Counts (best estimate, at least two sources each)

| Province / territory | LighthouseFriends standing / lost | Directory (all) | Wikidata (≈standing) | Wikipedia list rows | **Best estimate standing** | **Lost** |
|---|---|---|---|---|---|---|
| Nova Scotia | 167 / 93 | 192 | 122 | hub only | **about 160** (150–170) | **about 70** (51+ per NSLPS, 93 per LHF) |
| Newfoundland and Labrador | 82 / 58 | 99 | 67 | about 108 | **about 80** (DFO: 55 major) | **about 55** |
| New Brunswick | 80 / 56 | 101 | 59 | about 100 | **about 80** | **about 55** |
| Prince Edward Island | 61 / 4 | 63 | 59 | about 60 | **about 60** | **5–10** |
| Quebec | 142 / 97 | 219 | 57 | hub only | **90–140** | **about 95** |
| Ontario | 155 / 79 | 244 | 52 | about 58 | **about 150** | **about 80** |
| British Columbia | 47 / 15 | 76 | 48 | about 44 | **about 50** | **15–25** |
| Manitoba | 10 / 2 | 26 | 15 | about 25 | **about 12** | **2–10** |
| Yukon, NWT, Nunavut, Alberta, Saskatchewan | none | 29 + 25 + 3 + 1 (mostly small beacons) | none | – | **0–5, needs manual vetting** | unknown |
| **Canada** | **744 / 404 (1,148)** | **1,078** | **488** | – | **about 740** (DFO "more than 750") | **about 390** |

Expected Fresnel Canadian station records after merging range pairs and same-place duplicates:
**about 1,000 to 1,150** (the DESIGN.md "~490" is the Wikidata number and understates this by about
half). Heritage: 115 designated Heritage Lighthouses (+13 National Historic Sites, about 60
Federal Heritage Buildings with lighthouses, overlapping). Active aids with international numbers in
the CCG List: about 2,000 (mostly towers that are **not** Fresnel-era lighthouses; the design's
"modern automated beacons are excluded" rule will remove most). Staffed: 25 BC + 23 NL + 1 NB = 49.
Lightship stations: 15–25 (estimate). Lifesaving: 10–40 (estimate).

## 7. Gaps and risks

1. **Wikipedia Action API robots** (top of this file) still needs a ruling; Canadiana, BAnQ, LAC and Nauticapedia are
   unavailable, so pre-1900 keeper rosters rest on LighthouseFriends/Lighthouse Digest, the
   Internet Archive 1901–1925 reports and the 1871 DFO scan.
2. **Lost-light inventory is source-thin outside LighthouseFriends**: the Directory mixes lost and
   standing; the CCG list has no lost lights; Wikidata has 4 dissolved dates. Cross-check counts by
   province before publishing "lost" totals. Some LHF "destroyed" entries are minor pole lights; vet
   against the 1901 and earlier lists of lights with establishment dates.
3. **Quebec is under-covered in open data** (57 Wikidata items vs about 140 standing). Use the Route
   des phares list, RPCQ ids (only 19 in Wikidata) and the 2009–10 *Inventaire des phares du Québec*
   (not found online; ask the owner / try the Ministère de la Culture).
4. **CRHP search is broken from outside** (HTTP 500 on GET); ids from Wikidata only.
5. **LighthouseFriends encoding** (cp1252 with no declared charset) and an ASP site with ASP-style
   IDs: parse defensively. Its licence is all-rights-reserved: facts only.
6. **Territories and the prairie provinces**: the Directory lists 54 northern pages of mostly river
   beacons; real lighthouses likely under 5. The CCG Arctic volume (74 pages) is the check.
7. **Lightships and lifesaving**: no register anywhere; the Marine reports (1901–1925, IA) include a
   list of lights with lightship stations by year, so a research pass on those reports is the best
   build path. BC lifesaving is unsourced.
8. **Overpass is flaky and now off limits**; use QLever for OSM (fast: 140 ms for the Canada count).
   Geofabrik provincial PBFs are the fallback (NS is 99 MB; the other sizes were not checked).
9. **Staffed lists are 2010-based** with a 2024 BC change; no official 2026 list was found.
10. **Open Government Licence is clear for DFHD; the Lights List is Crown copyright with no open
    licence stated**; assume facts + credit.

## 8. Recommended fetcher order

1. **DFHD CSV + Parks Canada HL page** (two requests): 115 heritage lights with coordinates,
   designation, statements of significance. OGL.
2. **CCG Lights List** (5 PDFs or about 190 HTML sections): characteristic, focal height, range,
   Admiralty / list numbers, structure description, position for every active light.
3. **Wikidata via QLever** (a cached 488-row WDQS extract exists as a cross-check): ARLHS, CCG id,
   CRHP id, French labels, enwiki/frwiki links, to join the above.
4. **Lighthouse Directory** (39 pages): ARLHS / CCG / Admiralty crosswalk, years in service, lost
   lights.
5. **LighthouseFriends** (8 index pages, then about 1,150 station pages, about 40 min): the station
   list of record for standing + lost, coordinates, keeper lists, access flags (already collected:
   `lhf_canada_index.json`, `lhf_access_flags.json`).
6. **Regional supplements**: NSLPS table (one page), Route des phares (47 pages), PEI Lighthouse
   Society (7 pages), RPCQ by id, CRHP by id.
7. **OSM** via QLever for cross-check, not as a seed.
8. **Research tooling** (for the story agents): a helper that pulls the IA `_djvu.txt` of the
   Marine reports and greps by station; Sémaphore / Érudit PDFs; DFO library via the catalogue.
