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

## Left open

- **Fort Barrancas Range and Pensacola Light, Tybee Island Range and the Tybee lighthouse.** The Light List and the archive suggest the rear light of each range is the lighthouse itself; the archive's years do not match, so the range stays a station of its own beside the lighthouse (both are in the table of stations kept apart). A source that states it settles it.
- **USLHS lightship and life-saving stations.** 131 of 134 lightship stations and all 67 life-saving stations have no position in the archive; those that match a station by name join it, the rest are leads in `not_shown` (the Lightship Station Index is the next source for them).
- **Canada.** 3 possible duplicate pairs and 28 close namesakes of the Canadian build remain in the lists; they are `agent/sources-ca`'s to decide.
- **Two Rivers (WI)** is decided on the sources' years and map points (the lighthouse stands 1.2 km from the pier it served); no extract states the move. Worth a line of research before the story is written.

