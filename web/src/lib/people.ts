/**
 * The keepers index (DESIGN.md 3.6): the shapes of the data the pipeline writes to data/k/
 * (pipeline/keepers.py), and the pure logic of the /keepers/ page: names folded the way the
 * pipeline folds them, which index chunks a search needs, and which rows pass the filters.
 * No DOM here, so test/people.test.ts can run it.
 */

/** A person id: an archive slug ("joshua-f-strout"), or "<station id>--<slug>" for a person only the research names. */
const PERSON_ID_RE = /^(?:[a-z]{2}-[a-z0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*--)?[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function isPersonId(value: unknown): value is string {
  return typeof value === 'string' && value.length <= 160 && PERSON_ID_RE.test(value);
}

export interface PersonStint {
  /** "uslhs" (the archive's roster) or "research" (a checked roster in data/research). */
  src: 'uslhs' | 'research';
  /** The station on the map, when there is one. */
  station?: string | null;
  station_name?: string | null;
  /** The archive's place, when the station is not on the map or the stint is the archive's. */
  place?: string | null;
  place_name?: string | null;
  place_url?: string | null;
  /** State, territory or province code. */
  region?: string | null;
  role?: string | null;
  role_raw?: string | null;
  span?: string | null;
  from?: number | string | null;
  to?: number | string | null;
  from_approx?: boolean;
  to_approx?: boolean;
  note?: string | null;
  /** Research source numbers, as on the station's page (#rs-<n>). */
  cite?: number[] | null;
  checked?: boolean;
  /** The station whose research roster named this service elsewhere. */
  via?: string | null;
  /** The station has a written history. */
  story?: boolean;
  /** …and the history names this person. */
  mentioned?: boolean;
}

export interface PossibleMatch {
  id: string;
  name: string;
  from: number | null;
  to: number | null;
  places: string[];
}

export interface PersonRecord {
  id: string;
  name: string;
  source: 'uslhs' | 'research';
  /** The archive's own page for the person. */
  archive?: string | null;
  stints: PersonStint[];
  possibly?: PossibleMatch[];
  /** The archive files stints that overlap far apart under this one record. */
  check?: string | null;
  fixture?: boolean;
}

/** index.json: what /keepers/ needs before any chunk is loaded. */
export interface KeeperManifest {
  built: string;
  total: number;
  multi: number;
  withheld: number;
  letters: Record<string, number>;
  regions: { code: string; name: string; n: number }[];
  roles: { id: string; n: number }[];
  stations: number;
}

/** [id, name, first year, last year, regions (space-separated), role numbers, station numbers] */
export type IndexRow = [string, string, number | null, number | null, string, number[], number[]];

export interface IndexChunk {
  letter: string;
  rows: IndexRow[];
}

export interface StationChoice {
  id: string;
  name: string;
  region: string;
}

/* ---------- Names, folded as pipeline/keepers.py norm_name does ---------- */

export function foldName(name: string): string {
  return name
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^\x00-\x7f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

const SUFFIXES = new Set(['jr', 'sr', 'ii', 'iii', 'iv', '2nd', '3rd']);

/** The surname, folded: the last word, after nicknames in quotes or brackets and a trailing Jr. / Sr. are set aside. */
export function surnameOf(name: string): string {
  const words = foldName(name.replace(/\([^)]*\)|"[^"]*"/g, ' ')).split(' ').filter(Boolean);
  while (words.length > 1 && SUFFIXES.has(words[words.length - 1]!)) words.pop();
  return words[words.length - 1] ?? '';
}

/** The index chunk of a name: the first letter of the surname, "#" when it is not a letter. */
export function letterOf(name: string): string {
  const c = surnameOf(name).charAt(0);
  return /^[a-z]$/.test(c) ? c.toUpperCase() : '#';
}

/** The file name (without .json) of a chunk under k/i/ and k/p/: the letter, or "other" for "#". */
export function chunkName(letter: string): string {
  return letter === '#' ? 'other' : letter;
}

/** Years as the index shows them: "1861–1878", "1861", "from 1861", "until 1878", "" when unknown. */
export function yearsText(y0: number | null | undefined, y1: number | null | undefined): string {
  if (y0 != null && y1 != null) return y0 === y1 ? String(y0) : `${y0}–${y1}`;
  if (y0 != null) return `from ${y0}`;
  if (y1 != null) return `until ${y1}`;
  return '';
}

/* ---------- The /keepers/ search ---------- */

export interface Filters {
  /** Typed name, as the visitor wrote it. */
  q: string;
  /** Region code, or "". */
  region: string;
  /** Role id, or "". */
  role: string;
  /** Station id, or "". */
  station: string;
  /** Browsing one letter, or "". */
  letter: string;
  /** Also search first names: reads every chunk. */
  everywhere: boolean;
}

export const NO_FILTERS: Filters = { q: '', region: '', role: '', station: '', letter: '', everywhere: false };

export function queryWords(q: string): string[] {
  return foldName(q).split(' ').filter(Boolean);
}

export function hasAnyFilter(f: Filters): boolean {
  return !!(queryWords(f.q).length || f.region || f.role || f.station || f.letter);
}

/**
 * The chunks a search has to read. A letter being browsed: that one. A name: the chunks of the
 * initials of its words (a surname is one of them), or every chunk when the visitor asks to search
 * first names too. Only a region, role or station: every chunk. Nothing: none.
 */
export function chunksNeeded(f: Filters, letters: Iterable<string>): string[] {
  const have = [...letters];
  const words = queryWords(f.q);
  if (f.letter && !words.length) return have.includes(f.letter) ? [f.letter] : [];
  if (words.length && !f.everywhere) {
    const wanted = new Set(words.map((w) => (/^[a-z]/.test(w) ? w.charAt(0).toUpperCase() : '#')));
    return have.filter((l) => wanted.has(l));
  }
  if (words.length || f.region || f.role || f.station) return have;
  return [];
}

/** Does a row pass? Every typed word must begin a word of the name; then the region, role and station filters. */
export function rowMatches(row: IndexRow, f: Filters, roleNumber: number, stationNumber: number): boolean {
  const words = queryWords(f.q);
  if (words.length) {
    const own = foldName(row[1]).split(' ');
    if (!words.every((w) => own.some((o) => o.startsWith(w)))) return false;
  }
  if (f.region && !row[4].split(' ').includes(f.region)) return false;
  if (f.role && !row[5].includes(roleNumber)) return false;
  if (f.station && !row[6].includes(stationNumber)) return false;
  return true;
}

export function filterRows(rows: readonly IndexRow[], f: Filters, roleNumber: number, stationNumber: number): IndexRow[] {
  return rows.filter((r) => rowMatches(r, f, roleNumber, stationNumber));
}

/** Search state in the address, so a search can be shared: ?q=strout&state=ME&role=head%20keeper&station=…&l=S */
export function filtersToParams(f: Filters): URLSearchParams {
  const p = new URLSearchParams();
  if (f.q.trim()) p.set('q', f.q.trim());
  if (f.region) p.set('state', f.region);
  if (f.role) p.set('role', f.role);
  if (f.station) p.set('station', f.station);
  if (f.letter && !f.q.trim()) p.set('l', f.letter);
  if (f.everywhere) p.set('all', '1');
  return p;
}

export function filtersFromParams(p: URLSearchParams): Filters {
  const letter = (p.get('l') ?? '').toUpperCase();
  return {
    q: (p.get('q') ?? '').slice(0, 80),
    region: /^[A-Z]{2}$/.test(p.get('state') ?? '') ? p.get('state')! : '',
    role: (p.get('role') ?? '').slice(0, 40),
    station: (p.get('station') ?? '').slice(0, 120),
    letter: /^[A-Z#]$/.test(letter) ? letter : '',
    everywhere: p.get('all') === '1',
  };
}

/** Sort order of the results: surname, then the rest of the name. */
export function rowSortKey(name: string): string {
  return `${surnameOf(name)}\u0000${foldName(name)}`;
}

/** Labels for the station filter's list: "Portland Head Light (ME)"; a name two stations share also gets the id. */
export function stationLabels(stations: readonly StationChoice[]): string[] {
  const count = new Map<string, number>();
  for (const s of stations) count.set(`${s.name} (${s.region})`, (count.get(`${s.name} (${s.region})`) ?? 0) + 1);
  return stations.map((s) => {
    const base = `${s.name} (${s.region})`;
    return (count.get(base) ?? 0) > 1 ? `${s.name} (${s.region}, ${s.id})` : base;
  });
}
