# Review of the Canadian entries in the merge report, 2026-10-21

Branch `agent/sources-ca`. The first build (1,779 stations, 652 of them Canadian) was merged again with
the six Canadian sources (DESIGN.md 2.3). This file records what the merge report listed, what each item
turned out to be, and what was decided. Every decision that changes the data is an entry with a reason in
`data/curation_ca.json` (`rekind`, `join`, `apart`, `detach`, `hide`, `rename`, `merge_stations`); this file
holds the evidence. Where a source disagrees with another, the page keeps both (`conflicts`).

After the merge (local run on the committed stations): **1,193 Canadian stations shown** (652 before; 628
new, of which 617 were started by Lighthouse Friends, nine by the Coast Guard list and two by the lightship
source) and 74 hidden (7 of them were hidden before this review began). 16 Canadian ids are retired with
`merged_into` (15 by curation, 1 by range pairing); no file is deleted. By province: BC 75, MB 18, NB 137,
NL 149, NS 256, NU 10, ON 237, PE 59, QC 252, and none in AB, NT, SK or YT. By status: 697 active, 133
inactive, 301 lost, 16 replica, 1 ruins, 45 unknown. By kind: 917 lighthouse, 258 range lights, 14 pier
light, 3 harbor light, 2 lightship station, 2 life-saving station. 707 are "facts agree"; 486 are still
Unverified.

## 1. Duplicates (`possible_duplicates`, 17 Canadian pairs after the first merge)

A pair is within 150 m with the same kind group. **Merged** means `merge_stations` (both ids existed; the
second id stays on disk with `merged_into`) or `join` (one id was new this run, so no id is retired).

| Pair | Evidence | Decision |
|---|---|---|
| Richibucto Head / Cap-Lumière (6 m) | Lighthouse Friends' page is "Richibucto Head (Cap Lumière)"; the Coast Guard lists Richibucto Cape at the same point | merged into `ca-nb-richibucto-head` |
| Brigus / North Head (2 m) | the two Wikidata items have the same coordinates; the Brigus light stands on North Head | merged into `ca-nl-brigus` |
| Lennard Island, two stations (4 m) | OpenStreetMap's "Light Station" elements beside the station Wikidata and the staffed list hold (Wikidata's own point is 1.1 km out) | merged into `ca-bc-lennard-island` |
| Cape Tormentine range, two stations (146 m) | one range listed twice: a Wikidata whole-range item with OpenStreetMap's nodes, and Wikidata's front and rear items | merged into `ca-nb-cape-tormentine-range` |
| Wrights Range / Wright's Front Range (4 m) | the whole-range item and the front light with all its other sources | merged into `ca-pe-wrights-range` |
| Warren Landing Lower Range, front / rear / range (34 m, 778 m) | the Upper and Lower ranges share a base name, so the pairing code refused to pair any of them | the three Lower stations merged into `ca-mb-warren-landing-lower-range`; the Upper rear into `ca-mb-warren-landing-upper-range-front` |
| Pointe-Sud / Bagot Bluff (34 m) | Lighthouse Friends: "Escarpement Bagot (South Point)" | merged into `ca-qc-bagot-bluff` |
| La Block / Pointe de la Prairie (37 m) | a second Wikidata item at the same cape; no source distinguishes a second light | merged into `ca-qc-la-pointe-de-la-prairie` (kept as a structure) |
| Quirpon / Cape Bauld (20 m) | OpenStreetMap's "Quirpon Lighthouse" way is the keeper's house of the Cape Bauld light, which runs as the Quirpon Lighthouse Inn | merged into `ca-nl-cape-bauld` |
| Medway Head / Medway Head (1927) (72 m) | two Lighthouse Friends pages for two towers of one station | `join` |
| Wood Islands Range, two stations (53 m) | Lighthouse Friends' front and rear are 3 m and 5 m from Wikidata's front and rear | `join` (front and rear) |
| Pointe du Chêne Range front (as "North Channel") / rear (148 m) | one range; the front sits in an OpenStreetMap station called North Channel, so base names differed | `join` |
| Horse Chops, lost / mapped (42 m) | Lighthouse Friends' lost light and OpenStreetMap's element, same name | `join` (the Coast Guard's "Flat Rock Fog Signal Station", 65 m on, is a separate place and stays a separate station) |
| Red River Range / Black Bear Island (40 m) | separate pages in every source | `apart` |
| Bustard Rocks / Bustard Rocks Range (89 m) | separate Lighthouse Friends pages (lighthouse and range) | `apart` |
| Point Clark / Imperial Towers (64 m) | "Imperial Towers" is a group designation of lighthouses built to one design; Wikidata's item sits on Point Clark | Point Clark kept; the group item hidden |
| Mimico / Toronto East Entrance Outer (2 m) | the Coast Guard's name for Mimico's light | joined automatically once low name scores no longer keep records 2 m apart separate (below) |
| Michipicoten Harbour / Perkwakwia Point (1 m), Pointe aux Anglais / CVL (3 m) | the same: one light under two names | joined automatically |

**Same name, kilometres apart.** Wikidata's coordinates for some lights are far out (offshore ones
especially), so the first build had a Wikidata-only station beside the richer station of the same light.
Merged by `merge_stations`: Cape St. James (18.8 km, 52.100 N against the 51.936 N that OpenStreetMap,
Lighthouse Friends and Coast Guard P770 agree on), Sisters Islets (10.3 km), Sambro Harbour (4.9 km),
Pointe Carleton (1.6 km). Joined by `join` (the other id was new): Flint Island (3.4 km), Cap-de-la-Table
(1.1 km), Little Denier Island (1.2 km), Belle Isle South End Lower (1.2 km: the heritage designation puts
it 1.2 km from where the Coast Guard does; the conflict stays on the page), Heath Point (70 m, successive
towers), St. Shotts (297 m, with the Coast Guard's St. Shotts Fog Signal Station).

**Flowers Cove / Harbour Point.** Wikidata's item "Flower's Cove Lighthouse" carries Flowers Cove's
numbers (ARLHS CAN657, Coast Guard N213, the numbers the Lighthouse Directory gives Flowers Cove) but the
coordinates of Harbour Point, 340 km away. The first build filed it under Harbour Point's station. `detach`
takes it out (by station id, so it stays out), `join` sends it to Lighthouse Friends' Flowers Cove, and
the Harbour Point station (`ca-nl-flowers-cove`, whose id cannot change) is renamed Harbour Point
Lighthouse; Flowers Cove is `ca-nl-flowers-cove-2`.

**Left apart for a human with a chart** (not merged because the sources disagree about which is which):
the four Sydney Range stations (OpenStreetMap labels the front and rear nodes the other way round; the
Coast Guard gives A782 and A783 positions 1 to 3 km from either), Malpeque Outer Range (OpenStreetMap
calls the node at Darnley Point the front, Lighthouse Friends calls the same spot the rear), Leards Range,
two stations 878 m apart, Pictou Island South, two stations 1.3 km apart, and Lyal Point, two
OpenStreetMap lights 2.3 km apart (`apart`).

## 2. Names and nameless records

- `ca-on-w2` (OpenStreetMap, name "w2", built 1903, 11 m, a major light): Lighthouse Friends and the
  Directory name the light 17 m away Slate Islands. Renamed.
- `ca-on-nsc` ("NSC"): the Coast Guard lists the light as Stillwater Park (Graham Bay), I1297. Renamed. It
  is a small modern aid and stays as a harbor light.
- `ca-qc-cvl` ("CVL", the operator tag of a CanVec import, 3 m from Lighthouse Friends' Pointe aux Anglais):
  renamed Pointe aux Anglais.
- `ca-nb-q135261059`: a Wikidata item with no label, so its name was its Q number. The merge now treats an
  unlabelled item as nameless; the station takes Lighthouse Friends' name (Anderson Hollow). The id stays.
- 118 Canadian OpenStreetMap lights have no name in any source (of 265 in all) and are not shown. One of
  them, at 52.3116 N 114.1021 W, is the Sylvan Lake lighthouse (Alberta, section 3).

## 3. Alberta: `ca-ab-clearwater-park`, `ca-ab-lighthouse-landing`

Both are OpenStreetMap-only, inland, with no light, register or other source. The Directory's Alberta page
and the Department of Fisheries and Oceans say Alberta has no official lights and name only the lake
lights: Sylvan Lake (the 1988 tower was demolished in 2012; a 2016 replacement stands), Lake Newell (6 m
tower at the resort, south of Brooks) and Pratt's Landing (a 2013 solar light on the Peace River). Neither
OpenStreetMap name is among them.

- **Lighthouse Landing** (51.161 N 114.057 W) is a condominium community in Country Hills Village, northwest
  Calgary (real-estate listings call it that). Not an aid to navigation: **hidden**.
- **Clearwater Park Lighthouse** (51.049 N 113.797 W, `operator=Private`, `height=27`, no light tags) near
  Chestermere: no list, register or web source found. Not misplaced (the point is inland on a lake
  community) and not a lake light the lists know: **hidden** with the reason that it can be unhidden if a
  source shows a lake light there.

The three real lake lights are in the Directory without positions (unplaced, section 6).

## 4. Minor beacons that slipped in, and records that are not lights

- The Coast Guard list has 4,482 lit fixed aids; only 60 clear lighthouses, 7 corroborated by the Directory
  (a lantern, no Lighthouse Friends page) and 844 within 150 m of a station in the other extracts are in the
  extract (911 records), and **a small aid never starts a station**. Five stations were started by the list: Newcastle
  Creek (NB), Flat Rock (NL, a fog signal station), Nameless Point Light (NL), Anse-à-Valleau and Pointe à
  Bigot (QC). They have a Coast Guard number and a Directory entry that names a lantern or gallery; they
  can be hidden if the owner reads them as beacons.
- Lighthouse Friends started 617 visible stations, 175 of them with no other source: 172 lost, and three not
  lost (Grande Anse NB, Reed's Point NB, Malpeque Harbour Approach Range Rear PE).
- Of the 761 Canadian OpenStreetMap elements that OSM itself marks "could be a beacon with a light" (the
  CanVec import), 208 join a station as another record of the same light (by place and name, or by an
  Admiralty number the Directory or the Coast Guard also gives) and 553 stay unshown.
- Hidden for being no light (5): the two Alberta items; `ca-bc-bickford-tower-dy118` (a navy dockyard
  signal tower at Esquimalt, DY118 being a dockyard building number); `ca-bc-lightship-relief-lv-76-wal-504`
  (the US lightship Relief, WAL-504, 1904-1960, ended as a derelict on the Fraser River: a vessel for the US
  vessel records); `ca-on-imperial-towers` (a group). The two decorative faux lighthouses of the first build
  (`ca-nb-grande-anse`, `ca-qc-maison-en-forme-de-phare-grande-riviere`) stay hidden.
- **Hidden as modern minor aids (67 harbor lights).** Every Canadian station of kind `harbor_light` (OpenStreetMap's
  own "light_minor" class, plus the Coast Guard list's tower or beacon entry for 61 of them) was
  known to OpenStreetMap or the Coast Guard only: not one has a Wikidata item, a heritage designation, a
  Lighthouse Friends page or a Directory entry. DESIGN 1 leaves out "modern automated beacons with no keeper
  history", and a light that no history source mentions has none to tell. The 67 are `hide` entries (by
  their OpenStreetMap key, with the station id and name beside it) with one reason; 66 of the 67 are in
  British Columbia, where OpenStreetMap carries the Coast Guard's small towers as lighthouses (BC drops from 141
  to 75 stations). An entry goes the day a source gives its light a history.
  The 14 pier lights stay: each has a Lighthouse Friends or Directory page.

## 5. Changes to the matcher found in the review

- A name that scores 0.2 or less was treated as an opposite (North / South) and never joined, but any name
  with nothing in common scores low: the Coast Guard's "Toronto East Entrance Outer" and Mimico's
  lighthouse, 2 m apart, stayed apart. For a Canadian record only real opposites keep two lights apart.
- "Shott's" became "Shott South": a possessive `'s` is now not the abbreviation of South. This and the
  next fix are global and changed five US stations in a local merge (`us-ny-charlotte-genesee`,
  `us-ma-cape-ann`, `us-hi-daniel-k-inouye-kilauea-point`, `us-nj-finns-point-range`, and
  `us-nj-finns-point-rear-range`, which is retired into the range); the orchestrator should look at them.
- A second record of one source in a station needed a strong name even when it was the rear light of the
  range whose front it had already supplied (Saugeen River). Front and rear are two structures by
  definition, so the rule no longer applies between them.
- An identifier join between two records of the same pass depended on the order they arrived in, so a second
  run (with memory) differed from the first. Records that join nothing now get one more try after both
  passes and after curation. A second run changes no file and not the report.

## 6. Not placed: leads for the next pass

- **Lighthouse Directory entries with no position, 241.** 122 give a Coast Guard number that is not in the
  2026 list (removed or renumbered aids, mostly Quebec ranges), 88 give one that is (small aids we dropped:
  poles, masts, skeletal towers), 7 more have neither. They are the Directory's own and carry the years;
  they join a station the day another source places it. `rowlett_not_joined` in the report lists them.
- **Alberta, Saskatchewan and the territories.** The three Alberta lake lights and Saskatchewan's Cochin
  light (1989) are in the Directory without positions; OpenStreetMap has Sylvan Lake nameless. The
  territories have only Nunavut's ten, all from OpenStreetMap, eight of them with Coast Guard Arctic entries.
- **Lightships and life-saving** (`ca_lightships_lifesaving`, 21 records): positions for Lower Traverse
  (Lighthouse Friends), Lurcher Shoal (the Coast Guard buoy that took its place; marked approximate) and
  the Sable Island Humane Establishment (the island's coordinates; approximate). Unplaced: Red Island Reef,
  Manicouagan Shoal and 14 lifeboat stations (Cobourg 1882, Toronto 1883, Wellington 1883, Point Traverse
  1883, Port Rowan 1883, Port Stanley 1885, Collingwood 1885, Goderich 1886, Port Hope 1889; the 1885
  lifeboats allotted to Devil's Island, Duncan's Cove, Yarmouth and Scatarie in Nova Scotia and Pelee Island
  in Ontario). There is **no Sambro lightship** (Sambro is a lighthouse of 1758). Leads not in the file:
  Sandheads (BC), Anticosti East Point, Île aux Coudres, Sandy Beach (Gaspé Bay), Upper Saint-Roch Traverse,
  Lake St. Louis (three vessels), Lake St. Peter (three), Lachine, Chateauguay, Miramichi Bay, Zephyr Rock,
  Barrington.
- **Range lights.** 64 Canadian ranges are paired; 122 halves (and one ambiguous group, Soulanges Canal) are
  not, mostly because the two halves have different base names in two sources or one source lists the
  range once. Four have halves 7.8 to 52 km apart, which is a wrong position in one source (Lighthouse
  Friends: Grant Beach, Stokes Bay; the Coast Guard: Wallace Harbour, Miminegash). Research agents should
  correct the position by hand.
- **Identifiers that point at two stations (15) or too far away (6)** are printed by every merge run
  (`identifier_ambiguous`, `identifier_far`), not saved.

## 7. Staffed lightstations (`ca_staffed_lightstations`)

There is no official current list. The names are those of the Coast Guard's April 2010 data as the Senate
committee printed them in October 2011: BC 27, NL 23, and Machias Seal Island (NB, kept for sovereignty
reasons). The newer sources:

- 31 July 2024, Coast Guard news release: keeper functions end at **Carmanah Point** and **Pachena Point**
  (unstable ground); "the twenty-five other staffed light stations on the British Columbia coast" continue.
  A Question Period note of 17 December 2024 says the keepers were relocated. Both are now `automated`,
  2024, with the safety note on their access. (Newer source wins over the 2010 list.)
- January 2025 (US Lighthouse Society): 49 staffed lighthouses in Canada, which is 51 minus the two.
- Per station: Cape Beale (a keeper there, January 2025), Triple Island (principal and assistant keepers,
  CTV, May 2025), Estevan Point (federal impact-assessment page of 2022-23: "staffed by two lightkeepers
  24/7"), Long Point at Twillingate (a 2023 interview), Machias Seal Island (two resident keepers, summer 2024).
- The Fisheries and Oceans Canada page names the same 23 in Newfoundland and Labrador (a 2005 brochure on a
  page modified in 2019). Most NL keepers commute and live in the neighbouring communities; only five
  stations are remote (Puffin Island, both Green Islands, Pass Island, Cape Race).

49 stations are staffed in the data, 2 destaffed. **44 rest only on the April 2010 list** (`staffing.check`;
for BC the 2024 count of 25 supports the set but names none), so a research agent must confirm each before a
page says "staffed" in the present tense:

`ca-bc-addenbroke-island ca-bc-boat-bluff ca-bc-bonilla-island ca-bc-cape-mudge ca-bc-cape-scott
ca-bc-chatham-point ca-bc-chrome-island ca-bc-dryad-point ca-bc-egg-island ca-bc-entrance-island
ca-bc-green-island ca-bc-ivory-island ca-bc-langara ca-bc-lennard-island ca-bc-mcinnes-island
ca-bc-merry-island ca-bc-nootka ca-bc-pine-island ca-bc-pulteney-point ca-bc-quatsino ca-bc-scarlett-point
ca-bc-trial-islands ca-nl-allans-island ca-nl-bell-island ca-nl-cape-anguille ca-nl-cape-bonavista
ca-nl-cape-norman ca-nl-cape-race ca-nl-cape-ray ca-nl-cape-st-marys ca-nl-fort-amherst ca-nl-fort-point
ca-nl-fortune-head ca-nl-fox-point ca-nl-green-island ca-nl-green-island-2 ca-nl-new-ferrolle-peninsula
ca-nl-northwest-head-ramea ca-nl-pass-island ca-nl-powles-head ca-nl-puffin-island ca-nl-saddle-island-red-bay
ca-nl-st-shotts ca-nl-tides-cove-point`

Each carries `access.level` `restricted` and the note "Staffed lightstation: the keepers' home and
workplace. Visit only where the station welcomes visitors, and never land uninvited." No source supports
`closed` for any of them (Cape Race, Cape Anguille, Long Point and Fort Amherst welcome visitors).

## 8. Access fields from the new sources

`access.level` was unknown for every Canadian station in the first build. Now: 139 closed, 53 private, 73
public, 51 restricted, 877 unknown. `private` is Lighthouse Friends' private flag; `closed` is the
Directory's "site closed" with no flag or wording that says anything is open; `public` only where the
Directory says site **and** tower are open or Lighthouse Friends says it is open for climbing. A "Site open,
tower closed" alone sets `visit.grounds_open` true and leaves the level unknown, because a wrong "open to
the public" is the harmful mistake. `visit.boat_only` comes from either source's boat wording (371
stations).

## 9. Questions for the owner

1. The 67 hidden harbor lights (section 4): confirm that a light no history source mentions stays out, or
   say which kind of small light you want (for example every Coast Guard list entry with a lantern).
2. The five Coast Guard–started stations (section 4): hide as beacons, or keep?
3. Hand-corrected positions for the ranges with halves 8 to 52 km apart, and the Sydney and Malpeque ranges:
   a research task, or leave them flagged?
4. The unplaced Directory entries: ask Russ Rowlett for coordinates (the drafted note in `docs/outreach/` is
   for the owner to send), or place them from the Coast Guard's own positions once question 1 is answered?

## Orchestrator's answers (2026-10-21)

1. **The 67 hidden harbor lights stay hidden**: DESIGN §1 leaves out modern automated beacons with no keeper
   history, and no history source mentions these. Any one comes back the day a source gives it a history.
2. **The five Coast Guard–started stations stay shown**: the Lighthouse Directory describes each one's lantern
   or gallery, so they are lights with a structure, not bare beacons.
3. **Ranges with halves far apart, Sydney and Malpeque**: left flagged; the story research for those stations
   checks the positions and files `corrections`.
4. **Unplaced Directory entries**: stay unplaced for now. The drafted note to Russ Rowlett was lost when the
   agent's worktree was removed (`docs/outreach/` is git-ignored); it will be re-drafted with the other outreach
   notes for the owner to send.

## 10. Duplicate audit (2026-10-27)

Story batches write a long history for each station, so a light split across two stations gets two histories.
This pass looked for such splits: a name scan (same province, names equal once the kind words are dropped and
Saint is folded to St.), a looser scan (also dropping Old / New, within 15 km), the report's 3 Canadian possible
duplicates and 28 close namesakes, and a check of every display name for words that are not a light's name. The
US side of the same audit is in `docs/sources/review_2026-10-us.md` ("Duplicate audit").

Rulings applied (DESIGN 3.2):

- **A range is one station**, also when its halves are kilometres apart because one tower was moved to private land
  or a park (Grant Beach, Wallace Harbour, Stokes Bay, Miminegash, L'Ardoise, Summerside, Calvaire). The moved tower
  stays a structure with its own position. This does not touch answer 3 above: the positions are not corrected here.
- **A tower moved away from its station is a structure of that station**, not a station of its own (the 1902 Pelee
  Passage tower at Windsor, the old Cape Tryon tower, the Northport back range light, Oakville's old lighthouse).
- **Two Wikidata items for one light** (Cap de Rabast, Bon-Désir, Belle Isle South End Lower) are one station.
- The id kept is the one with a published story, else the one in a story batch now (Leards Range and Belle Isle South
  End Lower keep their `-2` ids for that reason), else the one with more sources.

Every decision is an entry with its reason in `data/curation_ca.json`.

**Merged** (`merge_stations`; the retired id stays on disk with `merged_into`):

| Pair | Evidence | Decision |
|---|---|---|
| ca-nb-grant-beach-range-rear -> ca-nb-grant-beach-range-front (7.8 km) | Grant Beach Range (Miramichi, towers of 1903, inactive since 1972): the front and the rear of one range (DESIGN 3.2). Lighthouse Friends' points are 7.8 km apart because the towers were moved to private land (the front by its owners in 1986). | merged into `ca-nb-grant-beach-range-front` |
| ca-nl-belle-isle-south-end-lower -> ca-nl-belle-isle-south-end-lower-2 (1.4 km) | Two Wikidata-era stations for the one Belle Isle South End Lower light: Wikidata's item carries Heritage Lighthouse 14933, the number of the Parks Canada record in the other station, 1.4 km from the Coast Guard's N234. The kept id is in a story batch. | merged into `ca-nl-belle-isle-south-end-lower-2` |
| ca-ns-pictou-island-south-2 -> ca-ns-pictou-island-south (0 m) | Pictou Island South (the 1907 wharf light, Heritage Lighthouse 14894): Lighthouse Friends 1642, OpenStreetMap's way and Rowlett's entry made a second station 1.3 km from the first, whose pin was Wikidata's point at the island's west end. The storied id keeps the South light; the west-end records are detached to a station of their own. | merged into `ca-ns-pictou-island-south` |
| ca-ns-sydney-range-front -> ca-ns-sydney-range (0 m) | Sydney Range: the front (Lighthouse Friends 1648, OpenStreetMap, Rowlett's 2010 replica of the 1905 tower at Dixon Point) and the rear (Lighthouse Friends 1649, Rowlett's old and 2024 rears) of one range, 770 m apart (DESIGN 3.2). | merged into `ca-ns-sydney-range` |
| ca-ns-sydney-front-range -> ca-ns-sydney-range (1.8 km) | Wikidata's 'Sydney front range light' (a replica, 1.8 km from Lighthouse Friends' front) is the same front light; no source has a second Sydney front range. | merged into `ca-ns-sydney-range` |
| ca-ns-wallace-harbour-range-rear -> ca-ns-wallace-harbour-front-range (13.4 km) | Wallace Harbour Range (1904): the rear tower was sold in 1994 and moved in 1995 to Malagash Point as a summer home (Lighthouse Friends 1005), 13 km from the front; one range, one station (the storied front's id). | merged into `ca-ns-wallace-harbour-front-range` |
| ca-on-pelee-passage-2 -> ca-on-pelee-passage (61.2 km) | Pelee Passage: the 1902 tower, replaced on the passage in 1975 (Rowlett), now stands at Lakeview Park Marina, Windsor (Lighthouse Friends 1040). One station, its old tower relocated. | merged into `ca-on-pelee-passage` |
| ca-on-stokes-bay-range-rear -> ca-on-stokes-bay-range-front (52.5 km) | Stokes Bay Range: the 1904 rear tower was flown out by helicopter in 2009 when a new rear was built (Lighthouse Friends 1595), so the sources place it 52 km from the front; one range. | merged into `ca-on-stokes-bay-range-front` |
| ca-pe-brighton-beach-range-rear -> ca-pe-brighton-beach-range-front (398 m) | Brighton Beach Range: front (storied id) and rear, 400 m apart, with Wikidata's item for the pair (DESIGN 3.2). | merged into `ca-pe-brighton-beach-range-front` |
| ca-pe-leards-range -> ca-pe-leards-range-2 (878 m) | Leards Range: the front (Wikidata 'Leards Range Front Lighthouse', Lighthouse Friends 970, Rowlett's Victoria Harbour, OpenStreetMap's 'Victoria Range Light') and the rear (OpenStreetMap's 'Leards Back Range Light', Lighthouse Friends 971, Rowlett's rear, Wikidata's item for the pair), 880 m apart. The kept id is in a story batch. | merged into `ca-pe-leards-range-2` |
| ca-pe-malpeque-harbour-approach-range-rear -> ca-pe-malpeque-harbour-approach-range (1.0 km) | Malpeque Harbour Approach Range: Lighthouse Friends' rear (937, on Fish Island) is the rear light of the range whose station holds Wikidata's item and the OpenStreetMap rear node, 1 km away; one range. | merged into `ca-pe-malpeque-harbour-approach-range` |
| ca-pe-malpeque-outer-range-2 -> ca-pe-malpeque-outer-range (0 m) | Malpeque Outer Range (Darnley Point, towers of 1922): two stations 590 m apart hold its two lights; OpenStreetMap and Lighthouse Friends label front and rear the other way round, but they are the two halves of one range. | merged into `ca-pe-malpeque-outer-range` |
| ca-pe-miminegash-range-rear -> ca-pe-miminegash-range (18.4 km) | Miminegash Range: the old wooden rear tower was moved to a private cottage near Kildare (Lighthouse Friends 948), 18 km away; one range. | merged into `ca-pe-miminegash-range` |
| ca-pe-former-northport-back-range -> ca-pe-northport-range (307 m) | Northport Range: the 'Former Northport Back Range Light' (1897, moved to private land, Lighthouse Friends 991), Wikidata's item for the range and Lighthouse Friends' and Rowlett's rear are the storied station's range. | merged into `ca-pe-northport-range` |
| ca-pe-summerside-outer-range-rear -> ca-pe-summerside-outer-range-front (430 m) | Summerside Outer Range: front and rear, 430 m apart, with Wikidata's item for the pair (DESIGN 3.2). | merged into `ca-pe-summerside-outer-range-front` |
| ca-qc-calvaire-cap-charles-front-range -> ca-qc-calvaire-cap-charles-range (0 m) | Calvaire (Cap Charles) Range: the 1915 front tower was moved by Deschaillons in the 1980s to a rest area at the village's western entrance (Lighthouse Friends 1478), 3.6 km from the range; one station. | merged into `ca-qc-calvaire-cap-charles-range` |
| ca-qc-soulanges-canal-upper-entrance-range-rear -> ca-qc-soulanges-canal-upper-entrance-range-front (489 m) | Soulanges Canal Upper Entrance Range (1902-1960): front and rear, 490 m apart (DESIGN 3.2). | merged into `ca-qc-soulanges-canal-upper-entrance-range-front` |
| ca-ns-lardoise-harbor-front -> ca-ns-lardoise-range (0 m) | L'Ardoise range (Lower L'Ardoise, 1909, inactive about 1970): Lighthouse Friends' front (private, 4.2 km away) and the station holding Wikidata's item and the rear; one range. | merged into `ca-ns-lardoise-range` |
| ca-ns-pugwash-old -> ca-ns-old-pugwash (1.3 km) | Pugwash (Fishing Point): the 1871 tower (Lighthouse Friends 'Pugwash (Old)', destroyed 2018) and the 1962 tower (Wikidata, Lighthouse Friends 'Pugwash', demolished 2023), 1.3 km apart on the same point under one name; successive towers of one station. | merged into `ca-ns-old-pugwash` |
| ca-pe-murray-harbour-back-range -> ca-pe-murray-harbour-range (1.4 km) | Murray Harbour Range: Wikidata's 'Murray Harbour Back Range Light', the Coast Guard's rear (A965) and Rowlett's rear are the rear the storied station already holds through Lighthouse Friends 956. | merged into `ca-pe-murray-harbour-range` |
| ca-pe-cape-tryon-old -> ca-pe-cape-tryon (3.9 km) | Cape Tryon: the 1905 tower, retired in 1969 when the present tower was built, was moved to private land 3.9 km away (Lighthouse Friends 'Cape Tryon (Old)'); one station, the storied id. | merged into `ca-pe-cape-tryon` |
| ca-qc-cap-de-rabast -> ca-qc-pointe-nord (1.4 km) | Cap de Rabast (Pointe-Nord, Anticosti): Wikidata has two items, 'Cap-de-Rabast Lighthouse' (a rounded point) and 'Phare de Pointe-Nord'; OpenStreetMap, Lighthouse Friends, the Coast Guard (A1515.2) and Rowlett all describe one light. | merged into `ca-qc-pointe-nord` |
| ca-nl-flat-rock -> ca-nl-horse-chops (0 m) | The Coast Guard's 'Flat Rock Fog Signal Station' (N463, Admiralty H522) is 80 m from Horse Chops; OpenStreetMap's Horse Chops element carries H522 and Rowlett gives Horse Chops (fog signal) N463. The fog signal station is a structure of the Horse Chops light station (the first review had left it apart). | merged into `ca-nl-horse-chops` |
| ca-qc-cap-de-bon-desir -> ca-qc-bon-desir (250 m) | Bon-Désir: Wikidata has two items, 'Cap-de-Bon-Désir Lighthouse' (rounded point, 250 m) and 'Phare de Bon-Désir'; Lighthouse Friends, the Coast Guard (A1755) and Rowlett describe one light. | merged into `ca-qc-bon-desir` |
| ca-pe-summerside-range-front -> ca-pe-summerside-back-range (0 m) | Summerside Range: Lighthouse Friends' and Rowlett's front (private, inactive) is the front of the range whose rear is Wikidata's 'Summerside Back Range Light' (Coast Guard A1022); one range. | merged into `ca-pe-summerside-back-range` |
| ca-on-old -> ca-on-oakville (397 m) | Wikidata's 'Old Lighthouse' at Lakeside Park, Oakville, is the 1889 Oakville harbour lighthouse moved off the pier; one station with the present Oakville light. | merged into `ca-on-oakville` |

**Records moved without retiring an id.** Pictou Island: Wikidata's item for the South (wharf) light, Heritage
Lighthouse 14894, has the coordinates of the island's west end, so the first build filed the west-end records
(OpenStreetMap's "Pictou Island West End Lighthouse", Lighthouse Friends' "Pictou Island West", the Coast Guard's A897,
Rowlett's West End) under the South station and its pin sat at the west end; Lighthouse Friends' South (1642) made a
second South station. `detach` takes the four west-end records out of `ca-ns-pictou-island-south` (they make the
new station `ca-ns-pictou-island-west`), `apart` keeps them off Wikidata's item, and `merge_stations` brings the second South
station into the storied id, whose story is about the 1907 wharf light. Algernon Rock: Rowlett's "Roche à Veillon" was
filed under Pilier-de-Pierre by name; `detach` and `join` send it to Lighthouse Friends' Algernon Rock.

**Status.** The merged Sydney Range took `replica` from its 2010 front tower; `pipeline/record_joins.py` sets it
back to `active` (`STATUS_PICKS`: curation has no status entry), with a note that the front is a replica.

**Code.** The OpenStreetMap `wikidata=` tag path of the matcher ignored `detach` and `apart`, so the west-end element,
which carries the South light's Wikidata tag, went back to the South station; it now respects them like every other
path (`merge.py`, test `test_detach_and_apart_hold_against_an_osm_wikidata_tag`).

**Hidden** (`hide`; files kept):

- `ca-nb-barrack-block-h23`: A barracks building at Canadian Forces Base Gagetown (Barrack Block H23 and H21, federal heritage buildings), not a light. Two Wikidata items for barracks buildings at CFB Gagetown, Oromocto, inland; no Canadian light list or lighthouse source lists a light there.
- `ca-nb-junior-ranks-quarters-d23`: A quarters building at Canadian Forces Base Gagetown (Junior Ranks Quarters D23), not a light. A Wikidata item for a federal heritage building at CFB Gagetown, inland; no light source lists it.
- `ca-qc-hirondelles-noires-de-dorval`: A purple-martin nesting house shaped like a lighthouse (Dorval Purple Martin Lighthouse), not an aid to navigation. OpenStreetMap's 'Phare des hirondelles noires de Dorval' (Dorval Purple Martin Lighthouse); no Coast Guard list entry or lighthouse source.
- `ca-on-tower`: OpenStreetMap's 'Tower Light' on the Ottawa River: no light list or lighthouse source has a light here. OpenStreetMap only (man_made=lighthouse, no seamark tags); no Coast Guard list entry, Lighthouse Friends or Rowlett entry within 3 km.

**Renamed** (`rename`; ids unchanged):

| Station | Name shown | Why |
|---|---|---|
| ca-ns-old-pugwash | Pugwash | With the 1871 tower's station merged in, Lighthouse Friends' 'Pugwash (Old)' won the name; the station is the Pugwash light (Lighthouse Friends, Rowlett). |
| ca-ns-sydney-range | Sydney Range Lights | The merged range's name came out as 'Sydney range Lights' (from Wikidata's 'Sydney front range light'). |
| ca-ns-wallace-harbour-front-range | Wallace Harbour Range Lights | The station now holds the range's front (the sector light) and its moved rear; the merged name came out as 'Wallace Harbour range Lights'. |
| ca-pe-northport-range | Northport Range Lights | With the former back range light merged in, Wikidata's 'Former Northport Back Range Light' won the name; the station is the Northport range, as its story says. |
| ca-qc-calvaire-cap-charles-range | Calvaire (Cap Charles) Range | With the moved 1915 front merged in, its Lighthouse Friends name 'Calvaire (Cap Charles) Front Range' won; the station is the range (Lighthouse Friends 1732, the Coast Guard's A2019-A2020). |
| ca-nb-grant-beach-range-front | Grant Beach Range Lights | The station now holds the range's front and rear. |
| ca-on-stokes-bay-range-front | Stokes Bay Range Lights | The station now holds the range's front and rear. |
| ca-pe-summerside-outer-range-front | Summerside Outer Range Lights | The station now holds the range's front and rear; Wikidata's item for the pair is 'Summerside Outer Range Lights'. |
| ca-qc-soulanges-canal-upper-entrance-range-front | Soulanges Canal Upper Entrance Range Lights | The station now holds the range's front and rear. |
| ca-pe-summerside-back-range | Summerside Range Lights | The station now holds the range's front and rear. |
| ca-qc-pointe-nord | Cap-de-Rabast Lighthouse | OpenStreetMap, Lighthouse Friends, the Coast Guard (A1515.2) and Rowlett call the light Cap de Rabast; 'Phare de Pointe-Nord' is a second Wikidata label for the place. |
| ca-bc-sand-heads | Sand Heads Lighthouse | Wikidata's French label 'phare de Sand Heads' won the name; OpenStreetMap calls it Sand Heads Lighthouse, Lighthouse Friends, the Coast Guard and Rowlett Sand Heads. |
| ca-pe-wood-islands-range | Wood Islands Lighthouse | Wikidata's French labels produced 'phare de Wood Islands Range Lights'; the station is the 1876 Wood Islands lighthouse with its two range towers (Wikidata 'Wood Islands Lighthouse', Lighthouse Friends, the Coast Guard), as its story calls it. |
| ca-qc-cap-a-lest | Cap à l'Est | Wikidata's lower-case label 'phare de Cap-à-l'Est' won the name; Lighthouse Friends, the Coast Guard (A1798) and Rowlett call it Cap à l'Est. |
| ca-qc-la-pointe-duthie | Pointe Duthie | Wikidata's lower-case label 'phare de la Pointe Duthie'; Lighthouse Friends and Rowlett call it Pointe Duthie. |
| ca-qc-lile-aux-ufs | Île aux Oeufs | Wikidata's lower-case label; Lighthouse Friends and Rowlett call it Île aux Oeufs (Egg Island). |
| ca-qc-lile-du-grand-caoui | Île du Grand Caouis | Wikidata's lower-case label; Lighthouse Friends and Rowlett call it Île du Grand Caouis. |
| ca-qc-lile-sainte-marie | Île Sainte-Marie | Wikidata's lower-case label; Lighthouse Friends, the Coast Guard (A1562) and Rowlett call it Île Sainte-Marie. |
| ca-qc-vercheres-village-alignement-anterieur-feu-range | Verchères Village Range Lights | OpenStreetMap's Coast Guard text fragment ('Verchères, village – alignement antérieur, feu') won the name; Lighthouse Friends, the Coast Guard (A2319, A2320) and Rowlett call the pair Verchères Village Range. |
| ca-on-dr-robertson-woods | Niagara River Range Front | OpenStreetMap's name for the building ('Dr. Robertson-Woods') won the name; Lighthouse Friends, the Coast Guard (I549) and Rowlett call the light Niagara River Range Front. |
| ca-on-lighthouse-lighthouse-cove | Thames River Lighthouse | Wikidata's label 'Lighthouse/Lighthouse Cove' is the place, not the light; OpenStreetMap calls it Thames River Lighthouse, Lighthouse Friends and Rowlett Thames River Range Rear. |
| ca-on-port-burwell-marine-museum-and-historic | Port Burwell Lighthouse | Wikidata's label names the museum ('Port Burwell Marine Museum and Historic Lighthouse'); its alias, Lighthouse Friends and Rowlett call the light Port Burwell. |
| ca-nl-keppel-island-lighthouse-old | Keppel Island Lighthouse | OpenStreetMap's name for the old building ('Keppel Island Lighthouse (old)') won the station's name; the station is the Keppel Island light station (Coast Guard N208, Lighthouse Friends, Rowlett). |

**Kept apart** (the report's possible duplicates and close namesakes, now each with a `NOT_DUPLICATES` entry in
`pipeline/record_joins.py`, which is what the report reads for both countries; the name scan's other pairs are listed
for the record):

| Pair | Why |
|---|---|
| ca-on-bustard-rocks / ca-on-bustard-rocks-range | Separate Lighthouse Friends pages (the lighthouse and the range), 89 m apart; records already apart in the curation. |
| ca-mb-red-river-range / ca-mb-black-bear-island | Separate pages in every source, 40 m apart; records already apart in the curation. |
| ca-ns-terence-bay / ca-ns-pennant-harbour | Two lights 5.8 km apart (Coast Guard A498 and A501). |
| ca-ns-maugher-beach / ca-ns-mcnabs-island | Maugher Beach lighthouse and the McNabs Island range light (A528), 1.3 km apart. |
| ca-nb-beacon / ca-nb-saint-john-harbour | The 1828 Saint John Harbour Beacon and the Saint John Harbour range front, 2.6 km apart. |
| ca-nb-quaco-head / ca-nb-st-martins | Quaco Head lighthouse and the 1983 St. Martins replica in the village, 4 km apart. |
| ca-ns-cranberry-island / ca-ns-canso-harbour | Cranberry Island lighthouse and the Hart Island range at Canso, 5.3 km apart. |
| ca-ns-pictou-island-south / ca-ns-pictou-island-east-end | The South (wharf) light and the East End light, 7 km apart. |
| ca-ns-pictou-island-west / ca-ns-pictou-island-east-end | The west-end light (a station of its own after this audit) and the East End light, 7 km apart. |
| ca-qc-route-louiseville-downstream / ca-qc-route-louiseville-upstream | Two ranges (downstream and upstream, Coast Guard A2143 and A2144), 1.9 km apart. |
| ca-qc-grondines-upper-range / ca-qc-pointe-des-grondines-range | Two ranges (Upper, A2025-A2026; lower, A2023-A2024), 4.4 km apart. |
| ca-qc-saint-antoine-course-range / ca-qc-saint-antoine-traverse-range | Two ranges sharing one light (Rowlett: 'Traverse Range Front/Course Range Rear'), separate Lighthouse Friends pages. |
| ca-qc-algernon-rock-roche-a-veillon / ca-qc-pilier-de-pierre | Algernon Rock and Pilier-de-Pierre, 580 m apart; Rowlett's Roche à Veillon entry moves to Algernon Rock. |
| ca-nl-baccalieu-island-lighthouse-southwest-point / ca-nl-baccalieu-island-lighthouse-north-point | The two lights at the ends of Baccalieu Island, 4.8 km apart. |
| ca-nl-squarry-island / ca-nl-cape-bonavista | Squarry Island and Cape Bonavista, 6.3 km apart. |
| ca-qc-anse-a-valleau / ca-qc-pointe-a-la-renommee | The 1975 Anse-à-Valleau light and the Pointe-à-la-Renommée lighthouse it replaced, 3.9 km apart: a new site with its own name. |
| ca-mb-winnipeg-beach / ca-mb-winnipeg-beach-breakwater | The 1910 lighthouse (2017 replica) and the 2001 breakwater light, 330 m apart. |
| ca-nl-belle-isle-south-end-upper / ca-nl-belle-isle-south-end-lower-2 | The upper and the lower lights at Belle Isle's south end. |
| ca-qc-dorval / ca-qc-dorval-2 | The Dorval course range front and Lighthouse Friends' lost Dorval light, 1.8 km apart. |
| ca-nb-oak-point / ca-nb-oak-point-range-front | Oak Point (Saint John River) and Oak Point Range Front (Miramichi), 178 km apart. |
| ca-nl-green-island / ca-nl-green-island-2 | Green Island (Catalina) and Green Island (Fortune Bay), 290 km apart. |
| ca-nl-long-point / ca-nl-long-point-2 | Long Point (Twillingate) and Long Point (Port au Port), 305 km apart. |
| ca-ns-green-island / ca-ns-green-island-2 | Green Island (Cape Breton) and Green Island (Chebogue Point), 460 km apart. |
| ca-ns-louisbourg / ca-ns-louisbourg-range | Louisbourg lighthouse and the Louisbourg range, 2.5 km apart. |
| ca-ns-wedge-island / ca-ns-wedge-island-2 | Two Wedge Islands 118 km apart. |
| ca-on-pointe-aux-pins / ca-on-pointe-aux-pins-2 | Pointe aux Pins on Lake Erie and Pointe aux Pins near Sault Ste. Marie, 512 km apart; at the latter, the main light (lost) and the range are separate Lighthouse Friends pages. |
| ca-qc-sainte-croix / ca-qc-sainte-croix-range | Sainte-Croix lighthouse and the Sainte-Croix range, 2.4 km apart. |

**Left for the owner.** Two ranges are one station each by DESIGN 3.2, but both halves have a published story, so
they are not merged: Wright's Range (`ca-pe-wrights-range`, the front, and `ca-pe-wrights-back-range`, 690 m apart)
and Port Dalhousie (`ca-on-port-dalhousie-outer-range`, the front, and `ca-on-port-dalhousie-range-rear`, 460 m apart;
a first pass merged them before the rear's story was published in batch H7, and was undone). `ca-pe-leards-range-2` and
`ca-nl-belle-isle-south-end-lower-2`, ids in the running story batch, keep their ids and now hold the merged records.

**After the audit** (local merge of 2026-10-28): **1,165 Canadian stations shown** (1,194 before): 26 ids retired with
`merged_into` (42 in all), 4 hidden, one new station (`ca-ns-pictou-island-west`). `data/curation_ca.json` gained 26
`merge_stations`, 23 `rename`, 4 `hide`, 5 `detach`, 4 `apart` and 1 `join` entries. The report's 3 Canadian possible
duplicates and 28 close namesakes are now 0. A second run writes nothing.

**Pins that moved with a merge.** A range's pin stands on its front light (DESIGN 3.9). Where the front tower was moved
away, the merged station's pin is now on it: Calvaire (the 1915 front at the Deschaillons rest area, 3.6 km from the
active range), Summerside Range (Lighthouse Friends' private front, 3.9 km) and L'Ardoise (the private front, 4.2 km).
Curation has no way to set a position aside; these are listed for the owner.
