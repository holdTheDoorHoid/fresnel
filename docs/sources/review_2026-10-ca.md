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
