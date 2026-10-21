# Survey `history`: the research layer (archives a story agent can cite, and how to find "station X, year Y" by machine)

Surveyed 2026-10-21 by the `history` agent. Caches and samples: `data/raw/survey/history/` (git-ignored, 43 MB:
`ia_lhb/`, `ia_or/`, `lsb/`, `uslhs/`, `nara/`, `nrhp/`, `charts/`, `samples/`, `tools/`). Scope is the research
layer only; station lists belong to the other surveys. Every claim below was tested on 2026-10-21 unless it is
marked **UNVERIFIED**. Three test stations ran through every source: **Portland Head, Maine** (1791, a long-lived
East Coast station), **Split Rock, Minnesota** (lit 1910, Lake Superior) and **Point Reyes, California** (lit 1870,
the foggiest station in the Service). Section 12 has the results side by side.

Manners followed: FresnelBot/0.1 user agent, 2 s between requests per host (5 s for loc.gov, which asks for
`Crawl-Delay: 5`), robots.txt read for every host before use, no CAPTCHA/Cloudflare/login bypass, nothing submitted.
The orchestrator's later rules also followed: no query.wikidata.org or Overpass (not used), Canadiana, BAnQ and
Nauticapedia skipped, and history.uscg.mil left alone (on hold, section 2.7).

---

## 0. Verdict

**Does the "download the OCR text once, grep it locally" design work? Yes, for most of the record, with three
honest limits.**

| Series | On the Internet Archive (IA) with free OCR text? | Local corpus works? |
|---|---|---|
| Life-Saving Service annual reports 1876-1914 | About 37 volumes found, covering roughly 1876-1909 with a few holes (3.1) | **Yes.** ~50 MB of text. Best-fit series. |
| Lighthouse Service Bulletin 1912-1939 | 27 of 28 yearly PDFs at uslhs.org (1925 not found under the usual name); text layer present | **Yes.** ~280 MB of PDF, ~7 MB of text. |
| Canadian Marine reports (Sessional Papers) 1901-1925 | ~55 separate IA items, searchable | **Yes** for 1901-1925 (size not measured; estimate 100-150 MB of text). Earlier years not found. |
| Lighthouse Board annual reports 1852-1910 | **Only 7 compilation items, roughly fiscal years 1891-1902** | **Partly.** The other ~47 years are on HathiTrust/Google (blocked, 2.6) or inside Congressional Serial Set volumes on IA (not yet enumerated). |
| Commissioner of Lighthouses reports 1911-1939 | One volume found (fiscal 1915; IA's own metadata wrongly says 1911) | **Not yet.** The rest are on HathiTrust (blocked). |
| Official Register of the United States (keepers, salaries, birthplaces) | Yes, ~500 IA items (volumes and indexes) | **Greppable by surname only.** OCR scrambles the table columns, so "keeper at station X" cannot be read from the plain text (2.4). |

Limits: (1) the Lighthouse Board and Commissioner runs are the weak spot, and the fix needs a human or a browser
to pull files from HathiTrust, which sits behind a Cloudflare challenge; (2) OCR is Google-grade (see 2.1): station
names come out as "Point Reyesy", "Point Beyes", "lOlG"; any search must be fuzzy; (3) the plain `_djvu.txt` has **no
page breaks**, so page numbers for footnotes need IA's in-item search API or the hOCR file, not the text file.

**Best keeper-record source:** the **USLHS Digital Archive** (`archives.uslhs.org`), which serves a structured roster
per station (name, role, start year, end year, salary, source) as JSON, behind a URL pattern that worked in three
for three tests. It is Kraig Anderson's inventory, the same data LighthouseFriends prints, built from NARA's keeper
registers (M1373). See 4.1. NARA's own catalog cannot be used by machine (robots `Disallow: /`).

**Wrecks:** NOAA's AWOIS database (the one with names, year sunk and a history paragraph) is retired and its download
host now returns 404. The live source, NOAA ENC Direct, has wreck points and positions but **no names, years or
histories** in the data tested. So the "recorded wrecks near each light" layer will be positions and chart categories,
and the stories' rescue accounts must come from the Life-Saving Service reports and newspapers (section 8).

**Charts:** current NOAA charts work as an overlay (a WMS and an export endpoint, both tested, public domain). The
historical chart collection has **no georeferenced or IIIF service**, only images, and its robots.txt disallows all
crawling (section 9).

**Blockers:** HathiTrust and Chronicling America's HTML pages are behind Cloudflare; Canadiana and BAnQ name Anthropic
crawlers in robots.txt; the USCG Historian is on hold; the loc.gov JSON API is slow and flaky (30-75 s per query,
one 503); **archive.org stopped answering from this machine late in the survey** (timeouts on every endpoint from
about 10:00 on), which cost the verification of Putnam 1917 and Weiss 1926 and of later Official Register years.

---

## 1. The machine layer: Internet Archive

- **URL:** `https://archive.org/` (three endpoints tested; robots.txt allows everything except `/control/` and
  `/report/`).
- **robots.txt (fetched):** `User-agent: *` / `Disallow: /control/` / `Disallow: /report/`. No AI-crawler rules.
- **Licence:** US federal documents carry no copyright; IA's own scans are free to use for public-domain works.
  Per-item rights are in each item's metadata. Cite the original publication, not IA.
- **Endpoints that work (all tested, no key):**

| Job | URL pattern | Notes |
|---|---|---|
| Find items by metadata | `https://archive.org/advancedsearch.php?q=<lucene>&fl[]=identifier&fl[]=title&fl[]=date&fl[]=item_size&rows=200&output=json&sort[]=date asc` | Metadata only. ~0.5 s when IA is healthy. |
| One item's files and sizes | `https://archive.org/metadata/<id>` | Gives `server`, `dir` (needed for in-item search) and `files[].size`. |
| Download one volume's OCR | `https://archive.org/download/<id>/<id>_djvu.txt` | 0.4-5 MB per volume. Redirects to a `dn*.archive.org` host. Supports HTTP `Range`, so the first 60 KB identifies the year. |
| **Search inside one item, page-numbered** | `https://<server>/fulltext/inside.php?item_id=<id>&doc=<id>&path=<dir>&q=<phrase>` | Returns JSON with `matches[].text` (snippet with `<IA_FTS_MATCH>` marks) and `matches[].par[].page`. 9 s. This is the page-number source for footnotes. |
| **Search all of IA's full text** | `https://archive.org/services/search/beta/page_production/?service_backend=fts&user_query=<phrase>&hits_per_page=50&page=1` | JSON: `identifier`, `title`, `year`, and `highlight.text[]` snippets. `"Portland Head" "Joshua Strout"` gave 51 hits, mostly lending-library books (snippets only; not citable as full text). Could not filter to one identifier (HTTP 400 on `filter_map`; `identifier:` in the query returned 0). Useful for discovering which items mention a station. |
| Original page images | `https://archive.org/download/<id>/<id>.pdf` | 75-300 MB each; do not mirror. |

- **Cost of the corpus approach:** the 7 Lighthouse Board volumes (7.7 MB of text) came down in about 15 s of transfer.
- **Quality:** see 2.1; `_djvu.txt` has zero form-feed page separators, so line numbers in the text file are not page
  numbers. `_hocr_searchtext.txt.gz` (1-2 MB per volume) and `_chocr.html.gz` (35-70 MB) carry page structure;
  not tested beyond file sizes.
- **Risk:** IA went unreachable (timeouts on `robots.txt`, search and metadata) from about 10:00 local time, after ~120
  requests that morning at the 2 s rate. Cause unknown (outage or throttling). The first build of the corpus should
  retry with back-off and must not hammer.
- **Recommended use:** `bulk source` (the corpus) and `research source (cite per station)`. Sample scripts:
  `data/raw/survey/history/tools/` (`ia.py` metadata search, `fts.py`, `inside.py`, `yr.py`, `uslhs.py`).


---

## 2. Lighthouse Board, Commissioner of Lighthouses, Bulletin, Official Register, Instructions

### 2.1 Annual Report of the Light-House Board (1852-1910) on the Internet Archive

- **URLs:** `https://archive.org/details/<id>` for the seven items below.
- **Coverage:** these are **Google-scanned Harvard compilations**, each holding one to three fiscal years. Years below
  come from the front matter and the text itself (sampled, not read cover to cover), so treat them as approximate.
  **About fiscal years 1891-1902 only.** No item for 1852-1890 or 1903-1910 turned up under any title or creator
  search (IA metadata search returned 7 hits for the series title, 14 for "light-house board" as a title).

| IA identifier | Fiscal years (from text) | Pages | OCR text |
|---|---|---|---|
| `annualreportlig03statgoog` | 1891 | 725 | 1.63 MB |
| `annualreportlig01statgoog` | 1892 and 1893 | 975 | 2.01 MB |
| `annualreportlig00boargoog` | 1896 | 447 | 0.86 MB |
| `annualreportlig02statgoog` | 1896 | 497 | 1.04 MB |
| `annualreportlig04statgoog` | 1899, with 1900-01 text | 289 | 0.69 MB |
| `annualreportlig00statgoog` | 1900-1901 | 269 | 0.67 MB |
| `annualreportlig01boargoog` | 1901-1902 | 317 | 0.75 MB |

- **Fields:** prose by lighthouse district and station number (repairs, new buildings, fog-signal hours and coal burned,
  changes of characteristic, recommendations, wrecks near a light, occasional keeper commendations), appendices of
  stations by district, an alphabetical index with page numbers. **Keeper names are rare** (commendations, deaths,
  heroism). The reports do not carry keeper rosters; those are in the Official Register and the NARA registers.
- **Access:** `https://archive.org/download/<id>/<id>_djvu.txt` (all seven downloaded, in `ia_lhb/`).
- **OCR quality (measured on the seven volumes):** readable prose, damaged proper nouns. Seen: "Point Reyesy", "Point
  Beyes", "Point Ueyo3", "lOlG" for 1016, "Whalebaclc". A fuzzy pattern is required, for example
  `Point\s+R[eoa]y[eo]s?`. Words in IA's own search index are cleaned slightly better than the `_djvu.txt`.
  Also expect "Digitized by Google" lines between pages; none of the seven carries a page marker.
- **Typical yield per station per year:** one to three sentences. Portland Head across the seven volumes: fog trumpet
  hours (892 hours and 11.5 tons of coal in 1899; 1,013 hours and 14 tons in 1896), fog-signal characteristic
  changed 30 April 1896 and 15 May 1899, "the rubble tower, built in 1790, was extensively repointed" (1900-01), a 1891
  recommendation for a bell at Spring Point Ledge that mentions Portland Head's trumpet. Point Reyes: 35,000-gallon water
  tank (1896), steam siren replaced by 12-inch steam whistles (Sept. 1890), whistle hours (1,080 to 1,674 a year,
  1890s). **Name collision:** "Split Rock" in these volumes is **Split Rock, Lake Champlain, NY** (dwelling rebuilt
  1898); the Minnesota light does not exist until 1910.
- **Licence:** US federal publication, no copyright. Google-digitised scans carry a "Digitized by Google" page;
  Google's usage guidelines ask for non-commercial and attribution. Cite the report, not the scan.
- **Recommended use:** `research source (cite per station)` and part of the local corpus. **Gap:** ~47 of 59 years.

### 2.2 Annual Report of the Commissioner of Lighthouses (1911-1939)

- **URL:** `https://archive.org/details/bub_gb_B2dYAAAAYAAJ`. IA labels it 1911; the text is the **fiscal 1915** report
  (788 pages, 3.18 MB of text, 1.5 GB item). The only Commissioner report found.
- **Fields:** a five-year progress summary, per-district new works, appendices listing new lights, changes, and
  stations by name ("Split Rock, Minn." appears in three places, including a table of new light and fog-signal
  stations established, "Split Rock, Lake Superior, light and fog-signal station 1910"). The text has **double spaces
  between words** ("Split  Rock"), so normalise whitespace before matching. Portland Head: 0 hits (it was routine).
- **Gap:** all other years (1911-14, 1916-39) are on HathiTrust (Cloudflare) or the USCG Historian (on hold).
- **Recommended use:** `research source (cite per station)`, corpus build once more years are found.

### 2.3 Lighthouse Service Bulletin (monthly, 1912-1939)

- **URL pattern:** `https://uslhs.org/sites/default/files/bulletins/LighthouseServiceBulletin_<YYYY>.pdf`.
  **Tested by HEAD for every year 1912-1939:** HTTP 200 `application/pdf` for 27 years, **404 for 1925** (it may live
  under a different file name; not searched). Sizes 5.0-13.9 MB, about 280 MB for the run. The USLHS Digital Archive
  also lists 37 items under "U.S. Lighthouse Service Bulletin" (4.1), probably the same material split by issue.
- **Fields:** each PDF is a year of issues. Content per issue: station-level news (storms and damage, rescues,
  awards, new buildings, personnel notes), fog-hours tables, wreck and assistance statistics. Each PDF has an Adobe
  "Paper Capture" OCR layer (checked on 1912, 48 pages, and 1933, 25 pages).
- **Access:** `pdftotext file.pdf out.txt` (use the plain mode, not `-layout`: the two-column layout is otherwise
  interleaved). OCR is noisy ("durin"" for "during", "riecemb~~" for "December") but station names are usually clean.
- **robots.txt (uslhs.org):** `User-agent: *` with only Drupal admin, search, user and `/profiles/` `/core/` paths
  disallowed; `/sites/default/files/` is not listed, so the PDFs are allowed. No AI-crawler rules.
- **Licence:** US federal publication. USLHS hosts the scans and is a private society; it states nothing on these PDFs
  that I found. Mirror text for our own search, **link to the published PDF** rather than re-hosting.
- **Test results:** 1933 text has Point Reyes three times, including a piece about the station having the most hours of
  fog in fiscal 1932 (1,774 hours, 157 more than the next foggiest, Great Duck Island, Maine; in 1930 it had 2,129);
  1912 mentions Point Reyes once; Split Rock 0 times in the 1912 year (it opens in 1910 but the Bulletin starts Jan 1912).
  Portland Head 0 in both sampled years.
- **Recommended use:** `bulk source` for the corpus; `research source (cite per station)`.

### 2.4 Official Register of the United States (keepers, with salary, birthplace)

- **URL pattern:** IA identifiers of the form
  `sim_united-states-official-register-of-the-united-states_<YYYY-MM-DD>[_1|_2]` (and `..._<YYYY>_index`). A metadata
  search for the title returned **503 items**; the first 100 by date run **1816-1887** and were listed (biennial,
  1816-1873 one volume; from 1879 two volumes). Later years not enumerated (IA outage). Also `officialregister<YYYY>`
  (Interior Dept. copies, 1855-1887) and Google scans (`officialregiste0Ncommgoog`).
- **Which years list keepers:** verified in the **1857** (4.09 MB text), **1871** (4.54 MB) and **1881 vol. 1**
  (5.06 MB) volumes. They carry a Treasury Department table "Light-houses, &c." by district with columns: station,
  superintendent, **keeper's name, where born, compensation**, running over about 25 pages.
- **OCR quality for this table: poor where it matters.** Station names are in a dotted-leader column and are
  scrambled (Portland Head came out as "Pa mace TOP 25s isniameed" beside "Joshua F. Strout ... 620 00" and "Mrs. M. E.
  Strout ... 400 00" in 1871). A grep for `Portland Head` found **0** hits in the 1871 volume although the station is
  there. Grepping the **surname** works ("Strout" 4-5 hits per volume, but includes unrelated Strouts). Rows
  cannot be tied to stations from the text file; you would need the hOCR coordinates (`_chocr.html.gz`, 60-70 MB
  per volume) or the page image.
- **Recommended use:** `research source (cite per station)`, **by page image only, after the USLHS roster gives the
  surname and years**: the cite is "Official Register 1871, Treasury Dept., Light-houses, page N", with salary and
  birthplace as extra facts. Not suited to the local grep corpus, except for a surname fallback.
- **Licence:** US federal publication.

### 2.5 Instructions to Light-Keepers, rules, and the 1850s investigation

| Item | IA identifier or other | Notes |
|---|---|---|
| Instructions to Light-Keepers, July 1881 | `1881USLH` (100 MB item) | Full text; the standing daily duties. |
| Instructions and directions to light keepers, 1871 | `ldpd_8960711_000` (4.3 GB item, Columbia) | Text available but the item is huge; use in-item search. |
| Organization and Duties of the Light-house Board; Rules, Regulations & Instructions (1864) | `organizationand00boargoog` | Google scan. |
| Instructions to light-keepers, 1902 edition | `instructionstoli0000unse` | 1989 photoreproduction; **lending-library**, search only. |
| Laws relating to the Light-House establishment (1871) | HathiTrust `103448661`, `lawsofstatescedi00unit` on IA | HathiTrust blocked. |
| Papers on the comparative merits of the catoptric and dioptric systems (1861) | `papersonthecompa00unitiala` | The Lighthouse Board's own report on lenses. |
| Report of the Officers Constituting the Light-House Board (1851) and Pleasonton's Compilation of Public Documents (1840) | Google Books `vL9SAAAAcAAJ`, `K1JYAAAAYAAJ` (per the Online Books Page) | **UNVERIFIED:** not fetched. These are the 1850s investigation papers. Google Books API without a key returns "quota 0 per day" (HTTP 429), so no machine access. |
| Index-catalogue of the Library of the Light-House Board (1886) | `indexcataloguel00librgoog` | Bibliography; useful to find other period reports. |

- **The 1850s investigation** (the 1851 Board of officers that led to the Light-House Board, and the earlier
  Treasury-era papers) is partly in the two Google Books items above and partly in Congressional Serial Set volumes
  (which of the Serial Set volumes holds which paper was **not checked**). IA has Serial Set scans
  (`unitedstatescon450offigoog`, `unitedstatescon243offigoog`, `unitedstatescon245offigoog`, `congressionalse160offigoog`
  turned up in full-text search); the full-text endpoint can find page numbers. Not run to ground.
- **Also useful and verified on IA:** Secretary of the Treasury annual reports `SecTreasAnnReport1855`, `...1871`,
  `...1874`, `...1875`, `...1876` (the Lighthouse Board's summary and appropriation context).

### 2.6 Why not HathiTrust, Google Books or the USCG Historian for bulk text

- **HathiTrust** (`babel.hathitrust.org`, `catalog.hathitrust.org`, `www.hathitrust.org`): every request from this
  machine, including `robots.txt` and the catalog API, was redirected to `babel.hathitrust.org/cgi/ls` and answered
  with a Cloudflare "Just a moment..." challenge (HTTP 403). **Skipped; not automated around.** It holds the
  complete Lighthouse Board run and the Lighthouse Service Bulletin; a human with a browser can download volumes from
  the catalog records the Online Books Page lists (for example `catalog.hathitrust.org/Record/009422752`, annual report).
- **Google Books API:** quota is 0 requests a day without a key (429). Not usable.
- **NARA catalog:** see 4.2.

### 2.7 USCG Historian (history.uscg.mil), on hold

Akamai answers 403 "Access Denied" to curl and to the fetch tool (including `robots.txt`). Per the owner's hold, nothing was
read from it or its Wayback copies. For the record, from search snippets only: the site's Lighthouse Service
bibliography page lists the Board's annual reports, *Lighthouse Service Bulletin* run references, and a "Historic
Documents" collection that includes at least the Light-House Board report for fiscal 1884. It would be the best single
place for **PDFs of the Board and Commissioner reports** and station histories if the hold lifts.

---

## 3. US Life-Saving Service annual reports (1876-1914)

- **URLs:** `https://archive.org/details/<id>` (identifiers below). Series title: "Annual report of the operations of the
  United States Life-Saving Service for the fiscal year ended June 30, YYYY" (renamed "Annual report of the United
  States Life-Saving Service" from about 1902).
- **Coverage on IA:** two parallel sets, **37 volumes in all**, roughly **fiscal 1876-1909**. Year coverage was read
  from each volume's first 60 KB with an HTTP Range request (`tools/yr.py`), so the labels are reliable but some
  volumes hold two years.

| Years (fiscal) | IA identifiers | OCR text |
|---|---|---|
| 1876 | `annualreportope07servgoog` | 0.5 MB |
| 1876-77 | `annualreportope00servgoog` | 0.4 MB |
| 1878 | `annualreportope01servgoog` | 1.2 MB |
| 1879 | `lifesavingservic00unitrich` | 0.8 MB |
| 1880 | `lifesavingservic01unitrich` | 1.2 MB |
| 1881 | `lifesavingservic03unitrich` | 1.3 MB |
| 1883 (label; not read) | `annualreportope02servgoog` | metadata call returned HTTP 500 |
| 1884 | `annualreportofop00unit`, `annualreportope04servgoog`, `lifesavingservic10unitrich` | 1.8 / 1.7 / 1.6 MB |
| 1888 | `annualreporto301888unit`, `annualreportofop1888unit` (labelled 1888/89; text says 1889) | 2.0 / 1.6 MB |
| 1889 | `annualreportope10servgoog` | 1.7 MB |
| 1891 | `annualreportope08servgoog` | 0.8 MB |
| 1892 | `annualreportope09servgoog` | 1.1 MB |
| 1893 | `lifesavingservic08unitrich` | 1.3 MB |
| 1894 | `lifesavingservic09unitrich` | 1.4 MB |
| 1895 | `lifesavingservic06unitrich`, `annualreportope03servgoog` (1895-96) | 1.5 / 1.5 MB |
| 1896 | `lifesavingservic07unitrich`, `annualreportope05servgoog` | 1.6 / 1.7 MB |
| 1897 | `lifesavingservic02unitrich` | 1.7 MB |
| 1898 | `lifesavingservic13unitrich`, `annualreportope06servgoog` | 1.4 / 1.3 MB |
| 1899 | `lifesavingservic12unitrich` | 1.7 MB |
| 1900 | `lifesavingservic17unitrich` | 1.5 MB |
| 1901 | `lifesavingservic16unitrich` | 1.6 MB |
| 1902 | `lifesavingservic15unitrich`, `annualreportofun1902unit` | 1.6 / 1.6 MB |
| 1903 | `lifesavingservic14unitrich`, `united-states-life-saving-service-0001` (404 on the text file; item is 68 MB) | 1.6 MB |
| 1904 | `lifesavingservic04unitrich` | 1.6 MB |
| 1905 | `lifesavingservic05unitrich` | 1.6 MB |
| 1906 | `lifesavingservic97unitrich` | 1.5 MB |
| 1907 | `lifesavingservic98unitrich` | 1.7 MB |
| 1908 | `lifesavingservic99unitrich` | 1.6 MB |
| 1909 | `annualreportofun00unit_2` | 1.6 MB |

- **Not found:** 1877 separately, 1882, 1885-87, 1890, 1910-1914 (the Service merged into the Coast Guard in January
  1915; the last reports may sit under the Coast Guard's annual reports). These are probably on HathiTrust; searching IA
  under other titles was not finished before IA stopped answering.
- **Fields (UNVERIFIED in the downloaded text: I read only front matter and year labels of these volumes; the structure below is the series' known layout and must be confirmed on the first volume the corpus build opens):** the narrative front matter (new stations, boats, rewards); **a table of wrecks and casualties for the
  year, station by station** (vessel, date, place, persons on board, saved, lost, property value) with the district
  and station name in the heading; the "Medals of honor" narratives; the list of stations by district with the
  **keeper's name** and (in some years) crews ("surfmen"); the "Casualties" appendix by vessel. This is **the best
  source for wrecks and rescues**, station by station and tied to a named place, and it often names the lifesavers
  and the keepers of nearby light stations who helped.
- **Access:** same IA patterns as section 1; typical text volume 1.5 MB, about 500 pages. Page numbers via the in-item
  search endpoint.
- **OCR quality:** the Google scans have the same proper-noun damage as 2.1. Not sampled for station hits in this survey (time).
- **Licence:** US federal publication. 1876-1914 reports are public domain.
- **Recommended use:** `bulk source` for the corpus and `research source (cite per station)`. Rough size of the
  whole set on IA: **~50 MB of text** (the 20 `lifesavingservic*` volumes are ~30 MB; the other 17 ~20 MB), with
  duplicate years.
- **Pairing:** one IA hit per wreck should be cross-checked against the NOAA wreck layer and the newspapers.


---

## 4. Keeper records

### 4.1 USLHS Digital Archive / Research Catalog (best keeper-roster source)

- **Name and URL:** U.S. Lighthouse Society Digital Archive (a.k.a. Lighthouse Research Catalog),
  `https://archives.uslhs.org/`. Place page `https://archives.uslhs.org/places/<slug>`; person page
  `https://archives.uslhs.org/people/<slug>`; **roster endpoint `https://archives.uslhs.org/general/showPeople/<place-node-id>`**.
- **Coverage:** the place database says "Displaying 1 - 30 of **2299**" places (light stations, lightship stations,
  minor aids, life-saving stations, depots, fog signal stations, houses of refuge, museums, replicas), US states and
  territories (Puerto Rico, Guam, American Samoa, US Virgin Islands, Northern Marianas, Minor Outlying Islands are filter
  options). The collection facet "Kraig Anderson Inventory of Lighthouse Personnel" shows **47,592** records; "National
  Archives" 18,932; "National Archives Clippings Files" 1,772; "U.S. Lighthouse Service Bulletin" 37. The people records
  come from NARA's keeper registers (each person page ends "Source: Register of Lighthouse Keepers"). Standing and lost
  both; US only (no Canada).
- **Fields (person):** first and last name, middle initial, type (for example "Other Lighthouse Personnel"), place(s),
  **title/position** (Principal Lighthouse Keeper, Acting Principal, 1st/2nd/3rd Assistant, Laborer, Contractor, USCG),
  **year started, year departed** ("at least 1915" is used when only a later date is known), begin and end salary,
  source. Place pages also carry lat/long in degrees and minutes, county, year established, tower and keeper's quarters
  data, lens (original optic and year installed), automation year, owner, access, and links to Documents, Photographs,
  Postcards, Architectural Plans, **Newspaper Clippings**, Objects, People.
- **Access (tested, three stations):**
  1. Find the slug: `https://archives.uslhs.org/places?title=%22Portland+Head%22` returns a small HTML table;
     the exact-phrase quotes matter (without them it returns 104 partial matches). Slugs found: `portland-head`,
     `split-rock` (also `split-rock-point`), `point-reyes`. The unfiltered index pages 30 places at a time
     (`?page=N`, about 77 pages) and gives every slug, so one crawl of ~80 pages lists all places.
  2. Read the place page; it contains the node id in a link `showPeople/<nid>` (Portland Head 2931, Split Rock 3357,
     Point Reyes 2724).
  3. `GET /general/showPeople/<nid>` returns a short JSON (an Ajax command) whose `data` is HTML: `<h5>` role headings and
     `<li>` rows of "Name (start-end)". Portland Head's was 20 KB, Point Reyes 253 lines.
  Full enumeration is about 2,300 places x 2 requests = 4,600 requests = **about 2.6 hours at 2 s**. The roster JSON is
  one request per station and is all a story agent needs.
- **robots.txt (fetched, both `archives.uslhs.org` and `uslhs.org`):** `User-agent: *` disallows only Drupal
  internals (`/core/`, `/profiles/`, `/admin/`, `/search/`, `/user/...`, `/node/add/`, `/comment/reply/`). `/places`,
  `/people`, `/general/` and `/node/<n>` are not disallowed. No AI-crawler rules. (`/search/` is disallowed, which is why
  the `places?title=` view is used and not the site search.)
- **Licence:** footer on every page: "(c) 2026 U.S. Lighthouse Society, All Rights Reserved." No data licence stated.
  Treat as **facts only, with credit and a link** (names, roles, years, salaries), as the DESIGN rule for registry data;
  never copy its comments or descriptions.
- **Quality:** high and the same data as LighthouseFriends (below). Portland Head, 31 principal keepers 1791-1989 and
  about 30 first assistants, with ranges: for example Joshua F. Strout 1869-1904, then Joseph W. Strout 1904-1928.
  Cross-check with the **1871 Official Register** (page images aside, the text shows "Joshua F. Strout ... 620 00" and
  "Mrs. M. E. Strout ... 400 00"): the USLHS record has Mary E. Strout as first assistant 1869-1877, so the two sources
  agree. Split Rock's five principal keepers (Young 1910-28, Covell 1928-44, Gagnon 1944-46, Rhea 1946-47, Bennetts
  1947-61) match the Minnesota Historical Society's list. Known flaws: spelling (LighthouseFriends prints "Dave Dunacan",
  USLHS "Dave Duncan", NewEnglandLighthouses lists "Reuben Freeman 1795-1796" for the same slot, so **the first-keeper
  years at Portland Head are disputed**), year-only dates (no months), gaps (Point Reyes shows nobody between 1943 and 1954 except an "at least 1950-1951" entry), and "at least" dates after about 1950.
  **Rosters are a start, not a final word: every roster line in a story still needs a cite to a primary record.**
- **Recommended use:** **`bulk source` for the keepers roster (per station), `research source (cite per station)`,
  facts only, link on every page.** Sample record (our words): Split Rock, Minnesota, node 3357: principal keeper
  Orren P. Young 1910-1928, then Franklin J. Covell (who had been second and first assistant earlier); first assistant
  Edward F. Sexton 1910 only (he drowned that October with the second assistant Roy C. Gill, 1910); a crowded 1930s
  list of second and third assistants including Thomas S. Hassing (1933, then 1938-53 as first assistant).
  Samples: `data/raw/survey/history/uslhs/`.
- **People ids:** the roster gives names only; person pages are at `/people/<slug>` (Dexter W. Baker: laborer at
  Abagadasset Point Range, started 1903, salary $250-252). A person who served at two stations is two records; the
  **"never join two people by name alone"** rule of DESIGN 3.6 applies.

### 4.2 NARA Record Group 26 keeper records

- **Name and URL:** *Registers of Lighthouse Keepers, 1845-1912*, microfilm publication **M1373**, six rolls;
  descriptive pamphlet `https://www.archives.gov/files/research/military/coast-guard/m1373.pdf` (2 pages, fetched);
  overview `https://www.archives.gov/research/lighthouses`.
- **Coverage (pamphlet):** 19 volumes, filmed by region: roll 1 New England and the early all-region registers; roll 2
  New York to Virginia; roll 3 North Carolina to Texas; roll 4 Great Lakes 1845-1900; roll 5 Great Lakes 1901-1912; roll 6
  West Coast, Alaska, Hawaii. Each volume has a surname-and-station index filmed with every roll. Most lists start
  about 1849. Entries give the keeper's name, district and station, appointment date, date of resignation, discharge
  or death, and sometimes salary. The NARA page lists other keeper-related RG 26 series, **none microfilmed**: Series 97
  Appointments and Transfers 1870-1903; 98 Lighthouse Keepers and Other Employees 1853-1868; 100 Appointments of
  Keepers 1832-1860; 101 Record of Salaries 1801-1849 and 1881-1902; 105A Register of Employees 1871-1907; 82
  Correspondence Concerning Keepers and Assistants 1821-1902; 102 Letters of Appointment 1886-1907. The page says
  relatively few records are available online in the National Archives Catalog.
- **Digitised in the catalog without a login?** **Could not be tested.** `https://catalog.archives.gov/robots.txt` reads
  `User-agent: *` / `Disallow: /`, which covers the catalog's API host path too (`/api/v2/`), and that API needs a key
  requested from NARA by email in any case. Skipped per rules. The USLHS says (search summary, **UNVERIFIED**) that NARA
  scanned the six rolls to CD and that all of M1373's keeper data is in its Research Catalog (4.1), which matches the
  "Source: Register of Lighthouse Keepers" lines. **No open page-image copy of M1373 was found;** the USLHS archive does
  hold scans of register pages by station and date span (for example "Abagadasset Point Keepers: 1903 - 1904", a JPEG
  of the register page; `https://archives.uslhs.org/node/112709`), tagged "Registers of Lighthouse Keepers" under
  `https://archives.uslhs.org/document-types/registers-lighthouse-keepers`, which is the cite-able primary image.
- **FamilySearch / Ancestry / Fold3:** logins; not pursued. A search found no sign that M1373 is indexed there.
- **Recommended use:** `research source (cite per station)`: the cite is "NARA RG 26, M1373, roll N, volume page"; use
  the USLHS register-page images when they exist for that station. Never as a bulk fetch.

### 4.3 Community keeper lists (facts only)

| Site | URL pattern (tested) | Format | Coverage | robots.txt | Licence words seen |
|---|---|---|---|---|---|
| LighthouseFriends (Kraig Anderson) | `https://www.lighthousefriends.com/light.asp?ID=<n>`; Portland Head is `ID=546` (IDs 1 and 5 return "Not Found") | One HTML page per light. Line "Keepers: Head: Name (1791 - 1795), ... Assistant: ..." runs name and years inline; references listed at the bottom ("Lighthouse Board records, various years", D'Entremont, 2009, and others). | US (and some Canada); the roster is the same Anderson data as 4.1. Station count not taken (the other surveys count it). | **404, so no rules** | "Copyright (c) 2001- Lighthousefriends.com. Pictures on this page copyright Kraig Anderson, used by permission." |
| New England Lighthouses: A Virtual Guide (Jeremy D'Entremont) | `https://www.newenglandlighthouses.net/<slug>-history.html`, `...-bibliography.html` | A "Keepers:" paragraph: "Civilian principal keepers: Name (yyyy-yyyy); ..." then Coast Guard keepers. The page warns the list is a work in progress. | New England only | `User-agent: *` disallows `/ajax/` and `/apps/`; NerdyBot disallowed; dotbot `Crawl-delay: 10` | Page asks that copying the list is at the copier's own risk; copyright site. |
| Terry Pepper, *Seeing the Light* | `https://terrypepper.com/lights/superior/splitrock/splitrock.htm` (and `keepers.htm`, `splitrock01.htm` ... in the same folder). The guess `/lights/closeups/phead/index.htm` for Portland Head gave 404. | Long narrative history pages with keeper biographies and career paths (the Split Rock page traces Orrin Young from Huron Island 1901 through Grand Island East 1908 to Split Rock, 20 July 1910). | Great Lakes (Superior, Michigan, Huron etc.); other coverage **UNVERIFIED** | **404, so no rules** | Copyrighted prose; author died 2019. Facts only; link. |
| Minnesota Historical Society, Split Rock keepers | `https://www.mnhs.org/splitrock/learn/keepers` and a roster PDF `https://archive.mnhs.org/sites/default/files/splitrock/learn/keepers/keepers.pdf` (from search results, **not fetched**) | State historical society page and PDF compiled with Great Lakes Lighthouse Research | One station | not fetched | not fetched |
| Great Lakes Lighthouse Keepers Association (`gllka.org`) | `https://www.gllka.org/researching-lighthouse-keepers` (robots: `Allow: /`) | A how-to for researching Great Lakes keepers, links to registers | Great Lakes | `User-agent: *` / `Allow: /` | not fetched |

- **Observed disagreement worth building for:** at Portland Head LighthouseFriends and USLHS give Joseph K. Greenleaf
  1791-1795 then a one-year keeper in 1796 ("Dave Duncan"/"Dave Dunacan"); New England Lighthouses names Reuben Freeman
  1795-1796 instead; and web-search summaries (not fetched) report a Founders Online note giving Joseph Greenleaf's death as 1814, while PBS
  and others say he died about two years into the job. The research agent must record the conflict, not pick one.
- **Recommended use:** `facts only, link`, never copied prose; use as a second opinion on the USLHS roster.

---

## 5. Newspapers

### 5.1 Chronicling America through the loc.gov JSON API (works; slow)

- **Name and URL:** Library of Congress, Chronicling America (NDNP), queried as the loc.gov collection
  `https://www.loc.gov/collections/chronicling-america/`.
- **Query form that worked (no key):**
  `https://www.loc.gov/collections/chronicling-america/?q=%22Point+Reyes%22+lighthouse+keeper&dates=1890/1900&fo=json&c=5&at=results,pagination`
  - `fo=json` JSON output; `c=` page size; `dates=YYYY/YYYY` the date window (**`start_date`/`end_date` were
    ignored**: a first test returned 1871 pages for a 1910-1912 window); `at=results,pagination` cuts the reply from
    about **1.9 MB** (the default carries facets and site chrome) to 17-55 KB. Quote phrases.
  - Reply: `pagination` (`of` is the hit count, `perpage`), and `results[]` with `date`, `title` ("Image 6 of The San
    Francisco call (San Francisco [Calif.]), April 28, 1895"), `id` and `url` of the form
    `https://www.loc.gov/resource/<lccn>/<YYYY-MM-DD>/ed-1/?sp=<page>`, `page_id`, `partof`, `location_state`,
    `image_url[]` (IIIF thumbnails) and `word_coordinates_url`. **`description` is the first 250 characters of the page's OCR,
    not the matching passage,** so each hit needs the page text.
- **Page text, cheaply:** take the `segment=` value of `word_coordinates_url` (or rebuild it from `image_url`) and fetch
  the ALTO XML from storage:
  `https://tile.loc.gov/storage-services/service/ndnp/<awardee>/<batch>/data/<lccn>/<reel>/<yyyymmdd><ed>/<seq>.xml`
  (example: `.../mimtptc/batch_mimtptc_jackson_ver01/data/sn86086633/00296024521/1910092201/1240.xml`, 870 KB, 0.6 s,
  4,758 words in `CONTENT="..."` attributes). The plain `.txt` guess returned 404, and the legacy
  `chroniclingamerica.loc.gov/.../ocr.txt` was redirected to a loc.gov HTML page that gave a **Cloudflare challenge (HTTP
  403, not bypassed)**. HTML pages on loc.gov and chroniclingamerica.loc.gov are challenged; the JSON API and `tile.loc.gov`
  were not. `tile.loc.gov/text-services/word-coordinates-service?...` returns a JSON term-to-coordinates map (343 KB), not text.
- **Tested hits:** *Split Rock*, `"split rock" lighthouse`, 1910-1912: 4 pages. The Calumet News (Calumet, Michigan),
  22 Sep 1910, p. 3, ALTO text: a storm account about the tug *Redwing*, "used by the engineers' department at
  Duluth in transporting supplies to the split rock lighthouse" (a sourced detail for the construction chapter; the
  agent must read the whole page for the date and the outcome). *Point Reyes*, 1890-1900, `"Point Reyes" lighthouse keeper`: 10
  pages, mostly San Francisco papers (Call, Morning Call, Los Angeles Herald). *Portland Head*: the query died
  (see below) and was not repeated.
- **Rate rules (loc.gov "Working Within Limits" page, fetched):** the JSON/YAML API allows **20 requests a minute** and a
  breach is blocked **for 1 hour**; text services 150 a minute; image services 150; `/storage-services/` media 150. No key.
  Page size at most 1,000; paging past the 100,000th result unsupported. `robots.txt` for www.loc.gov: `Crawl-Delay: 5`;
  `Disallow: /search`, `/cgi-bin/`, `/fedsearch` etc. (the `/collections/` path is not disallowed). **Use one request every
  5 seconds.**
- **Reliability today:** the six successful queries took between 2.8 s (a HABS query) and 41 s (median about 31 s); one returned
  HTTP 503 after 45 s ("We're swamped and our servers are down"); one died after 75 s with an HTTP/2 INTERNAL_ERROR and a
  truncated body. Build in retries with long back-off.
- **Quality:** page-level OCR with the usual newspaper damage ("McDon McDonald's - ald's", split hyphenated words);
  relevance is fuzzy: an unquoted query returned a congressional appropriations list that merely mentioned "light-house".
- **Licence:** **not checked** in this survey; verify the LoC rights statement before quoting at length. Short
  quotations with a cite (paper, date, page, LCCN) are what the story guide needs.
- **Recommended use:** `research source (cite per station)`: primary for rescues, storms, appointments, deaths, the
  1890s-1920s. Cost per station: one search per name or phrase (5-40 s each) plus one ALTO per hit (a few seconds).

### 5.2 Other free newspaper archives (robots status)

| Archive | robots.txt result | Verdict |
|---|---|---|
| California Digital Newspaper Collection `cdnc.ucr.edu` (Veridian) | `User-agent: *` `Disallow: /`; only `archive.org_bot` is allowed | **skip** |
| NYS Historic Newspapers `nyshistoricnewspapers.org` | same Veridian file | **skip** |
| Digital Michigan Newspapers `digmichnews.cmich.edu` | same | **skip** |
| Virginia Chronicle `virginiachronicle.com`; Indiana `newspapers.library.in.gov` | same Veridian file | **skip** |
| Washington Digital Newspapers `washingtondigitalnewspapers.org`; Illinois `idnc.library.illinois.edu` | Cloudflare "Just a moment..." (403) on `robots.txt` | **skip** (no bypass) |
| Portal to Texas History `texashistory.unt.edu` | `User-agent: ClaudeBot` / `Disallow: /` (named) | **skip** |
| Fulton History `fultonhistory.com` | `User-agent: *` `Disallow: /` | **skip** |
| Google News Archive `news.google.com` | `User-agent: *` `Disallow: /` | **skip** |
| Canadiana `canadiana.ca`; BAnQ `numerique.banq.qc.ca` | name `anthropic-ai`, `ClaudeBot`, `Claude-Web` | **skip** (orchestrator rule) |
| Maritime History of the Great Lakes `maritimehistoryofthegreatlakes.ca` | Cloudflare challenge (403) | **skip** |
| Founders Online `founders.archives.gov` | `robots.txt` returned HTTP 202 with an empty body (unreadable) | not used; search results showed it carries the 1789-91 Treasury letters about the first keepers |
| Florida UFDC `ufdc.ufl.edu` | `User-agent: *` disallows only `*.DZI`, `*.JP2` | allowed; **search and API not tested** |
| DigitalNC `newspapers.digitalnc.org` | `Disallow: /data/`, `Crawl-delay: 1`; Google-Extended and GoogleOther disallowed | allowed; not tested |
| Historic Oregon Newspapers `oregonnews.uoregon.edu` | `Disallow: /data/` | allowed; not tested |
| Georgia Historic Newspapers `gahistoricnewspapers.galileo.usg.edu` | disallows `*.pdf`, `*.txt`, `*.xml` | allowed pages only; no OCR text files |
| Utah Digital Newspapers `newspapers.lib.utah.edu` | `User-agent: *` open | allowed; inland, little use |

The big Veridian state sites that matter for coasts (CDNC, NYS, Michigan) are closed to crawlers except the Internet
Archive's own. **Chronicling America carries the volume**, and the 1890s-1920s West Coast, Great Lakes and New England
papers it holds are enough for most lights. Gaps: papers not in NDNP (many 1850s-1880s local weeklies).

### 5.3 Trade periodicals on the Internet Archive (full-text searchable, robots-clean)

`marine-record_<YYYY-MM-DD>` and `marine-review_<YYYY-MM-DD>` (Cleveland weeklies, Great Lakes shipping news, 1890s-1900s)
turned up in the IA full-text search for lighthouse terms (other trade titles were not searched for). They carry wreck, storm, collision and light-station notes for the Lakes. Same IA endpoints as section 1. Cite as "Marine Record, 14 June 1894".

---

## 6. NRHP nominations and HABS/HAER records

### 6.1 NRHP nomination PDFs through NPGallery (still working on 2026-10-21)

- **Name and URLs (all tested):**
  - Nomination text PDF: `https://npgallery.nps.gov/pdfhost/docs/NRHP/Text/<NRIS reference number>.pdf`
    (for example `73000121.pdf` = Portland Headlight: 354 KB, 5 pages, a typed 1969-form with a text layer).
  - Metadata page: `https://npgallery.nps.gov/AssetDetail/NRIS/<reference number>` (29 KB HTML: title, NRIS id,
    criteria, architects, areas and periods of significance, significant years, resource type, file size, date published,
    county, plus the `GetAsset/<guid>` links for the text and photo PDFs).
  - `https://npgallery.nps.gov/GetAsset/<guid>` (and `/NRHP/GetAsset/<guid>`) is the generic file route.
    **The old name-style route `GetAsset/NRHP_73000121_text` is dead** (it returns a 1,965-byte PNG, not a PDF).
- **If the record is not digitised,** the Text URL still answers 200 `application/pdf` but returns a **22,151-byte
  placeholder** whose only text is "The PDF file for this National Register record has not yet been digitized."
  (identical bytes for two different references, 69000093 and 70000329). **Detect it by size and that sentence.**
  A recent listing (16000099) came back as a 6.9 MB PDF with the full modern form.
- **Photos PDF:** `.../pdfhost/docs/NRHP/Photos/<ref>.pdf` is the usual sibling; **not tested**.
- **"NPGallery is being retired":** a search found no notice to that effect (newest source March 2026: the NPGallery About
  page still describes it as the National Register's digital asset system, with `nr_reference@nps.gov` for undigitised
  documents). The 2026 retirement news in the results concerned **Canada's Register of Historic Places** ("to be
  decommissioned this spring" in an advocacy post; `www.historicplaces.ca` still answered HTTP 200 on 2026-10-21):
  **flag for the Canada survey.** The `pdfhost` pattern is an old one, so a mirror matters: cache every nomination PDF
  the first time it is read (`research/fetch_text.py` already caches by URL).
- **robots.txt:** `https://npgallery.nps.gov/robots.txt` is 404 (no rules). Responses came back in 0.3-0.5 s.
- **Bulk reference numbers:** `https://home.nps.gov/subjects/nationalregister/data-downloads.htm` links spreadsheets
  dated 2026-05-22 (`national-register-listed_20260522.xlsx`, removed, MPS covers, NHLs, determinations, "everything"),
  an NRIS terminology PDF, and the public spatial dataset (IRMA DataStore profile 2210280); the station lists will use
  these to map stations to reference numbers.
- **Licence:** US federal record; the AssetDetail page carries a "Copyright Information" panel, not read in full. Credit NPS.
- **Quality:** 1960s-70s lighthouse nominations are 3-6 pages (little history); post-1990 nominations and NHL
  nominations are 20-100 pages with real history, often footnoted, and are the best prose to cite (as secondary, not
  primary, sources). The nomination's bibliography is a pointer to the primary sources.
- **Recommended use:** `research source (cite per station)`. Cite as "NRHP nomination, ref. 73000121, section 8".

### 6.2 HABS/HAER through loc.gov

- **URL:** `https://www.loc.gov/collections/historic-american-buildings-landscapes-and-engineering-records/?q=portland+head+light&fo=json&c=5&at=results,pagination`
  returned 3 results in 15 s, the first the right one: *Portland Head Light, Portland Head, approximately 1/2 mile East of
  Shore Road, Cape Elizabeth* at `https://www.loc.gov/item/me0026/` ("Documentation compiled after 1933").
  The item record `https://www.loc.gov/item/me0026/?fo=json&at=item,resources` took 1 s (56 KB) and lists the files:
  - **Data pages (the written history):** `https://tile.loc.gov/storage-services/master/pnp/habshaer/me/me0000/me0026/data/me0026data.pdf`
    (329 KB, **9 pages, about 2,000 words** of typed history and description, with a text layer; mentions the 1791
    tower, the 1890 keepers' double-dwelling plans and Coast Guard keepers),
  - `.../data/me0026cap.pdf` (photo captions),
  - `.../photos/087744pu.tif` and others (large TIFF masters; use the JPEG renditions instead).
- **Pattern:** `<state>/<state>0000/<id>/data/<id>data.pdf` under `https://tile.loc.gov/storage-services/master/pnp/habshaer/`.
- **A tile.loc.gov wrinkle:** one HTTP/2 download of that PDF died with `INTERNAL_ERROR` and a truncated file; `curl --http1.1` worked.
- **Coverage of the test stations:** Portland Head found. A query for `split rock light station` returned only an unrelated
  record, so Split Rock probably has no HABS record (not exhaustively confirmed; a different phrase might hit).
  Point Reyes not queried.
- **Rate rules and robots:** same as 5.1 (the JSON API is 20 requests a minute; use 5 s).
- **Licence:** federal documentation; rights are stated on each LoC item page (**not read** in this survey).
- **Recommended use:** `research source (cite per station)`: "HABS ME-xx, data pages, p. N", with the NRHP nomination.

---

## 7. General histories (public domain, full text) for marked period context

Rule from DESIGN 1: general context may only be cited to a history of the service, and framed as general. These are the
free full texts found. Identifiers were confirmed in IA metadata searches (title, creator, date, item size); full text was
**not opened** except where stated, because IA stopped answering.

| Work | Where (full text) | Notes |
|---|---|---|
| Arnold B. Johnson, *The Modern Light-House Service* (Washington: GPO, 1889/1890) | IA `modernlighthous00boargoog` (370 MB item) and `modernlighthous01boargoog` (50 MB). HathiTrust records `001623546` (1889) and `008615525` (1890) (Cloudflare). Appeared in full-text hits for lighthouse-service terms. | The standard late-1880s account by the Board's secretary: duties of keepers, lamps, fog signals, tenders. The core "how the service worked" cite for the 1870s-80s. |
| *Instructions to Light-Keepers* (1871, 1881, 1902 editions) | IA `ldpd_8960711_000`, `1881USLH`; 1902 as `instructionstoli0000unse` (lending only) | The daily-duty rules themselves; cite for what keepers were required to do. |
| Sumner I. Kimball, *Organization and Methods of the United States Life-Saving Service* (1912) | IA `organizationmeth00kimb`, `organizationmeth00kimbrich`, `organizationand00kimbgoog`, `organizationand01kimbgoog`, `organizationand02kimbgoog`, `cu31924030900009` | By the Service's general superintendent; how a station and its patrols worked. |
| Sumner I. Kimball, "The Life Saving Service" (1891) and S. S. Cox, "The Life-Saving Service" (1881) | IA `jstor-27898238`, `jstor-25100961` (early journal content) | Short period accounts. |
| W. D. O'Connor, *United States Life-Saving Service* (1884 sketch) | IA `sketch-of-the-united-states-lifesaving-watermark` (14 MB) | IA spells the author "O'Conner". |
| James Otis, *The Life Savers: A Story of the United States Life-Saving Service* (1899) | IA `lifesaversstoryo00otisiala`; Project Gutenberg `thelifesaversast43961gut` | A book for young readers: **cite with care as a narrative, not a record**. |
| George H. Elliott, *European Light-House Systems* (1875, tour of inspection for the Board) | IA `europeanlighthou00elliuoft`, `cu31924074297361`; the 1874 report `reportoftourofin00unitrich` | Comparison with Europe; Fresnel lens orders in use. |
| Frederick A. Talbot, *Lightships and Lighthouses* (1913, British, general) | Project Gutenberg #52817: `https://gutenberg.org/cache/epub/52817/pg52817-images.html` (from a search result; not fetched) | For lightship life in general; British slant. |
| D. P. Heap, *Ancient and Modern Light-houses* (1889) | IA `ancientmodernlig00heapuoft`, `ancientandmoder01heapgoog`, others | Technical history of lights. |
| **George R. Putnam, *Lighthouses and Lightships of the United States* (1917)** | **UNVERIFIED.** Searches found no archive.org, Gutenberg or HathiTrust full-text link (the HathiTrust hit was a different Putnam book). A lighthouse-history site says ForgottenBooks hosts it. NOAA's photo library has plates from it. | Written by the Commissioner of Lighthouses; the best single early-20th-century account. **Needs a human to locate a scan** (HathiTrust likely). |
| **George Weiss, *The Lighthouse Service: Its History, Activities and Organization* (Johns Hopkins Press, 1926)** | **UNVERIFIED.** The Online Books Page points to HathiTrust page images; no IA copy found. | A service monograph; best account of the Bureau of Lighthouses era. |
| USCG "Chronology of Aids to Navigation" PDF | `https://media.defense.gov/2020/Feb/28/2002256603/-1/-1/0/USLHS_CHRON.PDF` (from a search result; **not fetched**; media.defense.gov robots not read) | A dated chronology useful for context; cite its sources, not itself. |
| Canadian: *Review of Improvements in Lighthouse and Coast Service of Canada between 1896 and 1904* (Dept. of Marine and Fisheries, 1904) | IA `reviewofimprovem00canarich` (121 MB) | The best Canadian service-level source found. **No free full-text general history of the Canadian lighthouse service (the Weiss/Johnson equivalent) turned up.** `List of Lights and Fog-signals ... of the Dominion` (IA `listlightsandfo00unkngoog`, 1874) is a station list. |

- **Licence:** all US federal or pre-1930 works; no restriction. Canadian Crown works of this age are out of copyright.
- **Recommended use:** `research source (cite per station)` only for framed general context; also useful for vocabulary
  (what a "second assistant" or a "fourth-order lens" meant at the time).

---

## 8. Wrecks

### 8.1 NOAA: what exists today (and what no longer does)

- **AWOIS is retired.** The page `https://nauticalcharts.noaa.gov/data/wrecks-and-obstructions.html` now says the Office of
  Coast Survey has stopped updating AWOIS, "retired the AWOIS service", and points to **ENC Direct to GIS**.
- **The old download host is gone.** `wrecks.nauticalcharts.noaa.gov` presents a certificate for `gis.charttools.noaa.gov`
  (name mismatch, so curl refuses) and `HEAD /downloads/AWOIS_Wrecks.kml` returned **404** (checked once with certificate
  checking off, headers only, nothing kept). The Data.gov/AmeriGEO catalog still lists eleven resources
  (`AWOIS_Wrecks.kml`, `ENC_Wrecks.kml`, `AWOIS_Obstructions.kml`, the three `.xls` twins, a REST MapService, a WMS) with
  "License not specified" and a 2014 modified date (metadata record refreshed 2025-11-22). **Treat those as dead links.**
  The AWOIS User's Guide PDF at `nauticalcharts.noaa.gov/data/docs/wrecks-and-obstructions/awois-users-guide-2013.pdf` is also 404.
- **The AWOIS schema** (seen in a third-party ArcGIS Online extract of 359 California records, `Wrecks_Obstructions_AWOIS_DFG`):
  `RECRD`, `VESSLTERMS`, `AREA_ID`, `CHART`, `LATDEC`, `LONDEC`, `GP_QUALITY`, `GP_SOURCE`, `DEPTH`, `SOUNDING_T`, **`YEARSUNK`,
  `HISTORY`**, `REFERENCE`, `WorO`. A web-search summary describes the same fields on NOAA's merged database. That
  merged database (AWOIS + ENC) is what a "name, year sunk, history" layer needs. Where a current copy lives is **not
  established**: the HIFLD Open "Wrecks and Obstructions" layer was archived (DataLumos project 241132, ~3.5 MB per its
  portal page, January 2026) but DataLumos refused the fetch tool (403) and the NASA mirror (`maps.nccs.nasa.gov`) refused connections.
  A story agent can still read AWOIS text pasted into old Coast Guard or state publications, but there is no bulk source.

### 8.2 NOAA ENC Direct (live, tested; thin)

- **Endpoints:** `https://encdirect.noaa.gov/arcgis/rest/services/encdirect/<band>/MapServer/<layer>/query`, where `<band>`
  is `enc_harbour` (layer **36** `Harbor.Wreck_point`, 158 `Wreck_area`, 33/99/156 obstructions), `enc_coastal` (layer
  **33** `Coastal.Wreck_point`, 120 `Wreck_area`, 30/78/118 obstructions), and the other scale bands (`enc_approach`,
  `enc_berthing`, `enc_general`, `enc_overview`; layer ids not listed). Same service is also at `gis.charttools.noaa.gov`.
  Query example (tested): `.../enc_harbour/MapServer/36/query?geometry=-70.30,43.55,-70.10,43.70&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&outSR=4326&f=json`
  (0.2 s, 12 wrecks around Portland Head). `maxRecordCount` is 1,000; counts: **8,175** harbour-band and **3,790**
  coastal-band wreck points.
- **Fields:** `OBJL`, `CATWRK` (dangerous wreck / non-dangerous / showing hull ...), `CONRAD`, `CONVIS`, `EXPSOU`, `HEIGHT`,
  `OBJNAM`, `QUASOU`, `SOUACC`, `TECSOU`, `VALSOU` (depth), `VERACC`, `VERDAT`, `VERLEN`, `WATLEV`, `INFORM`, `SCAMIN`,
  `SORDAT` (source date, for example 20070316), `SORIND` (source, for example "US,US,graph,Chart 13292"), `DSNM` (the ENC cell).
- **Finding:** `OBJNAM <> ''` and `INFORM <> ''` each returned **0** in both layers. **These layers carry no wreck
  names, no year sunk and no history text.** What they do give is position, category, depth, and the chart source.
- **Coverage:** US coastal waters, Great Lakes and territories where there is an ENC (not checked per territory).
- **robots.txt:** `encdirect.noaa.gov` and `gis.charttools.noaa.gov` serve ArcGIS REST; no robots file was fetched for them (the NOAA
  Coast Survey site `nauticalcharts.noaa.gov/robots.txt` is 404). Responses are fast; use 2 s.
- **Licence:** NOAA/US federal public domain. The services say "not intended for navigation" and the standard NOAA
  chart disclaimers apply.
- **Recommended use:** `bulk source` for the **map layer of positions** (DESIGN 3.7 "Recorded wrecks within 5 nm"); label
  them "wreck, category, source year" and do **not** name them. Names, dates and fates come from stories.

### 8.3 Rescue and wreck facts for the story text (not NOAA)

1. **Life-Saving Service annual reports** (section 3): vessel, date, place, persons saved and lost, station.
2. **USLHS Digital Archive** categories (counts from the site's facet list): *Gale or Hurricane* [450], *Rescue* [111],
   *Accident* [647], *Construction* [9,640], *Civil War* [22], *WWI* [22], *WWII* [48], *Automation* [172]: document and
   photo records tagged by place. Not opened.
3. **Chronicling America** and **IA trade periodicals** (5.1, 5.3).
4. **Great Lakes leads (untested):** the Wisconsin Historical Society shipwreck database, NOAA's Thunder Bay National
   Marine Sanctuary lists, and BGSU's Historical Collections of the Great Lakes vessel index. Not fetched; the
   orchestrator should assign one agent if the Lakes layer needs fates and years.
- **Canada:** the CHS electronic charts carry the same S-57 wreck features (service host `gisp.dfo-mpo.gc.ca` did not resolve
  from here; the CHS and Open Government Licence details are in 9.3). **No open Canadian wreck-history dataset was
  found** (Nauticapedia is excluded by rule).

---

## 9. Charts

### 9.1 NOAA Historical Map & Chart Collection: images only

- **URL:** `https://historicalcharts.noaa.gov/` (search page `search.php`; also `collections.php`, `publications.php`).
- **robots.txt (fetched, 25 bytes):** `User-agent: *` / `Disallow: /`. **Skip crawling;** a human can use it. (Not read beyond the home page.)
- **What it is:** a search by map point or place name with filters (chart type: Nautical Chart, Great Lakes, H-Sheet, T-Sheet,
  Annual Report, Civil War...; state), results shown as footprints on an OpenLayers map, download of scanned images. A
  search summary says more than 35,000 scanned images, mid-1700s onward, marked not for navigation. **No georeferenced tile,
  WMS or IIIF service was found** on the site or in the NOAA ArcGIS folders listed at `gis.charttools.noaa.gov`
  (folders include `USCHC` and `RNC`, which hold only a US-Canada boundary layer and raster-chart footprints).
- **Licence:** NOAA public domain.
- **Recommended use:** `skip` for the overlay. Use only as a pointer to which historical charts exist for a station
  (a human or a one-off agent can cite "NOAA/Coast Survey chart of 18xx").

### 9.2 NOAA Shoreline T-sheets: georeferenced, worth a follow-up (from search results only)

Web-search summaries report that NOAA's Shoreline site (`https://shoreline.noaa.gov/t-sheets.html`) offers
**georeferenced** historical topographic survey sheets (T-sheets, 1840s onward) as JPG downloads at 1:10,000-1:60,000 on
NAD83, covering the continental US, Alaska, Hawaii, Puerto Rico and the US Virgin Islands; some sheets are only at NARA;
alignment against modern basemaps is imperfect. They show shorelines, wharves and buildings at lighthouse sites and are
the right "then and now" material. **UNVERIFIED:** `shoreline.noaa.gov/robots.txt` returns an S3 "Access Denied"
XML (no robots file readable) and the host named in one result (`shoreline.chs.coast.noaa.gov`) did not resolve; no tile or
WMTS endpoint was found. A Maine state WMS built from 1858-1909 NOAA charts, and a PSMFC ArcGIS service of 1840s-1912
T-sheets for the National Estuarine Research Reserves, were cited as examples of georeferenced overlays built by others.

### 9.3 Current NOAA charts as an overlay (tested)

| Option | URL | Result |
|---|---|---|
| **ENC chart display WMS (works)** | `https://gis.charttools.noaa.gov/arcgis/rest/services/MCS/NOAAChartDisplay/MapServer/exts/MaritimeChartService/WMSServer` | GetCapabilities 151 KB (layers 0-12). A GetMap for one web-mercator tile (`crs=EPSG:3857`, 256x256, `format=image/png`, `transparent=true`, layers `0,...,12`) returned a 37 KB PNG in 0.24 s: `.../WMSServer?service=WMS&version=1.3.0&request=GetMap&layers=0,1,2,3,4,5,6,7,8,9,10,11,12&styles=&crs=EPSG:3857&bbox={bbox-epsg-3857}&width=256&height=256&format=image/png&transparent=true` works as a MapLibre raster source. |
| ENC chart display export | `.../MapServer/exts/MaritimeChartService/MapServer/export?bbox=-70.25,43.60,-70.15,43.66&bboxSR=4326&imageSR=3857&size=800,600&format=png&f=image` | 800x600 PNG in paper-chart style (checked by eye: Portland Head approaches, depths, buoys). |
| NOAA XYZ tiles `tileservice.charts.noaa.gov/tiles/50000_1/{z}/{x}/{y}.png` | the documented tile service | **Timed out three times from this machine** (the host resolves to 140.90.101.147). Retry from another network before relying on it. |
| WMTS `.../MarineChart_Services/NOAACharts/MapServer/WMTS` | capabilities XML loads (19 KB, ResourceURL template, `GoogleMapsCompatible`) | **Not working:** the MapServer behind it answers "Could not find service", and a tile request returned HTTP 400 "Invalid URL". |
| ENC Direct vector services | section 8.2 | Lights, wrecks, obstructions as features (also the source for the "light at night" fields). |

- **Licence:** US federal public domain; services say not for navigation. A map overlay must carry that line.
- **robots.txt:** none published for `charts.noaa.gov` (404) or `nauticalcharts.noaa.gov` (404); REST host not checked.
- **Recommended use:** `bulk source` for the current-chart overlay via the WMS (no key, public domain).

### 9.4 Canada

- The Canadian Hydrographic Service ENC "Maritime Chart Service" is published as a WMS and an ESRI REST service (per the
  open.canada.ca record; coverage-limit layers state the Open Government Licence - Canada; the digital chart *downloads* need
  a GCKey account; the service says not for navigation). The host the search results named, `gisp.dfo-mpo.gc.ca`, **did not
  resolve** from this machine; `egisp.dfo-mpo.gc.ca` resolves and lists 761 open-data MapServers but **no ENC chart service**
  (only `chs_edh_s57_individual_enc_limits`, `chs_edh_paper_nautical_chart_limits`, `chs_edh_cd_collections_chart_limits`,
  `chs_edh_survey_index`, `bc_lightstations_and_other_sample_sites` and `lighthouse_inventory_hlpa`, the last being the
  Heritage Lighthouse Protection Act inventory: **flag for the Canada survey**). No official CHS tile (WMTS) service was found.
- **Canadian historical charts:** none found as a georeferenced open service; Library and Archives Canada was not queried.

---

## 10. Weather and logbooks

- **Station logs and journals that are online (all small, scattered):**
  - *Port Sanilac Light Journals*, Sanilac District Library, Michigan: volume 1 covers 13 Oct 1886 to 22 Mar 1901 and later
    volumes run to 1918; library staff **transcribed** them to searchable PDFs
    (`https://sanilacdistrictlibrary.specialdistrict.org/port-sanilac-lighthouse-journals`; robots blocks only SemrushBot and
    AhrefsBot). The best match for "openly searchable keeper's journal".
  - *South Haven (Michigan) lighthouse logs*, Western Michigan University Libraries: high-resolution page images of keeper
    journals from 1872 (end date varies by source, 1880 to 1889); mostly James Donahue; only selected transcriptions
    (`wmich.edu/library/lighthouse-logs-collection`). Not fetched.
  - Yaquina Head (Oregon) keeper's logs and letters from NARA, volunteer transcription on FromThePage
    (`fromthepage.com/YaquinaLights`; 2017 post, project status not checked; its `robots.txt` was only skimmed, with several named bots such as Amazonbot disallowed).
  - Brant Point Light Station record of inspections (Nantucket Historical Association), IA `ab314` (a 58 MB item).
  - NARA RG 26 holds the original logs; the NARA page lists them but the catalog is closed to us (4.2).
  - Sombrero Island lighthouse journal 1895-1898 (Anguilla), British Library Endangered Archives: images only.
- **Storm and weather records (open, public domain, machine-readable):**
  - HURDAT2 (Atlantic hurricane tracks 1851 onward): `https://www.nhc.noaa.gov/data/hurdat/` (index fetched; text files
    named `hurdat2-1851-YYYY-*.txt`; `nhc.noaa.gov/robots.txt` allows everything). Gives dates, tracks and winds for named storms.
  - **The Lighthouse Service Bulletin** (2.3) carries storm reports and fog-hours tables station by station for 1912-39;
    the Board reports (2.1) carry fog-signal hours by station each year.
  - The **USLHS archive** facet "Gale or Hurricane" (450 records) (4.1) tags documents by place.
  - Leads not tested: the Weather Bureau's *Monthly Weather Review* (from 1872), NOAA Daily Weather Maps (1871 on),
    the Old Weather project (`oldweather.org`, robots 404) for logbook-derived weather from ships and cutters.
- **Lightship logs:** none found openly searchable; the USLHS archive has a "Vessels" section (not opened).
- **Recommended use:** the Bulletin and the Board reports for fog and storm numbers; HURDAT2 only to confirm that a named
  storm was within range on a date a source already gives; transcribed journals (Port Sanilac, South Haven) as primary
  atmosphere for the few stations they cover.

---

## 11. The three test stations, source by source

| Source | Portland Head, ME | Split Rock, MN (lit 1910) | Point Reyes, CA (lit 1870) |
|---|---|---|---|
| USLHS roster (`showPeople`) | place node 2931: 31 principal keepers 1791-1989 (Greenleaf 1791-95 to Davis Simpson 1986-89), about 30 first assistants, contractors, a 1989 Coast Guard entry | node 3357: 5 principal keepers 1910-1961 (Young, Covell, Gagnon, Rhea, Bennetts) plus 5 Coast Guard-era principals to 1968; 11 first assistants; 27 second assistants; third assistants | node 2724: 253 roster lines from John C. Bull 1870 through the 1970s, acting keepers, first assistants and below |
| Light-House Board reports on IA (FY1891-1902, 7 vols) | 2-4 mentions per volume: fog trumpet hours, characteristic changes (30 Apr 1896, 15 May 1899), tower repointed (1900-01), a 1892-93 note on the Spring Point Ledge bell | none for Minnesota; **"Split Rock" = Lake Champlain, NY** (dwelling work, 1898) | 1-4 per volume: siren replaced by steam whistles (Sept 1890), whistle hours 1,080-1,674 a year, 35,000-gallon tank (1896), a note that the stretch to Point Arena is the scene of many wrecks |
| Commissioner report (FY1915, only one found) | 0 | 3 mentions, including the table of stations established ("light and fog-signal station 1910") | not searched |
| Lighthouse Service Bulletin (1912, 1933 sampled) | 0 | 0 in 1912 | 1912: 1; 1933: 3 (foggiest station: 1,774 hours in fiscal 1932, 2,129 in 1930) |
| Official Register (1857, 1871, 1881) | Strout rows readable; station column scrambled (grep for "Portland Head" = 0 in 1871) | not applicable before 1910 | a "Point Reyes ... 800 00" row in 1881; keeper name column misaligned |
| NRHP nomination | ref 73000121: 5 pages, digitised | not looked up | not looked up |
| HABS | `me0026`: 9-page data pages PDF, about 2,000 words | a query returned no Split Rock record | not queried |
| Chronicling America (loc.gov API) | query failed (HTTP/2 error); not repeated | 4 pages, 1910-12; Calumet News 22 Sep 1910 p. 3 on the tug *Redwing* | 10 pages (of 47 hits) 1890-1900, San Francisco papers |
| NOAA ENC wreck points | 12 points in a 0.2 x 0.15 degree box (harbour band); no names | not queried | not queried |
| Other | Joshua Strout's 35 years; NewEnglandLighthouses lists a different 1795-96 keeper than USLHS | Terry Pepper page with keeper career paths; MNHS keeper PDF | n/a |

Take-away: **Portland Head's story is thick on people and thin in the Board reports; Split Rock's is thick in newspapers
and the Pepper/MNHS secondaries because its record starts in 1910 (after the Board era); Point Reyes is dense in the
Bulletin and Board reports because of fog.** No single source covers a station; the method in section 13 layers them.

---

## 12. Counts, gaps, risks

**Counts (this survey).**

| Item | Count |
|---|---|
| USLHS places / personnel records | 2,299 places; 47,592 personnel records (collection facet) |
| NARA keeper registers (M1373) | 19 volumes on 6 rolls, 1845-1912 (microfilm only; no open scans found) |
| Light-House Board report volumes on IA | 7 compilations, about FY1891-1902 (of 59 years) |
| Commissioner of Lighthouses reports on IA | 1 (fiscal 1915) (of about 29) |
| Lighthouse Service Bulletin | 27 yearly PDFs of 28 at uslhs.org (1925 missing under the standard name) |
| Life-Saving Service annual reports on IA | 37 volumes, about 28 of 39 fiscal years |
| Official Register on IA | 503 items matched by title (volumes plus indexes) |
| Canadian Marine and Fisheries reports on IA | about 55 items, 1901-1925 |
| NOAA ENC wreck points (harbour band / coastal band) | 8,175 / 3,790 |
| Local-corpus text size | LHB 7.7 MB (have); LSS ~50 MB; Canada est. 100-150 MB (**estimate**); Bulletin ~7 MB of text from ~280 MB of PDF; Official Register ~250 MB (**optional**) |

**Gaps.**
1. **Light-House Board annual reports for ~47 of 59 years** and the Commissioner reports for ~28 of 29 years are not on IA;
   HathiTrust has them behind Cloudflare, Google Books needs a key, the USCG Historian is on hold. The most valuable
   missing years are the 1850s-1880s (first lenses, rebuilds) and 1910-1939.
2. **Life-Saving Service** missing years (1882, 1885-87, 1890, 1910-14) and the second half of the Service in the Coast Guard reports.
3. **No keeper record images except scattered USLHS register pages;** NARA's catalog is closed to us.
4. **No names, years or histories for wrecks** from any open NOAA service now (AWOIS retired; ENC fields blank).
5. **No georeferenced historical charts** (NOAA Shoreline T-sheets are the lead).
6. **Canada:** Canadiana and BAnQ closed to us; the only free Canadian primary text found is the Marine reports on IA
   (1901-1925, no keeper-by-keeper lists checked); no Canadian roster source like the USLHS one; no general history.
7. Putnam 1917 and Weiss 1926 scans not located.

**Risks.**
- **archive.org was unreachable from this machine for the last part of the survey** (every request timed out). The IA
  corpus build must retry with back-off and verify counts. Any identifier here that the survey could not open is marked.
- The **loc.gov API** is slow (2.8-75 s), sometimes 503, and limited to 20 requests a minute with a 1-hour block; a
  newspaper step needs a queue, caching of every response, and 5 s spacing.
- **OCR damage:** Google-scanned volumes mangle proper nouns; the Official Register's tables lose row alignment; the Bulletin
  PDFs have column noise. Every quote must be verified against the page image or the in-item search snippet (the existing
  `check_quotes.py` approach).
- **Name collisions** (Split Rock NY vs MN; many "Point Reyes"-style repeats; "Wood Island" etc.): searches need station plus
  state plus years.
- **Facts-only licence** on USLHS, LighthouseFriends, NewEnglandLighthouses and Terry Pepper: names and years only, linked.
- **Dead NOAA links** documented in 8.1; do not code against `wrecks.nauticalcharts.noaa.gov`.
- **Cloudflare/Akamai walls:** HathiTrust, loc.gov HTML, Washington and Illinois newspapers, Maritime History of the Great Lakes,
  USCG Historian: none bypassed.

---

## 13. Recommended research method for the story guide

**What to pre-build (once, cheap):**
1. **Keeper roster cache:** crawl the USLHS place index (~80 pages) for all slugs, then one `places/<slug>` page and one
   `showPeople/<nid>` JSON per place (2,299 x 2 requests, about 2.6 hours at 2 s) into `data/raw/uslhs/`. Parse "Name (start-end)"
   lines by role. It feeds the roster table, the station `keepers_count`, and `data/people/` (never join people by name alone).
2. **Local text corpus** `data/raw/corpus/<series>/<year>/` with a `corpus_index.json` (series, fiscal year, IA identifier,
   source URL, pages, sha256):
   - Life-Saving Service (37 IA volumes, ~50 MB), Light-House Board (7 volumes now, more when sourced), Commissioner
     (1 now), Canadian Marine reports (1901-1925; measure sizes first), Lighthouse Service Bulletin (27 PDFs, run `pdftotext`
     **in plain mode** with form feeds so each page maps to a number).
   - Total transfer about 380 MB (of which ~280 MB is the Bulletin PDFs); text on disk about 70-200 MB depending on the Canadian set.
     About 150-200 requests: roughly 10 minutes of politeness delay plus transfer. Well under the 500 MB cap.
   - Skip the Official Register as a text corpus (tables are unreadable); fetch pages on demand.
3. A small `research/corpus.py grep <station aliases> --series ... --years ...` that applies a **fuzzy station pattern**
   (OCR variants, "Point R[eoa]y[eo]s?", plus state to separate the Split Rocks), normalises whitespace (the Commissioner text has double spaces), and
   prints `series | year | snippet` only. For each hit it should say that **the page number is not in the text file** and give
   the IA in-item search call (section 1) to fetch it. For the Bulletin PDFs the page number is the form-feed count.

**Order of use for a typical station:**
1. **Identity and roster:** USLHS `showPeople` (1 request); compare with LighthouseFriends, NewEnglandLighthouses, Pepper/MNHS where they cover it; record every disagreement as a `conflict`.
2. **Chronology skeleton:** NRHP nomination (cache PDF; `fetch_text.py --grep`), HABS data pages (`loc.gov/item/<id>`), the
   station's Wikipedia page for names only (articles only).
3. **Official reports, by local grep:** Board reports and Commissioner reports (works, repairs, rebuilds, lens changes, fog signal, hours), the
   Bulletin 1912-39 (storms, awards, personnel), Life-Saving Service reports (wrecks and rescues near the light, named rescuers), Canadian Marine reports for Canada.
   Confirm each hit's page through the in-item search endpoint, and quote with the verified snippet.
4. **Newspapers (Chronicling America):** up to about ten queries per well-documented station: station name + keeper name; then date windows around events
   found in step 3. Read the ALTO page text for the hits that matter. At 5 s spacing and 30 s response times, budget 5-8 minutes per station.
5. **Keeper detail on demand:** USLHS register-page image for a name and years; Official Register page image for birthplace and salary;
   NARA M1373 roll and volume as the printed cite.
6. **Atmosphere:** transcribed logs (Port Sanilac, South Haven) only where they exist; HURDAT2 to check that a named storm fits a date a source already gives.
7. **General period context:** Johnson 1890, Kimball 1912, Instructions to Light-Keepers (and Putnam/Weiss once a scan is located), always framed as general.

**What cannot be pre-built or fetched by machine:** HathiTrust volumes, the USCG Historian's PDFs, NARA catalog, Canadiana, BAnQ,
CDNC/NYS/Michigan newspapers. The orchestrator or the owner can hand-download specific volumes into the corpus (a
`data/raw/corpus/manual/` folder keyed by the same index) if a station depends on them.

**Rough costs per station (my estimates, to be checked on the pilot):** roster read 1-3k tokens; corpus grep output
capped at about 10-15k tokens; NRHP and HABS grep 5-15k; newspapers 10-25k (ALTO text is large, grep it); a thin station
10-20k tokens in all, a well-documented one 50-90k. Wall-clock is dominated by loc.gov (minutes), not by the corpus (seconds).

**Open items for a follow-up agent, once archive.org answers again (30 minutes):** (a) fetch and count the 20 + 17 LSS volumes and
check the wrecks-table layout; (b) enumerate Official Register years after 1887 and Commissioner/LHB items under other
titles (try `creator:"United States. Light-House Board"` and Serial Set volumes); (c) confirm `_hocr_searchtext.txt.gz` carries
page breaks (it would give page numbers for plain-text grep without the in-item API); (d) find scans of Putnam 1917 and
Weiss 1926; (e) size the Canadian Marine reports and test one for keeper salary lists; (f) repeat the Portland Head
Chronicling America query; (g) try NRHP, HABS and ENC wrecks for Split Rock and Point Reyes.

---

### Follow-up 2026-10-21 (corpus agent: `research/roster.py`, `corpus.py`, `newspapers.py`)

What was built, and what building it found. Shared layer `research/polite.py` (one lock per site, robots.txt, back-off);
caches under `data/raw/{uslhs,corpus,newspapers}/` (git-ignored). Corpus root `data/raw/corpus/`: 114 volumes, about 90 MB of text
(`corpus.py status` lists them).

**archive.org.** Probes at 11:41 and 12:12 failed (robots.txt and search timed out at 25 s; `web.archive.org` answered); the 12:42 probe
succeeded. Then 37 LSS volumes came down in 3.5 minutes at one request per 2 s (each file takes two requests, the `download/` URL
redirects to a `dn` host), with no errors.

**Open items (a)-(g) answered**

- **(a) LSS.** The 37 volumes are in. Years read from the text: FY1876, 1877, 1878, 1879, 1880, 1881, **1882** (item `annualreportope02servgoog`,
  labelled 1883), 1884 (three copies), 1888, 1889 (two copies), 1891-1899 (two copies each of 1895, 1896, 1898), 1900, 1901, 1902 (two copies
  plus `united-states-life-saving-service-0001`, a 0.2 MB duplicate labelled 1903), 1903-1909. **Still missing from IA: 1883, 1885, 1886, 1887, 1890 and 1910-1914.**
  Layout checked: the station table ("Quoddy Head ... Manned from Aug. 21, 1894, to May 31, 1895; 6 surfmen"), the table of casualties
  (date, vessel, place, "Nature of casualty and service rendered") and the narratives of the year's rescues all print as separate column blocks, so a
  vessel's date, place and outcome do not sit on one line: read around a hit. Station names appear as "Point Reyes, coast of California".
- **(b) Other Board and Commissioner items.** `creator:"United States. Light-House Board"` (34 items), the Board's title and the Commissioner's title
  return nothing new: **the Board run on IA is still the seven compilations, and the Commissioner run is the one volume** (which holds eight reports, below).
  Full-text searches for the Board's report inside Serial Set volumes found only `unitedstatescon243offigoog` and the Secretary of the Treasury's
  reports for 1873-75 (`SecTreasAnnReport187x`), which summarise the Board. The 1852-90 and 1902-10 Board reports and the 1911-14 and 1923-39
  Commissioner reports remain HathiTrust / USCG Historian only. **Official Register:** 236 items under the `sim_united-states-official-register...` prefix,
  every two years 1816-1905 (one or two volumes each), then 1913, 1921, 1932, 1945, 1951, 1955, plus 140 undated identifiers; not downloaded.
- **(c) `_hocr_searchtext.txt.gz` page breaks.** The search text has **no form feeds**, but each item that has it also has
  `<id>_hocr_pageindex.json.gz`, a list with one `[start, end, ...]` entry per scan page giving the page's character range in the search text, which is
  exactly a page map (399 entries for a 399-leaf book). 66 of the 81 archive.org volumes have the pair; the 15 without are Google scans of
  the 1860s-90s: five Board volumes (`annualreportlig00boargoog`, `...02statgoog`, `...04statgoog`, `...00statgoog`, `...01boargoog`), six LSS volumes (the `annualreportope0[06-9]servgoog` and `...06servgoog` scans and `united-states-life-saving-service-0001`) and four general histories; for these `corpus.py page` falls back to the in-item search API. `corpus.py` downloads the pair (about 0.1-1 MB
  each, 31 MB for the lot) and maps a hit to its scan page by matching the words around it in the search text. The `_scandata.xml` file often carries a
  `pageNumber` for each leaf, but in the Google scans it can be a page out (leaf 52 of `annualreportlig03statgoog` reads 40 while the page's own head says 41),
  so the tool reports a printed page as certain only when scan data and the page's OCR head agree. The in-item search API (`inside.php`) works as in
  section 1 only with the phrase in double quotes: unquoted, it matches any of the words (79 hits for "Portland Head" in a volume with 2).
- **(d) Putnam 1917 and Weiss 1926 are on IA.** Putnam: `lighthousesandl00putngoog` (Google scan, `_djvu.txt` 395 KB) and `lighthouseslight00putn`; Weiss:
  `lighthouseservic0000geor` ("the lighthouse service it's history activities and organization", 1926; not access-restricted; `_djvu.txt` 392 KB). The 1974
  reprint `lighthouseservic0000weis` is access-restricted. Putnam, Weiss and the other works of section 7 are corpus series `general` (11 volumes, 3.6 MB).
- **(e) Canadian Marine reports.** The usable items are the Sessional Paper 21 volumes `<year>v<vol>i<issue>p21_<seq>` ("Report of the Department of Marine and
  Fisheries (Marine)"; the Fisheries branch is p22, "List of Shipping" p21b/p22, and the steamboat-inspection supplements p23): **25 reports, fiscal 1900 to 1923-24**
  (June 30 year-end to 1906, March 31 from 1907), 0.3-1.3 MB of text each, **17.8 MB in all, not the 100-150 MB estimated**. 111 items match "Marine and
  Fisheries" 1900-26; the Canadian run before 1900 and the report for 1924-25 were not found (the creator search lists a 1867 `Annual report`, 528 MB, and two
  `Supplement to the annual report` items, not downloaded). Keeper lists: yes. The Marine report prints tables of lightkeepers with name, station, date of appointment and salary
  ("Name. Station. Appointed. Salary."), but the OCR prints each column as its own block, so names and stations must be paired by position. A grep finds, for example, the Inner Sambro Island pole light (lit 3 January 1900) in the report for fiscal 1900.
- **(f)** Portland Head on Chronicling America works (31 pages for the keeper query, 1880-1910, papers printed in Maine); the survey's failure was the HTTP/2 error.
- **(g) NRHP, HABS, ENC for Split Rock and Point Reyes.** NRHP `69000073` is Split Rock (digitised, 19.7k characters). **NRHP `91001100`, the number
  the station record `us-ca-point-reyes` carries, is the Point Reyes Lifeboat Station, not the lighthouse.** HABS: Point Reyes Lighthouse is `ca1357`; Split Rock has no
  HABS record (a search returned a Blue Ridge Parkway item). ENC Direct's `enc_harbour/MapServer/36` answered "Could not find service" (HTTP 500 body) at 12:07, so
  section 8.2's endpoint needs a re-test before the wrecks layer relies on it.

**Other findings**

- **The Commissioner volume `bub_gb_B2dYAAAAYAAJ` (IA label 1911) is eight annual reports, fiscal 1915 to 1922** (title pages at text offsets 185, 347,187, 672,197, 1,020,156,
  1,301,261, 1,643,793, 2,034,020 and 2,361,172 of 2.66 MB normalised). Section 2.2's "one volume, fiscal 1915" becomes 8 of about 29 Commissioner years. The year check on the text is what showed it.
- **Year labels of the seven Lighthouse Board volumes were off** (the survey read 60 KB of front matter). From the whole text: `annualreportlig03statgoog` FY1891 and 1892,
  `...01statgoog` 1893 and 1894 (not 1892-93), `...00boargoog` **1895** (not 1896; so the "1,013 hours and 14 tons" Portland Head figure is FY1895), `...02statgoog` 1896 and 1897,
  `...04statgoog` 1899, `...00statgoog` 1900, `...01boargoog` 1901. The run on IA is FY1891-97 and 1899-1901 (1898 is missing). Forward references ("estimates for the year ending
  June 30, 1892") can add a year, so chosen years err on the inclusive side; `corpus.py` stores the label, the counts and the chosen years for every volume.
- **Lighthouse Service Bulletin: all 28 years exist, and there are five index volumes.** The listing page is `https://uslhs.org/resources/bulletins`. 1925 is
  `Lighthouse%20Service%20Bulletins%201925.pdf`; 1913 and 1936 are listed as `..._1913_0.pdf` and `..._1936_0.pdf` (1913 is byte-identical to the plain name; the 1936 file differs, 7.64 MB
  against 7.50 MB, and the listed one is used); the indexes are `Index to volume 1.pdf` (1912-17), `1918_1923_Index.pdf`, `1924_1929_Index.pdf`, `1930_1935_Index.pdf`, `1936_1939_Index.pdf`: station by
  station ("Point Reyes light station, report of severe storm 166"), the cheapest way to find which Bulletin page mentions a station. 33 files, 319 MB of PDF, 5.9 MB of text; a yearly PDF is 25-57 pages.
- **Chronicling America.** The state filter that works is `fa=location_state:<lowercase state name>` ("papers printed in", not "places mentioned"). `at=results,pagination` keeps replies small; a
  search takes 5-40 s. Under load the API once answered `of: 0` for a query that has 188 hits, so empty replies are not cached. The ALTO text comes from
  `tile.loc.gov/storage-services/service/ndnp/...xml`, derived from the hit's IIIF `image_url`; a page URL not seen in a search resolves with one `?fo=json&at=page,resources` request.
  Tested: Point Reyes (CA, 1890-1900, `lighthouse`) 188 pages; Portland Head + keeper (ME, 1880-1910) 31; Split Rock 1910-12 (no state) 3 pages (Calumet News, 22 Sep 1910, p. 3, the tug *Redwing*).
- **USLHS.** The roster list carries only name, years and the role heading. Salary, source ("Register", "RG 26 Entry 18 - Letters Sent Regarding the Light-House Service") and birth and death years are
  on the person page (one request each: `roster.py --detail N`; `crawl-people` for all, about a day at 2 s). Coordinates are degrees and minutes with no hemisphere, and some are
  wrong: Split Rock is 23 km from the real light (47°20'N 91°36'W against 47.200, -91.367), Boston Light reads 40° for 42°, Buck Island (VI) has 64° 88.70', and "Baker's Island" (MA) carries Maine's Baker Island position.
  The tool flags minutes of 60 or more and matches by name first.
