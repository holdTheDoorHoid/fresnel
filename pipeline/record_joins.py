"""Human decisions the merge cannot take from the data (DESIGN.md 3.9), each with its evidence in
docs/sources/review_2026-10-us.md.

RECORD_JOINS     a source record's key -> the station it belongs to: a station id (permanent) or the key of
                 any record that station holds. merge.py attaches the record there before it tries its key
                 memory, a shared register number or the position. A station all of whose records are sent
                 elsewhere this way is retired: its file stays (ids never change), hidden, with `merged_into`
                 naming the station that took its records, and the site sends its old address to the new one.
NO_POSITION      record keys whose coordinates a human has found wrong (a Wikidata item that copies another light's
                 position): the record keeps its facts and joins by RECORD_JOINS, but its position is not used.
NAME_PICKS       station id -> the name to show, where the sources' own are a typo or a misleading form.
KEEP_APART_PAIRS pairs of record keys that are two stations, though their names and positions agree: the
                 matcher never puts them in one station.
STATUS_PICKS     station id -> (status, note): a status a human has settled from evidence the sources do not
                 agree on (or that no source states); the note is shown beside it.
HIDE             station id -> reason: shown on the map no more (a decorative "lighthouse" that never served as
                 an aid to navigation, a vessel's name, a duplicate listing); the file stays.
KEEP_VISIBLE     station ids reviewed and kept, so the report's decorative-suspect list no longer names them.
NOT_DUPLICATES   pairs of station ids reviewed and found to be two stations, so the report's possible-duplicate
                 list no longer names them (twins at one site, a light and its own range light...).
REPLICA_OF       station id of a scale copy -> the station id of the light it copies (DESIGN 3.2: status `replica`,
                 related `replica_of`).
SUCCESSION       pairs (older id, newer id) of separately named successive lights (Old and New Point Loma): related
                 `succeeded_by` / `preceded_by` both ways.
"""
from __future__ import annotations












RECORD_JOINS: dict[str, str] = {}
NO_POSITION: set[str] = set()
KEEP_APART_PAIRS: set[frozenset] = set()
NAME_PICKS: dict[str, str] = {}
STATUS_PICKS: dict[str, tuple[str, str]] = {}
HIDE: dict[str, str] = {}
KEEP_VISIBLE: set[str] = set()
NOT_DUPLICATES: set[frozenset] = set()
REPLICA_OF: dict[str, str] = {}
SUCCESSION: list[tuple[str, str]] = []


def _join(target: str, *keys: str) -> None:
    for key in keys:
        assert key not in RECORD_JOINS, key
        RECORD_JOINS[key] = target


def _not_duplicates(a: str, b: str) -> None:
    NOT_DUPLICATES.add(frozenset((a, b)))


def _keep_apart(a: str, b: str) -> None:
    KEEP_APART_PAIRS.add(frozenset((a, b)))


# ---------------------------------------------------------------------------------------------
# Joins: one station, or one station's record, that belongs to another (retired ids keep their file)
# ---------------------------------------------------------------------------------------------

# us-pr-punta-borinquen-2 into us-pr-punta-borinquen (clear, 3 m)
# Wikidata has two items for Punta Borinquen: Q7260508, the 1889 Spanish tower (NRHP 81000559, abandoned
# after the 1918 earthquake, ruins 1.8 km west) and Q109232559, the 1922 tower that still shows a light
# (Light List 3-30715, HAER PR-37). Rowlett and LighthouseFriends list one station with two towers; the OSM
# way for the 1922 tower carries the 1889 item's tag, which is how the first build mixed them. One station,
# two structures; the OSM way is pinned so it lands on the 1922 tower.
_join('us-pr-punta-borinquen',
      'osm:way/1071349499',
      'wikidata:Q109232559')

# us-fl-gasperilla-island into us-fl-boca-grande (range, 17 m between pins)
# 'Gasperilla Island Lighthouse' (Wikidata, with a typo) is the Boca Grande Entrance rear range light, 1927
# skeleton tower at the north end of Gasparilla Island (LighthouseFriends 'Gasparilla Island (Boca Grande
# Entrance Rear Range)', Rowlett 'Gasparilla Island', Light List 3-1310). The station it was flagged
# against, Boca Grande, is the 1890 Port Boca Grande tower at the south end (Light List 3-1305) plus this
# rear light, which the first build had already pinned as its map position, 2.7 km from the tower. The two
# form the Boca Grande entrance range, which DESIGN 3.2 makes one station with two structures; the rear
# light joins it.
_join('us-fl-boca-grande',
      'osm:node/1584749762',
      'wikidata:Q34157194')

# us-fl-tierra-verde into us-fl-tampa-bay-watch (clear, 13 m)
# OpenStreetMap calls the 2005 lighthouse at Tampa Bay Watch's headquarters 'Tierra Verde Lighthouse';
# Wikidata calls it Tampa Bay Watch Light (ARLHS USA1335); the Society's passport list has 'Tampa Bay
# Watch'. Same point, 13 m.
_join('us-fl-tampa-bay-watch',
      'osm:way/522540102')

# us-ms-ship-island into us-ms-gulfport-harbor (clear, 4 m)
# OpenStreetMap's 'Ship Island Light' stands at Gulfport Harbor, 30.365 N, 89.090 W, the position of
# Wikidata's Gulfport Harbor Light (2011, Light List 4-10020, Rowlett: maintained by the city), and 25 km
# from Ship Island. The 2011 harbour lighthouse is modelled on the Ship Island light; the element is the
# harbour tower named for it. One structure.
_join('us-ms-gulfport-harbor',
      'osm:way/757719980')

# us-ca-point-stuart-2 into us-ca-point-stuart (clear, position copied)
# Wikidata's Point Stuart Light (1915, retired 1960) has the coordinates of Point Blunt Light (37.853,
# -122.419, the other end of Angel Island); OpenStreetMap's 'Point Stuart Lighthouse' is on the northwest
# point (37.861, -122.446), where the Light List and ENC chart the Point Stuart light. One light with a
# copied position.
_join('us-ca-point-stuart',
      'wikidata:Q44082465')

# us-nj-finns-point-rear-range into us-nj-finns-point-range (clear, 71 m)
# Two Wikidata items for the one surviving Finns Point rear range tower: Q5450597 'Finn's Point Rear Range
# Light' (NRHP 78001792) and Q14705497 'Finns Point Range Light'; both 1877, both retired 1950, 71 m apart,
# one entry in Rowlett and in LighthouseFriends. The front light is gone and is in neither source as a
# separate station.
_join('us-nj-finns-point-range',
      )

# us-nj-navesink-south into us-nj-navesink-north (twin lights, 22 m)
# RULING (DESIGN 3.2): twin lights are one station. The Navesink Twin Lights (Highlands, NJ) stood as one
# station with one set of keepers; Wikidata has one item for the station (Q6982276), one for each tower, and
# the NRHP lists them as 'Twin Lights'. The south tower joins the north station as its second structure.
_join('us-nj-navesink-north',
      'wikidata:Q80183144')

# us-ny-plum-gut into us-ny-plum-island (clear, 4 m)
# Plum Gut Lighthouse and Plum Island Light are two Wikidata items for the one lighthouse on Plum Island (it
# guards Plum Gut): same point (4 m), same Light List number 1-21090, one NRHP listing (11000014).
_join('us-ny-plum-island',
      'wikidata:Q7205317')

# us-ma-nantucket-range-rear into us-ma-nantucket-harbor-range (range, 24 m)
# The Nantucket Harbor Range is one range: a front (the Light List calls it 'Nantucket Harbor Range Front
# Light', 1-15160, Wikidata 'Nantucket Reef Range Front Light') and a rear (1-15165), both 1908; Wikidata
# also has an item for the range as a whole. DESIGN 3.2: a range is one station with a front and a rear
# structure.
_join('us-ma-nantucket-harbor-range',
      'osm:node/3445730777',
      'wikidata:Q108751326')

# us-ma-nantucket-reef-range-front into us-ma-nantucket-harbor-range (range, 93 m)
# The front half of the Nantucket Harbor Range (see the rear): Light List 1-15160, Rowlett 'Nantucket Harbor
# Range Front', 1908.
_join('us-ma-nantucket-harbor-range',
      'osm:node/3445730778',
      'wikidata:Q108751334')

# us-ma-nantucket-cliff-front-range into us-ma-nantucket-cliff-rear-range (range, 10 m)
# The Nantucket Cliff Range (1838, retired 1912): Wikidata has the front, the rear and the range as one item
# at one point; OpenStreetMap maps it as one relation; LighthouseFriends lists one 'Nantucket Cliff Range'.
# One range, two structures.
_join('us-ma-nantucket-cliff-rear-range',
      'wikidata:Q108765429')

# us-oh-perrys-memorial into us-oh-perrys-victory-and-international-peace-memorial (clear, 9 m)
# Perry's Victory and International Peace Memorial at Put-in-Bay is a monument with a navigation light on
# top (Light List 7-5670 'Perry Memorial Monument Light', ARLHS USA1317). Wikidata has an item for the
# monument and one for 'Perry's memorial lighthouse' (1915); LighthouseFriends lists 'Perry Memorial'. One
# structure; it does serve as an aid, so it stays.
_join('us-oh-perrys-victory-and-international-peace-memorial',
      'wikidata:Q81057033')

# us-mi-st-joseph-north-pier-outer into us-mi-st-joseph-north-pier-inner (pair on one pier, 109 m)
# The St. Joseph North Pier Inner and Outer Lights (1907 and 1906) are one NRHP listing (05001211), one
# Wikidata item for the pair (Q24641189), one LighthouseFriends entry ('St. Joseph Pier'). They work as a
# pair on one pier; the outer light joins the inner as the second structure.
_join('us-mi-st-joseph-north-pier-inner',
      'wikidata:Q88349781')

# us-ny-south-buffalo-north-side-2 into us-ny-south-buffalo-north-side (clear, positions copied)
# South Buffalo North Side Light (1903, inactive since 1988; NRHP 83001673) is in Buffalo Harbor at 42.835
# N, 78.868 W (Wikidata, NRHP, ENC). OpenStreetMap's node and LighthouseFriends's 'Buffalo South Entrance
# North Side' sit at 42.493 N, 79.354 W, which is Dunkirk Harbor, 55 km west; Rowlett and the Society's
# archive describe the Buffalo light. One light; the two positions are wrong.
_join('us-ny-south-buffalo-north-side',
      'lighthousefriends:907',
      'osm:node/9843815382')

# us-mi-st-clair-flats-range-front into us-mi-st-clair-flats-front-and-rear-range (range, 17 m)
# The St. Clair Flats South Channel Range: Wikidata has the front light (Q89911087), the rear (Q90016470)
# and the pair (Q7587573); OpenStreetMap has the front and rear nodes; NRHP 90000853 lists the range. The
# station with the pair already holds the rear and the OSM front; the front-only station is the same front
# light 17 m away.
_join('us-mi-st-clair-flats-front-and-rear-range',
      'wikidata:Q89911087')

# us-mi-pentwater-south-pierhead into us-mi-pentwater (successive structures, 0 m)
# Pentwater South Pierhead Light (1937) replaced the Pentwater pier light of 1873 at the same spot: Rowlett
# writes 'station established 1873', Wikidata gives the 1873 light's end as 1937, LighthouseFriends has one
# 'Pentwater Pier'. Successive towers of one station at one place (DESIGN 3.2). The North Pierhead Light
# (1997) is on the other pier and stays apart.
_join('us-mi-pentwater',
      'wikidata:Q87971112')

# us-me-winter-harbor-2 into us-me-winter-harbor (clear, position copied)
# Wikidata's 'Winter Harbor Light' (1856, retired 1933) has Pumpkin Island Light's coordinates (44.309,
# -68.743); NRHP 87002538 'Winter Harbor Light Station' and OpenStreetMap put the light at 44.362 N, 68.088
# W (Mark Island, Winter Harbor), with LighthouseFriends. One light with a copied position.
_join('us-me-winter-harbor',
      'wikidata:Q8026238')

# us-wi-baileys-harbor-directional into us-wi-baileys-harbor-range-front (successor on the same Light List
# number, 73 m)
# The Baileys Harbor Directional Light (1969-2015) is the post light that replaced the range's front light
# and carries its Light List number, 7-21228. A modern post, not a station of its own (DESIGN 1): it joins
# the range it replaced.
_join('us-wi-baileys-harbor-range-front',
      'wikidata:Q108657557')

# us-wi-baileys-harbor-range-rear into us-wi-baileys-harbor-range-front (range, 116 m)
# The Baileys Harbor range is one range, front 1869 and rear 1870, both retired 1969 and relit 2015
# (Rowlett); the Society and LighthouseFriends list it as 'Baileys Harbor Range Lights'; NRHP 89001466
# covers the pair. One station, two structures (DESIGN 3.2).
_join('us-wi-baileys-harbor-range-front',
      'osm:way/560438007',
      'wikidata:Q83856128')

# us-ak-lighthouse-ruins into us-ak-scotch-cap (ruins of the 1940 tower, 51 m)
# Scotch Cap's third tower (1940) was destroyed by the 1946 tsunami; OpenStreetMap's 'Lighthouse Ruins' are
# its remains, 51 m from the Scotch Cap Light of today. They are a structure of the Scotch Cap station, not
# a station.
_join('us-ak-scotch-cap',
      'osm:way/540628059')

# us-fl-cape-canaveral-2 into us-fl-cape-canaveral (same headland, 1.6 km)
# Cape Canaveral Light: the 1848 tower (lost, Wikidata) and the present 1868 tower 1.6 km inland (Light
# List, OSM, Rowlett, USLHS). Same name, same headland, a move inland like Cape Hatteras's: one station with
# two structures (DESIGN 3.2).
_join('us-fl-cape-canaveral',
      'osm:way/1219644136',
      'wikidata:Q5034639')

# records into us-ms-horn-island (unique name in the state, 6.5 km)
# LighthouseFriends's 'Horn Island' (destroyed) is Wikidata's Horn Island Light (1874, retired 1961);
# positions 6.5 km apart along the 22-km island; the only Horn Island light in the state.
_join('us-ms-horn-island',
      'lighthousefriends:1822')

# records into us-nc-cape-fear (clear, position copied)
# Wikidata's Cape Fear Light carries Oak Island Light's coordinates (33.893, -78.035, 4.7 km from the site).
# The station's OSM service buildings, NRHP 78001931 and LighthouseFriends all put the 1903 tower's site at
# 33.846 N, 77.967 W on Bald Head Island; LighthouseFriends and the Society's archive both say the tower is
# gone (1958). One lost lighthouse.
_join('us-nc-cape-fear',
      'lighthousefriends:350',
      'uslhs:8846')

# records into us-md-north-point-range (clear)
# LighthouseFriends's lost 'North Point' (39.196 N, 76.443 W) is the North Point Range Lights of 1822-1873
# (Wikidata); Wikidata's own point for them copies the Craighill Channel Upper Range Front Light's.
_join('us-md-north-point-range',
      'lighthousefriends:1956')

# us-ma-thacher-island-north into us-ma-cape-ann (twin lights, 228 m)
# RULING (DESIGN 3.2): twin lights are one station. Cape Ann Light Station on Thacher Island had two towers,
# the North (1771, Wikidata 'Thacher Island North Light') and the South (the one that still shows the
# light), with one set of keepers; the NRHP and the Society list 'Cape Ann Light Station / Twin Lights'. The
# north tower joins the Cape Ann station as its second structure.
_join('us-ma-cape-ann',
      'wikidata:Q62075617')

# us-mi-copper-harbor-front-range into us-mi-copper-harbor-range (range, 1.4 km)
# Copper Harbor Front Range Light (Wikidata, Light List 7-15175) and the Copper Harbor Range station (OSM
# relation with front and rear, 7-15185) are the front and the rear of one range 1.4 km apart.
_join('us-mi-copper-harbor-range',
      'wikidata:Q5168732')

# us-il-william-e-dever-crib-2 into us-il-william-e-dever-crib (unique name, 2.6 km)
# William E. Dever Crib: Wikidata (41.929, -87.599, Light List 7-20040) and OpenStreetMap with
# LighthouseFriends (41.917, -87.572) name the one crib light off Chicago 2.6 km apart; there is one Dever
# crib.
_join('us-il-william-e-dever-crib',
      'osm:node/7042993335')

# records into us-fl-cape-florida (unique name, 7.3 km)
# The Society's archive has Cape Florida at 25.659 N, 80.083 W, 7 km east of the tower on Key Biscayne
# (25.667 N, 80.156 W; Wikidata, OSM, NRHP, Light List). It is the one Cape Florida light, with a wrong
# position.
_join('us-fl-cape-florida',
      'uslhs:2768')

# records into lighthousefriends:1804 (unique name, 6.5 km)
# LighthouseFriends's Bayou Bonfouca (with the Light List's 4-11025) and the Society's Bayou Bonfouca
# (1848-1862) are the one lost light on Lake Pontchartrain; positions differ by 6.5 km.
_join('lighthousefriends:1804',
      'uslhs:8435')

# records into us-ny-ambrose (unique name, 2.9-7.8 km)
# Ambrose Light, the Texas tower of 1967-2008 (Wikidata, ARLHS USA009, Light List 1-34785): the Society's
# archive and Rowlett list the tower as gone; LighthouseFriends's 'Ambrose' is the same tower pinned 8 km
# off. The lightship that served the Ambrose station is a separate vessel record.
_join('us-ny-ambrose',
      'lighthousefriends:2415',
      'rowlett:nj:ambrose-2',
      'uslhs:8555')

# records into us-nj-tuckers-beach (same replica, 354 m)
# Wikidata's 'phare de Tucker's Beach' (1999) is the replica at Tuckerton Seaport that OpenStreetMap,
# LighthouseFriends ('Tuckers Beach (Replica)') and Rowlett's Tucker's Island entry describe; 354 m between
# the two points. The tower it copies, Tucker's Island Light (lost 1927), has no station of its own yet.
_join('us-nj-tuckers-beach',
      'lighthousefriends:858',
      'osm:node/12287471638',
      'rowlett:nj:tucker-s-island')

# records into us-md-cedar-point (unique name, 8 km)
# Cedar Point (Maryland, Chesapeake Bay): Wikidata (38.299 N, 76.368 W), LighthouseFriends (38.276 N, 76.463
# W) and the Society's archive (typed 39.299 N) name one screwpile light, lit 1896, gone.
_join('us-md-cedar-point',
      'lighthousefriends:1771',
      'uslhs:8457')

# records into us-mn-split-rock (unique name, 17 km)
# The Society's archive gives Split Rock at 47.333 N, 91.600 W; the lighthouse is at 47.200 N, 91.367 W
# (Wikidata, OSM, NRHP). One lighthouse, one wrong position.
_join('us-mn-split-rock',
      'uslhs:3357')

# us-de-baker-range-rear into us-de-baker-shoal-range-rear (unique name, 0.7 km)
# The Society's 'Baker Range Rear' (lost) and Rowlett's entry are the rear light that Wikidata,
# OpenStreetMap and LighthouseFriends call Baker Shoal Range Rear, 743 m away by the Society's rounded
# position.
_join('us-de-baker-shoal-range-rear',
      'rowlett:de:baker-range-rear-2',
      'uslhs:8387',
      'uslhs:8388')

# records into us-va-bay-creek (same replica, 13 m)
# OpenStreetMap's 'Bay Creek Lighthouse' (Cape Charles, VA) is the 2004 replica of Old Plantation Flats
# Light that LighthouseFriends ('Old Plantation Flats (Replica)') and Rowlett describe, 13 m apart. The
# replica takes the station OpenStreetMap started; the original (lost 1962) stays its own station.
_join('us-va-bay-creek',
      'lighthousefriends:1692',
      'rowlett:va:old-plantation-flats')

# records into lighthousefriends:1120 (replica separated from the original, 117 m)
# The Blakistone (Blackistone) Island replica at St. Clement's Island Museum (2008): OpenStreetMap's
# 'Blackistone Lighthouse' and the passport stamp are the replica; LighthouseFriends, the Society's archive
# and Rowlett list it as a replica. The first build had put the replica's OSM element on the 1851 original's
# station.
_join('lighthousefriends:1120',
      'osm:way/718624721',
      'uslhs_passport:stamp:md:blackistone')

# records into us-ma-newburyport-harbor-range (range, 1 m)
# Newburyport Harbor Range: the station already holds Wikidata's front and rear items, the OSM front and
# rear elements and LighthouseFriends's rear entry. LighthouseFriends's front entry (602) and Rowlett's
# front entry sit on the same front light, 1 m from it, and had started a front-only station.
_join('us-ma-newburyport-harbor-range',
      'lighthousefriends:602',
      'rowlett:ma:newburyport-harbor-range-front')

# records into us-nj-finns-point-range (unique name, 3.1 km)
# The Society's archive has two records for the Finns Point range (a 'Range Lights' entry, inactive,
# 1877-1950) at the rounded point 39.589 N, 75.537 W, 3 km from the rear tower: they are the range of the
# Finns Point station.
_join('us-nj-finns-point-range',
      'uslhs:3379',
      'uslhs:8778')

# us-pr-punta-borinquen-3 into us-pr-punta-borinquen (clear, 3 m)
# The 1922 Punta Borinquen tower is described by LighthouseFriends's entry 1163 (the other, 1162, is the
# 1889 tower), the Light List's 3-30715, the HAER record PR-37 and an ENC point, all within 3 m of
# Wikidata's Punta Borinquen Light of 1922. The first review joined the Wikidata and OpenStreetMap items of
# the two towers; these four records started a third station on the same spot.
_join('us-pr-punta-borinquen',
      'enc:18.49720,-67.14873',
      'lighthousefriends:1163',
      'territories:haer-pr-37',
      'uscg_light_list:3-30715')

# us-va-nansemond into us-va-nansemond-river (clear, 63 m)
# OpenStreetMap's 'Nansemond Lighthouse' is a node tagged abandoned, taken from a USGS map scan; it is 63 m
# from LighthouseFriends's position for Nansemond River Light (screwpile, 1878-1935, destroyed), the only
# light of that name in Virginia.
_join('us-va-nansemond-river',
      'osm:node/1054711348')

# us-mi-six-mile-point-range-front into us-mi-six-mile-point-range (clear, positions wrong in two sources)
# The Six Mile Point Range lights (1895, inactive) are on the St. Marys River below Sault Ste. Marie: the
# Light List's 7-14045 (46.440 N, 84.266 W) and the Society's archive (46.438 N, 84.265 W) agree.
# LighthouseFriends puts its front light at 45.993 N, 83.899 W and its rear at 45.999 N, 84.350 W, 40 km
# from each other, which no range can be; the OpenStreetMap nodes repeat those two points. The Light List
# and archive records join the front station; the four wrong points are set aside (NO_POSITION).
_join('us-mi-six-mile-point-range',
      'lighthousefriends:1560',
      'rowlett:miup:six-mile-point-range-front-2',
      'uscg_light_list:7-14045',
      'uslhs:9829')

# us-mi-six-mile-point-range-rear into us-mi-six-mile-point-range (one range, 0 m)
# The Six Mile Point Range's rear light (1895): LighthouseFriends's and OpenStreetMap's rear entries (their
# points set aside), Rowlett's rear and the Society's Six Mile Point Range Rear. The sources give the rear
# no point of its own that can be trusted (the archive's is the front's, 0 m away), so the range is one
# station with a front and a rear structure and the rear's published id is retired into it.
_join('us-mi-six-mile-point-range',
      'lighthousefriends:1559',
      'osm:node/1012232474',
      'rowlett:miup:six-mile-point-range-rear-3',
      'uslhs:9830')

# us-nj-horseshoe-range-east-group-upper-front into lighthousefriends:1882 (one group, 740 m)
# The Horseshoe Range's East Group (Delaware River, 1881, all gone) has a lower front, a rear and an upper
# front in the Society's archive; LighthouseFriends lists the group as one entry. The upper front joins the
# group as its third structure.
_join('lighthousefriends:1882',
      'uslhs:8783')

# us-pa-horseshoe-range-west-group-lower-front into lighthousefriends:1883 (one group, point copied from the
# East Group)
# The archive files the West Group under Pennsylvania but gives its three lights the same points as the East
# Group (39.8705 N, 75.1503 W and so on), 5 km from where LighthouseFriends puts the West Group (39.883 N,
# 75.209 W). The West Group's records join LighthouseFriends's entry and their points are set aside.
_join('lighthousefriends:1883',
      'uslhs:8887')

# us-pa-horseshoe-range-west-group-range-rear into lighthousefriends:1883 (one group, point copied from the
# East Group)
# The West Group's rear light: see the lower front.
_join('lighthousefriends:1883',
      'uslhs:8888')

# us-pa-horseshoe-range-west-group-upper-front into lighthousefriends:1883 (one group, point copied from the
# East Group)
# The West Group's upper front light: see the lower front.
_join('lighthousefriends:1883',
      'uslhs:8889')

# us-oh-maumee-bay-straight-channel-range-east-front into lighthousefriends:1988 (one range, 360 m)
# The Straight Channel Range of Maumee Bay (1884; an east and a west range with two lights each, and two
# centre lights discontinued in 1895) is one entry in LighthouseFriends and the Light List; the Society's
# archive lists its six lights separately, with one point for each pair. The East Front joins the range.
_join('lighthousefriends:1988',
      'uslhs:9928')

# us-oh-maumee-bay-straight-channel-range-west-rear into lighthousefriends:1988 (one range, 360 m)
# The West Rear light of the Straight Channel Range: see the East Front.
_join('lighthousefriends:1988',
      'uslhs:9925')

# us-fl-st-joseph-point-beacon-hill-range-rear into us-fl-st-joseph-point (same years, 1.0 km)
# Wikidata's St. Joseph Point Light (lit 1902, retired 1960) and the Society's St. Joseph Point Range (front
# 1902; rear 'Beacon Hill', 1902-1960) have the same years; Rowlett lists the range's rear as 'St. Joseph
# Point (Beacon Hill) Range Rear', inactive since 1960. The archive's points are rounded to 0.1 minute and
# lie 0.3 to 1.0 km from Wikidata's. One range, one station with a front and a rear structure.
_join('us-fl-st-joseph-point',
      'rowlett:flw:st-joseph-point-beacon-hill-range-rear-1',
      'uslhs:15242',
      'uslhs:2788')

# us-ga-tybee-knoll-cut-range-front into us-ga-tybee-island-range-front (one range, 750 m)
# The Tybee Knoll Cut Range (1878): the Society's front light joins the station that already holds its rear
# (the archive), LighthouseFriends's 'Tybee Knoll Cut Range', Rowlett's front and rear and the Light List's
# 3-4715. Wikidata names the same two lights 'Tybee Island Range Front / Rear Light'.
_join('us-ga-tybee-island-range-front',
      'uslhs:8414')

# us-md-mathias-point-shoal into us-md-mathias-point (clear, 430 m)
# The Society's Mathias Point Shoal (1876-1963, lost) is Mathias Point Light: Wikidata lit 1876, retired
# 1961, LighthouseFriends 'Mathias Point' destroyed, Rowlett 'Mathias Point Shoal' 1876; the archive's point
# is 430 m off (rounded).
_join('us-md-mathias-point',
      'uslhs:8963')

# us-nj-tinicum-island-range-rear into us-nj-tinicum-island-range (clear, archive point rounded)
# The Society's Tinicum Island Range Rear (1880) is the rear light of the Tinicum Island (Billingsport)
# Range that Wikidata, OpenStreetMap, LighthouseFriends, the NRHP and the Light List describe; the archive's
# point is 1.6 km off.
_join('us-nj-tinicum-island-range',
      'uslhs:3390')

# us-ny-long-beach-bar-replica into us-ny-orient-long-beach-bar (same site, 20 m)
# Orient Long Beach Bar Light ('Bug Light', 1871) burned in 1963 and a replica was built on the spot in 1990
# and lit as an aid (Rowlett: 'Light station reactivated'; Light List 1-27975; OpenStreetMap: 'Bug Light').
# The Society lists the 1871 light and the 1990 replica as two places 20 m apart at the same site; one
# station.
_join('us-ny-orient-long-beach-bar',
      'uslhs:34236',
      'uslhs:8815')

# us-oh-vermilion-replica into us-oh-vermilion (same lighthouse, 650 m)
# Vermilion Light's present tower is the replica of the 1877 lighthouse built in 1991-92 at the Inland Seas
# Maritime Museum and lit as an aid (Light List 7-4451 'Vermilion Museum Lighthouse'; Wikidata lit 1992).
# Rowlett's and the Society's 'Vermilion (Replica)' are that tower; the archive's point is 650 m east.
_join('us-oh-vermilion',
      'rowlett:oh:vermilion-5',
      'uslhs:9953')

# us-mi-saginaw-river into us-mi-saginaw-river-rear-range (same years, 1.1 km)
# The Society's Saginaw River (lit 1841, tower of 1876, retired 1960) is the Saginaw River Rear Range Light
# station (Wikidata built 1876, retired 1960; NRHP 'Saginaw River Light Station'); the archive's point is
# 1.1 km off.
_join('us-mi-saginaw-river-rear-range',
      'uslhs:3330')

# us-wi-grassy-island-range-rear into us-wi-grassy-island-range (clear, archive point rounded)
# The Society's front and rear (both 1872) and Rowlett's rear are the Grassy Island Range Lights (Wikidata,
# NRHP, LighthouseFriends); the archive gives both lights one point 2.4 km off.
_join('us-wi-grassy-island-range',
      'rowlett:widp:grassy-island-range-rear',
      'uslhs:8994',
      'uslhs:8995')

# us-la-ship-shoal-2 into us-la-ship-shoal (clear, 1.7 km)
# The Society's Ship Shoal (1859-1965) is Ship Shoal Light (Wikidata retired 1965, Rowlett built 1859); the
# archive's point is rounded and 1.7 km from LighthouseFriends's and the Light List's.
_join('us-la-ship-shoal',
      'uslhs:2813')

# us-ny-oswego-harbor-west-pierhead-2 into us-ny-oswego-harbor-west-pierhead (clear, archive point wrong)
# The Society's Oswego Harbor West Pierhead (1934, active) is the pierhead light that Wikidata,
# OpenStreetMap, LighthouseFriends, the NRHP and the Light List describe at 43.473 N, 76.517 W. The
# archive's point for it (43.789 N, 76.861 W) is 40 km off, and it gave the same point to two other Oswego
# lights (see NO_POSITION).
_join('us-ny-oswego-harbor-west-pierhead',
      'uslhs:3426')

# RULING (DESIGN 3.2): Old Point Loma (1855, on the ridge, now a museum in Cabrillo National Monument) and
# New Point Loma (1891, at the shore) are two stations, each with its own established name, 0.8 km apart.
# The published station keeps the active light; the ridge tower's records start the Old Point Loma station,
# and the two are linked as successive lights. Nothing is retired.
_join('new:us-ca-old-point-loma', 'wikidata:Q7084751')

# Old Point Loma Lighthouse, OpenStreetMap's way for the 1855 tower.
_join('new:us-ca-old-point-loma', 'osm:way/90687227')

# NRHP 74000350 is the Old Point Loma Lighthouse.
_join('new:us-ca-old-point-loma', 'nrhp:74000350')

# LighthouseFriends's second 'Point Loma' entry, on the ridge.
_join('new:us-ca-old-point-loma', 'lighthousefriends:29')

# Rowlett's first Point Loma entry: 1855, inactive since 1891.
_join('new:us-ca-old-point-loma', 'rowlett:ca2:point-loma-1')

# The Passport Club keeps separate stamps for 'Point Loma (Old)' and '(New)'.
_join('new:us-ca-old-point-loma', 'uslhs_passport:stamp:ca:point-loma-old')

# LighthouseFriends's 'Ship Shoal' (28.915 N, 91.071 W) and the Light List's 'Ship Shoal Obstruction Lights'
# 4-730 are Ship Shoal Light, the offshore tower of 1859-1965. Wikidata's item for it (Q7497938) carries
# South Pass Range's coordinates, which is why the first build put it 80 km from the shoal.
_join('us-la-ship-shoal', 'lighthousefriends:816')

# Two Rivers (Wisconsin): Wikidata's Two Rivers Light (retired 1969) and Rowlett's Two Rivers (1886,
# inactive since 1969) are the lighthouse that OpenStreetMap and LighthouseFriends map as 'Two Rivers
# Lighthouse', 1.2 km north of the pier where Wikidata puts it: one tower, which no longer stands where it
# served. The pier now has the North Pierhead Light (1969, Light List 7-20925), a modern pier light that is
# not a station of Fresnel's (DESIGN section 1); its records stay out of the lighthouse's station (see the
# records kept apart).
_join('us-wi-two-rivers', 'wikidata:Q7859191')

# Rowlett's Two Rivers, the 1886 lighthouse inactive since 1969.
_join('us-wi-two-rivers', 'rowlett:wi:two-rivers-1')

# Rowlett's Lazaretto Point (built 1985, inactive) is the replica that OpenStreetMap and LighthouseFriends
# map; the original (1831-1926) is the Society's Lazaretto Point, 530 m off.
_join('us-md-lazaretto-point', 'rowlett:md:lazaretto-point')

# HAER PR-32, the Library of Congress's record of the Spanish-era Punta Tuna lighthouse; the library's point
# is a geocode 4 km from the light, and no other Puerto Rico station has this name.
_join('us-pr-punta-tuna', 'territories:haer-pr-32')

# HAER PR-35, 'Faro del Puerto de Ponce': the lighthouse of Ponce's harbour is the one on Cardona Island,
# 670 m from the library's point.
_join('us-pr-cardona-island', 'territories:haer-pr-35')

# HAER PR-36, the lighthouse of Caja de Muertos island, 935 m from the library's point.
_join('us-pr-caja-de-muertos', 'territories:haer-pr-36')

# HAER PR-38, 'Faro de los Morillos de Arecibo': Arecibo Light, 1.4 km from the library's point.
_join('us-pr-arecibo', 'territories:haer-pr-38')

# HAER PR-41, 'Faro del Puerto de Guanica': Guanica Light, 7 km from the library's geocode of the harbour.
_join('us-pr-guanica', 'territories:haer-pr-41')

# HAER PR-45, the Puerto Ferro lighthouse on Vieques, 770 m from the library's point.
_join('us-pr-puerto-ferro', 'territories:haer-pr-45')

# HAER PR-46, the lighthouse of the Castillo de San Felipe del Morro (Port San Juan Light), 710 m from the
# library's point.
_join('us-pr-el-morro-or-port-san-juan', 'territories:haer-pr-46')

# The Society's 'Tucker Beach' (wood tower of 1848, 14 m, lost 1927; the archive files it under Sea Haven)
# is Tucker's Island Light, the original that the Tuckerton Seaport replica copies. It is its own station,
# linked to the replica; the first review had left it without one.
_join('new:us-nj-tuckers-island', 'uslhs:8793')

# ---- Positions found wrong: the record keeps its facts, the merge does not use its coordinates ----
# Ship Shoal Light's Wikidata item copies the coordinates of South Pass Range Lights (29.015, -89.167), 80
# km north of the shoal; LighthouseFriends and the Light List give the shoal.
NO_POSITION.add('wikidata:Q7497938')

# Cape Fear Light's Wikidata item copies Oak Island Light's coordinates (33.893, -78.035), 4.7 km from the
# Bald Head Island site.
NO_POSITION.add('wikidata:Q5034789')

# Point Stuart Light's Wikidata item copies Point Blunt Light's coordinates (37.853, -122.419).
NO_POSITION.add('wikidata:Q44082465')

# North Point Range Lights' Wikidata item copies the Craighill Channel Upper Range Front Light's coordinates
# (39.197, -76.448).
NO_POSITION.add('wikidata:Q14692309')

# Winter Harbor Light's Wikidata item copies Pumpkin Island Light's coordinates (44.309, -68.743).
NO_POSITION.add('wikidata:Q8026238')

# OpenStreetMap places South Buffalo North Side Light at Dunkirk Harbor, 55 km from Buffalo Harbor.
NO_POSITION.add('osm:node/9843815382')

# LighthouseFriends places 'Buffalo South Entrance North Side' at Dunkirk Harbor, 55 km from Buffalo Harbor.
NO_POSITION.add('lighthousefriends:907')

# Blakistone Island Light's Wikidata item sits at the replica's site (St. Clement's Island Museum), not on
# the island where the 1851 tower stood.
NO_POSITION.add('wikidata:Q4924664')

# The Society's archive puts Cape Florida 7 km east of the tower.
NO_POSITION.add('uslhs:2768')

# The Society's archive puts Split Rock 17 km from the lighthouse.
NO_POSITION.add('uslhs:3357')

# OpenStreetMap's Six Mile Point Range Light repeats LighthouseFriends's point, 45.993 N, 83.899 W, 50 km
# from the St. Marys River where the Light List and the Society put the range.
NO_POSITION.add('osm:node/1011891274')

# LighthouseFriends's Six Mile Point Range Front is 50 km from the St. Marys River, where the Light List
# (7-14045) and the Society put the range, and 40 km from its own rear light.
NO_POSITION.add('lighthousefriends:1560')

# OpenStreetMap's Six Mile Point Range Rear Lighthouse repeats LighthouseFriends's point, 45.999 N, 84.350
# W, 45 km from the St. Marys River.
NO_POSITION.add('osm:node/1012232474')

# LighthouseFriends's Six Mile Point Range Rear is 45 km from the St. Marys River, where the Society puts
# the range.
NO_POSITION.add('lighthousefriends:1559')

# The Society's point for Oswego Harbor West Pierhead (43.789 N, 76.861 W) is 40 km from Oswego; the same
# point is given to two other Oswego lights.
NO_POSITION.add('uslhs:3426')

# The Society's point for Oswego Harbor (43.789 N, 76.861 W) is 40 km from Oswego.
NO_POSITION.add('uslhs:8817')

# The Society's point for Oswego Breakwater (43.789 N, 76.861 W) is 40 km from Oswego.
NO_POSITION.add('uslhs:7344')

# The Society's Horseshoe Range West Group, Lower Front has the East Group's point.
NO_POSITION.add('uslhs:8887')

# The Society's Horseshoe Range West Group, Range Rear has the East Group's point.
NO_POSITION.add('uslhs:8888')

# The Society's Horseshoe Range West Group, Upper Front has the East Group's point.
NO_POSITION.add('uslhs:8889')

# Wikidata's Two Rivers Light is at the pier (44.143 N, 87.560 W) where the lighthouse served until 1969;
# the lighthouse itself is mapped by OpenStreetMap and LighthouseFriends 1.2 km north, and the pier's lights
# (the Light List's 7-20925 and 7-20930) are not its.
NO_POSITION.add('wikidata:Q7859191')

# ---- Records that are two stations although names and positions agree ----
# Light List 4-12597 is Port Eads Marina Lower Dock Light, at South Pass (29.015 N, 89.166 W), which is the
# point Wikidata's Ship Shoal Light item copies. Ship Shoal Light's own number is 4-730.
_keep_apart('uscg_light_list:4-12597', 'wikidata:Q7497938')

# Light List 7-20925 is the Two Rivers North Pierhead Light (1969) on the pier; Wikidata's item for the old
# lighthouse carries its number, but the lighthouse no longer stands there.
_keep_apart('uscg_light_list:7-20925', 'wikidata:Q7859191')

# The ENC light at the Two Rivers pier is the North Pierhead Light, not the old lighthouse.
_keep_apart('enc:44.14269,-87.56070', 'wikidata:Q7859191')

# Rowlett lists the 1969 North Pierhead Light apart from the Two Rivers lighthouse.
_keep_apart('rowlett:wi:two-rivers-north-pierhead-2', 'wikidata:Q7859191')

# ---------------------------------------------------------------------------------------------
# Pairs of stations reviewed and found to be two stations
# ---------------------------------------------------------------------------------------------

# Fort Tompkins Light (1828, relit 1873) and Fort Wadsworth Light (1903) are 13 m apart under two names;
# linked as successive lights, not joined.
_not_duplicates('us-ny-fort-tompkins', 'us-ny-fort-wadsworth')

# The first Chicago Harbor light and the 1893 light are 2.4 km apart (linked as successive lights).
_not_duplicates('us-il-chicago-harbor-2', 'us-il-chicago-harbor')

# Buffalo Harbor South Entrance Light (NRHP 07001191) and South Buffalo North Side Light (NRHP 83001673) are
# two NRHP-listed lights 185 m apart at the harbor's south entrance.
_not_duplicates('us-ny-buffalo-harbor-south-entrance', 'us-ny-south-buffalo-north-side')

# The 1851 original and its 2008 replica, 587 m apart (linked as replica_of).
_not_duplicates('us-md-blakistone-island', 'us-md-blackistone')

# South Pass Range Lights and Ship Shoal Light are different lights 80 km apart; Wikidata gave Ship Shoal
# the range's coordinates.
_not_duplicates('us-la-south-pass-range', 'us-la-ship-shoal')

# Cape Fear Light (Bald Head Island, 1903-1958) and Oak Island Light (1958, mainland) are different towers
# 4.7 km apart; Wikidata gave Cape Fear Oak Island's coordinates.
_not_duplicates('us-nc-cape-fear', 'us-nc-oak-island')

# Point Stuart and Point Blunt are the two ends of Angel Island, 2.5 km apart.
_not_duplicates('us-ca-point-stuart', 'us-ca-point-blunt')

# Craighill Channel Upper Range Front Light (1886) and the North Point Range Lights of 1822-1873 are
# different lights; Wikidata copied the first's coordinates onto the second.
_not_duplicates('us-md-craighill-channel-upper-range-front', 'us-md-north-point-range')

# The Nantucket Harbor Range (1908) and Brant Point Light (1746; towers 1856 and 1901) are different lights
# 140 m apart on Brant Point.
_not_duplicates('us-ma-nantucket-harbor-range', 'us-ma-brant-point')

# Two lost Boston Harbor ranges: Broad Sound Channel Inner Range (1903-1950) and Spectacle Island Range
# (1897-1913), listed apart by Wikidata and LighthouseFriends (entries 1978 and 1977), 60 m apart at
# Spectacle Island.
_not_duplicates('us-ma-broad-sound-channel-inner-range', 'us-ma-spectacle-island-range')

# The south and north pierhead lights of Grand Haven stand on opposite piers, 142 m apart.
_not_duplicates('us-mi-grand-haven-south-pierhead-entrance', 'us-mi-grand-haven-north-pierhead')

# Pentwater Light (south pier, 1873/1937) and the North Pierhead Light (north pier, 1997) are on different
# piers, 95 m apart.
_not_duplicates('us-mi-pentwater', 'us-mi-pentwater-north-pierhead')

# Buffalo North Breakwater's end light and Buffalo Main Light (1833) are different lights 50 m apart.
_not_duplicates('us-ny-buffalo-north-breakwater-east-end', 'us-ny-buffalo-main')

# Duluth's south breakwater outer light and north pier light are on different piers, 105 m apart.
_not_duplicates('us-mn-duluth-south-breakwater-outer', 'us-mn-duluth-harbor-north-pier')

# The Plum Island Range Lights (1896) and the ruins of the 1849 lighthouse are different structures 73 m
# apart; the ruins are a station of their own.
_not_duplicates('us-wi-plum-island-range', 'us-wi-1849-lighthouse-ruins')

# Lake Havasu's one-third-scale copies of the Wind Point and Alpena lights, 95 m apart on the shore.
_not_duplicates('us-az-wind-point', 'us-az-alpena')

# Lake Havasu's copies of the Currituck Beach and Buffalo Main lights, 113 m apart.
_not_duplicates('us-az-currituck-beach', 'us-az-buffalo-main')

# Lake Havasu's copies of the West Quoddy and East Quoddy Head lights, 94 m apart.
_not_duplicates('us-az-west-quoddy', 'us-az-east-quoddy')

# The first Chicago Harbor light (1832-1859) and the Chicago Pierhead Range front light (1891): different
# lights; the Society's archive gives both the river-mouth point 41.885 N, 87.6195 W.
_not_duplicates('us-il-chicago-harbor-2', 'us-il-chicago-pierhead-range-front')

# Morris Island Light (1876) and Charleston Light (1962, Sullivans Island) are different towers 7.9 km
# apart; 'Charleston Light' is an old name of the first.
_not_duplicates('us-sc-morris-island', 'us-sc-charleston')

# Southwest Point and Northwest Point Royal Shoal lights are two lights 4.3 km apart.
_not_duplicates('us-nc-southwest-point-royal-shoal', 'us-nc-northwest-point-royal-shoal')

# Cape Henlopen Light (1764/1767) and the Cape Henlopen Beacon (1825) were two lights 1.4 km apart.
_not_duplicates('us-de-cape-henlopen', 'us-de-cape-henlopen-beacon')

# The Delaware Breakwater range and the breakwater's west-end light are different lights 4.7 km apart.
_not_duplicates('us-de-delaware-breakwater-range', 'us-de-delaware-breakwater-west-end')

# Delaware Breakwater East End Light (1885) and Harbor of Refuge Light (1908) are different lights 2 km
# apart (they share an NRHP listing, 89000289).
_not_duplicates('us-de-delaware-breakwater-east-end', 'us-de-harbor-of-refuge')

# The lower and upper Craighill ranges are different ranges 4.7 km apart.
_not_duplicates('us-md-craighill-channel-lower-range-front', 'us-md-craighill-channel-upper-range-front')

# The upper and lower Craighill ranges are different ranges 6 km apart.
_not_duplicates('us-md-craighill-channel-upper-range-rear', 'us-md-craighill-channel-lower-range-rear')

# The front and rear of the Baker Shoal range are 3.2 km apart, beyond the 3 km the merge pairs
# automatically; left as two stations.
_not_duplicates('us-de-baker-shoal-range-front', 'us-de-baker-shoal-range-rear')

# Staten Island Light (1912) and New Dorp Light (1856, inactive) are different towers 1.9 km apart.
_not_duplicates('us-ny-staten-island', 'us-ny-new-dorp')

# New Haven Outer Breakwater light (lost) and Five Mile Point Light (New Haven Harbor Light, 1805) are
# different lights 4.5 km apart.
_not_duplicates('us-ct-new-haven-outer-breakwater', 'us-ct-five-mile-point')

# Lorain's west and east breakwater lights are on different breakwaters, 543 m apart.
_not_duplicates('us-oh-lorain-west-breakwater', 'us-oh-lorain-east-breakwater')

# Cleveland's west and east pierhead lights are on different piers, 232 m apart.
_not_duplicates('us-oh-cleveland-west-pierhead', 'us-oh-cleveland-east-pierhead')

# Hyannis Rear Range Light (1849) and OpenStreetMap's 'Hyannis Harbor Lighthouse' (disused) are 1.7 km
# apart; no source says they are one tower.
_not_duplicates('us-ma-hyannis-rear-range', 'us-ma-hyannis-harbor')

# Old Michigan City Light (1858, museum) and the Michigan City East Pierhead Light (1904) are different
# towers 862 m apart.
_not_duplicates('us-in-old-michigan-city', 'us-in-michigan-city-east')

# Erie Land Light (1818) and Presque Isle Light (1872) are different lights 5 km apart.
_not_duplicates('us-pa-erie-land', 'us-pa-presque-isle')

# St. Clair Flats Canal lights and the South Channel Range are different aids 2.1 km apart.
_not_duplicates('us-mi-st-clair-flats-canal-lower', 'us-mi-st-clair-flats-front-and-rear-range')

# The St. Clair Flats Canal Range (1871) and the South Channel Range (1859) are different ranges 3.8 km
# apart.
_not_duplicates('us-mi-st-clair-flats-canal-range', 'us-mi-st-clair-flats-front-and-rear-range')

# Kenosha Light (1866, inactive) and the Kenosha North Pier Light (1906) are different towers 583 m apart.
_not_duplicates('us-wi-kenosha-north-pier', 'us-wi-kenosha')

# North Manitou Shoal Light (1935) and North Manitou Island Light (1898, lost) are different lights 4.7 km
# apart.
_not_duplicates('us-mi-north-manitou-shoal', 'us-mi-north-manitou-island')

# St. Johns Light (1954) and St. Johns River Light (1859) are different towers 2.8 km apart (linked as
# successive lights).
_not_duplicates('us-fl-st-johns', 'us-fl-st-johns-river')

# The Three Sisters of Nauset (1838) and Nauset Light (1877) are different structures 370 m apart (linked as
# successive lights).
_not_duplicates('us-ma-three-sisters-of-nauset', 'us-ma-nauset')

# Old and New Presque Isle Light are two stations (RULING, DESIGN 3.2), linked as successive lights.
_not_duplicates('us-mi-old-presque-isle', 'us-mi-new-presque-isle')

# The original screwpile light (lost 1962) and the 2004 replica at Bay Creek are 3 km apart.
_not_duplicates('us-va-old-plantation-flats', 'us-va-bay-creek')

# The original Stingray Point light (1858-1965) and its replica are 3.3 km apart.
_not_duplicates('us-va-stingray-point', 'us-va-stingray-point-replica')

# The 1851 original (lost 1955) and the 2008 replica at the museum, 117 m apart by the sources' points.
_not_duplicates('us-md-blakistone-island', 'us-md-blackistone-island-replica')

# RULING (DESIGN 3.2): Old and New Point Loma are two stations 0.8 km apart, linked as successive lights.
_not_duplicates('us-ca-point-loma', 'us-ca-old-point-loma')

# Smith Point Light (1897) and the earlier Smith Point light (1868-1898, the Society's 'Smith Point (Old)')
# were 1.2 km apart; linked as successive lights.
_not_duplicates('us-va-smith-point-old', 'us-va-smith-point')

# Hawkins Point Light and Leading Point Light are the front and rear of the Brewerton Channel Range, each
# with its own item and name, 1.8 km apart.
_not_duplicates('us-md-hawkins-point', 'us-md-leading-point')

# The Keweenaw Waterway Lower Entrance Light (1920) and Jacobsville (Portage River) Lighthouse (1856-1920)
# are different lights 1.7 km apart.
_not_duplicates('us-mi-keweenaw-waterway-lower-entrance', 'us-mi-jacobsville')

# The Santa Cruz Lighthouse (the 1967 memorial copy at Lighthouse Point) and the West Breakwater Light
# (1964) are different lights 2.4 km apart.
_not_duplicates('us-ca-santa-cruz', 'us-ca-santa-cruz-breakwater')

# The Light List calls Pensacola Light the rear light of the Fort Barrancas Range (4-4785), and the Society
# lists the range's front and rear as lost; they are kept as two stations, the range at Fort Barrancas 600 m
# south-west, until a source settles whether the lost 'rear' is the Pensacola tower.
_not_duplicates('us-fl-fort-barrancas-range', 'us-fl-pensacola')

# The Society's Tybee Island Range (front 1822, lost; rear 1793, active) is probably the Tybee lighthouse as
# the rear of its range, but its dates (1793, not the station's 1736 or the tower's 1867) do not match; kept
# apart until a source settles it.
_not_duplicates('us-ga-tybee-island-range', 'us-ga-tybee-island-lighthouse-and-museum')

# The Tybee Island Range (Savannah River entrance, 1822) and the Tybee Knoll Cut Range (1878) are different
# ranges 6.7 km apart.
_not_duplicates('us-ga-tybee-island-range', 'us-ga-tybee-island-range-front')

# Olcott Light (1873, lost) and its replica of 2003 are 575 m apart.
_not_duplicates('us-ny-olcott', 'us-ny-olcott-2')

# The 1985 replica at Lazaretto Point and the original light (1831-1926), 530 m apart.
_not_duplicates('us-md-lazaretto-point', 'us-md-lazaretto-point-2')

# The Horseshoe Range's East Group (New Jersey side) and West Group (Pennsylvania side) are two groups of
# lights the sources keep apart.
_not_duplicates('us-nj-horseshoe-range-east-group', 'us-pa-horseshoe-range-west-group')

# ---- Names ----
# The ridge tower of 1855 (Cabrillo National Monument).
NAME_PICKS['us-ca-old-point-loma'] = 'Old Point Loma Lighthouse'

# Twin lights, one station (DESIGN 3.2): the east tower (1874, active) and the west tower (1874, retired
# 1924); Wikidata's item for the west tower won the name.
NAME_PICKS['us-me-cape-elizabeth-light-western'] = 'Cape Elizabeth Light'

# One station, two towers: the name the NRHP, Wikidata and the state park use. The id keeps the first
# build's 'north'.
NAME_PICKS['us-nj-navesink-north'] = 'Navesink Twin Lights'

# The twin-tower station on Thacher Island is Cape Ann Light Station (NRHP, the Society, Rowlett);
# Wikidata's item for the north tower won the name.
NAME_PICKS['us-ma-cape-ann'] = 'Cape Ann Light Station'

# The station started as OpenStreetMap's 'Bay Creek Lighthouse'; the lighthouse is a replica of Old
# Plantation Flats Light, as LighthouseFriends and Rowlett call it.
NAME_PICKS['us-va-bay-creek'] = 'Old Plantation Flats (Replica)'

# The station is both the 1890 Port Boca Grande tower and the rear light; 'Gasparilla Island' is the name
# the Society, LighthouseFriends and the Coast Guard use.
NAME_PICKS['us-fl-boca-grande'] = 'Boca Grande Lighthouse (Gasparilla Island Light)'

# OpenStreetMap's name for the oil house of the light station ('Oil Shed') won the station's name; the light
# is Old Michigan City Light (1858, NRHP 74000023), now a museum.
NAME_PICKS['us-in-old-michigan-city'] = 'Old Michigan City Light'

# The original of 1848-1927; the replica at Tuckerton Seaport is us-nj-tuckers-beach. Rowlett and
# LighthouseFriends call the island's light Tucker's Island / Tuckers Beach.
NAME_PICKS['us-nj-tuckers-island'] = "Tucker's Island Light"

# ---- Statuses settled from evidence ----
# The 1851 Blakistone Island lighthouse was lost in 1955 (Wikidata: retired 1956; the Society's archive:
# lost). A 2008 replica stands on the mainland.
STATUS_PICKS['us-md-blakistone-island'] = ('lost', None)

# The North Point Range Lights (1822, retired 1873) are listed as destroyed by LighthouseFriends; Wikidata
# gives an end date.
STATUS_PICKS['us-md-north-point-range'] = ('lost', None)

# The 1903 skeleton tower at Cape Fear was taken down in 1958; LighthouseFriends and the Society's archive
# list it as gone. Its foundation and station buildings remain (the OpenStreetMap elements).
STATUS_PICKS['us-nc-cape-fear'] = ('lost', None)

# Lit 1884, discontinued 1909 (Wikidata gives an end date of 1939); the Society's archive lists the
# Christiana light station as lost. No source maps a structure.
STATUS_PICKS['us-de-christiana-north-jetty'] = ('lost', None)

# Both lights of the Delaware Breakwater range are gone: LighthouseFriends and the Society's archive list
# the rear as destroyed (retired 1918), Wikidata gives the front's end as 1903 / 1950.
STATUS_PICKS['us-de-delaware-breakwater-range'] = ('lost', None)

# The Cedar Point screwpile light (lit 1896, retired 1920) is listed as destroyed by LighthouseFriends and
# as lost by the Society's archive.
STATUS_PICKS['us-md-cedar-point'] = ('lost', None)

# Greenbury Point's two lights (1848, 1892; the second retired 1934) are listed as destroyed by
# LighthouseFriends; no source maps a structure.
STATUS_PICKS['us-md-greenbury-point'] = ('lost', None)

# A light on the Fairhaven swing bridge, lit 1888 and ended 1891; the Society's archive lists it only as a
# minor aid. No source maps or lists a structure.
STATUS_PICKS['us-ma-fairhaven-bridge'] = ('lost', None)

# The Roanoke Marshes screwpile light (1877) was taken down in 1955; the Light List's 'Roanoke Marshes Light
# RM' is a modern pile light at the site.
STATUS_PICKS['us-nc-roanoke-marshes-2'] = ('lost', None)

# Hog Island Light: one source (Wikidata, 1853-1948).
STATUS_PICKS['us-va-hog-island'] = ('unknown', "Reviewed 2026-10: Wikidata's end date (1948) is the only evidence that this light is gone; no source maps or lists a structure.")

# The Old Plantation Flats screwpile light (1886) ended in 1962 (Wikidata); the Light List's 'Warning Light
# A' is a modern light at the site, and the 2004 replica is a separate station.
STATUS_PICKS['us-va-old-plantation-flats'] = ('lost', None)

# OpenStreetMap maps the remains of the 1849 Plum Island lighthouse as ruins.
STATUS_PICKS['us-wi-1849-lighthouse-ruins'] = ('ruins', None)

# The name says it: a replica, mapped by OpenStreetMap and listed by LighthouseFriends.
STATUS_PICKS['us-md-bethel-bridge-lighthouse-replica'] = ('replica', None)

# Mathias Point Light (1876): LighthouseFriends lists it as destroyed and the Society's archive as lost
# (retired 1963); Wikidata gives an end date. The Light List's 'Upper Potomac River Channel Light 5' is a
# modern light at the site.
STATUS_PICKS['us-md-mathias-point'] = ('lost', None)

# The replica of Bug Light shows a light as an aid (Light List 1-27975); the 1871 original burned in 1963.
STATUS_PICKS['us-ny-orient-long-beach-bar'] = ('active', None)

# The replica lighthouse shows a light as an aid (Light List 7-4451); the 1877 original is gone.
STATUS_PICKS['us-oh-vermilion'] = ('active', None)

# The lighthouse of New Buffalo (1840-1859) is listed as destroyed by LighthouseFriends and as lost by the
# Society's archive; OpenStreetMap maps a lighthouse-shaped structure in the town, 950 m from
# LighthouseFriends's point, which the Society lists as a private (faux) lighthouse.
STATUS_PICKS['us-mi-new-buffalo'] = ('lost', None)

# ---- Hidden: shown no more, file kept ----
# OpenStreetMap's second 'Pooles Island Light' 3.3 km south of the 1825 tower, with the Light List's modern
# light as its only other record: a modern aid with no history of its own (DESIGN 1).
HIDE['us-md-pooles-island-2'] = 'A modern light on the shoal south of Pooles Island (Light List 2-8663); the historic Pooles Island Light is us-md-pooles-island'

# OpenStreetMap's node marks Nauset Light's old site, 94 m from the tower; it is a place on the Nauset
# station, not a station.
HIDE['us-ma-original-location-of-nauset-lighthouse-prior-to-1996'] = 'A marker for the spot where Nauset Light stood before it was moved in 1996 (recorded on us-ma-nauset), not a station'

# OpenStreetMap's way 'Lighthouse Point Park' is the park around Buffalo Main Light.
HIDE['us-ny-lighthouse-point-park'] = 'A park named for the Buffalo Main Light, not a light'

# Machias Seal Island, with its light, is administered by Canada (New Brunswick); LighthouseFriends and the
# Society's passport list file it under Maine. The Canadian station has the Wikidata record.
HIDE['us-me-machias-seal-island'] = 'The light is in Canada: see ca-nb-machias-seal-island'

# Lake Havasu Marina's lighthouse (2001) is not a copy of a named light (Rowlett's other Havasu entries all
# say which light they copy).
HIDE['us-az-lake-havasu-marina'] = "A marina's decorative lighthouse that copies no particular light and is not an aid to navigation"

# Inland, OpenStreetMap only, in no register, no light list and no lighthouse directory.
HIDE['us-co-frisco-bay-marina'] = 'A decorative lighthouse at a marina on a mountain reservoir: not an aid to navigation'

# OpenStreetMap only; named for the Stevns lighthouse in Denmark.
HIDE['us-ky-stevns-fyr'] = 'A copy of a Danish lighthouse in Kentucky: decorative, not an aid to navigation'

# Inland, OpenStreetMap only, in no register or light list.
HIDE['us-mo-lake-chesterfield'] = 'A decorative lighthouse on a suburban lake: not an aid to navigation'

# A memorial structure; no light list or register lists it as an aid.
HIDE['us-mo-mark-twain-memorial'] = 'A memorial lighthouse (1935) on Cardiff Hill, Hannibal: not an aid to navigation'

# Inland, OpenStreetMap only.
HIDE['us-mt-lake-frances'] = 'A decorative lighthouse at a reservoir: not an aid to navigation'

# Inland, OpenStreetMap only.
HIDE['us-ne-linoma'] = 'A decorative lighthouse at a beach resort on the Platte River: not an aid to navigation'

# Inland, OpenStreetMap only (disused).
HIDE['us-tn-omohundro-waterworks'] = 'A waterworks tower built to look like a lighthouse: not an aid to navigation'

# Inland, OpenStreetMap only.
HIDE['us-ut-northshore'] = 'A decorative lighthouse on Utah Lake: not an aid to navigation'

# The Society's archive lists it as a private (faux) lighthouse; OpenStreetMap only otherwise.
HIDE['us-ny-celoron'] = 'A private (faux) lighthouse at Celoron, Chautauqua Lake: not an aid to navigation'

# The Society's archive lists it as a private (faux) lighthouse; OpenStreetMap only otherwise.
HIDE['us-wa-dimick'] = 'A private (faux) lighthouse built in 1990 at Dimick: not an aid to navigation'

# OpenStreetMap's 'Hyannis Harbor Lighthouse' is tagged disused; Rowlett calls the Lewis Bay light privately
# maintained and unofficial, and the Society lists it as a private (faux) lighthouse.
HIDE['us-ma-hyannis-harbor'] = 'A privately kept, unofficial light on Lewis Bay, not an aid to navigation'

# OpenStreetMap only, with the Society's listing as a private (faux) lighthouse.
HIDE['us-nh-spindle-point'] = 'A private (faux) lighthouse on Lake Winnipesaukee: not an aid to navigation'

# OpenStreetMap, Rowlett ('privately maintained and unofficial') and the Society's private (faux) listing.
HIDE['us-oh-rattlesnake-island'] = 'A privately kept, unofficial light (1990): not an aid to navigation'

# OpenStreetMap, Rowlett and the Society's private (faux) listing; in no Light List.
HIDE['us-wv-summersville-lake'] = 'A decorative lighthouse (2012) on an inland lake: not an aid to navigation'

# ---- Scale copies (status replica, replica_of the light they copy) ----
# The 2004 replica of Old Plantation Flats Light at Bay Creek Resort, Cape Charles (OpenStreetMap: 'Bay
# Creek Lighthouse'; LighthouseFriends and Rowlett: replica).
REPLICA_OF['us-va-bay-creek'] = 'us-va-old-plantation-flats'

# The replica of Stingray Point Light (LighthouseFriends and Rowlett: replica).
REPLICA_OF['us-va-stingray-point-replica'] = 'us-va-stingray-point'

# The 2008 replica of Blakistone Island Light at St. Clement's Island Museum (OpenStreetMap,
# LighthouseFriends, the Society, Rowlett).
REPLICA_OF['us-md-blackistone'] = 'us-md-blakistone-island'

# Lake Havasu City's one-third-scale copy of Algoma Pierhead Light (Rowlett: 'Spectator Point (Algoma
# Pierhead Replica)').
REPLICA_OF['us-az-algoma'] = 'us-wi-algoma-pierhead'

# Lake Havasu's copy of Alpena Light (Rowlett: 'Southwest Point I (Alpena Replica)').
REPLICA_OF['us-az-alpena'] = 'us-mi-alpena'

# Lake Havasu's copy of Barnegat Light (Rowlett: 'Red Rock Point (Barnegat Replica)').
REPLICA_OF['us-az-barnegat'] = 'us-nj-barnegat-2'

# Lake Havasu's copy of the Berwick light, which is Southwest Reef Light at Berwick Bay (Rowlett: 'Larned
# Landing (Berwick Replica)'; the passport list names the original 'Southwest Reef (Berwick)').
REPLICA_OF['us-az-berwick'] = 'us-la-southwest-reef'

# Lake Havasu's copy of Buffalo Main Light (Rowlett: 'Bridgewater Channel West (Buffalo Main Replica)').
REPLICA_OF['us-az-buffalo-main'] = 'us-ny-buffalo-main'

# Lake Havasu's copy of Cape Hatteras Light (Rowlett: 'Windsor Beach I (Cape Hatteras Replica)').
REPLICA_OF['us-az-cape-hatteras'] = 'us-nc-cape-hatteras'

# Lake Havasu's copy of the new Cape Henry Light (Rowlett: 'Windsor Beach II (New Cape Henry Replica)').
REPLICA_OF['us-az-cape-henry'] = 'us-va-cape-henry'

# Lake Havasu's copy of the Chicago Harbor Southeast Guidewall Light (Rowlett: 'South Point (Chicago Harbor
# Southeast Guidewall Replica)').
REPLICA_OF['us-az-chicago-harbor-navy-pier'] = 'us-il-chicago-harbor-southeast-guidewall'

# Lake Havasu's copy of Currituck Beach Light (Rowlett: 'Bridgewater Channel East (Currituck Replica)').
REPLICA_OF['us-az-currituck-beach'] = 'us-nc-currituck-beach'

# Lake Havasu's copy of East Quoddy Head Light, Head Harbour Light Station on Campobello Island (Rowlett:
# 'Bridgewater Channel North (East Quoddy Head Replica)').
REPLICA_OF['us-az-east-quoddy'] = 'ca-nb-head-harbour'

# Lake Havasu's copy of Fire Island Light (Rowlett: 'Thompson Bay (Fire Island Replica)').
REPLICA_OF['us-az-fire-island'] = 'us-ny-fire-island'

# Lake Havasu's copy of Pemaquid Point Light.
REPLICA_OF['us-az-pemaquid-point'] = 'us-me-pemaquid-point'

# Lake Havasu's copy of Point Gratiot Light, which is Dunkirk Light (Rowlett: 'West Point II (Dunkirk
# Replica, Point Gratiot Replica)').
REPLICA_OF['us-az-point-gratoit'] = 'us-ny-dunkirk'

# Lake Havasu's copy of the Robert H. Manning Memorial Light (Rowlett: 'Crazy Horse Marina (Robert R.
# Manning Replica)').
REPLICA_OF['us-az-robert-h-manning'] = 'us-mi-manning-memorial'

# Lake Havasu's copy of Split Rock Lighthouse (Rowlett: 'West Point I (Split Rock Replica)').
REPLICA_OF['us-az-split-rock'] = 'us-mn-split-rock'

# Lake Havasu's copy of Vermilion Light (Rowlett: 'Pittsburgh Point (Vermilion Replica)').
REPLICA_OF['us-az-vermilion'] = 'us-oh-vermilion'

# Lake Havasu's copy of West Quoddy Head Light (Rowlett: 'Lake Havasu Yacht Club (West Quoddy Head
# Replica)').
REPLICA_OF['us-az-west-quoddy'] = 'us-me-west-quoddy-head'

# Lake Havasu's copy of White Shoal Light (Rowlett: 'Havasu Island Golf Course (White Shoal Replica)').
REPLICA_OF['us-az-white-shoal'] = 'us-mi-white-shoal'

# Lake Havasu's copy of Wind Point Light (Rowlett: 'Southwest Point II (Wind Point Replica)').
REPLICA_OF['us-az-wind-point'] = 'us-wi-wind-point'

# A copy of Grays Harbor Light on the Colorado River side of Lake Havasu.
REPLICA_OF['us-ca-grays-harbor'] = 'us-wa-grays-harbor'

# A copy of Portland Head Light on Lake Havasu (Rowlett: 'Pilot Rock (Portland Head Replica)').
REPLICA_OF['us-ca-portland-head'] = 'us-me-portland-head'

# A copy of Umpqua River Light on Lake Havasu.
REPLICA_OF['us-ca-umpqua-river'] = 'us-or-umpqua-river'

# Mystic Seaport's 1966 copy of Brant Point Light (OpenStreetMap: 'Brant Point Replica Lighthouse';
# LighthouseFriends: 'Mystic Seaport (Replica)').
REPLICA_OF['us-ct-mystic-seaport'] = 'us-ma-brant-point'

# The Trinidad Memorial Lighthouse is a copy of Trinidad Head Light, built as a memorial to lost fishermen
# (LighthouseFriends: memorial).
REPLICA_OF['us-ca-trinidad-memorial'] = 'us-ca-trinidad-head'

# The 1985 replica of Lazaretto Point Light (OpenStreetMap, LighthouseFriends: replica; Rowlett built 1985);
# the original of 1831-1926 is the Society's Lazaretto Point.
REPLICA_OF['us-md-lazaretto-point'] = 'us-md-lazaretto-point-2'

# The replica of Olcott Light (2003; Rowlett: a decorative light is displayed); the original of 1873 is the
# Society's Olcott.
REPLICA_OF['us-ny-olcott'] = 'us-ny-olcott-2'

# The replica at Tuckerton Seaport (1999) copies Tucker's Island Light (1848-1927).
REPLICA_OF['us-nj-tuckers-beach'] = 'us-nj-tuckers-island'

# ---- Successive lights that are two stations (preceded_by / succeeded_by) ----
# RULING (DESIGN 3.2): Old Point Loma (1855-1891) and New Point Loma (1891-) are two stations, linked.
SUCCESSION.append(('us-ca-old-point-loma', 'us-ca-point-loma'))

# Fort Tompkins Light (1828, relit 1873) and Fort Wadsworth Light (1903) stand within 13 m on Staten Island
# under different names; the fort changed its name. Linked, not joined: the sources do not say the first
# tower was replaced by the second.
SUCCESSION.append(('us-ny-fort-tompkins', 'us-ny-fort-wadsworth'))

# The first Chicago Harbor light (1832-1859, at the river mouth) and Chicago Harbor Light (1893, Navy Pier
# breakwater, 2.4 km east) are two stations under one name at separate sites.
SUCCESSION.append(('us-il-chicago-harbor-2', 'us-il-chicago-harbor'))

# St. Johns River Light (1859, Mayport) and St. Johns Light (1954) are separate towers 2.8 km apart under
# different names.
SUCCESSION.append(('us-fl-st-johns-river', 'us-fl-st-johns'))

# The Three Sisters of Nauset (1838), now preserved in a park, were Nauset's first lights; Nauset Light
# (1877) replaced them 370 m away.
SUCCESSION.append(('us-ma-three-sisters-of-nauset', 'us-ma-nauset'))

# RULING (DESIGN 3.2): Old Presque Isle Light (1840) and the New Presque Isle Light (1871) are two stations
# 1.9 km apart, each with its own established name.
SUCCESSION.append(('us-mi-old-presque-isle', 'us-mi-new-presque-isle'))

# The screwpile light of 1868 and the present Smith Point Light (1897), 1.2 km apart.
SUCCESSION.append(('us-va-smith-point-old', 'us-va-smith-point'))

# ---- Reviewed and kept visible ----
# Listed by the Light List (7-18366) as a lit aid.
KEEP_VISIBLE.add('us-mi-manning-memorial')

# Listed by the Light List (7-8260) as a lit aid.
KEEP_VISIBLE.add('us-mi-william-livingstone-memorial')

# A memorial lighthouse that showed a light for ships (1913-1967).
KEEP_VISIBLE.add('us-ny-titanic-memorial')

# A monument with a lit aid on top (Light List 7-5670).
KEEP_VISIBLE.add('us-oh-perrys-victory-and-international-peace-memorial')

# A private aid in the Light List (6-0640), although the Society calls it faux.
KEEP_VISIBLE.add('us-or-cleft-of-the-rock')

# Wikidata, ARLHS and Rowlett list it as a lighthouse; it is lit, although the Society calls it faux.
KEEP_VISIBLE.add('us-wi-asylum')

# Charted as a fixed green light (NOAA ENC 33.760 N, 118.194 W), though the Society calls it a private
# (faux) lighthouse.
KEEP_VISIBLE.add('us-ca-lions')

# Listed by the Light List (7-12608) as a lit aid, though the Society calls it a private (faux) lighthouse.
KEEP_VISIBLE.add('us-mi-wawatam')

# NRHP-listed (82003614) and in Wikidata, although the Society calls it a private (faux) lighthouse.
KEEP_VISIBLE.add('us-oh-grand-lake-st-marys')

# A historic light of 1887 (Wikidata, LighthouseFriends, Rowlett) that the Society lists as a private (faux)
# lighthouse.
KEEP_VISIBLE.add('us-pa-turtle-rock')

# Listed by the Light List (7-20765) as a lit private aid, though the Society calls it a private (faux)
# lighthouse.
KEEP_VISIBLE.add('us-wi-kevich')

# The lost lighthouse of 1840-1859 (LighthouseFriends, the Society); the faux lighthouse the Society also
# lists in the town is a separate structure.
KEEP_VISIBLE.add('us-mi-new-buffalo')

