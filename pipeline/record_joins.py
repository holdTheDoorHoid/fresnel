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

# Hog Island Light (1853, tower of 1896, discontinued 1948). First review: Wikidata's end date was the only evidence.
# Duplicate audit (2026-10-27): LighthouseFriends (destroyed) and Rowlett, a station of their own until then, join it, and
# the Society's archive lists it as lost.
STATUS_PICKS['us-va-hog-island'] = ('lost', "Discontinued in 1948; LighthouseFriends lists the tower as destroyed and the Society's archive as lost. Its lens is displayed at Portsmouth.")

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



# ---------------------------------------------------------------------------------------------
# Life-Saving Service lists (agent/gaps, 2026-10-21): records of data/sources/lss_reports.json that are the
# same station as one another source already holds, where the list's approximate position is too far from the
# register's point (or the register names the building by its number) for the matcher to see it. Evidence for
# each: the station's name in the report, the register's name, and the distance between the two points.
# ---------------------------------------------------------------------------------------------

# "Umpqua River" station (Winchester Bay), 1891; the Coast Guard station that replaced it stands on the same
# spot. The printed position is 4.4 km from the register's point; no other Umpqua River station exists.
_join('us-or-u-s-coast-guard-station-umpqua-river-administration-and-equipment', 'lss_reports:or-umpqua-river')

# Wikidata/NRHP "Coquille River Life Boat Station", 0.5 km from the printed position of "Coquille River".
_join('us-or-coquille-river-life-boat-station', 'lss_reports:or-coquille-river')

# NRHP "Indian River Life Saving Service Station", 0.7 km from the printed position of "Indian River Inlet".
_join('us-de-indian-river-life-saving-service-station', 'lss_reports:de-indian-river-inlet')

# NRHP "U.S. Life Saving Station No. 14" (Island Beach State Park), 0.2 km from "Island Beach"; the list's
# fourteenth station of the Fifth District.
_join('us-nj-u-s-life-saving-station-no-14', 'lss_reports:nj-island-beach')

# NRHP "U.S. Life-Saving Station No. 35" (Strathmere), 0.5 km from "Tathams".
_join('us-nj-u-s-life-saving-station-no-35', 'lss_reports:nj-tathams')

# Klipsan Beach Life Saving Station (Ocean Park, WA), 0.4 km from the list's "Ilwaco Beach", which the 1909 list
# places "13 miles north of Cape Disappointment": the same station under the name of the nearest town.
_join('us-wa-klipsan-beach-life-saving-station', 'lss_reports:wa-ilwaco-beach')

# West Quoddy Lifesaving Station (NRHP, Wikidata), 1.3 km from the list's "Quoddy Head".
_join('us-me-west-quoddy-lifesaving-station', 'lss_reports:me-quoddy-head')


# ---------------------------------------------------------------------------------------------
# Lightship stations (agent/gaps, 2026-10-21): lightship_stations records whose station the matcher cannot see.
# ---------------------------------------------------------------------------------------------

# Wikidata's "Five Fathom Bank light station" (Q18150126) is the Society's Five Fathom Bank lightship station, but
# its point (38.8354 N, 75.0119 W) is at the mouth of Delaware Bay, 38 km from where the Light List prints the
# lightship (1900, page 92, entry 462: 38 47 20 N, 74 34 36 W, off Cape May). The Light List's point leads; Wikidata's is set aside.
_join('us-nj-five-fathom-bank', 'lightship_stations:five-fathom-bank')
NO_POSITION.add('wikidata:Q18150126')

# The Society's and Light Lists' name for the station is "Five Fathom Bank"; Wikidata's label adds "light station".
NAME_PICKS['us-nj-five-fathom-bank'] = 'Five Fathom Bank'

# The surviving lightship Swiftsure (LV-83) was two stations: us-wa-swiftsure (Wikidata Q7656131) and us-wa-swiftsure-2
# (Lighthouse Friends 185 and the National Register 75001852). One vessel: both carry NRHP number 75001852, Wikidata's Wikipedia
# link is "United States lightship Swiftsure (LV-83)" and Lighthouse Friends' title is "Lightship Swiftsure LV 83/WAL 508", both are
# in King County, WA. The matcher kept them apart because Wikidata's point (47.6749 N, 122.207 W) is 11.0 km from the register's
# batch point (47.6282, -122.3367) and Lighthouse Friends' (47.62806, -122.33703), which agree with each other to 30 m and lie at
# Lake Union, Seattle, where the ship is berthed; the hard-key join reaches 10 km. Wikidata's point is the wrong one. The records of
# us-wa-swiftsure-2 join the plainer id (both are live; the file of -2 stays, hidden, with merged_into, and its address redirects).
_join('us-wa-swiftsure', 'lighthousefriends:185', 'nrhp:75001852')
NO_POSITION.add('wikidata:Q7656131')


# ---------------------------------------------------------------------------------------------
# Duplicate audit (2026-10-27; docs/sources/review_2026-10-us.md, "Duplicate audit"): stations that turned out to be
# one station split in two (a rebuilt or relocated tower, the two halves of a range, a Society or National Register
# record whose point is far off), records filed under the wrong station, and display names that are not the light's.
# ---------------------------------------------------------------------------------------------

# us-fl-cape-saint-george into us-fl-cape-st-george (rebuilt tower, 19.7 km)
# Cape St. George Light: the 1852 tower on Cape St. George (Little St. George Island; Wikidata Q5035066, NRHP
# 74000625, the Society's archive, Rowlett) toppled into the Gulf on 21 October 2005 and was rebuilt in 2007-08
# from the original drawings in the county park in the town of St. George Island, 19.7 km north-east, opened in
# November 2008 and dedicated on 4 April 2009 (LighthouseFriends 592). The OpenStreetMap way, LighthouseFriends,
# the Light List's 'St. George Lighthouse' (4-75) and the ENC point are the rebuilt tower; OpenStreetMap tags it
# with the same NRHP number. One station whose tower was rebuilt elsewhere, not two; the Light List number 4-75 is
# Wikidata's 4-0075.
_join('us-fl-cape-st-george',
      'enc:29.66294,-84.86287',
      'lighthousefriends:592',
      'osm:way/319963532',
      'uscg_light_list:4-75')

# us-ak-cape-hinchinbrook-2 into us-ak-cape-hinchinbrook (register point wrong, 33 km)
# The National Register's Cape Hinchinbrook Light Station (05000728) is the station that Wikidata and
# OpenStreetMap already tag with that number; the register's batch point is 33 km south, in open water.
_join('us-ak-cape-hinchinbrook', 'nrhp:05000728')
NO_POSITION.add('nrhp:05000728')

# us-ak-cape-st-elias-2 into us-ak-cape-st-elias (archive point wrong, 131 km)
# The Society's Cape St. Elias (1916, active, third-order lens) is Cape St. Elias Light on Kayak Island; the
# archive's point (60.158 N, 146.835 W) is 131 km away, near Cordova.
_join('us-ak-cape-st-elias', 'uslhs:2688')
NO_POSITION.add('uslhs:2688')

# us-ca-cape-mendocino-2 into us-ca-cape-mendocino (relocated tower, 54.5 km)
# Cape Mendocino Light's 1868 iron tower was taken down in 1998 and re-erected at Mal Coombs Park, Shelter Cove,
# 54 km south; OpenStreetMap's 'Cape Mendocino Light' and LighthouseFriends map it there. Wikidata and the
# Society's archive place the station on the cape. One station, its tower now elsewhere.
_join('us-ca-cape-mendocino',
      'lighthousefriends:25',
      'osm:way/940995632')

# us-ca-carquinez-strait-2 into us-ca-carquinez-strait (archive point wrong, 13 km)
# The Society's Carquinez Strait (1910 dwelling, discontinued 1951) is the lighthouse Wikidata, LighthouseFriends
# and Rowlett place at Glen Cove, Vallejo; the archive's rounded point is 13 km west and no other Carquinez light
# exists.
_join('us-ca-carquinez-strait', 'uslhs:2704')
NO_POSITION.add('uslhs:2704')

# us-ca-punta-gorda-2 into us-ca-punta-gorda (archive point wrong, 27 km)
# The Society's Punta Gorda (1912, discontinued 1951) is Punta Gorda Light; the archive's point is 27 km out at
# sea.
_join('us-ca-punta-gorda', 'uslhs:2727')
NO_POSITION.add('uslhs:2727')

# us-ca-southampton-shoal-2 into us-ca-southampton-shoal (relocated tower, 81 km)
# LighthouseFriends' Southampton Shoal is the 1905 lighthouse whose top two stories were lifted off the shoal in
# 1966 and barged to Tinsley Island in the Delta for the St. Francis Yacht Club; its point is where they stand
# now. The station (Wikidata, the Light List's 6-5480, Rowlett, the Society) is on the shoal.
_join('us-ca-southampton-shoal', 'lighthousefriends:101')

# us-ca-table-bluff-2 into us-ca-table-bluff (relocated tower, 15.5 km)
# Table Bluff Light (1892, discontinued 1961; Wikidata, the Society's archive) stood on the bluff south of
# Humboldt Bay; the lighthouse was cut in two and moved to Woodley Island Marina, Eureka, in 1987
# (LighthouseFriends 62, OpenStreetMap). One station, its tower now elsewhere.
_join('us-ca-table-bluff',
      'uslhs:2731',
      'wikidata:Q7673128')

# us-de-liston-range-front-2 into us-de-liston-range-front (register point wrong, 31 km)
# The National Register's Liston Range Front Lighthouse (03001386) is the front light that Wikidata and
# OpenStreetMap tag with that number; the register's batch point is 31 km north, near Wilmington.
_join('us-de-liston-range-front', 'nrhp:03001386')
NO_POSITION.add('nrhp:03001386')

# us-de-mispillion-2 into us-de-mispillion (relocated tower, 24 km)
# LighthouseFriends' Mispillion (place Lewes, private) is the 1873 Mispillion River lighthouse, moved to Lewes
# after the 2002 fire; the station (Wikidata, NRHP 86002919, Rowlett, the Society) is at the river mouth.
_join('us-de-mispillion', 'lighthousefriends:455')

# us-de-port-penn-range-front into us-de-port-penn-range (range, 3.2 km)
# The Society's Port Penn Range Front (1877-1904) is the front light of LighthouseFriends' Port Penn Range; DESIGN
# 3.2: a range is one station with a front and a rear structure.
_join('us-de-port-penn-range', 'uslhs:32690')

# us-de-port-penn-range-rear into us-de-port-penn-range (range, 280 m)
# The Society's Port Penn Range Rear (1877-1905) is the rear light of the same range, 280 m from
# LighthouseFriends' point.
_join('us-de-port-penn-range', 'uslhs:8400')

# us-de-reedy-island-range-front into us-de-reedy-island-range-rear (range, 4.1 km)
# The Society's Reedy Island Range Front (1904) is the front of the range whose rear is the Taylors Bridge tower
# (Wikidata, NRHP 89000288, Light List 2-2585); one station with a front and a rear structure.
_join('us-de-reedy-island-range-rear', 'uslhs:33270')
NO_POSITION.add('uslhs:33270')

# records into us-de-reedy-island-range-rear (record misfiled)
# The Society's 'Reedy Island Range Rear' (1904, fourth-order lens of 1910, active) is the Taylors Bridge rear
# light; the archive gave it the same point as its 'Reedy Island Old' (39.5017 N, 75.57 W), so the first build
# filed it under the old Reedy Island light 10.6 km north. The record moves to the range; Old Reedy Island keeps
# its own records.
_join('us-de-reedy-island-range-rear', 'uslhs:2762')
NO_POSITION.add('uslhs:2762')

# us-fl-cape-san-blas-2 into us-fl-cape-san-blas (relocated tower, 16.5 km)
# The Society's Cape San Blas (1885 tower, discontinued 1996) is Cape San Blas Light; its point is the cape, where
# the tower stood until it was moved to Port St. Joe in 2014 (Wikidata, OpenStreetMap, NRHP 15000208 'Cape San
# Blas Lighthouse at Port St. Joe').
_join('us-fl-cape-san-blas', 'uslhs:2769')

# us-fl-charlotte-harbor-2 into us-fl-charlotte-harbor (archive point wrong, 95 km)
# The Society's Charlotte Harbor (1890-1943) is Charlotte Harbor Light (Wikidata, LighthouseFriends); the
# archive's point is 95 km out in the Gulf.
_join('us-fl-charlotte-harbor', 'uslhs:8404')
NO_POSITION.add('uslhs:8404')

# us-fl-st-johns-2 into us-fl-st-johns (archive point wrong, 38 km)
# The Society's St. Johns (1954, automated 1967) is St. Johns Light at Mayport; the archive's point is 38 km
# north-west.
_join('us-fl-st-johns', 'uslhs:41509')
NO_POSITION.add('uslhs:41509')

# us-fl-st-johns-river-2 into us-fl-st-johns-river (archive point wrong, 40 km)
# The Society's St. Johns River (1859 tower, 1830-1929) is St. Johns River Light at Mayport; the archive's point
# is 40 km north-west.
_join('us-fl-st-johns-river', 'uslhs:2787')
NO_POSITION.add('uslhs:2787')

# us-ga-saint-simons-island-range-front into us-ga-st-simons-island (range, 870 m)
# The Society's Saint Simons Island Range Front (1895) is the front of the range whose rear was the St. Simons
# lighthouse itself (the archive's 'St. Simons Island Range Rear', already in the station); one station.
_join('us-ga-st-simons-island', 'uslhs:15265')
NO_POSITION.add('uslhs:15265')

# us-la-amite-river-2 into us-la-amite-river (archive point wrong, 87 km)
# Amite River light (1882, lost): the Society's point is a geocode of the town 87 km inland; LighthouseFriends and
# the Light List's Amite River Entrance Light place the light at the river's mouth on Lake Maurepas. One light;
# the plain id is kept.
_join('us-la-amite-river',
      'lighthousefriends:1802',
      'uscg_light_list:4-11650')
NO_POSITION.add('uslhs:8432')

# us-la-east-rigolets-2 into us-la-east-rigolets (archive point wrong, 44 km)
# The Society's East Rigolets (1833-1874) is East Rigolets Light (Wikidata, LighthouseFriends); the archive's
# point is 44 km west, on the north shore of Lake Pontchartrain.
_join('us-la-east-rigolets', 'uslhs:8440')
NO_POSITION.add('uslhs:8440')

# us-la-oyster-bayou-2 into us-la-oyster-bayou (archive point wrong, 17 km)
# Oyster Bayou light (1904-1975, lost): LighthouseFriends places it at the bayou's mouth on the Gulf; the
# Society's point is 17 km inland in the marsh. One light; the plain id is kept.
_join('us-la-oyster-bayou', 'lighthousefriends:1811')
NO_POSITION.add('uslhs:8444')

# us-la-pass-a-l-outre into us-la-pass-a-loutre (archive point wrong, 14 km)
# The Society's 'Pass a L' Outre' (1855-1934) is Pass A L'Outre Light (Wikidata, LighthouseFriends, Rowlett); the
# archive's point is 14 km north. The ids differ only by the apostrophe.
_join('us-la-pass-a-loutre', 'uslhs:2808')
NO_POSITION.add('uslhs:2808')

# us-ma-old-harbor-u-s-life-saving-station-2 into us-ma-old-harbor-u-s-life-saving-station (relocated station, 48.7 km)
# Old Harbor Life-Saving Station (1897) stood on Nauset Beach, Chatham (NRHP 75000159 and the Service's list place
# it there); it was floated by barge to Race Point, Provincetown, in 1977, where Wikidata places it (its item has
# the 1977 relocation). One station.
_join('us-ma-old-harbor-u-s-life-saving-station',
      'lss_reports:ma-old-harbor',
      'nrhp:75000159')

# us-md-seven-foot-knoll-2 into us-md-seven-foot-knoll (relocated tower, 22.5 km)
# The Society's Seven Foot Knoll (1855-1987) is Seven Foot Knoll Light; its point is the knoll in the Patapsco,
# where the screwpile stood until it was moved to Baltimore's Inner Harbor in 1988 (Wikidata, OpenStreetMap,
# NRHP).
_join('us-md-seven-foot-knoll', 'uslhs:2881')

# us-me-mount-desert-2 into us-me-mount-desert (register point wrong, 66 km)
# The National Register's Mount Desert Light Station (88000155, 'Mount Desert Rock Light Station') is the light on
# Mount Desert Rock that Wikidata and OpenStreetMap tag with that number; the batch point is 66 km west.
_join('us-me-mount-desert', 'nrhp:88000155')
NO_POSITION.add('nrhp:88000155')

# us-me-ram-island-2 into us-me-ram-island (register point wrong, 90 km)
# The National Register's Ram Island Light Station (87002280, Lincoln County) is Ram Island Light at Boothbay,
# which Wikidata tags with that number; the batch point is 90 km east.
_join('us-me-ram-island', 'nrhp:87002280')
NO_POSITION.add('nrhp:87002280')

# us-mi-frying-pan-island-2 into us-mi-frying-pan-island (relocated tower, 66 km)
# Frying Pan Island light (1882, discontinued 1988): the Society's record says 'relocated to Coast Guard Station
# Sault St. Marie', where OpenStreetMap and LighthouseFriends map the tower; the archive's point and the Light
# List's modern 'Frying Pan Island Light 7' are at the island off De Tour. One station, its tower now elsewhere;
# the plain id is kept.
_join('us-mi-frying-pan-island',
      'uscg_light_list:7-12835',
      'uslhs:8506')

# us-mi-peche-island-range-rear into us-mi-peche-island-rear-range (archive point wrong, 86 km)
# Peche Island Range Rear: the 1908 tower moved to Marine City in 1983 (Wikidata, OpenStreetMap,
# LighthouseFriends) and Rowlett's present rear light (Light List 7-8410) at the range; the Society's point is 86
# km west, inland. One station.
_join('us-mi-peche-island-rear-range',
      'rowlett:misel:peche-island-range-rear-5',
      'uslhs:7104')
NO_POSITION.add('uslhs:7104')

# us-mi-presque-isle-range-rear into us-mi-presque-isle-rear-range (range, 607 m)
# Presque Isle Harbor Range (1870-71): the Light List's front (7-11565) and rear (7-11570) are 240 m apart;
# OpenStreetMap's 'Presque Isle Rear Range Lighthouse', LighthouseFriends' 'Presque Isle Range' and Rowlett's
# front made one station, the Society's, Rowlett's and the Light List's rear another. DESIGN 3.2: one station with
# a front and a rear.
_join('us-mi-presque-isle-rear-range',
      'enc:45.33834,-83.48243',
      'rowlett:minel:presque-isle-range-rear-1',
      'rowlett:minel:presque-isle-range-rear-2',
      'uscg_light_list:7-11570',
      'uslhs:9820')

# us-mi-squaw-island-2 into us-mi-squaw-island (archive point wrong, 130 km)
# The Society's Squaw Island (1892) is Squaw (Ojibwa) Island Light off Beaver Island; the archive's point is 130
# km south, inland.
_join('us-mi-squaw-island', 'uslhs:3340')
NO_POSITION.add('uslhs:3340')

# us-mn-minnesota-point-2 into us-mn-minnesota-point (archive point wrong, 54 km)
# The Society's Minnesota Point (1858, ruins) is Minnesota Point Light on Park Point, Duluth; the archive's point
# is 54 km north, inland.
_join('us-mn-minnesota-point', 'uslhs:8539')
NO_POSITION.add('uslhs:8539')

# us-ms-biloxi-2 into us-ms-biloxi (archive point wrong, 65 km)
# The Society's Biloxi (1848, active, town Biloxi) is Biloxi Light; the archive's point is 65 km north-west,
# inland.
_join('us-ms-biloxi', 'uslhs:3359')
NO_POSITION.add('uslhs:3359')

# us-ms-ship-island-3 into us-ms-ship-island-2 (archive point wrong, 64 km)
# The Society's Ship Island (1853) is Ship Island Light (Wikidata, LighthouseFriends, Light List 4-335); the
# archive's point is 64 km west, inland.
_join('us-ms-ship-island-2', 'uslhs:8549')
NO_POSITION.add('uslhs:8549')

# us-nc-roanoke-river-3 into us-nc-roanoke-river (relocated tower, 14.5 km)
# The Society's Roanoke River (1887-1941) is the screwpile cottage that stood at the river's mouth, the archive's
# point; it was moved to Edenton, where Wikidata, OpenStreetMap and LighthouseFriends place it. The 2003 replica
# at Plymouth (us-nc-roanoke-river-2) is a separate station.
_join('us-nc-roanoke-river', 'uslhs:3370')

# us-ny-new-dorp-range-rear into us-ny-new-dorp (same light, 630 m)
# The Society's New Dorp Range Rear (1856-1964) is New Dorp Light, the rear of the Swash Channel Range (Rowlett:
# 'New Dorp (Swash Channel Range Rear)'); same years, the archive's point rounded 630 m off.
_join('us-ny-new-dorp', 'uslhs:3420')

# us-ny-shinnecock-2 into us-ny-shinnecock (archive point wrong, 29 km)
# The Society's Shinnecock (1858-1931) is Shinnecock (Ponquogue) Light; the archive's point is 29 km west.
_join('us-ny-shinnecock', 'uslhs:8825')
NO_POSITION.add('uslhs:8825')

# us-ny-strawberry-island-upper-cut-range-rear into us-ny-strawberry-island-upper-cut-range (range, archive point wrong)
# The Society's Strawberry Island Upper Cut Range Rear (1908-1951) is the rear of the Upper Cut Range on the
# Niagara River at Buffalo; the archive's point is in Lake Ontario near Toronto, 86 km away.
_join('us-ny-strawberry-island-upper-cut-range', 'uslhs:8831')
NO_POSITION.add('uslhs:8831')

# records into us-ny-strawberry-island-lower-cut-range (range, record misfiled)
# Rowlett's Strawberry Island Lower Cut Range Rear (1908) is the rear of the Lower Cut Range (LighthouseFriends,
# the Light List's front 7-3015); a truncated ARLHS number (Rowlett's 'USA-122') had filed it under a station
# named Titanic Memorial. The Society's record of the same rear stays in that station, now hidden, because a
# station needs a positioned record and the Society's is the only one there.
_join('us-ny-strawberry-island-lower-cut-range', 'rowlett:nyw:strawberry-island-lower-cut-range-rear-4')

# us-ny-titanic-memorial-3 into us-ny-titanic-memorial (archive point wrong, 52 km)
# The Society's Titanic Memorial (1913) is the Titanic Memorial Lighthouse at South Street Seaport (Wikidata,
# LighthouseFriends); the archive's point is 52 km north.
_join('us-ny-titanic-memorial', 'uslhs:8835')
NO_POSITION.add('uslhs:8835')

# records into us-ny-titanic-memorial (record misfiled)
# Rowlett's Titanic Memorial (built 1913, light shown 1913-1967) is the Manhattan memorial; its truncated ARLHS
# number 'USA-122' (Wikidata: USA1229) had filed it with two unrelated upstate lights.
_join('us-ny-titanic-memorial', 'rowlett:nydn:titanic-memorial')

# us-oh-ashtabula-west-pier-range-rear into us-oh-ashtabula-west-pier-range-front (range, archive point wrong)
# The Society's Ashtabula West Pier Range Rear (1876) is the rear of the range whose front it also lists; the
# archive's point for the rear is 5.9 km inland. One station with a front and a rear.
_join('us-oh-ashtabula-west-pier-range-front', 'uslhs:7419')
NO_POSITION.add('uslhs:7419')

# us-oh-cunningham-creek-2 into us-oh-cunningham-creek (archive point wrong, 93 km)
# The Society's Cunningham Creek (1835-1847) is LighthouseFriends' lost Cunningham Creek light at Madison on Lake
# Erie; the archive's point is 93 km south (41.01 N for 41.85 N).
_join('us-oh-cunningham-creek', 'uslhs:8873')
NO_POSITION.add('uslhs:8873')

# us-or-yaquina-bay-2 into us-or-yaquina-bay (archive point wrong, 46 km)
# The Society's Yaquina Bay (1871, discontinued 1874) is Yaquina Bay Light at Newport; the archive's point is 46
# km north.
_join('us-or-yaquina-bay', 'uslhs:3467')
NO_POSITION.add('uslhs:3467')

# us-sc-bloody-point-range-rear into us-sc-bloody-point-range (range, 680 m)
# The Society's Bloody Point Range Rear (1883-1899) is the rear of the Bloody Point Range (Wikidata's item for the
# range, LighthouseFriends' and the Society's front); one station with a front and a rear.
_join('us-sc-bloody-point-range', 'uslhs:8910')

# us-sc-bulls-bay-2 into us-sc-bulls-bay (archive point wrong, 18 km)
# The Society's Bulls Bay (1852-1913) is Bulls Bay Light (Wikidata, LighthouseFriends); the archive's point is 18
# km north, inland.
_join('us-sc-bulls-bay', 'uslhs:8911')
NO_POSITION.add('uslhs:8911')

# us-sc-fort-ripley-shoal-2 into us-sc-fort-ripley-shoal (archive point wrong, 80 km)
# The Society's Fort Ripley Shoal (1878-1932) is Fort Ripley Shoal Light in Charleston Harbor; the archive's point
# is 80 km inland.
_join('us-sc-fort-ripley-shoal', 'uslhs:8915')
NO_POSITION.add('uslhs:8915')

# us-sc-hilton-head-range-front into us-sc-hilton-head-range-rear (range, 1.7 km)
# The Society's Hilton Head Range Front (1880-1932, lost) is the front of the range whose rear is the Leamington
# tower; one station with a front and a rear.
_join('us-sc-hilton-head-range-rear', 'uslhs:8917')
NO_POSITION.add('uslhs:8917')

# us-sc-morris-island-range-rear into us-sc-morris-island-range-front (range, 3.7 km)
# The Society's Morris Island Range Front and Rear (1902) are the two lights of one range, kept apart from the
# Morris Island lighthouse (the archive lists the range separately).
_join('us-sc-morris-island-range-front', 'uslhs:8919')

# records into us-sc-morris-island (record misfiled)
# The Society's 'Morris Island' (other name Old Charleston; tower 1876, light 1768-1962) is Morris Island Light;
# the archive's point is the Sullivan's Island light 7 km north, so the first build made it a second tower of
# us-sc-charleston.
_join('us-sc-morris-island', 'uslhs:3515')
NO_POSITION.add('uslhs:3515')

# us-tx-galveston-jetty-2 into us-tx-galveston-jetty (archive point wrong, 65 km)
# Galveston Jetty light (1918-1973): LighthouseFriends places it on the south jetty at Galveston; the Society's
# point is 65 km inland, south of Houston. One light; the plain id is kept.
_join('us-tx-galveston-jetty', 'lighthousefriends:154')
NO_POSITION.add('uslhs:3516')

# us-tx-sabine-bank-2 into us-tx-sabine-bank (shore point, 68 km)
# LighthouseFriends' Sabine Bank is the 1906 caisson light on Sabine Bank, 16 miles off the Sabine River; its
# point is on shore at Port Arthur, 68 km from the bank (Wikidata), and is set aside.
_join('us-tx-sabine-bank', 'lighthousefriends:150')
NO_POSITION.add('lighthousefriends:150')

# us-va-hog-island-2 into us-va-hog-island (lens display point, 82 km)
# LighthouseFriends' and Rowlett's Hog Island (tower of 1896, discontinued 1948) is Hog Island Light on the
# Eastern Shore (place Machipongo); the point LighthouseFriends gives is Portsmouth, where the light's lens is
# displayed (Rowlett: 'lens'), and is set aside.
_join('us-va-hog-island',
      'lighthousefriends:1894',
      'rowlett:va:hog-island-2')
NO_POSITION.add('lighthousefriends:1894')

# us-va-wolf-trap-2 into us-va-wolf-trap (register point wrong, 18 km)
# The National Register's Wolf Trap Light Station (02001434) is Wolf Trap Light, which Wikidata tags with that
# number; the batch point is 18 km south.
_join('us-va-wolf-trap', 'nrhp:02001434')
NO_POSITION.add('nrhp:02001434')

# us-vt-colchester-reef-2 into us-vt-colchester-reef (archive point wrong, 96 km)
# The Society's Colchester Reef (1871-1933) is Colchester Reef Light, now at the Shelburne Museum; the archive's
# longitude (72.05 W) is 96 km east of Lake Champlain.
_join('us-vt-colchester-reef', 'uslhs:3534')
NO_POSITION.add('uslhs:3534')

# us-wa-gig-harbor-2 into us-wa-gig-harbor (archive point wrong, 38 km)
# The Society's Gig Harbor is the Gig Harbor light (OpenStreetMap, LighthouseFriends, Light List 6-17221), the
# only light of that name; the archive's point is 38 km north-west.
_join('us-wa-gig-harbor', 'uslhs:8982')
NO_POSITION.add('uslhs:8982')

# us-wi-racine-north-breakwater-2 into us-wi-racine-north-breakwater (archive point wrong, 69 km)
# The Society's 'RACINE North Breakwater' (1872-1987) is Racine North Breakwater Light; the archive's point is 69
# km inland.
_join('us-wi-racine-north-breakwater', 'uslhs:3580')
NO_POSITION.add('uslhs:3580')

# us-wi-racine-harbor into us-wi-racine-harbor-lighthouse-and-life-saving (archive point wrong, 69 km)
# The Society's Racine Harbor (1866) is the Racine Harbor (Root River) lighthouse of 1866; the archive gives it
# the same inland point as its Racine North Breakwater, 69 km off.
_join('us-wi-racine-harbor-lighthouse-and-life-saving', 'uslhs:35833')
NO_POSITION.add('uslhs:35833')

# us-fl-fort-barrancas into us-fl-fort-barrancas-range (range, 720 m)
# LighthouseFriends' Fort Barrancas page is the history of the Fort Barrancas range lights (front and rear), which
# the Society lists as the range; one station. Whether the range's rear is the Pensacola tower stays open.
_join('us-fl-fort-barrancas-range', 'lighthousefriends:1832')

# us-ga-elba-island into us-ga-elba-island-range (same light, 860 m)
# The Society's Elba Island (light station, 1905) and LighthouseFriends' Elba Island Range are the Savannah River
# lights on Elba Island, which LighthouseFriends describes as a range of two lights; no source has another light
# on the island.
_join('us-ga-elba-island-range', 'uslhs:8411')
NO_POSITION.add('uslhs:8411')

# us-ga-wolf-island into us-ga-wolf-island-range (range, 570 m)
# LighthouseFriends' Wolf Island page describes the Wolf Island beacons as a range (1822 beacon, 1868 rear range
# light), the range the Society lists with its front and rear; one station.
_join('us-ga-wolf-island-range', 'lighthousefriends:1851')

# us-mi-ecorse into us-mi-ecorse-range (range, 820 m)
# LighthouseFriends' Ecorse (lost) and the Society's Ecorse Range front and rear (1895) are the Ecorse range
# lights on the Detroit River; one station.
_join('us-mi-ecorse-range', 'lighthousefriends:1996')

# us-nc-brant-island into us-nc-brant-island-shoal (same light, 340 m)
# LighthouseFriends' Brant Island (lost) is the Brant Island Shoal screwpile light in Pamlico Sound that Rowlett,
# the Society and the Light List (2-32650) call Brant Island Shoal; 340 m apart.
_join('us-nc-brant-island-shoal',
      'enc:35.13597,-76.29296',
      'lighthousefriends:1907')

# us-hi-lahaina-harbor into us-hi-lahaina (same light, 345 m)
# The Society's and the passport list's Lahaina Harbor is Lahaina Light (Wikidata, LighthouseFriends, Light List
# 6-28460); 345 m apart, rounded.
_join('us-hi-lahaina',
      'uslhs:18617',
      'uslhs_passport:stamp:hi:lahaina-harbor')
NO_POSITION.add('uslhs:18617')

# us-tx-brazos-santiago-pass-tx-new into us-tx-brazos-santiago (same light, 350 m)
# The Society's 'Brazos Santiago Pass TX (New)' and 'Brazos Santiago Pass' are LighthouseFriends' Brazos Santiago
# at Port Isabel, 350 m apart.
_join('us-tx-brazos-santiago',
      'uslhs:13395',
      'uslhs:8925')

# us-nc-southwest-point into us-nc-southwest-point-royal-shoal (same light, 365 m)
# The Society's Southwest Point (other name Royal Shoal) is LighthouseFriends' Southwest Point Royal Shoal, 365 m
# apart.
_join('us-nc-southwest-point-royal-shoal', 'uslhs:8866')

# us-wa-semiahmoo into us-wa-semiahmoo-harbor (same light, 430 m)
# LighthouseFriends' Semiahmoo (lost) is Semiahmoo Harbor Light (Wikidata, the Society, Light List 6-19920 at the
# site); 430 m apart.
_join('us-wa-semiahmoo-harbor', 'lighthousefriends:1783')

# us-mi-grassy-island-south-channel-range into us-mi-grassy-island (range, 860 m)
# LighthouseFriends' 'Grassy Island South Range' page (in this station with Wikidata's Grassy Island Light) is the
# history of the Grassy Island light station and its south range; the Society's South Channel Range front and rear
# are that range.
_join('us-mi-grassy-island',
      'uslhs:8509',
      'uslhs:9658')

# us-mi-grassy-island-north-channel-range-rear into us-mi-grassy-island-north-range (range, 930 m)
# The Society's Grassy Island North Channel Range Rear is the rear of LighthouseFriends' Grassy Island North
# Range.
_join('us-mi-grassy-island-north-range', 'uslhs:9656')

# records into us-mi-grassy-island-north-range (record misfiled)
# The Society's Grassy Island North Channel Range Front belongs with the north range, not with the Grassy Island
# light station's south range.
_join('us-mi-grassy-island-north-range', 'uslhs:9657')

# us-mi-grosse-isle-south-channel-range-front into us-mi-grosse-isle-south-range (range, 520 m)
# The Grosse Ile South Channel Range: the Light List's and the Society's front (7-7165) joins the station that
# holds the rear (LighthouseFriends' Grosse Isle South Range, Rowlett, Light List 7-7170).
_join('us-mi-grosse-isle-south-range',
      'enc:42.18421,-83.14053',
      'enc:42.18530,-83.14195',
      'uscg_light_list:7-7165',
      'uslhs:9660')

# us-il-waukegan-harbor-pierhead into us-il-waukegan-harbor (same light, 560 m)
# The Society's Waukegan Harbor Pierhead is the Waukegan Harbor light on the north pierhead (the station holds the
# Light List's Waukegan North Pierhead Light); no other Waukegan station exists in the archive.
_join('us-il-waukegan-harbor', 'uslhs:8428')
NO_POSITION.add('uslhs:8428')

# us-nc-bald-head-old-baldy into us-nc-bald-head (same light, 600 m)
# The Society's 'Bald Head "Old Baldy"' is Bald Head Lighthouse (Old Baldy), 600 m off by its rounded point.
_join('us-nc-bald-head', 'uslhs:3361')

# us-md-fishing-battery-island into us-md-fishing-battery (same light, 610 m)
# The Society's Fishing Battery Island is Fishing Battery Light, 610 m off by its rounded point.
_join('us-md-fishing-battery', 'uslhs:2873')

# us-ca-ano-nuevo-island into us-ca-ano-nuevo (same light, 650 m)
# The Society's Ano Nuevo Island is the Año Nuevo light station on the island, 650 m off by its rounded point.
_join('us-ca-ano-nuevo', 'uslhs:8371')

# us-ny-elm-tree-range-front into us-ny-elm-tree-beacon (same light, 730 m)
# The Society's Elm Tree Range Front is Elm Tree Beacon Light, the front of the Swash Channel Range (Rowlett: 'Elm
# Tree (Swash Channel Range Front)').
_join('us-ny-elm-tree-beacon', 'uslhs:8804')
NO_POSITION.add('uslhs:8804')

# us-ny-buffalo-1818 into us-ny-buffalo-main (successive tower, 350 m)
# The Society's 'Buffalo 1818' is the first Buffalo lighthouse (1818), replaced in 1833 by the Buffalo Main tower
# at the same river mouth; successive towers of one station (DESIGN 3.2).
_join('us-ny-buffalo-main', 'uslhs:6802')

# us-mi-menominee into us-mi-menominee-pier (same light, 1.6 km)
# The Society's Menominee (other name North Pier, active) is Menominee Pier Light; the archive's point is rounded
# to five minutes.
_join('us-mi-menominee-pier', 'uslhs:2996')
NO_POSITION.add('uslhs:2996')

# us-in-michigan-city-old into us-in-old-michigan-city (archive point wrong, 72 km)
# The Society's Michigan City (Old) is Old Michigan City Light; the archive's latitude 41.073 is a slip for
# 41.723.
_join('us-in-old-michigan-city', 'uslhs:2805')
NO_POSITION.add('uslhs:2805')

# us-mi-south-fox-island-new into us-mi-south-fox-island (archive point wrong, 53 km)
# The Society's South Fox Island New is the 1934 skeleton tower of South Fox Island Light, which the station
# already holds through OpenStreetMap; the archive's point is 53 km away.
_join('us-mi-south-fox-island', 'uslhs:9235')
NO_POSITION.add('uslhs:9235')

# us-oh-vermilion-pierhead into us-oh-vermilion (same light, 2.3 km)
# The Society's Vermilion Pierhead (lost) is the 1877 Vermilion light whose replica stands at the museum and
# carries the light today (the station); the archive's point is rounded.
_join('us-oh-vermilion', 'uslhs:34241')

# us-ga-sapelo-island-range-front into us-ga-sapelo-island (range, 205 m)
# Sapelo Island: about 1877 the 1820 tower was relit as the rear light of a range whose front was the iron beacon
# 205 m away (Wikidata's 'Sapelo Island Range Front Light', LighthouseFriends 327; both discontinued 1898-99). The
# Society files the lighthouse itself as 'Sapelo Island Range Rear'. DESIGN 3.2: one station with two structures,
# kept under the storied lighthouse id; the range front's story was held back from publishing. The Society's rear
# record describes the station as a whole (its rounded point would have made a second tower).
_join('us-ga-sapelo-island',
      'lighthousefriends:327',
      'rowlett:ga:sapelo-island-range-front-2',
      'uslhs:15257',
      'uslhs:2793',
      'wikidata:Q16961245')
NO_POSITION.add('uslhs:2793')

# us-mn-two-harbors-east-breakwater into us-mn-two-harbors-breakwater (archive point wrong, 34 km)
# The Society's Two Harbors East Breakwater (1895) is the light that Rowlett ('Two Harbors East Breakwater'), the
# Light List (7-16505) and LighthouseFriends 268 place on the breakwater at Two Harbors; the archive's point is
# near Duluth, 34 km away.
_join('us-mn-two-harbors-breakwater', 'uslhs:9219')
NO_POSITION.add('uslhs:9219')

# us-ca-long-beach-harbor into us-ca-long-beach (archive point wrong, 55 km)
# The Society's Long Beach Harbor (1949) is the 1949 'Robot Light' on the Long Beach breakwater,
# LighthouseFriends' 'Long Beach Harbor'; the archive's point is 55 km north, inland.
_join('us-ca-long-beach', 'uslhs:8375')
NO_POSITION.add('uslhs:8375')

# us-fl-gasparilla-island-rear-range into us-fl-boca-grande (archive point wrong, 58 km)
# The Society's Gasparilla Island Rear Range (active) is the Boca Grande entrance rear range light at the north
# end of Gasparilla Island, which the station already holds (Wikidata, Light List 3-1310); the archive's point is
# 58 km north.
_join('us-fl-boca-grande', 'uslhs:7610')
NO_POSITION.add('uslhs:7610')

# us-md-lazaretto-point-replica into us-md-lazaretto-point (archive point wrong, 38 km)
# The Society's Lazaretto Point (Replica) (1985) is the replica that OpenStreetMap, Wikidata and LighthouseFriends
# ('Lazaretto Point (Replica)') place at Baltimore; the archive's point is 38 km west.
_join('us-md-lazaretto-point', 'uslhs:23261')
NO_POSITION.add('uslhs:23261')

# us-mi-frankfort-south-pierhead into us-mi-frankfort (archive point wrong, 49 km)
# The Society's Frankfort South Pierhead is Frankfort's first light, on the south pier from 1873
# (LighthouseFriends 198, whose page is the station's history); the archive's point is 49 km north.
_join('us-mi-frankfort', 'uslhs:8505')
NO_POSITION.add('uslhs:8505')

# us-mi-grosse-isle-north-channel-range-rear into us-mi-grosse-ile-north-channel-range-front (range, 480 m)
# The Society's Grosse Isle North Channel Range Rear (1894) is the rear of the range whose front the station holds
# (OpenStreetMap, LighthouseFriends 'Grosse Ile North Range', Rowlett, the Light List, the Society's front).
_join('us-mi-grosse-ile-north-channel-range-front', 'uslhs:9659')

# us-nc-prices-creek-range-front into us-nc-price-creek (archive point wrong, 92 km)
# The Society's Prices Creek Range Front (1850-1867) is Price's Creek Light, the front range light that Wikidata,
# OpenStreetMap, LighthouseFriends and Rowlett ('Price's Creek Range Front') place at Southport; the archive's
# point is 92 km inland.
_join('us-nc-price-creek', 'uslhs:8863')
NO_POSITION.add('uslhs:8863')

# us-ny-barbers-point-ny into us-ny-barbers-point (archive point wrong, 24 km)
# The Society's Barber's Point NY (1873-1935) is Barber's Point Light at Westport on Lake Champlain; the archive's
# point is 24 km inland.
_join('us-ny-barbers-point', 'uslhs:3391')
NO_POSITION.add('uslhs:3391')

# us-ri-block-island into us-ri-block-island-north (archive point wrong, 29 km)
# The Society's Block Island (other name North; tower of 1867, station of 1829) is Block Island North Light; the
# archive's rounded point (41.23 N, 71.23 W) is 29 km from it.
_join('us-ri-block-island-north', 'uslhs:3488')
NO_POSITION.add('uslhs:3488')

# us-sc-daufuskie-island-range into us-sc-haig-point-range (same range, 1 km)
# The Society's Daufuskie Island Range front and rear (1873) are the Haig Point range on Daufuskie Island
# (LighthouseFriends 'Daufuskie Island (Haig Point)', Wikidata's front, rear and pair); the archive's points are 1
# km off and are set aside so the storied station gains no extra towers.
_join('us-sc-haig-point-range',
      'uslhs:15281',
      'uslhs:8914')
NO_POSITION.add('uslhs:15281')
NO_POSITION.add('uslhs:8914')

# ---- Names (duplicate audit) ----
# With the range front joined, the station holds a front and a rear; it keeps the lighthouse's name, as its story
# does.
NAME_PICKS['us-ga-sapelo-island'] = 'Sapelo Island Light'

# Wikidata's label 'Moose Peak Light Shalen’s New Home' is not the light's name; OpenStreetMap and the Light List
# (1-1390) call it Moose Peak Light, LighthouseFriends, Rowlett, the Society and the passport list Moose Peak. The
# id keeps the first build's slug.
NAME_PICKS['us-me-moose-peak-light-shalens-new-home'] = 'Moose Peak Light'

# OpenStreetMap's name for the keeper's house ('Keeper's House') won the station's name; the light is Old Point
# Comfort Light (Wikidata, NRHP 73002212, LighthouseFriends, Rowlett, the Society).
NAME_PICKS['us-va-keepers-house'] = 'Old Point Comfort Light'

# The NRHP's inverted index form 'Orchard Shoal Light Station, Old' won the name; Wikidata, OpenStreetMap and the
# Light List call it Old Orchard Shoal Light.
NAME_PICKS['us-ny-old-orchard-shoal'] = 'Old Orchard Shoal Light'

# Both Presque Isle stations showed 'Presque Isle'; the 1840 tower is Old Presque Isle Light (Wikidata,
# OpenStreetMap, NRHP), its successor New Presque Isle Light.
NAME_PICKS['us-mi-old-presque-isle'] = 'Old Presque Isle Light'

# Both Presque Isle stations showed 'Presque Isle'; the 1870 tower is New Presque Isle Light (Wikidata,
# OpenStreetMap).
NAME_PICKS['us-mi-new-presque-isle'] = 'New Presque Isle Light'

# The NRHP district's name 'Racine Harbor Lighthouse and Life Saving Station' was the lighthouse's display name;
# LighthouseFriends calls it Racine Harbor, and the life-saving station of the district has its own station.
NAME_PICKS['us-wi-racine-harbor-lighthouse-and-life-saving'] = 'Racine Harbor Lighthouse'

# The station holds both lights of the range (Wikidata's, OpenStreetMap's, LighthouseFriends' and Rowlett's front
# and rear); the name 'Newburyport Harbor Range Front' named only one of them.
NAME_PICKS['us-ma-newburyport-harbor-range'] = 'Newburyport Harbor Range Lights'

# Rowlett's name for the modern rear aid ('St. Joseph Bay (Beacon Hill) Range Rear') won the station's name; the
# station is St. Joseph Point Light and its range (Wikidata, the Society).
NAME_PICKS['us-fl-st-joseph-point'] = 'St. Joseph Point Light'

# The Society's entry title 'Big Marco Pass And Rear Range' is a fragment; the record is the Big Marco Pass front
# and rear range.
NAME_PICKS['us-fl-big-marco-pass-and-rear-range'] = 'Big Marco Pass Range Lights'

# The station now holds the front and the rear of the Presque Isle Harbor Range; LighthouseFriends and the
# passport list call it Presque Isle Range.
NAME_PICKS['us-mi-presque-isle-rear-range'] = 'Presque Isle Range Lights'

# The station now holds the front and the rear of the range.
NAME_PICKS['us-oh-ashtabula-west-pier-range-front'] = 'Ashtabula West Pier Range Lights'

# The station now holds the front and the rear of the range.
NAME_PICKS['us-sc-morris-island-range-front'] = 'Morris Island Range Lights'

# OpenStreetMap's bare 'Light 2'; the Light List calls the two aids at the Great Lakes harbor Great Lakes Light 1
# and Light 2 (7-20290, 7-20285).
NAME_PICKS['us-il-light-2'] = 'Great Lakes Light 2'

# With LighthouseFriends' 'Brant Island' joined, its name won; the light is Brant Island Shoal (Rowlett, the
# Society, the Light List's 'Brant Island Shoal Light BI').
NAME_PICKS['us-nc-brant-island-shoal'] = 'Brant Island Shoal Light'

# With the Taylors Bridge rear's record moved to the range, the station is the old light on Reedy Island
# (LighthouseFriends 'Old Reedy Island', the Light List's 'Old Reedy Island Light', the Society's 'Reedy Island
# Old').
NAME_PICKS['us-de-reedy-island-range-rear-2'] = 'Old Reedy Island Light'

# ---- Statuses (duplicate audit): stations joined above whose tower was moved or rebuilt, or whose evidence changed ----
STATUS_PICKS['us-hi-lahaina'] = ('active', "In the Coast Guard's Light List (6-28460, Lahaina Light); the Society's archive, whose record joined this station in the duplicate audit, calls the light inactive.")

STATUS_PICKS['ca-ns-sydney-range'] = ('active', "The range's front tower is a 2010 replica of the 1905 front (Rowlett, Wikidata); the range still shows its lights (OpenStreetMap's seamark lights; a new rear tower in 2024).")

STATUS_PICKS['us-fl-cape-st-george'] = ('active', 'The 1852 tower on Cape St. George toppled into the Gulf on 21 October 2005; it was rebuilt in 2007-08 in the town of St. George Island, 20 km north-east, and shows a light again (Light List 4-75).')

STATUS_PICKS['us-ca-cape-mendocino'] = ('relocated', 'The 1868 tower was moved in 1998-99 from the cape to Mal Coombs Park, Shelter Cove, 54 km south; a modern light marked the cape until 2013.')

STATUS_PICKS['us-ca-table-bluff'] = ('relocated', 'The 1892 lighthouse was cut in two and moved from Table Bluff to Woodley Island Marina, Eureka, in 1987; the light was discontinued in 1961.')

STATUS_PICKS['us-de-mispillion'] = ('relocated', 'The 1873 lighthouse at the mouth of the Mispillion River was moved to Lewes after the 2002 fire; the light ended in 1929.')

STATUS_PICKS['us-ma-old-harbor-u-s-life-saving-station'] = ('relocated', 'Built in 1897 on Nauset Beach, Chatham; floated by barge to Race Point, Provincetown, in 1977.')

STATUS_PICKS['us-mi-frying-pan-island'] = ('relocated', 'The 1882 tower was moved from Frying Pan Island, off De Tour, to the Coast Guard station at Sault Ste. Marie; a modern light (Frying Pan Island Light 7) marks the island.')

# ---- Hidden (duplicate audit) ----
# The station was built from four records that a truncated ARLHS number ('USA-122' in Rowlett's directory) tied
# together: Rowlett's Titanic Memorial, Rowlett's Shoal Point and the Strawberry Island Lower Cut Range Rear of
# Rowlett and the Society, under the name Titanic Memorial at a point in Lake Ontario. The Titanic and Strawberry
# records go to their stations; the station cannot be retired into one of them (the merge retires a station into
# one other station only, and a station needs a positioned record), so it is hidden with the two records left.
HIDE['us-ny-titanic-memorial-2'] = "A duplicate listing: Rowlett's Titanic Memorial is us-ny-titanic-memorial and the Strawberry Island Lower Cut Range Rear is part of us-ny-strawberry-island-lower-cut-range; what is left is the Society's record of that rear (its point is in Lake Ontario) and Rowlett's 'Shoal Point' (upstate New York, 1890), filed here by a truncated ARLHS number"

# OpenStreetMap's 'Airport Beacon' (man_made=lighthouse) near Franklin, PA, inland; OpenStreetMap only; no light
# list, register or lighthouse directory lists a light within 3 km.
HIDE['us-pa-airport-beacon'] = 'An airport rotating beacon, not an aid to navigation on the water'

# OpenStreetMap's second 'Airport Beacon' in western Pennsylvania, inland; OpenStreetMap only; no light list,
# register or lighthouse directory lists a light within 3 km.
HIDE['us-pa-airport-beacon-2'] = 'An airport rotating beacon, not an aid to navigation on the water'

# OpenStreetMap's 'Airport Beacon' at Springfield, IL, inland; OpenStreetMap only; no light list, register or
# lighthouse directory lists a light within 3 km.
HIDE['us-il-airport-beacon'] = 'An airport rotating beacon, not an aid to navigation on the water'

# OpenStreetMap's 'Airport Beacon' at Appleton, WI, inland; OpenStreetMap only; no light list, register or
# lighthouse directory lists a light within 3 km.
HIDE['us-wi-airport-beacon'] = 'An airport rotating beacon, not an aid to navigation on the water'

# OpenStreetMap's 'PIAFB Beacon', inland at Presque Isle, ME; OpenStreetMap only; no light list, register or
# lighthouse directory lists a light within 3 km.
HIDE['us-me-piafb-beacon'] = 'The aerodrome beacon of the former Presque Isle Air Force Base, not an aid to navigation on the water'

# OpenStreetMap's 'IWD Beacon', inland near Ironwood, MI; OpenStreetMap only; no light list, register or
# lighthouse directory lists a light within 3 km.
HIDE['us-mi-iwd-beacon'] = 'The aerodrome beacon of Gogebic-Iron County Airport (IWD), not an aid to navigation on the water'

# OpenStreetMap's 'Edwards AFB Aerodrome Beacon' in the Mojave Desert; OpenStreetMap only; no light list, register
# or lighthouse directory lists a light within 3 km.
HIDE['us-ca-edwards-afb-aerodrome-beacon'] = 'The aerodrome beacon of Edwards Air Force Base, not an aid to navigation'

# The National Register listing 70000411 is the stone altar screen of the chapel of Our Lady of Light; the
# register record was read as a lighthouse by its name.
HIDE['us-nm-reredos-of-our-lady-of'] = 'A church altar screen in Santa Fe (Reredos of Our Lady of Light), not a lighthouse'

# The National Register listing 11000131 'Light House' is in San Antonio, 200 km from the coast; no light list or
# lighthouse directory lists it.
HIDE['us-tx-light-house'] = "A building named 'Light House' in San Antonio, not a lighthouse"

# OpenStreetMap's building 'The Lighthouse' (man_made=lighthouse, building=yes) is 1 km from Tongue Point Light,
# which is its own station; nothing lists a light at the building.
HIDE['us-ct-the'] = "A building called 'The Lighthouse' in Bridgeport, not a light"

# OpenStreetMap's 'Kenly 95' is at the Kenly 95 travel plaza on Interstate 95, 140 km from the coast;
# OpenStreetMap only; no light list, register or lighthouse directory lists a light within 3 km.
HIDE['us-nc-kenly-95'] = 'A lighthouse-shaped tower at an inland travel stop (Kenly 95), not an aid to navigation'

# OpenStreetMap's element is named 'N41°44.423 W83°27.167 (6' Deep)' in western Lake Erie; no light list, chart or
# lighthouse directory has a light there.
HIDE['us-mi-n41-44-423-w83-27-167-6-deep'] = "An OpenStreetMap point named only by its coordinates ('6' Deep'), not a light station"

# Wikidata's item is the Wikipedia list article 'Unmanned reef lights of the Florida Keys' (the minor reef lights
# as a group), with one point for all of them; the lights it covers that have a history are stations of their own.
HIDE['us-fl-unmanned-reef-lights-of-the-florida-keys'] = 'A group article about several reef lights, not one station'

# ---- Scale copies (duplicate audit) ----
# OpenStreetMap's 'Pigeon Point Lighthouse' at Lake Havasu City, among the town's scale copies of named lights
# (DESIGN 3.2), 790 km from Pigeon Point.
REPLICA_OF['us-ca-pigeon-point-2'] = 'us-ca-pigeon-point'

# OpenStreetMap's 'Table Bluff Lighthouse' at Lake Havasu City, one of the town's scale copies of named lights,
# 1,100 km from Table Bluff.
REPLICA_OF['us-ca-table-bluff-3'] = 'us-ca-table-bluff'

# The 2012 Choptank River Lighthouse at Cambridge: LighthouseFriends 'Choptank River (Replica)', Rowlett and the
# Society list it as a replica of the 1871 screwpile.
REPLICA_OF['us-md-choptank-river-2'] = 'us-md-choptank-river'

# The 2004 lighthouse at Manteo: LighthouseFriends, Rowlett and the Society list it as the Roanoke Marshes
# replica; the 1877 screwpile is us-nc-roanoke-marshes-2.
REPLICA_OF['us-nc-roanoke-marshes'] = 'us-nc-roanoke-marshes-2'

# The 2003 lighthouse at Plymouth: LighthouseFriends, Rowlett and the Society list it as the Roanoke River
# replica; the 1887 lighthouse (now at Edenton) is us-nc-roanoke-river.
REPLICA_OF['us-nc-roanoke-river-2'] = 'us-nc-roanoke-river'

# ---- Canadian pairs the report listed, reviewed and found to be two (docs/sources/review_2026-10-ca.md) ----
# Separate Lighthouse Friends pages (the lighthouse and the range), 89 m apart; records already apart in the
# curation.
_not_duplicates('ca-on-bustard-rocks', 'ca-on-bustard-rocks-range')

# Separate pages in every source, 40 m apart; records already apart in the curation.
_not_duplicates('ca-mb-red-river-range', 'ca-mb-black-bear-island')

# Two lights 5.8 km apart (Coast Guard A498 and A501).
_not_duplicates('ca-ns-terence-bay', 'ca-ns-pennant-harbour')

# Maugher Beach lighthouse and the McNabs Island range light (A528), 1.3 km apart.
_not_duplicates('ca-ns-maugher-beach', 'ca-ns-mcnabs-island')

# The 1828 Saint John Harbour Beacon and the Saint John Harbour range front, 2.6 km apart.
_not_duplicates('ca-nb-beacon', 'ca-nb-saint-john-harbour')

# Quaco Head lighthouse and the 1983 St. Martins replica in the village, 4 km apart.
_not_duplicates('ca-nb-quaco-head', 'ca-nb-st-martins')

# Cranberry Island lighthouse and the Hart Island range at Canso, 5.3 km apart.
_not_duplicates('ca-ns-cranberry-island', 'ca-ns-canso-harbour')

# The South (wharf) light and the East End light, 7 km apart.
_not_duplicates('ca-ns-pictou-island-south', 'ca-ns-pictou-island-east-end')

# The west-end light (a station of its own after this audit) and the East End light, 7 km apart.
_not_duplicates('ca-ns-pictou-island-west', 'ca-ns-pictou-island-east-end')

# Two ranges (downstream and upstream, Coast Guard A2143 and A2144), 1.9 km apart.
_not_duplicates('ca-qc-route-louiseville-downstream', 'ca-qc-route-louiseville-upstream')

# Two ranges (Upper, A2025-A2026; lower, A2023-A2024), 4.4 km apart.
_not_duplicates('ca-qc-grondines-upper-range', 'ca-qc-pointe-des-grondines-range')

# Two ranges sharing one light (Rowlett: 'Traverse Range Front/Course Range Rear'), separate Lighthouse Friends
# pages.
_not_duplicates('ca-qc-saint-antoine-course-range', 'ca-qc-saint-antoine-traverse-range')

# Algernon Rock and Pilier-de-Pierre, 580 m apart; Rowlett's Roche à Veillon entry moves to Algernon Rock.
_not_duplicates('ca-qc-algernon-rock-roche-a-veillon', 'ca-qc-pilier-de-pierre')

# The two lights at the ends of Baccalieu Island, 4.8 km apart.
_not_duplicates('ca-nl-baccalieu-island-lighthouse-southwest-point', 'ca-nl-baccalieu-island-lighthouse-north-point')

# Squarry Island and Cape Bonavista, 6.3 km apart.
_not_duplicates('ca-nl-squarry-island', 'ca-nl-cape-bonavista')

# The 1975 Anse-à-Valleau light and the Pointe-à-la-Renommée lighthouse it replaced, 3.9 km apart: a new site with
# its own name.
_not_duplicates('ca-qc-anse-a-valleau', 'ca-qc-pointe-a-la-renommee')

# The 1910 lighthouse (2017 replica) and the 2001 breakwater light, 330 m apart.
_not_duplicates('ca-mb-winnipeg-beach', 'ca-mb-winnipeg-beach-breakwater')

# The upper and the lower lights at Belle Isle's south end.
_not_duplicates('ca-nl-belle-isle-south-end-upper', 'ca-nl-belle-isle-south-end-lower-2')

# The Dorval course range front and Lighthouse Friends' lost Dorval light, 1.8 km apart.
_not_duplicates('ca-qc-dorval', 'ca-qc-dorval-2')
