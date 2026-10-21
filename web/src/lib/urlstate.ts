/**
 * Map position, filters and the selected station live in the URL query, so any view can be
 * shared by copying the address bar. Example:
 *
 *   ?at=9/43.61/-70.21&s=us-me-portland-head&status=active,inactive&kind=lighthouse&region=ME
 *
 * Switches: &climb=1 (climbable), &stay=1 (somewhere to stay), &reg=1 (on a heritage register),
 * &story=1 (has a written history), &staffed=1 (keepers live there), &noboat=1 (hide boat-only
 * stations). Access levels: &access=public,restricted. Checklist: &mine=visited,want.
 * Place: one state, territory or province (&region=NS; the codes are unique across countries;
 * &state= is read too), or one whole country (&country=CA).
 *
 * Defaults are left out, so a plain visit has a clean URL. Unknown or malformed values are
 * dropped rather than causing an error.
 */
import { MARKS, type Mark } from './checklist.ts';
import { defaultFilters, type Filters } from './filters.ts';
import { isStationId } from './station-id.ts';
import { ACCESS_ORDER, KIND_ORDER, STATUS_ORDER, VERIFICATION_ORDER } from './vocab.ts';
import { REGIONS } from './regions.ts';

export interface View {
  zoom: number;
  lat: number;
  lon: number;
}

export interface AppState {
  filters: Filters;
  view: View | null;
  selected: string | null;
}

export function defaultState(): AppState {
  return { filters: defaultFilters(), view: null, selected: null };
}

/** "none" encodes a deliberately empty selection (every box unticked). */
const NONE = 'none';

function parseSet(value: string | null, allowed: readonly string[]): Set<string> | null {
  if (value === null) return null;
  if (value === NONE) return new Set();
  const picked = value.split(',').map((v) => v.trim()).filter((v) => allowed.includes(v));
  if (picked.length === 0) return null;
  const set = new Set(picked);
  return allowed.every((v) => set.has(v)) ? null : set;
}

function formatSet(set: Set<string> | null, order: readonly string[]): string | null {
  if (set === null) return null;
  if (set.size === 0) return NONE;
  const known = order.filter((v) => set.has(v));
  const extra = [...set].filter((v) => !order.includes(v)).sort();
  return [...known, ...extra].join(',');
}

function parseView(value: string | null): View | null {
  if (!value) return null;
  const parts = value.split('/').map(Number);
  if (parts.length !== 3 || parts.some((n) => !Number.isFinite(n))) return null;
  const [zoom, lat, lon] = parts as [number, number, number];
  // Longitudes past 180 are allowed: a view of Alaska or the Pacific crosses the 180th meridian.
  if (zoom < 0 || zoom > 22 || lat < -85 || lat > 85 || lon < -360 || lon > 360) return null;
  return { zoom, lat, lon };
}

function trim(n: number, digits: number): string {
  return String(Number(n.toFixed(digits)));
}

export function formatView(v: View): string {
  return `${trim(v.zoom, 2)}/${trim(v.lat, 4)}/${trim(v.lon, 4)}`;
}

const SWITCHES: [keyof Filters, string][] = [
  ['climbable', 'climb'],
  ['stay', 'stay'],
  ['registered', 'reg'],
  ['story', 'story'],
  ['staffed', 'staffed'],
  ['noBoat', 'noboat'],
];

export function parseState(search: string): AppState {
  const q = new URLSearchParams(search);
  const state = defaultState();
  const f = state.filters;
  f.status = parseSet(q.get('status'), STATUS_ORDER);
  f.kind = parseSet(q.get('kind'), KIND_ORDER);
  f.verification = parseSet(q.get('ver'), VERIFICATION_ORDER);
  f.access = parseSet(q.get('access'), ACCESS_ORDER);
  for (const [key, param] of SWITCHES) (f[key] as boolean) = q.get(param) === '1';
  const region = (q.get('region') ?? q.get('state') ?? '').toUpperCase();
  f.region = Object.hasOwn(REGIONS, region) ? region : null;
  const country = (q.get('country') ?? '').toUpperCase();
  f.country = !f.region && (country === 'US' || country === 'CA') ? country : null;
  const mine = (q.get('mine') ?? '').split(',').filter((m): m is Mark => (MARKS as readonly string[]).includes(m));
  f.mine = mine.length ? new Set(mine) : null;
  state.view = parseView(q.get('at'));
  const s = q.get('s');
  state.selected = isStationId(s) ? s : null;
  return state;
}

/** Returns "?..." or "" when everything is at its default. */
export function serializeState(state: AppState): string {
  const q = new URLSearchParams();
  const f = state.filters;
  if (state.view) q.set('at', formatView(state.view));
  if (state.selected) q.set('s', state.selected);
  const status = formatSet(f.status, STATUS_ORDER);
  if (status !== null) q.set('status', status);
  const kind = formatSet(f.kind, KIND_ORDER);
  if (kind !== null) q.set('kind', kind);
  const ver = formatSet(f.verification, VERIFICATION_ORDER);
  if (ver !== null) q.set('ver', ver);
  const access = formatSet(f.access, ACCESS_ORDER);
  if (access !== null) q.set('access', access);
  for (const [key, param] of SWITCHES) if (f[key]) q.set(param, '1');
  if (f.region) q.set('region', f.region);
  else if (f.country) q.set('country', f.country);
  if (f.mine && f.mine.size) q.set('mine', MARKS.filter((m) => f.mine!.has(m)).join(','));
  const s = q.toString().replace(/%2C/g, ',').replace(/%2F/g, '/');
  return s ? `?${s}` : '';
}
