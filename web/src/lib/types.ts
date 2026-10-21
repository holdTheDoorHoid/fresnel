/**
 * Data contracts the site consumes, produced by pipeline/build_site_data.py into public/data/.
 *
 * stations.geojson: one Point feature per visible station. Property names are short to keep the
 * file small at ~3,000 features. Absent optional keys mean null / false (meta.json "format").
 *
 *   i   id                 "us-me-portland-head"          (always)
 *   n   name               "Portland Head Light"          (always)
 *   r   region             "ME", "PR", "NS"               (always; unique across countries)
 *   cc  country            "CA"                           (absent = US)
 *   c   county / local unit "Cumberland"                  (absent = unknown)
 *   k   kind               vocab.kind                     (always)
 *   s   status             vocab.status                   (always)
 *   v   verification       vocab.verification             (always)
 *   a   access level       vocab.access                   (absent = unknown)
 *   sf  staffing           "staffed" | "volunteer"        (absent = otherwise)
 *   bo  boat only          1                              (absent = no, or not recorded)
 *   tr  tribal land        1  (ownership tribal)          (absent = no, or not recorded)
 *   cl  climbable          1
 *   sy  somewhere to stay  1
 *   rg  heritage register  1
 *   o   other names        "Old name|Another"
 *   y0  first year a light is recorded here
 *   y1  year the light went out or the station was lost
 *   st  has a story        1
 *
 * Coordinates are [lon, lat] rounded to 5 decimal places (about 1 m).
 */

export interface StationProps {
  i: string;
  n: string;
  r: string;
  k: string;
  s: string;
  v: string;
  cc?: string;
  c?: string;
  a?: string;
  sf?: 'staffed' | 'volunteer';
  bo?: 1;
  tr?: 1;
  cl?: 1;
  sy?: 1;
  rg?: 1;
  o?: string;
  y0?: number;
  y1?: number;
  st?: 1;
}

export interface StationFeature {
  type: 'Feature';
  geometry: { type: 'Point'; coordinates: [number, number] };
  properties: StationProps;
}

export interface StationCollection {
  type: 'FeatureCollection';
  features: StationFeature[];
}

export interface LatLon {
  lat: number;
  lon: number;
}

export interface Structure {
  role?: string | null;
  name?: string | null;
  type?: string | null;
  material?: string | null;
  built?: number | null;
  height_m?: number | null;
  status?: string | null;
  note?: string | null;
  from?: string | null;
  /** When the structure stands apart from the station's pin (a rear range light). */
  location?: LatLon | null;
}

export interface Lens {
  type?: string | null;
  order?: string | null;
  status?: string | null;
  where?: string | null;
}

export interface Light {
  first_lit?: number | null;
  deactivated?: number | null;
  lens?: Lens | null;
  /** As charted: "Fl W 4s", "Fl(2) R 10s", "F W" (lib/characteristic.ts reads it). */
  characteristic?: string | null;
  focal_height_m?: number | null;
  range_nm?: number | null;
  fog_signal?: string | null;
  from?: string | null;
}

export interface Register {
  register: string;
  number?: string | null;
  url?: string | null;
}

export interface Aton {
  uscg_llnr?: string | null;
  arlhs?: string | null;
  ccg_list_number?: string | null;
  nga?: string | null;
}

export interface Visit {
  grounds_open?: boolean | null;
  climbable?: boolean | null;
  museum?: boolean | null;
  tours?: string | null;
  boat_only?: boolean | null;
  passport_stamp?: boolean | null;
  note?: string | null;
}

export interface Stay {
  type?: string | null;
  provider?: string | null;
  url?: string | null;
  season?: string | null;
  note?: string | null;
  checked?: string | null;
}

export interface StationEvent {
  year?: number | null;
  event: string;
  note?: string | null;
  from?: string | null;
}

export interface Related {
  id: string;
  relation?: string | null;
  name?: string | null;
}

export interface Photo {
  url?: string | null;
  thumb_url?: string | null;
  source_url?: string | null;
  credit?: string | null;
  license?: string | null;
  caption?: string | null;
  year?: number | null;
}

export interface Link {
  label: string;
  url: string;
  kind?: string | null;
}

export interface SourceRef {
  source: string;
  key?: string | null;
  fields?: string[] | null;
}

export interface ConflictValue {
  source: string;
  value: unknown;
}

export interface Conflict {
  field: string;
  values?: ConflictValue[] | null;
  distance_m?: number | null;
  note?: string | null;
}

/** A keeper roster line (DESIGN.md 3.6). Years are a number, a "YYYY" or "YYYY-MM-DD" string, or null. */
export interface Keeper {
  name: string;
  role?: string | null;
  from?: number | string | null;
  to?: number | string | null;
  note?: string | null;
  /** Numbers (`n`) of the research_sources entries this line rests on. */
  cite?: number[] | null;
  person?: string | null;
  /** The source gives only an approximate year ("about 1880"). */
  from_approx?: boolean;
  to_approx?: boolean;
  /** Service elsewhere, only when a source names it (feeds the keepers index later). */
  other_stations?: { name?: string; from?: number | string | null; to?: number | string | null; cite?: number[] }[];
}

export interface ResearchSource {
  n: number;
  title?: string | null;
  publisher?: string | null;
  url?: string | null;
  accessed?: string | null;
  date?: string | null;
}

export interface ResearchStamp {
  researched?: string | null;
  checked?: string | null;
  verdict?: 'pass' | 'fixed' | 'fail' | string | null;
  confidence?: string | null;
}

export interface Chapter {
  id: string;
  title: string;
}

export interface StationRecord {
  id: string;
  name: string;
  other_names?: string[] | null;
  country?: string | null;
  region: string;
  county?: string | null;
  water?: string | null;
  setting?: string | null;
  kind: string;
  location: LatLon & { precision?: string | null; from?: string | null };
  status: string;
  status_note?: string | null;
  structures?: Structure[] | null;
  light?: Light | null;
  registers?: Register[] | null;
  aton?: Aton | null;
  agency?: string | null;
  ownership?: string | null;
  access?: { level?: string | null; note?: string | null } | null;
  staffing?: { status?: string | null; as_of?: string | null } | null;
  visit?: Visit | null;
  stay?: Stay | null;
  events?: StationEvent[] | null;
  keepers_count?: number | null;
  related?: Related[] | null;
  photos?: Photo[] | null;
  links?: Link[] | null;
  sources?: SourceRef[] | null;
  conflicts?: Conflict[] | null;
  verification: string;
  updated?: string | null;
  fixture?: boolean | null;
  /* Added by build_site_data.py when there is a story or research. */
  story_html?: string | null;
  chapters?: Chapter[] | null;
  keepers?: Keeper[] | null;
  research_sources?: ResearchSource[] | null;
  research?: ResearchStamp | null;
}

export interface SourceInfo {
  id: string;
  title: string;
  url?: string | null;
  license?: string | null;
  credit?: string | null;
  retrieved?: string | null;
  /** Records in the source's extract. */
  records?: number | null;
  /** Visible stations that cite it. */
  stations?: number | null;
}

export interface Meta {
  built: string;
  fixtures: boolean;
  counts: {
    total: number;
    hidden?: number;
    merged?: number;
    skipped?: number;
    stories?: number;
    rosters?: number;
    registered?: number;
    by_status?: Record<string, number>;
    by_kind?: Record<string, number>;
    by_region?: Record<string, number>;
    by_country?: Record<string, number>;
    by_country_kind?: Record<string, Record<string, number>>;
    by_verification?: Record<string, number>;
  };
  regions?: {
    countries: {
      code: string;
      name: string;
      region_words?: string[];
      regions: { code: string; name: string; territory?: boolean; stations: number }[];
    }[];
  };
  sources: SourceInfo[];
  format?: Record<string, Record<string, string>>;
}
