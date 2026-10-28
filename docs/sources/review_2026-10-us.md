# US review, October 2026: the suspect lists of the first build, decided

The first US build (`data/merge_report.json`, 2026-10-21) listed **50 possible duplicate pairs** (two stations within 150 m), **56 possibly lost** stations (a Wikidata end date and nothing else) and **40 decorative suspects** (inland, OpenStreetMap only, a scale copy under another light's name). This round has the evidence the first build lacked: LighthouseFriends's state pages, the Society's Digital Archive (2,299 places), the National Register, NOAA's charts, the Coast Guard's Light List, Rowlett's directory and the Passport Club list (DESIGN 2.4). Each suspect was decided on that evidence. The decisions are code, not notes: `pipeline/record_joins.py` (generated from this review; every entry carries its reason) is read by `pipeline/merge.py`, so the same answers come back on every run and a record is never joined, hidden or re-placed by hand in a station file. The rule that ids never change holds: a station found to be a duplicate keeps its file, hidden, with `merged_into`.

After the complete Society file (2,299 places) and the merge of the Canadian round the lists were looked at a second time; its entries are the second half of each table below (marked "pass 2").

## In numbers

| List | First build | After | Note |
|---|---|---|---|
| Possible duplicate pairs, US (150 m) | 50 | 0 | each joined, or kept apart below |
| Close namesakes, US (names agree, 150 m to 8 km; a list added after the first build) | - | 0 | each joined, linked or kept apart below |
| Possibly lost, US | 56 | 0 | each settled by a status pick, or by a source that now says it; Canada's are in its own review |
| Decorative suspects, US | 40 | 0 |  |

Decisions recorded in `pipeline/record_joins.py`:

| Kind | Entries |
|---|---|
| Records sent to a station (`RECORD_JOINS`) | 109 |
| Positions found wrong (`NO_POSITION`) | 21 |
| Records kept apart (`KEEP_APART_PAIRS`) | 4 |
| Pairs of stations reviewed and found to be two (`NOT_DUPLICATES`) | 55 |
| Names (`NAME_PICKS`) | 8 |
| Statuses settled (`STATUS_PICKS`) | 17 |
| Stations hidden (`HIDE`) | 19 |
| Scale copies (`REPLICA_OF`) | 30 |
| Successive lights linked (`SUCCESSION`) | 7 |
| Reviewed and kept visible (`KEEP_VISIBLE`) | 12 |

The duplicate audit of 2026-10-27 added to these (section "Duplicate audit" below).

## The three rulings (DESIGN 3.2)

- **Twin lights are one station with two structures.** Navesink Twin Lights (NJ) and Cape Ann Light Station (Thacher Island, MA) were two stations each in the first build; Cape Elizabeth (ME) was already one. The towers are the station's structures, with one set of keepers and one register entry.
- **Old and New Point Loma are two linked stations.** Each has its own established name and a different site, 0.8 km apart: `us-ca-point-loma` keeps the active light and `us-ca-old-point-loma` (new) takes the 1855 tower's records; the two are linked `preceded_by` / `succeeded_by`. Nothing published was retired. Old and New Presque Isle (MI) follow the same rule.
- **Lake Havasu's scale copies are `replica` stations with `replica_of`** the light they copy, never joined to it (30 copies, among them the eighteen at Lake Havasu City). A replica joins an original only on the spot, by a number, or by a decision here.

## Joined: stations that are one

A pair of stations (or a station and a record) found to be the same light or the same range. The retired id keeps its file with `merged_into`; a station that was only in the first build's trial and never published is simply not made. A target given as a record key is a station the review did not yet have an id for.

| Pair | Decision | Why |
|---|---|---|
| us-pr-punta-borinquen-2 -> us-pr-punta-borinquen | One station (clear, 3 m) | Wikidata has two items for Punta Borinquen: Q7260508, the 1889 Spanish tower (NRHP 81000559, abandoned after the 1918 earthquake, ruins 1.8 km west) and Q109232559, the 1922 tower that still shows a light (Light List 3-30715, HAER PR-37). Rowlett and LighthouseFriends list one station with two towers; the OSM way for the 1922 tower carries the 1889 item's tag, which is how the first build mixed them. One station, two structures; the OSM way is pinned so it lands on the 1922 tower. |
| us-fl-gasperilla-island -> us-fl-boca-grande | One station (range, 17 m between pins) | 'Gasperilla Island Lighthouse' (Wikidata, with a typo) is the Boca Grande Entrance rear range light, 1927 skeleton tower at the north end of Gasparilla Island (LighthouseFriends 'Gasparilla Island (Boca Grande Entrance Rear Range)', Rowlett 'Gasparilla Island', Light List 3-1310). The station it was flagged against, Boca Grande, is the 1890 Port Boca Grande tower at the south end (Light List 3-1305) plus this rear light, which the first build had already pinned as its map position, 2.7 km from the tower. The two form the Boca Grande entrance range, which DESIGN 3.2 makes one station with two structures; the rear light joins it. |
| us-fl-tierra-verde -> us-fl-tampa-bay-watch | One station (clear, 13 m) | OpenStreetMap calls the 2005 lighthouse at Tampa Bay Watch's headquarters 'Tierra Verde Lighthouse'; Wikidata calls it Tampa Bay Watch Light (ARLHS USA1335); the Society's passport list has 'Tampa Bay Watch'. Same point, 13 m. |
| us-ms-ship-island -> us-ms-gulfport-harbor | One station (clear, 4 m) | OpenStreetMap's 'Ship Island Light' stands at Gulfport Harbor, 30.365 N, 89.090 W, the position of Wikidata's Gulfport Harbor Light (2011, Light List 4-10020, Rowlett: maintained by the city), and 25 km from Ship Island. The 2011 harbour lighthouse is modelled on the Ship Island light; the element is the harbour tower named for it. One structure. |
| us-ca-point-stuart-2 -> us-ca-point-stuart | One station (clear, position copied) | Wikidata's Point Stuart Light (1915, retired 1960) has the coordinates of Point Blunt Light (37.853, -122.419, the other end of Angel Island); OpenStreetMap's 'Point Stuart Lighthouse' is on the northwest point (37.861, -122.446), where the Light List and ENC chart the Point Stuart light. One light with a copied position. |
| us-nj-finns-point-rear-range -> us-nj-finns-point-range | One station (clear, 71 m) | Two Wikidata items for the one surviving Finns Point rear range tower: Q5450597 'Finn's Point Rear Range Light' (NRHP 78001792) and Q14705497 'Finns Point Range Light'; both 1877, both retired 1950, 71 m apart, one entry in Rowlett and in LighthouseFriends. The front light is gone and is in neither source as a separate station. |
| us-nj-navesink-south -> us-nj-navesink-north | One station (twin lights, 22 m) | RULING (DESIGN 3.2): twin lights are one station. The Navesink Twin Lights (Highlands, NJ) stood as one station with one set of keepers; Wikidata has one item for the station (Q6982276), one for each tower, and the NRHP lists them as 'Twin Lights'. The south tower joins the north station as its second structure. |
| us-ny-plum-gut -> us-ny-plum-island | One station (clear, 4 m) | Plum Gut Lighthouse and Plum Island Light are two Wikidata items for the one lighthouse on Plum Island (it guards Plum Gut): same point (4 m), same Light List number 1-21090, one NRHP listing (11000014). |
| us-ma-nantucket-range-rear -> us-ma-nantucket-harbor-range | One station (range, 24 m) | The Nantucket Harbor Range is one range: a front (the Light List calls it 'Nantucket Harbor Range Front Light', 1-15160, Wikidata 'Nantucket Reef Range Front Light') and a rear (1-15165), both 1908; Wikidata also has an item for the range as a whole. DESIGN 3.2: a range is one station with a front and a rear structure. |
| us-ma-nantucket-reef-range-front -> us-ma-nantucket-harbor-range | One station (range, 93 m) | The front half of the Nantucket Harbor Range (see the rear): Light List 1-15160, Rowlett 'Nantucket Harbor Range Front', 1908. |
| us-ma-nantucket-cliff-front-range -> us-ma-nantucket-cliff-rear-range | One station (range, 10 m) | The Nantucket Cliff Range (1838, retired 1912): Wikidata has the front, the rear and the range as one item at one point; OpenStreetMap maps it as one relation; LighthouseFriends lists one 'Nantucket Cliff Range'. One range, two structures. |
| us-oh-perrys-memorial -> us-oh-perrys-victory-and-international-peace-memorial | One station (clear, 9 m) | Perry's Victory and International Peace Memorial at Put-in-Bay is a monument with a navigation light on top (Light List 7-5670 'Perry Memorial Monument Light', ARLHS USA1317). Wikidata has an item for the monument and one for 'Perry's memorial lighthouse' (1915); LighthouseFriends lists 'Perry Memorial'. One structure; it does serve as an aid, so it stays. |
| us-mi-st-joseph-north-pier-outer -> us-mi-st-joseph-north-pier-inner | One station (pair on one pier, 109 m) | The St. Joseph North Pier Inner and Outer Lights (1907 and 1906) are one NRHP listing (05001211), one Wikidata item for the pair (Q24641189), one LighthouseFriends entry ('St. Joseph Pier'). They work as a pair on one pier; the outer light joins the inner as the second structure. |
| us-ny-south-buffalo-north-side-2 -> us-ny-south-buffalo-north-side | One station (clear, positions copied) | South Buffalo North Side Light (1903, inactive since 1988; NRHP 83001673) is in Buffalo Harbor at 42.835 N, 78.868 W (Wikidata, NRHP, ENC). OpenStreetMap's node and LighthouseFriends's 'Buffalo South Entrance North Side' sit at 42.493 N, 79.354 W, which is Dunkirk Harbor, 55 km west; Rowlett and the Society's archive describe the Buffalo light. One light; the two positions are wrong. |
| us-mi-st-clair-flats-range-front -> us-mi-st-clair-flats-front-and-rear-range | One station (range, 17 m) | The St. Clair Flats South Channel Range: Wikidata has the front light (Q89911087), the rear (Q90016470) and the pair (Q7587573); OpenStreetMap has the front and rear nodes; NRHP 90000853 lists the range. The station with the pair already holds the rear and the OSM front; the front-only station is the same front light 17 m away. |
| us-mi-pentwater-south-pierhead -> us-mi-pentwater | One station (successive structures, 0 m) | Pentwater South Pierhead Light (1937) replaced the Pentwater pier light of 1873 at the same spot: Rowlett writes 'station established 1873', Wikidata gives the 1873 light's end as 1937, LighthouseFriends has one 'Pentwater Pier'. Successive towers of one station at one place (DESIGN 3.2). The North Pierhead Light (1997) is on the other pier and stays apart. |
| us-me-winter-harbor-2 -> us-me-winter-harbor | One station (clear, position copied) | Wikidata's 'Winter Harbor Light' (1856, retired 1933) has Pumpkin Island Light's coordinates (44.309, -68.743); NRHP 87002538 'Winter Harbor Light Station' and OpenStreetMap put the light at 44.362 N, 68.088 W (Mark Island, Winter Harbor), with LighthouseFriends. One light with a copied position. |
| us-wi-baileys-harbor-directional -> us-wi-baileys-harbor-range-front | One station (successor on the same Light List number, 73 m) | The Baileys Harbor Directional Light (1969-2015) is the post light that replaced the range's front light and carries its Light List number, 7-21228. A modern post, not a station of its own (DESIGN 1): it joins the range it replaced. |
| us-wi-baileys-harbor-range-rear -> us-wi-baileys-harbor-range-front | One station (range, 116 m) | The Baileys Harbor range is one range, front 1869 and rear 1870, both retired 1969 and relit 2015 (Rowlett); the Society and LighthouseFriends list it as 'Baileys Harbor Range Lights'; NRHP 89001466 covers the pair. One station, two structures (DESIGN 3.2). |
| us-ak-lighthouse-ruins -> us-ak-scotch-cap | One station (ruins of the 1940 tower, 51 m) | Scotch Cap's third tower (1940) was destroyed by the 1946 tsunami; OpenStreetMap's 'Lighthouse Ruins' are its remains, 51 m from the Scotch Cap Light of today. They are a structure of the Scotch Cap station, not a station. |
| us-fl-cape-canaveral-2 -> us-fl-cape-canaveral | One station (same headland, 1.6 km) | Cape Canaveral Light: the 1848 tower (lost, Wikidata) and the present 1868 tower 1.6 km inland (Light List, OSM, Rowlett, USLHS). Same name, same headland, a move inland like Cape Hatteras's: one station with two structures (DESIGN 3.2). |
| records -> us-ms-horn-island | One station (unique name in the state, 6.5 km) | LighthouseFriends's 'Horn Island' (destroyed) is Wikidata's Horn Island Light (1874, retired 1961); positions 6.5 km apart along the 22-km island; the only Horn Island light in the state. |
| records -> us-nc-cape-fear | One station (clear, position copied) | Wikidata's Cape Fear Light carries Oak Island Light's coordinates (33.893, -78.035, 4.7 km from the site). The station's OSM service buildings, NRHP 78001931 and LighthouseFriends all put the 1903 tower's site at 33.846 N, 77.967 W on Bald Head Island; LighthouseFriends and the Society's archive both say the tower is gone (1958). One lost lighthouse. |
| records -> us-md-north-point-range | One station (clear) | LighthouseFriends's lost 'North Point' (39.196 N, 76.443 W) is the North Point Range Lights of 1822-1873 (Wikidata); Wikidata's own point for them copies the Craighill Channel Upper Range Front Light's. |
| us-ma-thacher-island-north -> us-ma-cape-ann | One station (twin lights, 228 m) | RULING (DESIGN 3.2): twin lights are one station. Cape Ann Light Station on Thacher Island had two towers, the North (1771, Wikidata 'Thacher Island North Light') and the South (the one that still shows the light), with one set of keepers; the NRHP and the Society list 'Cape Ann Light Station / Twin Lights'. The north tower joins the Cape Ann station as its second structure. |
| us-mi-copper-harbor-front-range -> us-mi-copper-harbor-range | One station (range, 1.4 km) | Copper Harbor Front Range Light (Wikidata, Light List 7-15175) and the Copper Harbor Range station (OSM relation with front and rear, 7-15185) are the front and the rear of one range 1.4 km apart. |
| us-il-william-e-dever-crib-2 -> us-il-william-e-dever-crib | One station (unique name, 2.6 km) | William E. Dever Crib: Wikidata (41.929, -87.599, Light List 7-20040) and OpenStreetMap with LighthouseFriends (41.917, -87.572) name the one crib light off Chicago 2.6 km apart; there is one Dever crib. |
| records -> us-fl-cape-florida | One station (unique name, 7.3 km) | The Society's archive has Cape Florida at 25.659 N, 80.083 W, 7 km east of the tower on Key Biscayne (25.667 N, 80.156 W; Wikidata, OSM, NRHP, Light List). It is the one Cape Florida light, with a wrong position. |
| records -> lighthousefriends:1804 | One station (unique name, 6.5 km) | LighthouseFriends's Bayou Bonfouca (with the Light List's 4-11025) and the Society's Bayou Bonfouca (1848-1862) are the one lost light on Lake Pontchartrain; positions differ by 6.5 km. |
| records -> us-ny-ambrose | One station (unique name, 2.9-7.8 km) | Ambrose Light, the Texas tower of 1967-2008 (Wikidata, ARLHS USA009, Light List 1-34785): the Society's archive and Rowlett list the tower as gone; LighthouseFriends's 'Ambrose' is the same tower pinned 8 km off. The lightship that served the Ambrose station is a separate vessel record. |
| records -> us-nj-tuckers-beach | One station (same replica, 354 m) | Wikidata's 'phare de Tucker's Beach' (1999) is the replica at Tuckerton Seaport that OpenStreetMap, LighthouseFriends ('Tuckers Beach (Replica)') and Rowlett's Tucker's Island entry describe; 354 m between the two points. The tower it copies, Tucker's Island Light (lost 1927), has no station of its own yet. |
| records -> us-md-cedar-point | One station (unique name, 8 km) | Cedar Point (Maryland, Chesapeake Bay): Wikidata (38.299 N, 76.368 W), LighthouseFriends (38.276 N, 76.463 W) and the Society's archive (typed 39.299 N) name one screwpile light, lit 1896, gone. |
| records -> us-mn-split-rock | One station (unique name, 17 km) | The Society's archive gives Split Rock at 47.333 N, 91.600 W; the lighthouse is at 47.200 N, 91.367 W (Wikidata, OSM, NRHP). One lighthouse, one wrong position. |
| us-de-baker-range-rear -> us-de-baker-shoal-range-rear | One station (unique name, 0.7 km) | The Society's 'Baker Range Rear' (lost) and Rowlett's entry are the rear light that Wikidata, OpenStreetMap and LighthouseFriends call Baker Shoal Range Rear, 743 m away by the Society's rounded position. |
| records -> us-va-bay-creek | One station (same replica, 13 m) | OpenStreetMap's 'Bay Creek Lighthouse' (Cape Charles, VA) is the 2004 replica of Old Plantation Flats Light that LighthouseFriends ('Old Plantation Flats (Replica)') and Rowlett describe, 13 m apart. The replica takes the station OpenStreetMap started; the original (lost 1962) stays its own station. |
| records -> lighthousefriends:1120 | One station (replica separated from the original, 117 m) | The Blakistone (Blackistone) Island replica at St. Clement's Island Museum (2008): OpenStreetMap's 'Blackistone Lighthouse' and the passport stamp are the replica; LighthouseFriends, the Society's archive and Rowlett list it as a replica. The first build had put the replica's OSM element on the 1851 original's station. |
| records -> us-ma-newburyport-harbor-range | One station (range, 1 m) | Newburyport Harbor Range: the station already holds Wikidata's front and rear items, the OSM front and rear elements and LighthouseFriends's rear entry. LighthouseFriends's front entry (602) and Rowlett's front entry sit on the same front light, 1 m from it, and had started a front-only station. |
| records -> us-nj-finns-point-range | One station (unique name, 3.1 km) | The Society's archive has two records for the Finns Point range (a 'Range Lights' entry, inactive, 1877-1950) at the rounded point 39.589 N, 75.537 W, 3 km from the rear tower: they are the range of the Finns Point station. |
| us-pr-punta-borinquen-3 -> us-pr-punta-borinquen | One station (clear, 3 m); pass 2 | The 1922 Punta Borinquen tower is described by LighthouseFriends's entry 1163 (the other, 1162, is the 1889 tower), the Light List's 3-30715, the HAER record PR-37 and an ENC point, all within 3 m of Wikidata's Punta Borinquen Light of 1922. The first review joined the Wikidata and OpenStreetMap items of the two towers; these four records started a third station on the same spot. |
| us-va-nansemond -> us-va-nansemond-river | One station (clear, 63 m); pass 2 | OpenStreetMap's 'Nansemond Lighthouse' is a node tagged abandoned, taken from a USGS map scan; it is 63 m from LighthouseFriends's position for Nansemond River Light (screwpile, 1878-1935, destroyed), the only light of that name in Virginia. |
| us-mi-six-mile-point-range-front -> us-mi-six-mile-point-range | One station (clear, positions wrong in two sources); pass 2 | The Six Mile Point Range lights (1895, inactive) are on the St. Marys River below Sault Ste. Marie: the Light List's 7-14045 (46.440 N, 84.266 W) and the Society's archive (46.438 N, 84.265 W) agree. LighthouseFriends puts its front light at 45.993 N, 83.899 W and its rear at 45.999 N, 84.350 W, 40 km from each other, which no range can be; the OpenStreetMap nodes repeat those two points. The Light List and archive records join the front station; the four wrong points are set aside (NO_POSITION). |
| us-mi-six-mile-point-range-rear -> us-mi-six-mile-point-range | One station (one range, 0 m); pass 2 | The Six Mile Point Range's rear light (1895): LighthouseFriends's and OpenStreetMap's rear entries (their points set aside), Rowlett's rear and the Society's Six Mile Point Range Rear. The sources give the rear no point of its own that can be trusted (the archive's is the front's, 0 m away), so the range is one station with a front and a rear structure and the rear's published id is retired into it. |
| us-nj-horseshoe-range-east-group-upper-front -> lighthousefriends:1882 | One station (one group, 740 m); pass 2 | The Horseshoe Range's East Group (Delaware River, 1881, all gone) has a lower front, a rear and an upper front in the Society's archive; LighthouseFriends lists the group as one entry. The upper front joins the group as its third structure. |
| us-pa-horseshoe-range-west-group-lower-front -> lighthousefriends:1883 | One station (one group, point copied from the East Group); pass 2 | The archive files the West Group under Pennsylvania but gives its three lights the same points as the East Group (39.8705 N, 75.1503 W and so on), 5 km from where LighthouseFriends puts the West Group (39.883 N, 75.209 W). The West Group's records join LighthouseFriends's entry and their points are set aside. |
| us-pa-horseshoe-range-west-group-range-rear -> lighthousefriends:1883 | One station (one group, point copied from the East Group); pass 2 | The West Group's rear light: see the lower front. |
| us-pa-horseshoe-range-west-group-upper-front -> lighthousefriends:1883 | One station (one group, point copied from the East Group); pass 2 | The West Group's upper front light: see the lower front. |
| us-oh-maumee-bay-straight-channel-range-east-front -> lighthousefriends:1988 | One station (one range, 360 m); pass 2 | The Straight Channel Range of Maumee Bay (1884; an east and a west range with two lights each, and two centre lights discontinued in 1895) is one entry in LighthouseFriends and the Light List; the Society's archive lists its six lights separately, with one point for each pair. The East Front joins the range. |
| us-oh-maumee-bay-straight-channel-range-west-rear -> lighthousefriends:1988 | One station (one range, 360 m); pass 2 | The West Rear light of the Straight Channel Range: see the East Front. |
| us-fl-st-joseph-point-beacon-hill-range-rear -> us-fl-st-joseph-point | One station (same years, 1.0 km); pass 2 | Wikidata's St. Joseph Point Light (lit 1902, retired 1960) and the Society's St. Joseph Point Range (front 1902; rear 'Beacon Hill', 1902-1960) have the same years; Rowlett lists the range's rear as 'St. Joseph Point (Beacon Hill) Range Rear', inactive since 1960. The archive's points are rounded to 0.1 minute and lie 0.3 to 1.0 km from Wikidata's. One range, one station with a front and a rear structure. |
| us-ga-tybee-knoll-cut-range-front -> us-ga-tybee-island-range-front | One station (one range, 750 m); pass 2 | The Tybee Knoll Cut Range (1878): the Society's front light joins the station that already holds its rear (the archive), LighthouseFriends's 'Tybee Knoll Cut Range', Rowlett's front and rear and the Light List's 3-4715. Wikidata names the same two lights 'Tybee Island Range Front / Rear Light'. |
| us-md-mathias-point-shoal -> us-md-mathias-point | One station (clear, 430 m); pass 2 | The Society's Mathias Point Shoal (1876-1963, lost) is Mathias Point Light: Wikidata lit 1876, retired 1961, LighthouseFriends 'Mathias Point' destroyed, Rowlett 'Mathias Point Shoal' 1876; the archive's point is 430 m off (rounded). |
| us-nj-tinicum-island-range-rear -> us-nj-tinicum-island-range | One station (clear, archive point rounded); pass 2 | The Society's Tinicum Island Range Rear (1880) is the rear light of the Tinicum Island (Billingsport) Range that Wikidata, OpenStreetMap, LighthouseFriends, the NRHP and the Light List describe; the archive's point is 1.6 km off. |
| us-ny-long-beach-bar-replica -> us-ny-orient-long-beach-bar | One station (same site, 20 m); pass 2 | Orient Long Beach Bar Light ('Bug Light', 1871) burned in 1963 and a replica was built on the spot in 1990 and lit as an aid (Rowlett: 'Light station reactivated'; Light List 1-27975; OpenStreetMap: 'Bug Light'). The Society lists the 1871 light and the 1990 replica as two places 20 m apart at the same site; one station. |
| us-oh-vermilion-replica -> us-oh-vermilion | One station (same lighthouse, 650 m); pass 2 | Vermilion Light's present tower is the replica of the 1877 lighthouse built in 1991-92 at the Inland Seas Maritime Museum and lit as an aid (Light List 7-4451 'Vermilion Museum Lighthouse'; Wikidata lit 1992). Rowlett's and the Society's 'Vermilion (Replica)' are that tower; the archive's point is 650 m east. |
| us-mi-saginaw-river -> us-mi-saginaw-river-rear-range | One station (same years, 1.1 km); pass 2 | The Society's Saginaw River (lit 1841, tower of 1876, retired 1960) is the Saginaw River Rear Range Light station (Wikidata built 1876, retired 1960; NRHP 'Saginaw River Light Station'); the archive's point is 1.1 km off. |
| us-wi-grassy-island-range-rear -> us-wi-grassy-island-range | One station (clear, archive point rounded); pass 2 | The Society's front and rear (both 1872) and Rowlett's rear are the Grassy Island Range Lights (Wikidata, NRHP, LighthouseFriends); the archive gives both lights one point 2.4 km off. |
| us-la-ship-shoal-2 -> us-la-ship-shoal | One station (clear, 1.7 km); pass 2 | The Society's Ship Shoal (1859-1965) is Ship Shoal Light (Wikidata retired 1965, Rowlett built 1859); the archive's point is rounded and 1.7 km from LighthouseFriends's and the Light List's. |
| us-ny-oswego-harbor-west-pierhead-2 -> us-ny-oswego-harbor-west-pierhead | One station (clear, archive point wrong); pass 2 | The Society's Oswego Harbor West Pierhead (1934, active) is the pierhead light that Wikidata, OpenStreetMap, LighthouseFriends, the NRHP and the Light List describe at 43.473 N, 76.517 W. The archive's point for it (43.789 N, 76.861 W) is 40 km off, and it gave the same point to two other Oswego lights (see NO_POSITION). |
| wikidata:Q7084751 -> new:us-ca-old-point-loma | Record pinned | RULING (DESIGN 3.2): Old Point Loma (1855, on the ridge, now a museum in Cabrillo National Monument) and New Point Loma (1891, at the shore) are two stations, each with its own established name, 0.8 km apart. The published station keeps the active light; the ridge tower's records start the Old Point Loma station, and the two are linked as successive lights. Nothing is retired. |
| osm:way/90687227 -> new:us-ca-old-point-loma | Record pinned | Old Point Loma Lighthouse, OpenStreetMap's way for the 1855 tower. |
| nrhp:74000350 -> new:us-ca-old-point-loma | Record pinned | NRHP 74000350 is the Old Point Loma Lighthouse. |
| lighthousefriends:29 -> new:us-ca-old-point-loma | Record pinned | LighthouseFriends's second 'Point Loma' entry, on the ridge. |
| rowlett:ca2:point-loma-1 -> new:us-ca-old-point-loma | Record pinned | Rowlett's first Point Loma entry: 1855, inactive since 1891. |
| uslhs_passport:stamp:ca:point-loma-old -> new:us-ca-old-point-loma | Record pinned | The Passport Club keeps separate stamps for 'Point Loma (Old)' and '(New)'. |
| lighthousefriends:816 -> us-la-ship-shoal | Record pinned | LighthouseFriends's 'Ship Shoal' (28.915 N, 91.071 W) and the Light List's 'Ship Shoal Obstruction Lights' 4-730 are Ship Shoal Light, the offshore tower of 1859-1965. Wikidata's item for it (Q7497938) carries South Pass Range's coordinates, which is why the first build put it 80 km from the shoal. |
| wikidata:Q7859191 -> us-wi-two-rivers | Record pinned; pass 2 | Two Rivers (Wisconsin): Wikidata's Two Rivers Light (retired 1969) and Rowlett's Two Rivers (1886, inactive since 1969) are the lighthouse that OpenStreetMap and LighthouseFriends map as 'Two Rivers Lighthouse', 1.2 km north of the pier where Wikidata puts it: one tower, which no longer stands where it served. The pier now has the North Pierhead Light (1969, Light List 7-20925), a modern pier light that is not a station of Fresnel's (DESIGN section 1); its records stay out of the lighthouse's station (see the records kept apart). |
| rowlett:wi:two-rivers-1 -> us-wi-two-rivers | Record pinned; pass 2 | Rowlett's Two Rivers, the 1886 lighthouse inactive since 1969. |
| rowlett:md:lazaretto-point -> us-md-lazaretto-point | Record pinned; pass 2 | Rowlett's Lazaretto Point (built 1985, inactive) is the replica that OpenStreetMap and LighthouseFriends map; the original (1831-1926) is the Society's Lazaretto Point, 530 m off. |
| territories:haer-pr-32 -> us-pr-punta-tuna | Record pinned | HAER PR-32, the Library of Congress's record of the Spanish-era Punta Tuna lighthouse; the library's point is a geocode 4 km from the light, and no other Puerto Rico station has this name. |
| territories:haer-pr-35 -> us-pr-cardona-island | Record pinned | HAER PR-35, 'Faro del Puerto de Ponce': the lighthouse of Ponce's harbour is the one on Cardona Island, 670 m from the library's point. |
| territories:haer-pr-36 -> us-pr-caja-de-muertos | Record pinned | HAER PR-36, the lighthouse of Caja de Muertos island, 935 m from the library's point. |
| territories:haer-pr-38 -> us-pr-arecibo | Record pinned | HAER PR-38, 'Faro de los Morillos de Arecibo': Arecibo Light, 1.4 km from the library's point. |
| territories:haer-pr-41 -> us-pr-guanica | Record pinned | HAER PR-41, 'Faro del Puerto de Guanica': Guanica Light, 7 km from the library's geocode of the harbour. |
| territories:haer-pr-45 -> us-pr-puerto-ferro | Record pinned | HAER PR-45, the Puerto Ferro lighthouse on Vieques, 770 m from the library's point. |
| territories:haer-pr-46 -> us-pr-el-morro-or-port-san-juan | Record pinned | HAER PR-46, the lighthouse of the Castillo de San Felipe del Morro (Port San Juan Light), 710 m from the library's point. |
| uslhs:8793 -> new:us-nj-tuckers-island | Record pinned | The Society's 'Tucker Beach' (wood tower of 1848, 14 m, lost 1927; the archive files it under Sea Haven) is Tucker's Island Light, the original that the Tuckerton Seaport replica copies. It is its own station, linked to the replica; the first review had left it without one. |

## Kept apart: two stations although the report asked

Pairs the report listed as possible duplicates or close namesakes, decided to be two lights. They no longer appear in the lists; where one succeeded the other they are also linked (below).

| Pair | Decision | Why |
|---|---|---|
| us-ny-fort-tompkins / us-ny-fort-wadsworth | Two stations | Fort Tompkins Light (1828, relit 1873) and Fort Wadsworth Light (1903) are 13 m apart under two names; linked as successive lights, not joined. |
| us-il-chicago-harbor-2 / us-il-chicago-harbor | Two stations | The first Chicago Harbor light and the 1893 light are 2.4 km apart (linked as successive lights). |
| us-ny-buffalo-harbor-south-entrance / us-ny-south-buffalo-north-side | Two stations | Buffalo Harbor South Entrance Light (NRHP 07001191) and South Buffalo North Side Light (NRHP 83001673) are two NRHP-listed lights 185 m apart at the harbor's south entrance. |
| us-md-blakistone-island / us-md-blackistone | Two stations | The 1851 original and its 2008 replica, 587 m apart (linked as replica_of). |
| us-la-south-pass-range / us-la-ship-shoal | Two stations | South Pass Range Lights and Ship Shoal Light are different lights 80 km apart; Wikidata gave Ship Shoal the range's coordinates. |
| us-nc-cape-fear / us-nc-oak-island | Two stations | Cape Fear Light (Bald Head Island, 1903-1958) and Oak Island Light (1958, mainland) are different towers 4.7 km apart; Wikidata gave Cape Fear Oak Island's coordinates. |
| us-ca-point-stuart / us-ca-point-blunt | Two stations | Point Stuart and Point Blunt are the two ends of Angel Island, 2.5 km apart. |
| us-md-craighill-channel-upper-range-front / us-md-north-point-range | Two stations | Craighill Channel Upper Range Front Light (1886) and the North Point Range Lights of 1822-1873 are different lights; Wikidata copied the first's coordinates onto the second. |
| us-ma-nantucket-harbor-range / us-ma-brant-point | Two stations | The Nantucket Harbor Range (1908) and Brant Point Light (1746; towers 1856 and 1901) are different lights 140 m apart on Brant Point. |
| us-ma-broad-sound-channel-inner-range / us-ma-spectacle-island-range | Two stations | Two lost Boston Harbor ranges: Broad Sound Channel Inner Range (1903-1950) and Spectacle Island Range (1897-1913), listed apart by Wikidata and LighthouseFriends (entries 1978 and 1977), 60 m apart at Spectacle Island. |
| us-mi-grand-haven-south-pierhead-entrance / us-mi-grand-haven-north-pierhead | Two stations | The south and north pierhead lights of Grand Haven stand on opposite piers, 142 m apart. |
| us-mi-pentwater / us-mi-pentwater-north-pierhead | Two stations | Pentwater Light (south pier, 1873/1937) and the North Pierhead Light (north pier, 1997) are on different piers, 95 m apart. |
| us-ny-buffalo-north-breakwater-east-end / us-ny-buffalo-main | Two stations | Buffalo North Breakwater's end light and Buffalo Main Light (1833) are different lights 50 m apart. |
| us-mn-duluth-south-breakwater-outer / us-mn-duluth-harbor-north-pier | Two stations | Duluth's south breakwater outer light and north pier light are on different piers, 105 m apart. |
| us-wi-plum-island-range / us-wi-1849-lighthouse-ruins | Two stations | The Plum Island Range Lights (1896) and the ruins of the 1849 lighthouse are different structures 73 m apart; the ruins are a station of their own. |
| us-az-wind-point / us-az-alpena | Two stations | Lake Havasu's one-third-scale copies of the Wind Point and Alpena lights, 95 m apart on the shore. |
| us-az-currituck-beach / us-az-buffalo-main | Two stations | Lake Havasu's copies of the Currituck Beach and Buffalo Main lights, 113 m apart. |
| us-az-west-quoddy / us-az-east-quoddy | Two stations | Lake Havasu's copies of the West Quoddy and East Quoddy Head lights, 94 m apart. |
| us-il-chicago-harbor-2 / us-il-chicago-pierhead-range-front | Two stations | The first Chicago Harbor light (1832-1859) and the Chicago Pierhead Range front light (1891): different lights; the Society's archive gives both the river-mouth point 41.885 N, 87.6195 W. |
| us-sc-morris-island / us-sc-charleston | Two stations | Morris Island Light (1876) and Charleston Light (1962, Sullivans Island) are different towers 7.9 km apart; 'Charleston Light' is an old name of the first. |
| us-nc-southwest-point-royal-shoal / us-nc-northwest-point-royal-shoal | Two stations | Southwest Point and Northwest Point Royal Shoal lights are two lights 4.3 km apart. |
| us-de-cape-henlopen / us-de-cape-henlopen-beacon | Two stations | Cape Henlopen Light (1764/1767) and the Cape Henlopen Beacon (1825) were two lights 1.4 km apart. |
| us-de-delaware-breakwater-range / us-de-delaware-breakwater-west-end | Two stations | The Delaware Breakwater range and the breakwater's west-end light are different lights 4.7 km apart. |
| us-de-delaware-breakwater-east-end / us-de-harbor-of-refuge | Two stations | Delaware Breakwater East End Light (1885) and Harbor of Refuge Light (1908) are different lights 2 km apart (they share an NRHP listing, 89000289). |
| us-md-craighill-channel-lower-range-front / us-md-craighill-channel-upper-range-front | Two stations | The lower and upper Craighill ranges are different ranges 4.7 km apart. |
| us-md-craighill-channel-upper-range-rear / us-md-craighill-channel-lower-range-rear | Two stations | The upper and lower Craighill ranges are different ranges 6 km apart. |
| us-de-baker-shoal-range-front / us-de-baker-shoal-range-rear | Two stations | The front and rear of the Baker Shoal range are 3.2 km apart, beyond the 3 km the merge pairs automatically; left as two stations. |
| us-ny-staten-island / us-ny-new-dorp | Two stations | Staten Island Light (1912) and New Dorp Light (1856, inactive) are different towers 1.9 km apart. |
| us-ct-new-haven-outer-breakwater / us-ct-five-mile-point | Two stations | New Haven Outer Breakwater light (lost) and Five Mile Point Light (New Haven Harbor Light, 1805) are different lights 4.5 km apart. |
| us-oh-lorain-west-breakwater / us-oh-lorain-east-breakwater | Two stations | Lorain's west and east breakwater lights are on different breakwaters, 543 m apart. |
| us-oh-cleveland-west-pierhead / us-oh-cleveland-east-pierhead | Two stations | Cleveland's west and east pierhead lights are on different piers, 232 m apart. |
| us-ma-hyannis-rear-range / us-ma-hyannis-harbor | Two stations | Hyannis Rear Range Light (1849) and OpenStreetMap's 'Hyannis Harbor Lighthouse' (disused) are 1.7 km apart; no source says they are one tower. |
| us-in-old-michigan-city / us-in-michigan-city-east | Two stations | Old Michigan City Light (1858, museum) and the Michigan City East Pierhead Light (1904) are different towers 862 m apart. |
| us-pa-erie-land / us-pa-presque-isle | Two stations | Erie Land Light (1818) and Presque Isle Light (1872) are different lights 5 km apart. |
| us-mi-st-clair-flats-canal-lower / us-mi-st-clair-flats-front-and-rear-range | Two stations | St. Clair Flats Canal lights and the South Channel Range are different aids 2.1 km apart. |
| us-mi-st-clair-flats-canal-range / us-mi-st-clair-flats-front-and-rear-range | Two stations | The St. Clair Flats Canal Range (1871) and the South Channel Range (1859) are different ranges 3.8 km apart. |
| us-wi-kenosha-north-pier / us-wi-kenosha | Two stations | Kenosha Light (1866, inactive) and the Kenosha North Pier Light (1906) are different towers 583 m apart. |
| us-mi-north-manitou-shoal / us-mi-north-manitou-island | Two stations | North Manitou Shoal Light (1935) and North Manitou Island Light (1898, lost) are different lights 4.7 km apart. |
| us-fl-st-johns / us-fl-st-johns-river | Two stations | St. Johns Light (1954) and St. Johns River Light (1859) are different towers 2.8 km apart (linked as successive lights). |
| us-ma-three-sisters-of-nauset / us-ma-nauset | Two stations | The Three Sisters of Nauset (1838) and Nauset Light (1877) are different structures 370 m apart (linked as successive lights). |
| us-mi-old-presque-isle / us-mi-new-presque-isle | Two stations | Old and New Presque Isle Light are two stations (RULING, DESIGN 3.2), linked as successive lights. |
| us-va-old-plantation-flats / us-va-bay-creek | Two stations | The original screwpile light (lost 1962) and the 2004 replica at Bay Creek are 3 km apart. |
| us-va-stingray-point / us-va-stingray-point-replica | Two stations | The original Stingray Point light (1858-1965) and its replica are 3.3 km apart. |
| us-md-blakistone-island / us-md-blackistone-island-replica | Two stations | The 1851 original (lost 1955) and the 2008 replica at the museum, 117 m apart by the sources' points. |
| us-ca-point-loma / us-ca-old-point-loma | Two stations | RULING (DESIGN 3.2): Old and New Point Loma are two stations 0.8 km apart, linked as successive lights. |
| us-va-smith-point-old / us-va-smith-point | Two stations | Smith Point Light (1897) and the earlier Smith Point light (1868-1898, the Society's 'Smith Point (Old)') were 1.2 km apart; linked as successive lights. |
| us-md-hawkins-point / us-md-leading-point | Two stations | Hawkins Point Light and Leading Point Light are the front and rear of the Brewerton Channel Range, each with its own item and name, 1.8 km apart. |
| us-mi-keweenaw-waterway-lower-entrance / us-mi-jacobsville | Two stations | The Keweenaw Waterway Lower Entrance Light (1920) and Jacobsville (Portage River) Lighthouse (1856-1920) are different lights 1.7 km apart. |
| us-ca-santa-cruz / us-ca-santa-cruz-breakwater | Two stations | The Santa Cruz Lighthouse (the 1967 memorial copy at Lighthouse Point) and the West Breakwater Light (1964) are different lights 2.4 km apart. |
| us-fl-fort-barrancas-range / us-fl-pensacola | Two stations | The Light List calls Pensacola Light the rear light of the Fort Barrancas Range (4-4785), and the Society lists the range's front and rear as lost; they are kept as two stations, the range at Fort Barrancas 600 m south-west, until a source settles whether the lost 'rear' is the Pensacola tower. |
| us-ga-tybee-island-range / us-ga-tybee-island-lighthouse-and-museum | Two stations | The Society's Tybee Island Range (front 1822, lost; rear 1793, active) is probably the Tybee lighthouse as the rear of its range, but its dates (1793, not the station's 1736 or the tower's 1867) do not match; kept apart until a source settles it. |
| us-ga-tybee-island-range / us-ga-tybee-island-range-front | Two stations | The Tybee Island Range (Savannah River entrance, 1822) and the Tybee Knoll Cut Range (1878) are different ranges 6.7 km apart. |
| us-ny-olcott / us-ny-olcott-2 | Two stations | Olcott Light (1873, lost) and its replica of 2003 are 575 m apart. |
| us-md-lazaretto-point / us-md-lazaretto-point-2 | Two stations | The 1985 replica at Lazaretto Point and the original light (1831-1926), 530 m apart. |
| us-nj-horseshoe-range-east-group / us-pa-horseshoe-range-west-group | Two stations | The Horseshoe Range's East Group (New Jersey side) and West Group (Pennsylvania side) are two groups of lights the sources keep apart. |

## Records that are two stations although names and positions agree

| Records | Decision | Why |
|---|---|---|
| uscg_light_list:4-12597 / wikidata:Q7497938 | Never in one station | Light List 4-12597 is Port Eads Marina Lower Dock Light, at South Pass (29.015 N, 89.166 W), which is the point Wikidata's Ship Shoal Light item copies. Ship Shoal Light's own number is 4-730. |
| uscg_light_list:7-20925 / wikidata:Q7859191 | Never in one station | Light List 7-20925 is the Two Rivers North Pierhead Light (1969) on the pier; Wikidata's item for the old lighthouse carries its number, but the lighthouse no longer stands there. |
| enc:44.14269,-87.56070 / wikidata:Q7859191 | Never in one station | The ENC light at the Two Rivers pier is the North Pierhead Light, not the old lighthouse. |
| rowlett:wi:two-rivers-north-pierhead-2 / wikidata:Q7859191 | Never in one station | Rowlett lists the 1969 North Pierhead Light apart from the Two Rivers lighthouse. |

## Positions found wrong

The record keeps its facts (years, flags, numbers) and joins by decision, name or number; its coordinates are not used. The USLHS fetcher also drops by rule the positions it can show to be impossible (`extra.position_dropped`; 43 in the Society's file and 2 in the NRHP's).

| Record | Decision | Why |
|---|---|---|
| wikidata:Q7497938 | Position not used | Ship Shoal Light's Wikidata item copies the coordinates of South Pass Range Lights (29.015, -89.167), 80 km north of the shoal; LighthouseFriends and the Light List give the shoal. |
| wikidata:Q5034789 | Position not used | Cape Fear Light's Wikidata item copies Oak Island Light's coordinates (33.893, -78.035), 4.7 km from the Bald Head Island site. |
| wikidata:Q44082465 | Position not used | Point Stuart Light's Wikidata item copies Point Blunt Light's coordinates (37.853, -122.419). |
| wikidata:Q14692309 | Position not used | North Point Range Lights' Wikidata item copies the Craighill Channel Upper Range Front Light's coordinates (39.197, -76.448). |
| wikidata:Q8026238 | Position not used | Winter Harbor Light's Wikidata item copies Pumpkin Island Light's coordinates (44.309, -68.743). |
| osm:node/9843815382 | Position not used | OpenStreetMap places South Buffalo North Side Light at Dunkirk Harbor, 55 km from Buffalo Harbor. |
| lighthousefriends:907 | Position not used | LighthouseFriends places 'Buffalo South Entrance North Side' at Dunkirk Harbor, 55 km from Buffalo Harbor. |
| wikidata:Q4924664 | Position not used | Blakistone Island Light's Wikidata item sits at the replica's site (St. Clement's Island Museum), not on the island where the 1851 tower stood. |
| uslhs:2768 | Position not used | The Society's archive puts Cape Florida 7 km east of the tower. |
| uslhs:3357 | Position not used | The Society's archive puts Split Rock 17 km from the lighthouse. |
| osm:node/1011891274 | Position not used | OpenStreetMap's Six Mile Point Range Light repeats LighthouseFriends's point, 45.993 N, 83.899 W, 50 km from the St. Marys River where the Light List and the Society put the range. |
| lighthousefriends:1560 | Position not used | LighthouseFriends's Six Mile Point Range Front is 50 km from the St. Marys River, where the Light List (7-14045) and the Society put the range, and 40 km from its own rear light. |
| osm:node/1012232474 | Position not used | OpenStreetMap's Six Mile Point Range Rear Lighthouse repeats LighthouseFriends's point, 45.999 N, 84.350 W, 45 km from the St. Marys River. |
| lighthousefriends:1559 | Position not used | LighthouseFriends's Six Mile Point Range Rear is 45 km from the St. Marys River, where the Society puts the range. |
| uslhs:3426 | Position not used | The Society's point for Oswego Harbor West Pierhead (43.789 N, 76.861 W) is 40 km from Oswego; the same point is given to two other Oswego lights. |
| uslhs:8817 | Position not used | The Society's point for Oswego Harbor (43.789 N, 76.861 W) is 40 km from Oswego. |
| uslhs:7344 | Position not used | The Society's point for Oswego Breakwater (43.789 N, 76.861 W) is 40 km from Oswego. |
| uslhs:8887 | Position not used | The Society's Horseshoe Range West Group, Lower Front has the East Group's point. |
| uslhs:8888 | Position not used | The Society's Horseshoe Range West Group, Range Rear has the East Group's point. |
| uslhs:8889 | Position not used | The Society's Horseshoe Range West Group, Upper Front has the East Group's point. |
| wikidata:Q7859191 | Position not used | Wikidata's Two Rivers Light is at the pier (44.143 N, 87.560 W) where the lighthouse served until 1969; the lighthouse itself is mapped by OpenStreetMap and LighthouseFriends 1.2 km north, and the pier's lights (the Light List's 7-20925 and 7-20930) are not its. |

## Statuses

Settled where the sources disagree or only one end date speaks.

| Station | Status | Why |
|---|---|---|
| us-md-blakistone-island | lost | The 1851 Blakistone Island lighthouse was lost in 1955 (Wikidata: retired 1956; the Society's archive: lost). A 2008 replica stands on the mainland. |
| us-md-north-point-range | lost | The North Point Range Lights (1822, retired 1873) are listed as destroyed by LighthouseFriends; Wikidata gives an end date. |
| us-nc-cape-fear | lost | The 1903 skeleton tower at Cape Fear was taken down in 1958; LighthouseFriends and the Society's archive list it as gone. Its foundation and station buildings remain (the OpenStreetMap elements). |
| us-de-christiana-north-jetty | lost | Lit 1884, discontinued 1909 (Wikidata gives an end date of 1939); the Society's archive lists the Christiana light station as lost. No source maps a structure. |
| us-de-delaware-breakwater-range | lost | Both lights of the Delaware Breakwater range are gone: LighthouseFriends and the Society's archive list the rear as destroyed (retired 1918), Wikidata gives the front's end as 1903 / 1950. |
| us-md-cedar-point | lost | The Cedar Point screwpile light (lit 1896, retired 1920) is listed as destroyed by LighthouseFriends and as lost by the Society's archive. |
| us-md-greenbury-point | lost | Greenbury Point's two lights (1848, 1892; the second retired 1934) are listed as destroyed by LighthouseFriends; no source maps a structure. |
| us-ma-fairhaven-bridge | lost | A light on the Fairhaven swing bridge, lit 1888 and ended 1891; the Society's archive lists it only as a minor aid. No source maps or lists a structure. |
| us-nc-roanoke-marshes-2 | lost | The Roanoke Marshes screwpile light (1877) was taken down in 1955; the Light List's 'Roanoke Marshes Light RM' is a modern pile light at the site. |
| us-va-hog-island | unknown (Reviewed 2026-10: Wikidata's end date (1948) is the only evidence that this light is gone; no source maps or lists a structure.) | Hog Island Light: one source (Wikidata, 1853-1948). |
| us-va-old-plantation-flats | lost | The Old Plantation Flats screwpile light (1886) ended in 1962 (Wikidata); the Light List's 'Warning Light A' is a modern light at the site, and the 2004 replica is a separate station. |
| us-wi-1849-lighthouse-ruins | ruins | OpenStreetMap maps the remains of the 1849 Plum Island lighthouse as ruins. |
| us-md-bethel-bridge-lighthouse-replica | replica | The name says it: a replica, mapped by OpenStreetMap and listed by LighthouseFriends. |
| us-md-mathias-point | lost | Mathias Point Light (1876): LighthouseFriends lists it as destroyed and the Society's archive as lost (retired 1963); Wikidata gives an end date. The Light List's 'Upper Potomac River Channel Light 5' is a modern light at the site. |
| us-ny-orient-long-beach-bar | active | The replica of Bug Light shows a light as an aid (Light List 1-27975); the 1871 original burned in 1963. |
| us-oh-vermilion | active | The replica lighthouse shows a light as an aid (Light List 7-4451); the 1877 original is gone. |
| us-mi-new-buffalo | lost | The lighthouse of New Buffalo (1840-1859) is listed as destroyed by LighthouseFriends and as lost by the Society's archive; OpenStreetMap maps a lighthouse-shaped structure in the town, 950 m from LighthouseFriends's point, which the Society lists as a private (faux) lighthouse. |

## Names

| Station | Name shown | Why |
|---|---|---|
| us-ca-old-point-loma | Old Point Loma Lighthouse | The ridge tower of 1855 (Cabrillo National Monument). |
| us-me-cape-elizabeth-light-western | Cape Elizabeth Light | Twin lights, one station (DESIGN 3.2): the east tower (1874, active) and the west tower (1874, retired 1924); Wikidata's item for the west tower won the name. |
| us-nj-navesink-north | Navesink Twin Lights | One station, two towers: the name the NRHP, Wikidata and the state park use. The id keeps the first build's 'north'. |
| us-ma-cape-ann | Cape Ann Light Station | The twin-tower station on Thacher Island is Cape Ann Light Station (NRHP, the Society, Rowlett); Wikidata's item for the north tower won the name. |
| us-va-bay-creek | Old Plantation Flats (Replica) | The station started as OpenStreetMap's 'Bay Creek Lighthouse'; the lighthouse is a replica of Old Plantation Flats Light, as LighthouseFriends and Rowlett call it. |
| us-fl-boca-grande | Boca Grande Lighthouse (Gasparilla Island Light) | The station is both the 1890 Port Boca Grande tower and the rear light; 'Gasparilla Island' is the name the Society, LighthouseFriends and the Coast Guard use. |
| us-in-old-michigan-city | Old Michigan City Light | OpenStreetMap's name for the oil house of the light station ('Oil Shed') won the station's name; the light is Old Michigan City Light (1858, NRHP 74000023), now a museum. |
| us-nj-tuckers-island | Tucker's Island Light | The original of 1848-1927; the replica at Tuckerton Seaport is us-nj-tuckers-beach. Rowlett and LighthouseFriends call the island's light Tucker's Island / Tuckers Beach. |

## Hidden (file kept)

Decorative or modern structures that never served as an aid to navigation, or a light in another country (DESIGN section 1).

| Station | Reason | Why |
|---|---|---|
| us-md-pooles-island-2 | A modern light on the shoal south of Pooles Island (Light List 2-8663); the historic Pooles Island Light is us-md-pooles-island | OpenStreetMap's second 'Pooles Island Light' 3.3 km south of the 1825 tower, with the Light List's modern light as its only other record: a modern aid with no history of its own (DESIGN 1). |
| us-ma-original-location-of-nauset-lighthouse-prior-to-1996 | A marker for the spot where Nauset Light stood before it was moved in 1996 (recorded on us-ma-nauset), not a station | OpenStreetMap's node marks Nauset Light's old site, 94 m from the tower; it is a place on the Nauset station, not a station. |
| us-ny-lighthouse-point-park | A park named for the Buffalo Main Light, not a light | OpenStreetMap's way 'Lighthouse Point Park' is the park around Buffalo Main Light. |
| us-me-machias-seal-island | The light is in Canada: see ca-nb-machias-seal-island | Machias Seal Island, with its light, is administered by Canada (New Brunswick); LighthouseFriends and the Society's passport list file it under Maine. The Canadian station has the Wikidata record. |
| us-az-lake-havasu-marina | A marina's decorative lighthouse that copies no particular light and is not an aid to navigation | Lake Havasu Marina's lighthouse (2001) is not a copy of a named light (Rowlett's other Havasu entries all say which light they copy). |
| us-co-frisco-bay-marina | A decorative lighthouse at a marina on a mountain reservoir: not an aid to navigation | Inland, OpenStreetMap only, in no register, no light list and no lighthouse directory. |
| us-ky-stevns-fyr | A copy of a Danish lighthouse in Kentucky: decorative, not an aid to navigation | OpenStreetMap only; named for the Stevns lighthouse in Denmark. |
| us-mo-lake-chesterfield | A decorative lighthouse on a suburban lake: not an aid to navigation | Inland, OpenStreetMap only, in no register or light list. |
| us-mo-mark-twain-memorial | A memorial lighthouse (1935) on Cardiff Hill, Hannibal: not an aid to navigation | A memorial structure; no light list or register lists it as an aid. |
| us-mt-lake-frances | A decorative lighthouse at a reservoir: not an aid to navigation | Inland, OpenStreetMap only. |
| us-ne-linoma | A decorative lighthouse at a beach resort on the Platte River: not an aid to navigation | Inland, OpenStreetMap only. |
| us-tn-omohundro-waterworks | A waterworks tower built to look like a lighthouse: not an aid to navigation | Inland, OpenStreetMap only (disused). |
| us-ut-northshore | A decorative lighthouse on Utah Lake: not an aid to navigation | Inland, OpenStreetMap only. |
| us-ny-celoron | A private (faux) lighthouse at Celoron, Chautauqua Lake: not an aid to navigation | The Society's archive lists it as a private (faux) lighthouse; OpenStreetMap only otherwise. |
| us-wa-dimick | A private (faux) lighthouse built in 1990 at Dimick: not an aid to navigation | The Society's archive lists it as a private (faux) lighthouse; OpenStreetMap only otherwise. |
| us-ma-hyannis-harbor | A privately kept, unofficial light on Lewis Bay, not an aid to navigation | OpenStreetMap's 'Hyannis Harbor Lighthouse' is tagged disused; Rowlett calls the Lewis Bay light privately maintained and unofficial, and the Society lists it as a private (faux) lighthouse. |
| us-nh-spindle-point | A private (faux) lighthouse on Lake Winnipesaukee: not an aid to navigation | OpenStreetMap only, with the Society's listing as a private (faux) lighthouse. |
| us-oh-rattlesnake-island | A privately kept, unofficial light (1990): not an aid to navigation | OpenStreetMap, Rowlett ('privately maintained and unofficial') and the Society's private (faux) listing. |
| us-wv-summersville-lake | A decorative lighthouse (2012) on an inland lake: not an aid to navigation | OpenStreetMap, Rowlett and the Society's private (faux) listing; in no Light List. |

## Reviewed and kept visible

Suspects whose evidence says they are aids (listed in the Light List, charted, NRHP-listed or historic).

| Station | Why |
|---|---|
| us-mi-manning-memorial | Listed by the Light List (7-18366) as a lit aid. |
| us-mi-william-livingstone-memorial | Listed by the Light List (7-8260) as a lit aid. |
| us-ny-titanic-memorial | A memorial lighthouse that showed a light for ships (1913-1967). |
| us-oh-perrys-victory-and-international-peace-memorial | A monument with a lit aid on top (Light List 7-5670). |
| us-or-cleft-of-the-rock | A private aid in the Light List (6-0640), although the Society calls it faux. |
| us-wi-asylum | Wikidata, ARLHS and Rowlett list it as a lighthouse; it is lit, although the Society calls it faux. |
| us-ca-lions | Charted as a fixed green light (NOAA ENC 33.760 N, 118.194 W), though the Society calls it a private (faux) lighthouse. |
| us-mi-wawatam | Listed by the Light List (7-12608) as a lit aid, though the Society calls it a private (faux) lighthouse. |
| us-oh-grand-lake-st-marys | NRHP-listed (82003614) and in Wikidata, although the Society calls it a private (faux) lighthouse. |
| us-pa-turtle-rock | A historic light of 1887 (Wikidata, LighthouseFriends, Rowlett) that the Society lists as a private (faux) lighthouse. |
| us-wi-kevich | Listed by the Light List (7-20765) as a lit private aid, though the Society calls it a private (faux) lighthouse. |
| us-mi-new-buffalo | The lost lighthouse of 1840-1859 (LighthouseFriends, the Society); the faux lighthouse the Society also lists in the town is a separate structure. |

## Scale copies

Status `replica`, related `replica_of` / `replica`.

| Copy | Copies | Why |
|---|---|---|
| us-va-bay-creek | us-va-old-plantation-flats | The 2004 replica of Old Plantation Flats Light at Bay Creek Resort, Cape Charles (OpenStreetMap: 'Bay Creek Lighthouse'; LighthouseFriends and Rowlett: replica). |
| us-va-stingray-point-replica | us-va-stingray-point | The replica of Stingray Point Light (LighthouseFriends and Rowlett: replica). |
| us-md-blackistone | us-md-blakistone-island | The 2008 replica of Blakistone Island Light at St. Clement's Island Museum (OpenStreetMap, LighthouseFriends, the Society, Rowlett). |
| us-az-algoma | us-wi-algoma-pierhead | Lake Havasu City's one-third-scale copy of Algoma Pierhead Light (Rowlett: 'Spectator Point (Algoma Pierhead Replica)'). |
| us-az-alpena | us-mi-alpena | Lake Havasu's copy of Alpena Light (Rowlett: 'Southwest Point I (Alpena Replica)'). |
| us-az-barnegat | us-nj-barnegat-2 | Lake Havasu's copy of Barnegat Light (Rowlett: 'Red Rock Point (Barnegat Replica)'). |
| us-az-berwick | us-la-southwest-reef | Lake Havasu's copy of the Berwick light, which is Southwest Reef Light at Berwick Bay (Rowlett: 'Larned Landing (Berwick Replica)'; the passport list names the original 'Southwest Reef (Berwick)'). |
| us-az-buffalo-main | us-ny-buffalo-main | Lake Havasu's copy of Buffalo Main Light (Rowlett: 'Bridgewater Channel West (Buffalo Main Replica)'). |
| us-az-cape-hatteras | us-nc-cape-hatteras | Lake Havasu's copy of Cape Hatteras Light (Rowlett: 'Windsor Beach I (Cape Hatteras Replica)'). |
| us-az-cape-henry | us-va-cape-henry | Lake Havasu's copy of the new Cape Henry Light (Rowlett: 'Windsor Beach II (New Cape Henry Replica)'). |
| us-az-chicago-harbor-navy-pier | us-il-chicago-harbor-southeast-guidewall | Lake Havasu's copy of the Chicago Harbor Southeast Guidewall Light (Rowlett: 'South Point (Chicago Harbor Southeast Guidewall Replica)'). |
| us-az-currituck-beach | us-nc-currituck-beach | Lake Havasu's copy of Currituck Beach Light (Rowlett: 'Bridgewater Channel East (Currituck Replica)'). |
| us-az-east-quoddy | ca-nb-head-harbour | Lake Havasu's copy of East Quoddy Head Light, Head Harbour Light Station on Campobello Island (Rowlett: 'Bridgewater Channel North (East Quoddy Head Replica)'). |
| us-az-fire-island | us-ny-fire-island | Lake Havasu's copy of Fire Island Light (Rowlett: 'Thompson Bay (Fire Island Replica)'). |
| us-az-pemaquid-point | us-me-pemaquid-point | Lake Havasu's copy of Pemaquid Point Light. |
| us-az-point-gratoit | us-ny-dunkirk | Lake Havasu's copy of Point Gratiot Light, which is Dunkirk Light (Rowlett: 'West Point II (Dunkirk Replica, Point Gratiot Replica)'). |
| us-az-robert-h-manning | us-mi-manning-memorial | Lake Havasu's copy of the Robert H. Manning Memorial Light (Rowlett: 'Crazy Horse Marina (Robert R. Manning Replica)'). |
| us-az-split-rock | us-mn-split-rock | Lake Havasu's copy of Split Rock Lighthouse (Rowlett: 'West Point I (Split Rock Replica)'). |
| us-az-vermilion | us-oh-vermilion | Lake Havasu's copy of Vermilion Light (Rowlett: 'Pittsburgh Point (Vermilion Replica)'). |
| us-az-west-quoddy | us-me-west-quoddy-head | Lake Havasu's copy of West Quoddy Head Light (Rowlett: 'Lake Havasu Yacht Club (West Quoddy Head Replica)'). |
| us-az-white-shoal | us-mi-white-shoal | Lake Havasu's copy of White Shoal Light (Rowlett: 'Havasu Island Golf Course (White Shoal Replica)'). |
| us-az-wind-point | us-wi-wind-point | Lake Havasu's copy of Wind Point Light (Rowlett: 'Southwest Point II (Wind Point Replica)'). |
| us-ca-grays-harbor | us-wa-grays-harbor | A copy of Grays Harbor Light on the Colorado River side of Lake Havasu. |
| us-ca-portland-head | us-me-portland-head | A copy of Portland Head Light on Lake Havasu (Rowlett: 'Pilot Rock (Portland Head Replica)'). |
| us-ca-umpqua-river | us-or-umpqua-river | A copy of Umpqua River Light on Lake Havasu. |
| us-ct-mystic-seaport | us-ma-brant-point | Mystic Seaport's 1966 copy of Brant Point Light (OpenStreetMap: 'Brant Point Replica Lighthouse'; LighthouseFriends: 'Mystic Seaport (Replica)'). |
| us-ca-trinidad-memorial | us-ca-trinidad-head | The Trinidad Memorial Lighthouse is a copy of Trinidad Head Light, built as a memorial to lost fishermen (LighthouseFriends: memorial). |
| us-md-lazaretto-point | us-md-lazaretto-point-2 | The 1985 replica of Lazaretto Point Light (OpenStreetMap, LighthouseFriends: replica; Rowlett built 1985); the original of 1831-1926 is the Society's Lazaretto Point. |
| us-ny-olcott | us-ny-olcott-2 | The replica of Olcott Light (2003; Rowlett: a decorative light is displayed); the original of 1873 is the Society's Olcott. |
| us-nj-tuckers-beach | us-nj-tuckers-island | The replica at Tuckerton Seaport (1999) copies Tucker's Island Light (1848-1927). |

## Successive lights that are two stations

Related `preceded_by` / `succeeded_by`, both ways.

| Older | Newer | Why |
|---|---|---|
| us-ca-old-point-loma | us-ca-point-loma | RULING (DESIGN 3.2): Old Point Loma (1855-1891) and New Point Loma (1891-) are two stations, linked. |
| us-ny-fort-tompkins | us-ny-fort-wadsworth | Fort Tompkins Light (1828, relit 1873) and Fort Wadsworth Light (1903) stand within 13 m on Staten Island under different names; the fort changed its name. Linked, not joined: the sources do not say the first tower was replaced by the second. |
| us-il-chicago-harbor-2 | us-il-chicago-harbor | The first Chicago Harbor light (1832-1859, at the river mouth) and Chicago Harbor Light (1893, Navy Pier breakwater, 2.4 km east) are two stations under one name at separate sites. |
| us-fl-st-johns-river | us-fl-st-johns | St. Johns River Light (1859, Mayport) and St. Johns Light (1954) are separate towers 2.8 km apart under different names. |
| us-ma-three-sisters-of-nauset | us-ma-nauset | The Three Sisters of Nauset (1838), now preserved in a park, were Nauset's first lights; Nauset Light (1877) replaced them 370 m away. |
| us-mi-old-presque-isle | us-mi-new-presque-isle | RULING (DESIGN 3.2): Old Presque Isle Light (1840) and the New Presque Isle Light (1871) are two stations 1.9 km apart, each with its own established name. |
| us-va-smith-point-old | us-va-smith-point | The screwpile light of 1868 and the present Smith Point Light (1897), 1.2 km apart. |

## What the lists hold after this review

- Possible duplicates (US): 0. none.
- Close namesakes (US, 150 m to 8 km, names agreeing): 0, each decided above or a range the report lists as paired; the remainder:
- Possibly lost (US): 0.
- Decorative suspects (US): 0.

## What the build holds after the review (local merge, not committed)

US stations shown: **1432** (1082 already published, 350 new); hidden 20; retired with `merged_into` 27 (this build retired 26 of them).

By status: active 556, inactive 319, lost 363, replica 39, ruins 5, unknown 150. By kind: harbor light 1, life saving station 52, lighthouse 1121, lightship 17, lightship station 4, pier light 79, range lights 158.

| Source | US records | In a published station | In a new station | Not placed (leads, or nothing near) | New stations it started |
|---|---|---|---|---|---|
| lighthousefriends | 1076 | 878 | 172 | 26 | 162 |
| uslhs | 2139 | 865 | 307 | 967 | 164 |
| nrhp | 577 | 550 | 15 | 12 | 12 |
| enc | 1058 | 707 | 68 | 283 | 0 |
| uscg_light_list | 2054 | 825 | 70 | 1159 | 0 |
| rowlett | 1697 | 970 | 82 | 645 | 0 |
| uslhs_passport | 679 | 553 | 11 | 115 | 0 |
| territories | 22 | 15 | 7 | 0 | 4 |

## Duplicate audit (2026-10-27)

Story batches write a long history for each station, so a light split across two stations gets two histories and a
junk display name opens a story with a wrong name. This pass looked for both across every shown station:

- a name scan (same country and region, names equal once Light, Lighthouse, Range, Front, Rear, The, Of, De, La, Le,
  Du and Phare are dropped and Saint is folded to St.): 118 groups, 248 ids;
- a looser scan (also dropping Old, New, Original, years, Harbor, Pier, Beacon; within 15 km): 112 more pairs, most of
  them a light beside its life-saving station;
- every station held only by Society records at an approximate position (75), against the stations of its state whose
  records' names match, also after dropping East, West, Breakwater, Pierhead and similar words (37 had a candidate;
  11 were failed joins, such as Two Harbors East Breakwater, whose archive point is near Duluth);
- the report's lists (US: none open; Canada's are in `review_2026-10-ca.md`, section 10);
- every display name, for house, owner, building and park names, coordinates, labels in the wrong language and
  sentence fragments.

Each group was decided on the records' own evidence: positions, NRHP, Light List and ARLHS numbers, the Society's
dates and town, and LighthouseFriends' pages (read for every moved or rebuilt tower). Rulings applied (DESIGN 3.2):

- **A tower moved or rebuilt away from its station is a structure of that station, not a station of its own**: Cape
  St. George (rebuilt 20 km away in 2007-08), Cape Mendocino (Shelter Cove), Table Bluff (Woodley Island),
  Southampton Shoal (Tinsley Island), Mispillion (Lewes), Frying Pan Island (Sault Ste. Marie), Peche Island Range Rear
  (Marine City), and the Society's records of the original sites of Cape San Blas, Seven Foot Knoll and Roanoke River.
  The pin follows the precedence (OpenStreetMap first), so it is where the tower stands now when OpenStreetMap maps it;
  the other point stays on the page as a location conflict, and the status note says where it stood. A tower that
  no longer shows a light is `relocated`. **Cape St. George stays `active`**, as Cape Hatteras does: the rebuilt tower
  shows the light again (Light List 4-75), and `relocated` would make the site end the light's years at its 1994
  discontinuance (`build_site_data.year_range`); the note records the collapse and the rebuild.
- **A range is one station** with a front and a rear structure, also when the halves were filed apart (Port Penn,
  Reedy Island, Bloody Point, Hilton Head, Morris Island, Ashtabula West Pier, Presque Isle Harbor, Grosse Ile South
  Channel, Grassy Island, Strawberry Island Upper and Lower Cut, Fort Barrancas, Wolf Island, Ecorse, Elba Island).
- **A Society or National Register record whose point is far from the only light of its name** joins that light, its
  point set aside (`NO_POSITION`), as Split Rock and Cape Florida did in the first review. Most of these are the
  Society's points (a typed latitude, a town's geocode, a point in the wrong lake) and the Register's batch points
  (Cape Hinchinbrook, Liston Range Front, Mount Desert, Ram Island, Wolf Trap), whose numbers the light already held
  through Wikidata but more than 10 km away. Where a Society point is only rounded but, as a structure of its own,
  would have moved a station's pin or changed its status (Menominee, Lahaina, Waukegan, Elba Island, Elm Tree, and
  the lost range fronts of St. Simons, Hilton Head and Reedy Island, whose standing towers keep the pin), it is set
  aside too, and the record describes the station as a whole.
- The id kept is the one with a published story, else the one in a story batch, else the plainer id, else the one
  with more sources. No id with a story is retired.

### Joined: stations that are one, and records moved

| Pair | Decision | Why |
|---|---|---|
| us-fl-cape-saint-george -> us-fl-cape-st-george | One station (rebuilt tower, 19.7 km) | Cape St. George Light: the 1852 tower on Cape St. George (Little St. George Island; Wikidata Q5035066, NRHP 74000625, the Society's archive, Rowlett) toppled into the Gulf on 21 October 2005 and was rebuilt in 2007-08 from the original drawings in the county park in the town of St. George Island, 19.7 km north-east, opened in November 2008 and dedicated on 4 April 2009 (LighthouseFriends 592). The OpenStreetMap way, LighthouseFriends, the Light List's 'St. George Lighthouse' (4-75) and the ENC point are the rebuilt tower; OpenStreetMap tags it with the same NRHP number. One station whose tower was rebuilt elsewhere, not two; the Light List number 4-75 is Wikidata's 4-0075. |
| us-ak-cape-hinchinbrook-2 -> us-ak-cape-hinchinbrook | One station (register point wrong, 33 km) | The National Register's Cape Hinchinbrook Light Station (05000728) is the station that Wikidata and OpenStreetMap already tag with that number; the register's batch point is 33 km south, in open water. Positions set aside: `nrhp:05000728`. |
| us-ak-cape-st-elias-2 -> us-ak-cape-st-elias | One station (archive point wrong, 131 km) | The Society's Cape St. Elias (1916, active, third-order lens) is Cape St. Elias Light on Kayak Island; the archive's point (60.158 N, 146.835 W) is 131 km away, near Cordova. Positions set aside: `uslhs:2688`. |
| us-ca-cape-mendocino-2 -> us-ca-cape-mendocino | One station (relocated tower, 54.5 km) | Cape Mendocino Light's 1868 iron tower was taken down in 1998 and re-erected at Mal Coombs Park, Shelter Cove, 54 km south; OpenStreetMap's 'Cape Mendocino Light' and LighthouseFriends map it there. Wikidata and the Society's archive place the station on the cape. One station, its tower now elsewhere. |
| us-ca-carquinez-strait-2 -> us-ca-carquinez-strait | One station (archive point wrong, 13 km) | The Society's Carquinez Strait (1910 dwelling, discontinued 1951) is the lighthouse Wikidata, LighthouseFriends and Rowlett place at Glen Cove, Vallejo; the archive's rounded point is 13 km west and no other Carquinez light exists. Positions set aside: `uslhs:2704`. |
| us-ca-punta-gorda-2 -> us-ca-punta-gorda | One station (archive point wrong, 27 km) | The Society's Punta Gorda (1912, discontinued 1951) is Punta Gorda Light; the archive's point is 27 km out at sea. Positions set aside: `uslhs:2727`. |
| us-ca-southampton-shoal-2 -> us-ca-southampton-shoal | One station (relocated tower, 81 km) | LighthouseFriends' Southampton Shoal is the 1905 lighthouse whose top two stories were lifted off the shoal in 1966 and barged to Tinsley Island in the Delta for the St. Francis Yacht Club; its point is where they stand now. The station (Wikidata, the Light List's 6-5480, Rowlett, the Society) is on the shoal. |
| us-ca-table-bluff-2 -> us-ca-table-bluff | One station (relocated tower, 15.5 km) | Table Bluff Light (1892, discontinued 1961; Wikidata, the Society's archive) stood on the bluff south of Humboldt Bay; the lighthouse was cut in two and moved to Woodley Island Marina, Eureka, in 1987 (LighthouseFriends 62, OpenStreetMap). One station, its tower now elsewhere. |
| us-de-liston-range-front-2 -> us-de-liston-range-front | One station (register point wrong, 31 km) | The National Register's Liston Range Front Lighthouse (03001386) is the front light that Wikidata and OpenStreetMap tag with that number; the register's batch point is 31 km north, near Wilmington. Positions set aside: `nrhp:03001386`. |
| us-de-mispillion-2 -> us-de-mispillion | One station (relocated tower, 24 km) | LighthouseFriends' Mispillion (place Lewes, private) is the 1873 Mispillion River lighthouse, moved to Lewes after the 2002 fire; the station (Wikidata, NRHP 86002919, Rowlett, the Society) is at the river mouth. |
| us-de-port-penn-range-front -> us-de-port-penn-range | One station (range, 3.2 km) | The Society's Port Penn Range Front (1877-1904) is the front light of LighthouseFriends' Port Penn Range; DESIGN 3.2: a range is one station with a front and a rear structure. |
| us-de-port-penn-range-rear -> us-de-port-penn-range | One station (range, 280 m) | The Society's Port Penn Range Rear (1877-1905) is the rear light of the same range, 280 m from LighthouseFriends' point. |
| us-de-reedy-island-range-front -> us-de-reedy-island-range-rear | One station (range, 4.1 km) | The Society's Reedy Island Range Front (1904) is the front of the range whose rear is the Taylors Bridge tower (Wikidata, NRHP 89000288, Light List 2-2585); one station with a front and a rear structure. Positions set aside: `uslhs:33270`. |
| uslhs:2762 -> us-de-reedy-island-range-rear | Record moved (record misfiled) | The Society's 'Reedy Island Range Rear' (1904, fourth-order lens of 1910, active) is the Taylors Bridge rear light; the archive gave it the same point as its 'Reedy Island Old' (39.5017 N, 75.57 W), so the first build filed it under the old Reedy Island light 10.6 km north. The record moves to the range; Old Reedy Island keeps its own records. Positions set aside: `uslhs:2762`. |
| us-fl-cape-san-blas-2 -> us-fl-cape-san-blas | One station (relocated tower, 16.5 km) | The Society's Cape San Blas (1885 tower, discontinued 1996) is Cape San Blas Light; its point is the cape, where the tower stood until it was moved to Port St. Joe in 2014 (Wikidata, OpenStreetMap, NRHP 15000208 'Cape San Blas Lighthouse at Port St. Joe'). |
| us-fl-charlotte-harbor-2 -> us-fl-charlotte-harbor | One station (archive point wrong, 95 km) | The Society's Charlotte Harbor (1890-1943) is Charlotte Harbor Light (Wikidata, LighthouseFriends); the archive's point is 95 km out in the Gulf. Positions set aside: `uslhs:8404`. |
| us-fl-st-johns-2 -> us-fl-st-johns | One station (archive point wrong, 38 km) | The Society's St. Johns (1954, automated 1967) is St. Johns Light at Mayport; the archive's point is 38 km north-west. Positions set aside: `uslhs:41509`. |
| us-fl-st-johns-river-2 -> us-fl-st-johns-river | One station (archive point wrong, 40 km) | The Society's St. Johns River (1859 tower, 1830-1929) is St. Johns River Light at Mayport; the archive's point is 40 km north-west. Positions set aside: `uslhs:2787`. |
| us-ga-saint-simons-island-range-front -> us-ga-st-simons-island | One station (range, 870 m) | The Society's Saint Simons Island Range Front (1895) is the front of the range whose rear was the St. Simons lighthouse itself (the archive's 'St. Simons Island Range Rear', already in the station); one station. Positions set aside: `uslhs:15265`. |
| us-la-amite-river-2 -> us-la-amite-river | One station (archive point wrong, 87 km) | Amite River light (1882, lost): the Society's point is a geocode of the town 87 km inland; LighthouseFriends and the Light List's Amite River Entrance Light place the light at the river's mouth on Lake Maurepas. One light; the plain id is kept. Positions set aside: `uslhs:8432`. |
| us-la-east-rigolets-2 -> us-la-east-rigolets | One station (archive point wrong, 44 km) | The Society's East Rigolets (1833-1874) is East Rigolets Light (Wikidata, LighthouseFriends); the archive's point is 44 km west, on the north shore of Lake Pontchartrain. Positions set aside: `uslhs:8440`. |
| us-la-oyster-bayou-2 -> us-la-oyster-bayou | One station (archive point wrong, 17 km) | Oyster Bayou light (1904-1975, lost): LighthouseFriends places it at the bayou's mouth on the Gulf; the Society's point is 17 km inland in the marsh. One light; the plain id is kept. Positions set aside: `uslhs:8444`. |
| us-la-pass-a-l-outre -> us-la-pass-a-loutre | One station (archive point wrong, 14 km) | The Society's 'Pass a L' Outre' (1855-1934) is Pass A L'Outre Light (Wikidata, LighthouseFriends, Rowlett); the archive's point is 14 km north. The ids differ only by the apostrophe. Positions set aside: `uslhs:2808`. |
| us-ma-old-harbor-u-s-life-saving-station-2 -> us-ma-old-harbor-u-s-life-saving-station | One station (relocated station, 48.7 km) | Old Harbor Life-Saving Station (1897) stood on Nauset Beach, Chatham (NRHP 75000159 and the Service's list place it there); it was floated by barge to Race Point, Provincetown, in 1977, where Wikidata places it (its item has the 1977 relocation). One station. |
| us-md-seven-foot-knoll-2 -> us-md-seven-foot-knoll | One station (relocated tower, 22.5 km) | The Society's Seven Foot Knoll (1855-1987) is Seven Foot Knoll Light; its point is the knoll in the Patapsco, where the screwpile stood until it was moved to Baltimore's Inner Harbor in 1988 (Wikidata, OpenStreetMap, NRHP). |
| us-me-mount-desert-2 -> us-me-mount-desert | One station (register point wrong, 66 km) | The National Register's Mount Desert Light Station (88000155, 'Mount Desert Rock Light Station') is the light on Mount Desert Rock that Wikidata and OpenStreetMap tag with that number; the batch point is 66 km west. Positions set aside: `nrhp:88000155`. |
| us-me-ram-island-2 -> us-me-ram-island | One station (register point wrong, 90 km) | The National Register's Ram Island Light Station (87002280, Lincoln County) is Ram Island Light at Boothbay, which Wikidata tags with that number; the batch point is 90 km east. Positions set aside: `nrhp:87002280`. |
| us-mi-frying-pan-island-2 -> us-mi-frying-pan-island | One station (relocated tower, 66 km) | Frying Pan Island light (1882, discontinued 1988): the Society's record says 'relocated to Coast Guard Station Sault St. Marie', where OpenStreetMap and LighthouseFriends map the tower; the archive's point and the Light List's modern 'Frying Pan Island Light 7' are at the island off De Tour. One station, its tower now elsewhere; the plain id is kept. |
| us-mi-peche-island-range-rear -> us-mi-peche-island-rear-range | One station (archive point wrong, 86 km) | Peche Island Range Rear: the 1908 tower moved to Marine City in 1983 (Wikidata, OpenStreetMap, LighthouseFriends) and Rowlett's present rear light (Light List 7-8410) at the range; the Society's point is 86 km west, inland. One station. Positions set aside: `uslhs:7104`. |
| us-mi-presque-isle-range-rear -> us-mi-presque-isle-rear-range | One station (range, 607 m) | Presque Isle Harbor Range (1870-71): the Light List's front (7-11565) and rear (7-11570) are 240 m apart; OpenStreetMap's 'Presque Isle Rear Range Lighthouse', LighthouseFriends' 'Presque Isle Range' and Rowlett's front made one station, the Society's, Rowlett's and the Light List's rear another. DESIGN 3.2: one station with a front and a rear. |
| us-mi-squaw-island-2 -> us-mi-squaw-island | One station (archive point wrong, 130 km) | The Society's Squaw Island (1892) is Squaw (Ojibwa) Island Light off Beaver Island; the archive's point is 130 km south, inland. Positions set aside: `uslhs:3340`. |
| us-mn-minnesota-point-2 -> us-mn-minnesota-point | One station (archive point wrong, 54 km) | The Society's Minnesota Point (1858, ruins) is Minnesota Point Light on Park Point, Duluth; the archive's point is 54 km north, inland. Positions set aside: `uslhs:8539`. |
| us-ms-biloxi-2 -> us-ms-biloxi | One station (archive point wrong, 65 km) | The Society's Biloxi (1848, active, town Biloxi) is Biloxi Light; the archive's point is 65 km north-west, inland. Positions set aside: `uslhs:3359`. |
| us-ms-ship-island-3 -> us-ms-ship-island-2 | One station (archive point wrong, 64 km) | The Society's Ship Island (1853) is Ship Island Light (Wikidata, LighthouseFriends, Light List 4-335); the archive's point is 64 km west, inland. Positions set aside: `uslhs:8549`. |
| us-nc-roanoke-river-3 -> us-nc-roanoke-river | One station (relocated tower, 14.5 km) | The Society's Roanoke River (1887-1941) is the screwpile cottage that stood at the river's mouth, the archive's point; it was moved to Edenton, where Wikidata, OpenStreetMap and LighthouseFriends place it. The 2003 replica at Plymouth (us-nc-roanoke-river-2) is a separate station. |
| us-ny-new-dorp-range-rear -> us-ny-new-dorp | One station (same light, 630 m) | The Society's New Dorp Range Rear (1856-1964) is New Dorp Light, the rear of the Swash Channel Range (Rowlett: 'New Dorp (Swash Channel Range Rear)'); same years, the archive's point rounded 630 m off. |
| us-ny-shinnecock-2 -> us-ny-shinnecock | One station (archive point wrong, 29 km) | The Society's Shinnecock (1858-1931) is Shinnecock (Ponquogue) Light; the archive's point is 29 km west. Positions set aside: `uslhs:8825`. |
| us-ny-strawberry-island-upper-cut-range-rear -> us-ny-strawberry-island-upper-cut-range | One station (range, archive point wrong) | The Society's Strawberry Island Upper Cut Range Rear (1908-1951) is the rear of the Upper Cut Range on the Niagara River at Buffalo; the archive's point is in Lake Ontario near Toronto, 86 km away. Positions set aside: `uslhs:8831`. |
| rowlett:nyw:strawberry-island-lower-cut-range-rear-4 -> us-ny-strawberry-island-lower-cut-range | Record moved (range, record misfiled) | Rowlett's Strawberry Island Lower Cut Range Rear (1908) is the rear of the Lower Cut Range (LighthouseFriends, the Light List's front 7-3015); a truncated ARLHS number (Rowlett's 'USA-122') had filed it under a station named Titanic Memorial. The Society's record of the same rear stays in that station, now hidden, because a station needs a positioned record and the Society's is the only one there. |
| us-ny-titanic-memorial-3 -> us-ny-titanic-memorial | One station (archive point wrong, 52 km) | The Society's Titanic Memorial (1913) is the Titanic Memorial Lighthouse at South Street Seaport (Wikidata, LighthouseFriends); the archive's point is 52 km north. Positions set aside: `uslhs:8835`. |
| rowlett:nydn:titanic-memorial -> us-ny-titanic-memorial | Record moved (record misfiled) | Rowlett's Titanic Memorial (built 1913, light shown 1913-1967) is the Manhattan memorial; its truncated ARLHS number 'USA-122' (Wikidata: USA1229) had filed it with two unrelated upstate lights. |
| us-oh-ashtabula-west-pier-range-rear -> us-oh-ashtabula-west-pier-range-front | One station (range, archive point wrong) | The Society's Ashtabula West Pier Range Rear (1876) is the rear of the range whose front it also lists; the archive's point for the rear is 5.9 km inland. One station with a front and a rear. Positions set aside: `uslhs:7419`. |
| us-oh-cunningham-creek-2 -> us-oh-cunningham-creek | One station (archive point wrong, 93 km) | The Society's Cunningham Creek (1835-1847) is LighthouseFriends' lost Cunningham Creek light at Madison on Lake Erie; the archive's point is 93 km south (41.01 N for 41.85 N). Positions set aside: `uslhs:8873`. |
| us-or-yaquina-bay-2 -> us-or-yaquina-bay | One station (archive point wrong, 46 km) | The Society's Yaquina Bay (1871, discontinued 1874) is Yaquina Bay Light at Newport; the archive's point is 46 km north. Positions set aside: `uslhs:3467`. |
| us-sc-bloody-point-range-rear -> us-sc-bloody-point-range | One station (range, 680 m) | The Society's Bloody Point Range Rear (1883-1899) is the rear of the Bloody Point Range (Wikidata's item for the range, LighthouseFriends' and the Society's front); one station with a front and a rear. |
| us-sc-bulls-bay-2 -> us-sc-bulls-bay | One station (archive point wrong, 18 km) | The Society's Bulls Bay (1852-1913) is Bulls Bay Light (Wikidata, LighthouseFriends); the archive's point is 18 km north, inland. Positions set aside: `uslhs:8911`. |
| us-sc-fort-ripley-shoal-2 -> us-sc-fort-ripley-shoal | One station (archive point wrong, 80 km) | The Society's Fort Ripley Shoal (1878-1932) is Fort Ripley Shoal Light in Charleston Harbor; the archive's point is 80 km inland. Positions set aside: `uslhs:8915`. |
| us-sc-hilton-head-range-front -> us-sc-hilton-head-range-rear | One station (range, 1.7 km) | The Society's Hilton Head Range Front (1880-1932, lost) is the front of the range whose rear is the Leamington tower; one station with a front and a rear. Positions set aside: `uslhs:8917`. |
| us-sc-morris-island-range-rear -> us-sc-morris-island-range-front | One station (range, 3.7 km) | The Society's Morris Island Range Front and Rear (1902) are the two lights of one range, kept apart from the Morris Island lighthouse (the archive lists the range separately). |
| uslhs:3515 -> us-sc-morris-island | Record moved (record misfiled) | The Society's 'Morris Island' (other name Old Charleston; tower 1876, light 1768-1962) is Morris Island Light; the archive's point is the Sullivan's Island light 7 km north, so the first build made it a second tower of us-sc-charleston. Positions set aside: `uslhs:3515`. |
| us-tx-galveston-jetty-2 -> us-tx-galveston-jetty | One station (archive point wrong, 65 km) | Galveston Jetty light (1918-1973): LighthouseFriends places it on the south jetty at Galveston; the Society's point is 65 km inland, south of Houston. One light; the plain id is kept. Positions set aside: `uslhs:3516`. |
| us-tx-sabine-bank-2 -> us-tx-sabine-bank | One station (shore point, 68 km) | LighthouseFriends' Sabine Bank is the 1906 caisson light on Sabine Bank, 16 miles off the Sabine River; its point is on shore at Port Arthur, 68 km from the bank (Wikidata), and is set aside. Positions set aside: `lighthousefriends:150`. |
| us-va-hog-island-2 -> us-va-hog-island | One station (lens display point, 82 km) | LighthouseFriends' and Rowlett's Hog Island (tower of 1896, discontinued 1948) is Hog Island Light on the Eastern Shore (place Machipongo); the point LighthouseFriends gives is Portsmouth, where the light's lens is displayed (Rowlett: 'lens'), and is set aside. Positions set aside: `lighthousefriends:1894`. |
| us-va-wolf-trap-2 -> us-va-wolf-trap | One station (register point wrong, 18 km) | The National Register's Wolf Trap Light Station (02001434) is Wolf Trap Light, which Wikidata tags with that number; the batch point is 18 km south. Positions set aside: `nrhp:02001434`. |
| us-vt-colchester-reef-2 -> us-vt-colchester-reef | One station (archive point wrong, 96 km) | The Society's Colchester Reef (1871-1933) is Colchester Reef Light, now at the Shelburne Museum; the archive's longitude (72.05 W) is 96 km east of Lake Champlain. Positions set aside: `uslhs:3534`. |
| us-wa-gig-harbor-2 -> us-wa-gig-harbor | One station (archive point wrong, 38 km) | The Society's Gig Harbor is the Gig Harbor light (OpenStreetMap, LighthouseFriends, Light List 6-17221), the only light of that name; the archive's point is 38 km north-west. Positions set aside: `uslhs:8982`. |
| us-wi-racine-north-breakwater-2 -> us-wi-racine-north-breakwater | One station (archive point wrong, 69 km) | The Society's 'RACINE North Breakwater' (1872-1987) is Racine North Breakwater Light; the archive's point is 69 km inland. Positions set aside: `uslhs:3580`. |
| us-wi-racine-harbor -> us-wi-racine-harbor-lighthouse-and-life-saving | One station (archive point wrong, 69 km) | The Society's Racine Harbor (1866) is the Racine Harbor (Root River) lighthouse of 1866; the archive gives it the same inland point as its Racine North Breakwater, 69 km off. Positions set aside: `uslhs:35833`. |
| us-fl-fort-barrancas -> us-fl-fort-barrancas-range | One station (range, 720 m) | LighthouseFriends' Fort Barrancas page is the history of the Fort Barrancas range lights (front and rear), which the Society lists as the range; one station. Whether the range's rear is the Pensacola tower stays open. |
| us-ga-elba-island -> us-ga-elba-island-range | One station (same light, 860 m) | The Society's Elba Island (light station, 1905) and LighthouseFriends' Elba Island Range are the Savannah River lights on Elba Island, which LighthouseFriends describes as a range of two lights; no source has another light on the island. Positions set aside: `uslhs:8411`. |
| us-ga-wolf-island -> us-ga-wolf-island-range | One station (range, 570 m) | LighthouseFriends' Wolf Island page describes the Wolf Island beacons as a range (1822 beacon, 1868 rear range light), the range the Society lists with its front and rear; one station. |
| us-mi-ecorse -> us-mi-ecorse-range | One station (range, 820 m) | LighthouseFriends' Ecorse (lost) and the Society's Ecorse Range front and rear (1895) are the Ecorse range lights on the Detroit River; one station. |
| us-nc-brant-island -> us-nc-brant-island-shoal | One station (same light, 340 m) | LighthouseFriends' Brant Island (lost) is the Brant Island Shoal screwpile light in Pamlico Sound that Rowlett, the Society and the Light List (2-32650) call Brant Island Shoal; 340 m apart. |
| us-hi-lahaina-harbor -> us-hi-lahaina | One station (same light, 345 m) | The Society's and the passport list's Lahaina Harbor is Lahaina Light (Wikidata, LighthouseFriends, Light List 6-28460); 345 m apart, rounded. Positions set aside: `uslhs:18617`. |
| us-tx-brazos-santiago-pass-tx-new -> us-tx-brazos-santiago | One station (same light, 350 m) | The Society's 'Brazos Santiago Pass TX (New)' and 'Brazos Santiago Pass' are LighthouseFriends' Brazos Santiago at Port Isabel, 350 m apart. |
| us-nc-southwest-point -> us-nc-southwest-point-royal-shoal | One station (same light, 365 m) | The Society's Southwest Point (other name Royal Shoal) is LighthouseFriends' Southwest Point Royal Shoal, 365 m apart. |
| us-wa-semiahmoo -> us-wa-semiahmoo-harbor | One station (same light, 430 m) | LighthouseFriends' Semiahmoo (lost) is Semiahmoo Harbor Light (Wikidata, the Society, Light List 6-19920 at the site); 430 m apart. |
| us-mi-grassy-island-south-channel-range -> us-mi-grassy-island | One station (range, 860 m) | LighthouseFriends' 'Grassy Island South Range' page (in this station with Wikidata's Grassy Island Light) is the history of the Grassy Island light station and its south range; the Society's South Channel Range front and rear are that range. |
| us-mi-grassy-island-north-channel-range-rear -> us-mi-grassy-island-north-range | One station (range, 930 m) | The Society's Grassy Island North Channel Range Rear is the rear of LighthouseFriends' Grassy Island North Range. |
| uslhs:9657 -> us-mi-grassy-island-north-range | Record moved (record misfiled) | The Society's Grassy Island North Channel Range Front belongs with the north range, not with the Grassy Island light station's south range. |
| us-mi-grosse-isle-south-channel-range-front -> us-mi-grosse-isle-south-range | One station (range, 520 m) | The Grosse Ile South Channel Range: the Light List's and the Society's front (7-7165) joins the station that holds the rear (LighthouseFriends' Grosse Isle South Range, Rowlett, Light List 7-7170). |
| us-il-waukegan-harbor-pierhead -> us-il-waukegan-harbor | One station (same light, 560 m) | The Society's Waukegan Harbor Pierhead is the Waukegan Harbor light on the north pierhead (the station holds the Light List's Waukegan North Pierhead Light); no other Waukegan station exists in the archive. Positions set aside: `uslhs:8428`. |
| us-nc-bald-head-old-baldy -> us-nc-bald-head | One station (same light, 600 m) | The Society's 'Bald Head "Old Baldy"' is Bald Head Lighthouse (Old Baldy), 600 m off by its rounded point. |
| us-md-fishing-battery-island -> us-md-fishing-battery | One station (same light, 610 m) | The Society's Fishing Battery Island is Fishing Battery Light, 610 m off by its rounded point. |
| us-ca-ano-nuevo-island -> us-ca-ano-nuevo | One station (same light, 650 m) | The Society's Ano Nuevo Island is the Año Nuevo light station on the island, 650 m off by its rounded point. |
| us-ny-elm-tree-range-front -> us-ny-elm-tree-beacon | One station (same light, 730 m) | The Society's Elm Tree Range Front is Elm Tree Beacon Light, the front of the Swash Channel Range (Rowlett: 'Elm Tree (Swash Channel Range Front)'). Positions set aside: `uslhs:8804`. |
| us-ny-buffalo-1818 -> us-ny-buffalo-main | One station (successive tower, 350 m) | The Society's 'Buffalo 1818' is the first Buffalo lighthouse (1818), replaced in 1833 by the Buffalo Main tower at the same river mouth; successive towers of one station (DESIGN 3.2). |
| us-mi-menominee -> us-mi-menominee-pier | One station (same light, 1.6 km) | The Society's Menominee (other name North Pier, active) is Menominee Pier Light; the archive's point is rounded to five minutes. Positions set aside: `uslhs:2996`. |
| us-in-michigan-city-old -> us-in-old-michigan-city | One station (archive point wrong, 72 km) | The Society's Michigan City (Old) is Old Michigan City Light; the archive's latitude 41.073 is a slip for 41.723. Positions set aside: `uslhs:2805`. |
| us-mi-south-fox-island-new -> us-mi-south-fox-island | One station (archive point wrong, 53 km) | The Society's South Fox Island New is the 1934 skeleton tower of South Fox Island Light, which the station already holds through OpenStreetMap; the archive's point is 53 km away. Positions set aside: `uslhs:9235`. |
| us-oh-vermilion-pierhead -> us-oh-vermilion | One station (same light, 2.3 km) | The Society's Vermilion Pierhead (lost) is the 1877 Vermilion light whose replica stands at the museum and carries the light today (the station); the archive's point is rounded. |
| us-ga-sapelo-island-range-front -> us-ga-sapelo-island | One station (range, 205 m) | Sapelo Island: about 1877 the 1820 tower was relit as the rear light of a range whose front was the iron beacon 205 m away (Wikidata's 'Sapelo Island Range Front Light', LighthouseFriends 327; both discontinued 1898-99). The Society files the lighthouse itself as 'Sapelo Island Range Rear'. DESIGN 3.2: one station with two structures, kept under the storied lighthouse id; the range front's story was held back from publishing. The Society's rear record describes the station as a whole (its rounded point would have made a second tower). Positions set aside: `uslhs:2793`. |
| us-mn-two-harbors-east-breakwater -> us-mn-two-harbors-breakwater | One station (archive point wrong, 34 km) | The Society's Two Harbors East Breakwater (1895) is the light that Rowlett ('Two Harbors East Breakwater'), the Light List (7-16505) and LighthouseFriends 268 place on the breakwater at Two Harbors; the archive's point is near Duluth, 34 km away. Positions set aside: `uslhs:9219`. |
| us-ca-long-beach-harbor -> us-ca-long-beach | One station (archive point wrong, 55 km) | The Society's Long Beach Harbor (1949) is the 1949 'Robot Light' on the Long Beach breakwater, LighthouseFriends' 'Long Beach Harbor'; the archive's point is 55 km north, inland. Positions set aside: `uslhs:8375`. |
| us-fl-gasparilla-island-rear-range -> us-fl-boca-grande | One station (archive point wrong, 58 km) | The Society's Gasparilla Island Rear Range (active) is the Boca Grande entrance rear range light at the north end of Gasparilla Island, which the station already holds (Wikidata, Light List 3-1310); the archive's point is 58 km north. Positions set aside: `uslhs:7610`. |
| us-md-lazaretto-point-replica -> us-md-lazaretto-point | One station (archive point wrong, 38 km) | The Society's Lazaretto Point (Replica) (1985) is the replica that OpenStreetMap, Wikidata and LighthouseFriends ('Lazaretto Point (Replica)') place at Baltimore; the archive's point is 38 km west. Positions set aside: `uslhs:23261`. |
| us-mi-frankfort-south-pierhead -> us-mi-frankfort | One station (archive point wrong, 49 km) | The Society's Frankfort South Pierhead is Frankfort's first light, on the south pier from 1873 (LighthouseFriends 198, whose page is the station's history); the archive's point is 49 km north. Positions set aside: `uslhs:8505`. |
| us-mi-grosse-isle-north-channel-range-rear -> us-mi-grosse-ile-north-channel-range-front | One station (range, 480 m) | The Society's Grosse Isle North Channel Range Rear (1894) is the rear of the range whose front the station holds (OpenStreetMap, LighthouseFriends 'Grosse Ile North Range', Rowlett, the Light List, the Society's front). |
| us-nc-prices-creek-range-front -> us-nc-price-creek | One station (archive point wrong, 92 km) | The Society's Prices Creek Range Front (1850-1867) is Price's Creek Light, the front range light that Wikidata, OpenStreetMap, LighthouseFriends and Rowlett ('Price's Creek Range Front') place at Southport; the archive's point is 92 km inland. Positions set aside: `uslhs:8863`. |
| us-ny-barbers-point-ny -> us-ny-barbers-point | One station (archive point wrong, 24 km) | The Society's Barber's Point NY (1873-1935) is Barber's Point Light at Westport on Lake Champlain; the archive's point is 24 km inland. Positions set aside: `uslhs:3391`. |
| us-ri-block-island -> us-ri-block-island-north | One station (archive point wrong, 29 km) | The Society's Block Island (other name North; tower of 1867, station of 1829) is Block Island North Light; the archive's rounded point (41.23 N, 71.23 W) is 29 km from it. Positions set aside: `uslhs:3488`. |
| us-sc-daufuskie-island-range -> us-sc-haig-point-range | One station (same range, 1 km) | The Society's Daufuskie Island Range front and rear (1873) are the Haig Point range on Daufuskie Island (LighthouseFriends 'Daufuskie Island (Haig Point)', Wikidata's front, rear and pair); the archive's points are 1 km off and are set aside so the storied station gains no extra towers. Positions set aside: `uslhs:15281`, `uslhs:8914`. |

### Kept apart, and pairs left for the owner

| Pair | Decision | Why |
|---|---|---|
| us-de-liston-range-front / us-de-liston-range-rear | Left for the owner | One range (DESIGN 3.2: one station), but both stations have a published story: left for the owner. |
| us-md-craighill-channel-lower-range-front / us-md-craighill-channel-lower-range-rear | Left for the owner | One range, 4.5 km between the towers, each with its own NRHP listing; both stations have a published story: left for the owner. |
| us-md-craighill-channel-upper-range-front / us-md-craighill-channel-upper-range-rear | Left for the owner | One range ('Cut-Off Channel Range'), 2.5 km between the towers; both stations have a published story: left for the owner. |
| us-mn-duluth-south-breakwater-inner / us-mn-duluth-south-breakwater-outer | Two stations | The Duluth range (NRHP: 'Duluth South Breakwater Inner (Duluth Range Rear)'); both stations have a published story: left for the owner, with the Society-only us-mn-duluth-south-breakwater-range whose front and rear records belong to them. |
| us-ny-new-dorp / us-ny-elm-tree-beacon | Two stations | New Dorp Light (rear) and Elm Tree Beacon (front) were the Swash Channel Range, 2 km apart, each with its own name and NRHP history; kept as two stations (left for the owner: DESIGN 3.2 would make a range one station). |
| us-ma-newburyport-harbor / us-ma-newburyport-harbor-range | Two stations | Newburyport Harbor Light on Plum Island and the Newburyport range lights in town, 3.8 km apart. |
| us-md-thomas-point-shoal / us-md-thomas-point | Two stations | Thomas Point (1825, on the point) and Thomas Point Shoal (1875 screwpile), 800 m apart, two names. |
| us-md-greenbury-point / us-md-greenbury-point-shoal | Two stations | Greenbury Point (1848, on the point) and Greenbury Point Shoal (1891 screwpile): separate LighthouseFriends pages. |
| us-nc-pamlico-point / us-nc-pamlico-point-shoal | Two stations | Pamlico Point and Pamlico Point Shoal: two lights in the archive. |
| us-tx-red-fish-bar / us-tx-red-fish-bar-cut | Two stations | Red Fish Bar and Red Fish Bar Cut: separate LighthouseFriends pages. |
| us-nj-cross-ledge / us-nj-elbow-of-cross-ledge | Two stations | Cross Ledge and Elbow of Cross Ledge: two lights, 4 km apart. |
| us-ca-pigeon-point / us-ca-pigeon-point-2 | Two stations | us-ca-pigeon-point-2 is an OpenStreetMap-only 'Pigeon Point Lighthouse' at Lake Havasu, 790 km away: a scale copy (listed for the replica review). |
| us-ca-table-bluff / us-ca-table-bluff-3 | Two stations | us-ca-table-bluff-3 is an OpenStreetMap-only copy at Lake Havasu, 1,100 km away (listed for the replica review). |
| us-md-choptank-river / us-md-choptank-river-2 | Two stations | The lost 1871 light and the 2012 replica at Cambridge, 13 km apart (replica link listed for review). |
| us-nc-roanoke-marshes / us-nc-roanoke-marshes-2 | Two stations | The 2004 replica at Manteo and the lost 1877 screwpile, 11 km apart. |
| us-nc-roanoke-river / us-nc-roanoke-river-2 | Two stations | The 1887 light (now at Edenton) and the 2003 replica at Plymouth. |
| us-mi-round-island / us-mi-round-island-2 | Two stations | Round Island (St. Marys River, 1892), Round Island (Mackinac, 1895) and Round Island near Brimley (lost): three lights 53-68 km apart. |
| us-ny-stony-point / us-ny-stony-point-2 | Two stations | Stony Point (Henderson, Lake Ontario) and Stony Point (Hudson River): 346 km apart. |
| us-pa-airport-beacon / us-pa-airport-beacon-2 | Two stations | Two OpenStreetMap airport beacons 37 km apart; neither is a light station (listed as other problems). |
| us-mi-copper-harbor / us-mi-copper-harbor-range | Two stations | The lighthouse and the range lights, 770 m apart: separate aids. |
| us-mi-eagle-harbor / us-mi-eagle-harbor-range | Two stations | The lighthouse and the 1877 range lights, 630 m apart: separate aids. |
| us-me-doubling-point / us-me-doubling-point-range | Two stations | Doubling Point Light and the Kennebec River range lights, 890 m apart: separate aids, separate NRHP listings. |
| us-nc-oak-island / us-nc-oak-island-range | Two stations | The 1958 lighthouse and the range lights of 1849-1894, 690 m apart. |
| us-mi-muskegon-south-pierhead / us-mi-muskegon-south-pierhead-range-front | Two stations | The 1903 pierhead light and the Society's 1890 range front, 460 m apart: the archive lists them as separate places; not settled. |
| us-mi-windmill-point / us-mi-windmill-point-range-front-new | Two stations | Windmill Point Light and the Society's range front, 540 m apart. |
| us-ma-broad-sound-channel-range / us-ma-broad-sound-channel-inner-range | Two stations | The Society's Broad Sound Channel Range and the Inner Range, 480 m apart: which range the archive means is not settled; left as two. |
| us-fl-carysfort-reef / us-fl-carysfort-reef-2; us-la-south-pass-range / us-la-south-pass; us-la-trinity-shoal / us-la-trinity-shoal-2; us-ma-boston / us-ma-boston-2; us-mi-grays-reef / us-mi-grays-reef-2; us-mi-lake-st-clair / us-mi-lake-st-clair-2; us-mi-north-manitou-shoal / us-mi-north-manitou-shoal-2; us-nc-diamond-shoal / us-nc-diamond-shoal-2; us-nc-frying-pan-shoals / us-nc-frying-pan-shoals-2; us-ny-fire-island / us-ny-fire-island-2; us-ri-brenton-reef / us-ri-brenton-reef-2; us-ri-hog-island-shoal / us-ri-hog-island-shoal-2; us-sc-charleston / us-sc-charleston-2; us-va-cape-charles / us-va-cape-charles-2; us-wi-peshtigo-reef / us-wi-peshtigo-reef-2; us-nj-barnegat-2 / us-nj-barnegat | Two stations | A lightship station and the light that later marked the same place are different kinds of station (DESIGN 3.4); never one. |

The other groups of the name scan are different places that share a name (Green Island, Long Point, Round Island,
Stony Point, Pointe aux Pins...) or a light beside the life-saving station of the same name; they are not listed.

### Names

| Station | Name shown | Why |
|---|---|---|
| us-ga-sapelo-island | Sapelo Island Light | With the range front joined, the station holds a front and a rear; it keeps the lighthouse's name, as its story does. |
| us-me-moose-peak-light-shalens-new-home | Moose Peak Light | Wikidata's label 'Moose Peak Light Shalen’s New Home' is not the light's name; OpenStreetMap and the Light List (1-1390) call it Moose Peak Light, LighthouseFriends, Rowlett, the Society and the passport list Moose Peak. The id keeps the first build's slug. |
| us-va-keepers-house | Old Point Comfort Light | OpenStreetMap's name for the keeper's house ('Keeper's House') won the station's name; the light is Old Point Comfort Light (Wikidata, NRHP 73002212, LighthouseFriends, Rowlett, the Society). |
| us-ny-old-orchard-shoal | Old Orchard Shoal Light | The NRHP's inverted index form 'Orchard Shoal Light Station, Old' won the name; Wikidata, OpenStreetMap and the Light List call it Old Orchard Shoal Light. |
| us-mi-old-presque-isle | Old Presque Isle Light | Both Presque Isle stations showed 'Presque Isle'; the 1840 tower is Old Presque Isle Light (Wikidata, OpenStreetMap, NRHP), its successor New Presque Isle Light. |
| us-mi-new-presque-isle | New Presque Isle Light | Both Presque Isle stations showed 'Presque Isle'; the 1870 tower is New Presque Isle Light (Wikidata, OpenStreetMap). |
| us-wi-racine-harbor-lighthouse-and-life-saving | Racine Harbor Lighthouse | The NRHP district's name 'Racine Harbor Lighthouse and Life Saving Station' was the lighthouse's display name; LighthouseFriends calls it Racine Harbor, and the life-saving station of the district has its own station. |
| us-ma-newburyport-harbor-range | Newburyport Harbor Range Lights | The station holds both lights of the range (Wikidata's, OpenStreetMap's, LighthouseFriends' and Rowlett's front and rear); the name 'Newburyport Harbor Range Front' named only one of them. |
| us-fl-st-joseph-point | St. Joseph Point Light | Rowlett's name for the modern rear aid ('St. Joseph Bay (Beacon Hill) Range Rear') won the station's name; the station is St. Joseph Point Light and its range (Wikidata, the Society). |
| us-fl-big-marco-pass-and-rear-range | Big Marco Pass Range Lights | The Society's entry title 'Big Marco Pass And Rear Range' is a fragment; the record is the Big Marco Pass front and rear range. |
| us-mi-presque-isle-rear-range | Presque Isle Range Lights | The station now holds the front and the rear of the Presque Isle Harbor Range; LighthouseFriends and the passport list call it Presque Isle Range. |
| us-oh-ashtabula-west-pier-range-front | Ashtabula West Pier Range Lights | The station now holds the front and the rear of the range. |
| us-sc-morris-island-range-front | Morris Island Range Lights | The station now holds the front and the rear of the range. |
| us-il-light-2 | Great Lakes Light 2 | OpenStreetMap's bare 'Light 2'; the Light List calls the two aids at the Great Lakes harbor Great Lakes Light 1 and Light 2 (7-20290, 7-20285). |
| us-nc-brant-island-shoal | Brant Island Shoal Light | With LighthouseFriends' 'Brant Island' joined, its name won; the light is Brant Island Shoal (Rowlett, the Society, the Light List's 'Brant Island Shoal Light BI'). |
| us-de-reedy-island-range-rear-2 | Old Reedy Island Light | With the Taylors Bridge rear's record moved to the range, the station is the old light on Reedy Island (LighthouseFriends 'Old Reedy Island', the Light List's 'Old Reedy Island Light', the Society's 'Reedy Island Old'). |

### Statuses

| Station | Status | Why |
|---|---|---|
| us-hi-lahaina | active | In the Coast Guard's Light List (6-28460, Lahaina Light); the Society's archive, whose record joined this station in the duplicate audit, calls the light inactive. |
| us-fl-cape-st-george | active | The 1852 tower on Cape St. George toppled into the Gulf on 21 October 2005; it was rebuilt in 2007-08 in the town of St. George Island, 20 km north-east, and shows a light again (Light List 4-75). |
| us-ca-cape-mendocino | relocated | The 1868 tower was moved in 1998-99 from the cape to Mal Coombs Park, Shelter Cove, 54 km south; a modern light marked the cape until 2013. |
| us-ca-table-bluff | relocated | The 1892 lighthouse was cut in two and moved from Table Bluff to Woodley Island Marina, Eureka, in 1987; the light was discontinued in 1961. |
| us-de-mispillion | relocated | The 1873 lighthouse at the mouth of the Mispillion River was moved to Lewes after the 2002 fire; the light ended in 1929. |
| us-ma-old-harbor-u-s-life-saving-station | relocated | Built in 1897 on Nauset Beach, Chatham; floated by barge to Race Point, Provincetown, in 1977. |
| us-mi-frying-pan-island | relocated | The 1882 tower was moved from Frying Pan Island, off De Tour, to the Coast Guard station at Sault Ste. Marie; a modern light (Frying Pan Island Light 7) marks the island. |
| us-va-hog-island | lost (was unknown) | Discontinued in 1948; LighthouseFriends (destroyed) and Rowlett, a station of their own until this audit, join it, and the Society's archive lists it as lost. |

### Hidden

| Station | Reason | Why |
|---|---|---|
| us-ny-titanic-memorial-2 | A duplicate listing: Rowlett's Titanic Memorial is us-ny-titanic-memorial and the Strawberry Island Lower Cut Range Rear is part of us-ny-strawberry-island-lower-cut-range; what is left is the Society's record of that rear (its point is in Lake Ontario) and Rowlett's 'Shoal Point' (upstate New York, 1890), filed here by a truncated ARLHS number | The station was built from four records that a truncated ARLHS number ('USA-122' in Rowlett's directory) tied together: Rowlett's Titanic Memorial, Rowlett's Shoal Point and the Strawberry Island Lower Cut Range Rear of Rowlett and the Society, under the name Titanic Memorial at a point in Lake Ontario. The Titanic and Strawberry records go to their stations; the station cannot be retired into one of them (the merge retires a station into one other station only, and a station needs a positioned record), so it is hidden with the two records left. |
| us-pa-airport-beacon | An airport rotating beacon, not an aid to navigation on the water | OpenStreetMap's 'Airport Beacon' (man_made=lighthouse) near Franklin, PA, inland; OpenStreetMap only; no light list, register or lighthouse directory lists a light within 3 km. |
| us-pa-airport-beacon-2 | An airport rotating beacon, not an aid to navigation on the water | OpenStreetMap's second 'Airport Beacon' in western Pennsylvania, inland; OpenStreetMap only; no light list, register or lighthouse directory lists a light within 3 km. |
| us-il-airport-beacon | An airport rotating beacon, not an aid to navigation on the water | OpenStreetMap's 'Airport Beacon' at Springfield, IL, inland; OpenStreetMap only; no light list, register or lighthouse directory lists a light within 3 km. |
| us-wi-airport-beacon | An airport rotating beacon, not an aid to navigation on the water | OpenStreetMap's 'Airport Beacon' at Appleton, WI, inland; OpenStreetMap only; no light list, register or lighthouse directory lists a light within 3 km. |
| us-me-piafb-beacon | The aerodrome beacon of the former Presque Isle Air Force Base, not an aid to navigation on the water | OpenStreetMap's 'PIAFB Beacon', inland at Presque Isle, ME; OpenStreetMap only; no light list, register or lighthouse directory lists a light within 3 km. |
| us-mi-iwd-beacon | The aerodrome beacon of Gogebic-Iron County Airport (IWD), not an aid to navigation on the water | OpenStreetMap's 'IWD Beacon', inland near Ironwood, MI; OpenStreetMap only; no light list, register or lighthouse directory lists a light within 3 km. |
| us-ca-edwards-afb-aerodrome-beacon | The aerodrome beacon of Edwards Air Force Base, not an aid to navigation | OpenStreetMap's 'Edwards AFB Aerodrome Beacon' in the Mojave Desert; OpenStreetMap only; no light list, register or lighthouse directory lists a light within 3 km. |
| us-nm-reredos-of-our-lady-of | A church altar screen in Santa Fe (Reredos of Our Lady of Light), not a lighthouse | The National Register listing 70000411 is the stone altar screen of the chapel of Our Lady of Light; the register record was read as a lighthouse by its name. |
| us-tx-light-house | A building named 'Light House' in San Antonio, not a lighthouse | The National Register listing 11000131 'Light House' is in San Antonio, 200 km from the coast; no light list or lighthouse directory lists it. |
| us-ct-the | A building called 'The Lighthouse' in Bridgeport, not a light | OpenStreetMap's building 'The Lighthouse' (man_made=lighthouse, building=yes) is 1 km from Tongue Point Light, which is its own station; nothing lists a light at the building. |
| us-nc-kenly-95 | A lighthouse-shaped tower at an inland travel stop (Kenly 95), not an aid to navigation | OpenStreetMap's 'Kenly 95' is at the Kenly 95 travel plaza on Interstate 95, 140 km from the coast; OpenStreetMap only; no light list, register or lighthouse directory lists a light within 3 km. |
| us-mi-n41-44-423-w83-27-167-6-deep | An OpenStreetMap point named only by its coordinates ('6' Deep'), not a light station | OpenStreetMap's element is named 'N41°44.423 W83°27.167 (6' Deep)' in western Lake Erie; no light list, chart or lighthouse directory has a light there. |
| us-fl-unmanned-reef-lights-of-the-florida-keys | A group article about several reef lights, not one station | Wikidata's item is the Wikipedia list article 'Unmanned reef lights of the Florida Keys' (the minor reef lights as a group), with one point for all of them; the lights it covers that have a history are stations of their own. |

### Scale copies

| Copy | Copies | Why |
|---|---|---|
| us-ca-pigeon-point-2 | us-ca-pigeon-point | OpenStreetMap's 'Pigeon Point Lighthouse' at Lake Havasu City, among the town's scale copies of named lights (DESIGN 3.2), 790 km from Pigeon Point. |
| us-ca-table-bluff-3 | us-ca-table-bluff | OpenStreetMap's 'Table Bluff Lighthouse' at Lake Havasu City, one of the town's scale copies of named lights, 1,100 km from Table Bluff. |
| us-md-choptank-river-2 | us-md-choptank-river | The 2012 Choptank River Lighthouse at Cambridge: LighthouseFriends 'Choptank River (Replica)', Rowlett and the Society list it as a replica of the 1871 screwpile. |
| us-nc-roanoke-marshes | us-nc-roanoke-marshes-2 | The 2004 lighthouse at Manteo: LighthouseFriends, Rowlett and the Society list it as the Roanoke Marshes replica; the 1877 screwpile is us-nc-roanoke-marshes-2. |
| us-nc-roanoke-river-2 | us-nc-roanoke-river | The 2003 lighthouse at Plymouth: LighthouseFriends, Rowlett and the Society list it as the Roanoke River replica; the 1887 lighthouse (now at Edenton) is us-nc-roanoke-river. |

### Held story ids

- `us-fl-cape-saint-george` is retired into `us-fl-cape-st-george`, whose story covers the rebuilt tower.
- `us-ga-sapelo-island-range-front` is retired into `us-ga-sapelo-island` (one station: the 1820 tower was the range's
  rear light); its held-back story is not to be published under the retired id.
- `us-me-moose-peak-light-shalens-new-home` keeps its id; its name is now Moose Peak Light.
- `us-sc-bloody-point-range` keeps its id and now holds the range's rear.
- `us-la-south-pass-range` keeps its id: the South Pass lightship station (`us-la-south-pass`) is a different kind
  of station.

### What the audit changed

Local merge of 2026-10-28 on main after story batch H7 (`FRESNEL_RAW_ROOT` = the main checkout's cache): **1,552 US
stations shown** (1,653 before); 87 US ids retired with `merged_into` by this audit (115 in all; no file deleted), 14
hidden (the Titanic Memorial duplicate and 13 clear non-lights), 5 scale copies linked to their originals. Five
stations are now `relocated` (Cape Mendocino, Table Bluff, Mispillion, Old Harbor Life-Saving Station, Frying Pan
Island). A second run writes nothing.

`pipeline/record_joins.py` before and after the audit: records sent to a station (`RECORD_JOINS`) 119 -> 237, positions
set aside (`NO_POSITION`) 23 -> 81, names (`NAME_PICKS`) 9 -> 25, statuses (`STATUS_PICKS`) 17 -> 25 (Hog Island's
replaced), hidden (`HIDE`) 19 -> 33, scale copies (`REPLICA_OF`) 30 -> 35, pairs found to be two (`NOT_DUPLICATES`) 55 ->
74 (the 19 new ones Canadian). The report's possible-duplicate, close-namesake and decorative-suspect lists are empty for
both countries.

`pipeline/build_people.py` was run after the merge: the Society's rosters of the retired ids moved to the stations that
hold their records (generated files; no person file changed).

Code: a station retired into one that a later review retires as well now follows it (`merge.py`, test
`test_an_id_retired_into_a_station_that_is_retired_later_follows_it`): `ca-pe-northport-range-2` had been retired into
`ca-pe-former-northport-back-range`, which this audit retires into `ca-pe-northport-range`.

## Left open

- **Fort Barrancas Range and Pensacola Light, Tybee Island Range and the Tybee lighthouse.** The Light List and the archive suggest the rear light of each range is the lighthouse itself; the archive's years do not match, so the range stays a station of its own beside the lighthouse (both are in the table of stations kept apart). A source that states it settles it.
- **USLHS lightship and life-saving stations.** 131 of 134 lightship stations and all 67 life-saving stations have no position in the archive; those that match a station by name join it, the rest are leads in `not_shown` (the Lightship Station Index is the next source for them).
- **Canada.** 3 possible duplicate pairs and 28 close namesakes of the Canadian build remain in the lists; they are `agent/sources-ca`'s to decide.
- **Two Rivers (WI)** is decided on the sources' years and map points (the lighthouse stands 1.2 km from the pier it served); no extract states the move. Worth a line of research before the story is written.

