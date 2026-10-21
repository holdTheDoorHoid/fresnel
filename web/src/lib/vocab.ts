/**
 * Plain-language wording for the controlled vocabularies in data/vocab.json (DESIGN.md 3.4).
 * data/vocab.json is the data contract; this file is how the site says it to people.
 * test/vocab-and-search.test.ts checks that every code in data/vocab.json has wording here.
 * Unknown codes (added to the data later) fall back to the code in words, never a crash.
 */

export interface Wording {
  label: string;
  /** One sentence a first-time visitor understands. */
  meaning: string;
}

function words(code: string): string {
  return code.replace(/_/g, ' ');
}

/** What a station is (vocab.kind). */
export const KIND: Record<string, Wording & { short: string }> = {
  lighthouse: { label: 'Lighthouse', short: 'Lighthouse', meaning: 'A light station: a light on a tower or on its building, usually with a keeper’s house.' },
  range_lights: { label: 'Range lights', short: 'Range lights', meaning: 'A front and a rear light that line up to show a ship the middle of a channel.' },
  pier_light: { label: 'Pier or breakwater light', short: 'Pier light', meaning: 'A light at the end of a pier or breakwater, marking a harbor entrance.' },
  harbor_light: { label: 'Harbor or river light', short: 'Harbor light', meaning: 'A small harbor or river light with a structure and a history of its own.' },
  lightship_station: { label: 'Lightship station', short: 'Lightship station', meaning: 'A place at sea where lightships were anchored to mark a shoal or a harbor approach.' },
  lightship: { label: 'Lightship', short: 'Lightship', meaning: 'A surviving lightship, a vessel that carried a light, shown at its berth today.' },
  life_saving_station: { label: 'Life-saving station', short: 'Life-saving station', meaning: 'A station whose crew rescued people from wrecks: the US Life-Saving Service or its Canadian counterparts.' },
};

/** A station's status (vocab.status). Labels are what the map key and badges say. */
export const STATUS: Record<string, Wording> = {
  active: { label: 'Active light', meaning: 'Still an aid to navigation: the light shines at night.' },
  inactive: { label: 'Standing, light out', meaning: 'The structure stands, but it no longer shows a light.' },
  ruins: { label: 'Ruins', meaning: 'Only ruins or foundations are left.' },
  lost: { label: 'Lost', meaning: 'Gone: demolished, burned, washed away or collapsed. Only the site is left.' },
  relocated: { label: 'Moved', meaning: 'The structure was moved and now stands somewhere else.' },
  replica: { label: 'Replica', meaning: 'A copy of a historic light, not the original structure.' },
  unknown: { label: 'Status unknown', meaning: 'We do not know yet whether it still stands or shows a light.' },
};

/**
 * Status words for kinds that never had a light of their own (life-saving stations): "active"
 * means still in service, "inactive" standing but no longer a station.
 */
export const STATUS_NO_LIGHT: Record<string, Wording> = {
  active: { label: 'In service', meaning: 'Still in use as a rescue or Coast Guard station.' },
  inactive: { label: 'Standing', meaning: 'The building stands, but it is no longer a rescue station.' },
};

/** A structure's own status (vocab.structure_status). */
export const STRUCTURE_STATUS: Record<string, string> = {
  standing: 'Standing',
  lost: 'Lost',
  ruins: 'Ruins',
  relocated: 'Moved',
  unknown: 'Status unknown',
};

export const STRUCTURE_TYPE: Record<string, Wording> = {
  conical_masonry: { label: 'Masonry tower', meaning: 'A brick or stone tower, usually conical.' },
  cast_iron: { label: 'Cast-iron tower', meaning: 'A tower of cast-iron plates bolted together.' },
  skeletal: { label: 'Skeletal tower', meaning: 'An open framework of iron or steel.' },
  screwpile: { label: 'Screwpile', meaning: 'A house on iron legs screwed into a shoal or a muddy bottom.' },
  caisson: { label: 'Caisson (sparkplug)', meaning: 'A tower on a round iron and concrete foundation sunk into the bottom.' },
  crib: { label: 'Crib', meaning: 'A timber or concrete crib built up from a lake bottom.' },
  integral: { label: 'Lantern on the house', meaning: 'The lantern stands on the keeper’s dwelling, as in a schoolhouse or Cape Cod light.' },
  wood_frame: { label: 'Wood-frame', meaning: 'A wooden frame building or tower.' },
  concrete: { label: 'Concrete', meaning: 'A poured or reinforced concrete structure.' },
  texas_tower: { label: 'Offshore platform', meaning: 'A light on a steel platform at sea (a “Texas tower”).' },
  other: { label: 'Other', meaning: '' },
};

export const STRUCTURE_ROLE: Record<string, string> = {
  tower: 'Tower',
  dwelling: 'Keeper’s dwelling',
  fog_signal: 'Fog signal building',
  oil_house: 'Oil house',
  boathouse: 'Boathouse',
  front_range: 'Front range light',
  rear_range: 'Rear range light',
  other: 'Other building',
};

export const MATERIAL: Record<string, string> = {
  brick: 'Brick',
  stone: 'Stone',
  wood: 'Wood',
  concrete: 'Concrete',
  cast_iron: 'Cast iron',
  iron: 'Iron',
  steel: 'Steel',
  aluminium: 'Aluminium',
  fiberglass: 'Fiberglass',
  tabby: 'Tabby (lime, shell and sand)',
  mixed: 'Mixed materials',
};

export const LENS_TYPE: Record<string, string> = {
  fresnel: 'Fresnel lens',
  drum: 'Drum lens',
  modern: 'Modern optic',
  reflector: 'Reflectors (lamps with mirrors)',
  other: 'Other optic',
};

/** Fresnel lens orders: first is the largest. */
export const LENS_ORDER: Record<string, string> = {
  hyperradiant: 'Hyperradiant (larger than first order)',
  'meso-radiant': 'Meso-radiant (between first and second order)',
  '1': 'First order (the largest common size)',
  '2': 'Second order',
  '3': 'Third order',
  '3.5': 'Three-and-a-half order',
  '4': 'Fourth order',
  '5': 'Fifth order',
  '6': 'Sixth order (the smallest)',
};

export const LENS_STATUS: Record<string, string> = {
  in_place: 'Still in the lantern',
  on_display: 'On display',
  lost: 'Lost',
  unknown: 'Whereabouts unknown',
};

export const STAFFING: Record<string, string> = {
  staffed: 'Staffed: keepers live and work here',
  automated: 'Automated, no keepers',
  volunteer: 'Volunteer or caretaker keepers live here',
  unstaffed: 'No keepers',
  unknown: 'Not recorded',
};

export const OWNERSHIP: Record<string, string> = {
  federal: 'Federal government',
  state: 'State government',
  provincial: 'Provincial government',
  tribal: 'Tribal land',
  local: 'County, town or city',
  private: 'Private owner',
  nonprofit: 'Nonprofit group',
  unknown: 'Not recorded',
};

export type Tone = 'ok' | 'caution' | 'stop' | 'unknown';

export const ACCESS: Record<string, Wording & { tone: Tone }> = {
  public: { label: 'Open to the public', meaning: 'Anyone may visit the grounds.', tone: 'ok' },
  restricted: { label: 'Restricted access', meaning: 'Access is seasonal, gated, by tour only or needs a permit. Check before you go.', tone: 'caution' },
  permission: { label: 'Permission required', meaning: 'You need permission from the landowner or the tribe before you visit.', tone: 'stop' },
  private: { label: 'Private property', meaning: 'Not open to visitors. Please view it only from public land or the water, and do not trespass.', tone: 'stop' },
  closed: { label: 'Closed to visitors', meaning: 'The site is closed to the public.', tone: 'stop' },
  unknown: { label: 'Access not recorded', meaning: 'We do not know the access rules. Check with the owner or the managing agency before you go.', tone: 'unknown' },
};

export const VERIFICATION: Record<string, Wording> = {
  unverified: { label: 'Unverified', meaning: 'Not yet confirmed: no two independent sources agree on it, and nobody has checked it. Details may be wrong.' },
  facts: { label: 'Facts agree', meaning: 'Two or more independent sources agree on where it is and its status.' },
  researched: { label: 'Researched', meaning: 'Its history has been researched and written up, with footnoted sources.' },
  verified: { label: 'Verified', meaning: 'Researched, then checked independently.' },
};

export const STAY_TYPE: Record<string, string> = {
  rental: 'Rental',
  inn: 'Inn or bed and breakfast',
  hostel: 'Hostel',
  keeper_program: 'Volunteer keeper program',
};

export const SETTING: Record<string, string> = {
  coast: 'On the coast',
  island: 'On an island',
  offshore: 'Offshore, on a shoal or reef',
  bay: 'In a bay or sound',
  river: 'On a river',
  great_lakes: 'On the Great Lakes',
  harbor: 'In a harbor',
  pier: 'On a pier or breakwater',
};

export const EVENT: Record<string, string> = {
  built: 'Built',
  first_lit: 'First lit',
  rebuilt: 'Rebuilt',
  replaced: 'Replaced by a new structure',
  relit: 'Relit',
  deactivated: 'Light put out',
  automated: 'Automated',
  keeper_appointed: 'Keeper appointed',
  lens_installed: 'Lens installed',
  lens_removed: 'Lens removed',
  characteristic_changed: 'Light pattern changed',
  fog_signal_installed: 'Fog signal installed',
  damaged: 'Damaged',
  destroyed: 'Destroyed',
  burned: 'Burned',
  collapsed: 'Collapsed',
  removed: 'Removed',
  relocated: 'Moved',
  restored: 'Restored',
  modified: 'Altered',
  wreck: 'Wreck nearby',
  rescue: 'Rescue',
  storm: 'Storm',
  war: 'War',
  transferred: 'Ownership transferred',
  closed: 'Closed',
  opened_to_public: 'Opened to the public',
  nrhp_listed: 'Listed on the National Register of Historic Places',
  heritage_designated: 'Designated a heritage site',
  other: 'Event',
};

export const RELATION: Record<string, string> = {
  preceded_by: 'Came before it',
  succeeded_by: 'Replaced it',
  life_saving_station_nearby: 'Life-saving station nearby',
  light_station_nearby: 'Light station nearby',
  range_partner: 'Its range partner',
  same_place: 'At the same place',
  replica_of: 'This is a replica of',
  replica: 'A replica of it',
  related: 'Related',
};

export const LINK_KIND: Record<string, string> = {
  wikidata: 'Wikidata',
  wikipedia: 'Wikipedia',
  osm: 'OpenStreetMap',
  commons: 'Wikimedia Commons',
  register: 'Heritage register',
  website: 'Website',
  reference: 'Reference',
  station: 'Station page',
  other: 'Link',
};

export const REGISTER_NAMES: Record<string, string> = {
  NRHP: 'National Register of Historic Places',
  NHL: 'National Historic Landmark',
  'Heritage Lighthouse of Canada': 'Heritage Lighthouse (Heritage Lighthouse Protection Act)',
  CRHP: 'Canadian Register of Historic Places',
  FHBRO: 'Federal Heritage Buildings Review Office',
};

/** Aids-to-navigation numbers (aton) in words. */
export const ATON: Record<string, { label: string; meaning: string }> = {
  uscg_llnr: { label: 'USCG Light List number', meaning: 'Its number in the US Coast Guard Light List.' },
  ccg_list_number: { label: 'Canadian List of Lights number', meaning: 'Its number in the Canadian Coast Guard List of Lights.' },
  arlhs: { label: 'ARLHS number', meaning: 'Its number in the Amateur Radio Lighthouse Society’s World List of Lights.' },
  nga: { label: 'NGA number', meaning: 'Its number in the US National Geospatial-Intelligence Agency’s List of Lights.' },
};

/** Kinds whose stations carried a light (life-saving stations did not). */
export function hasLight(kind: string): boolean {
  return kind !== 'life_saving_station';
}

export function kindWording(code: string): Wording & { short: string } {
  return KIND[code] ?? { label: words(code), short: words(code), meaning: '' };
}
export function statusWording(code: string, kind?: string): Wording {
  if (kind && !hasLight(kind) && STATUS_NO_LIGHT[code]) return STATUS_NO_LIGHT[code]!;
  return STATUS[code] ?? { label: words(code), meaning: '' };
}
export function verificationWording(code: string): Wording {
  return VERIFICATION[code] ?? { label: words(code), meaning: '' };
}
export function eventLabel(code: string): string {
  return EVENT[code] ?? words(code);
}
export function lookup(table: Record<string, string>, code: string | null | undefined): string | null {
  if (code === null || code === undefined || code === '') return null;
  return table[code] ?? words(String(code));
}

/** Values offered as map filters, in display order. */
export const STATUS_ORDER = ['active', 'inactive', 'ruins', 'lost', 'relocated', 'replica', 'unknown'];
export const KIND_ORDER = ['lighthouse', 'range_lights', 'pier_light', 'harbor_light', 'lightship_station', 'lightship', 'life_saving_station'];
export const VERIFICATION_ORDER = ['unverified', 'facts', 'researched', 'verified'];
export const ACCESS_ORDER = ['public', 'restricted', 'permission', 'private', 'closed', 'unknown'];
