/**
 * Quick jumps on the map. The places Fresnel covers are far apart: Guam is near 145 E, American
 * Samoa near 170 W, the Aleutians cross the 180th meridian, Newfoundland is at 52 W. One box
 * holding them all would be mostly ocean, so the map opens on the lower 48 and the Atlantic
 * provinces and offers a jump to each group.
 *
 * Bounds are [[west, south], [east, north]]. A box that crosses the 180th meridian gives its
 * east edge past 180 (Alaska's -130 becomes 230), which MapLibre's fitBounds understands.
 */

export interface MapView {
  id: string;
  label: string;
  /** What the jump shows, for its title / screen readers. */
  about: string;
  bounds: [[number, number], [number, number]];
}

export const MAP_VIEWS: MapView[] = [
  { id: 'lower48', label: 'Lower 48 and Atlantic Canada', about: 'The lower 48 states and the Atlantic provinces of Canada', bounds: [[-126, 24], [-52, 50]] },
  { id: 'greatlakes', label: 'Great Lakes', about: 'The Great Lakes, in the US and Canada', bounds: [[-92.5, 41.2], [-75.5, 49.2]] },
  { id: 'canada', label: 'Canada', about: 'All of Canada', bounds: [[-141, 41.6], [-52.6, 70]] },
  { id: 'alaska', label: 'Alaska', about: 'Alaska, the Aleutians included', bounds: [[172, 51], [230, 71.5]] },
  { id: 'hawaii', label: 'Hawaii', about: 'The main Hawaiian Islands', bounds: [[-160.6, 18.7], [-154.6, 22.4]] },
  { id: 'pacific', label: 'Hawaii and the Pacific territories', about: 'Hawaii, Guam, the Northern Mariana Islands and American Samoa', bounds: [[144, -15], [206, 29]] },
  { id: 'marianas', label: 'Guam and the Northern Marianas', about: 'Guam and the Northern Mariana Islands', bounds: [[144.4, 13.1], [146.2, 20.7]] },
  { id: 'samoa', label: 'American Samoa', about: 'American Samoa', bounds: [[-171.2, -14.6], [-168.1, -11]] },
  { id: 'caribbean', label: 'Puerto Rico and the Virgin Islands', about: 'Puerto Rico and the US Virgin Islands', bounds: [[-68.1, 17.6], [-64.4, 18.8]] },
  { id: 'all', label: 'All of North America', about: 'The US and Canada, without the Pacific territories', bounds: [[-170, 15], [-50, 72]] },
];

/** The first view: the lower 48 and the Atlantic provinces. */
export const DEFAULT_VIEW = MAP_VIEWS[0]!.bounds;
