/**
 * Map filters. Pure logic, no DOM, so it is unit-tested directly.
 *
 * A multi-value filter is `null` when "everything" is allowed. That way new vocabulary values
 * added to the data later are shown by default instead of silently disappearing.
 */
import type { Mark } from './checklist.ts';
import type { StationProps } from './types.ts';
import { countryOf } from './regions.ts';

export interface Filters {
  status: Set<string> | null;
  kind: Set<string> | null;
  verification: Set<string> | null;
  /** Access levels to show; a station with no recorded level counts as "unknown". */
  access: Set<string> | null;
  /** Only stations where keepers or volunteer keepers live (sf). */
  staffed: boolean;
  /** Hide stations reached only by boat (bo). */
  noBoat: boolean;
  /** Only towers recorded as climbable (cl). */
  climbable: boolean;
  /** Only stations with somewhere to stay (sy). */
  stay: boolean;
  /** Only stations on a heritage register (rg). */
  registered: boolean;
  /** Only stations with a written history (st). */
  story: boolean;
  /** One state, territory or province code. */
  region: string | null;
  /** A whole country ("US", "CA"); a region filter implies its own. */
  country: string | null;
  /** Show only stations with any of these checklist marks; null = no checklist filter. */
  mine: Set<Mark> | null;
}

export function defaultFilters(): Filters {
  return {
    status: null, kind: null, verification: null, access: null,
    staffed: false, noBoat: false, climbable: false, stay: false, registered: false, story: false,
    region: null, country: null, mine: null,
  };
}

/** Minimal view of the checklist the filter needs (lets tests pass a stub). */
export interface ChecklistLookup {
  hasAny(id: string, marks: Iterable<Mark>): boolean;
}

export function accessOf(p: Pick<StationProps, 'a'>): string {
  return p.a ?? 'unknown';
}

export function countryOfProps(p: Pick<StationProps, 'cc' | 'r'>): string {
  return p.cc ?? countryOf(p.r) ?? 'US';
}

export function matches(p: StationProps, f: Filters, checklist?: ChecklistLookup | null): boolean {
  if (f.status && !f.status.has(p.s)) return false;
  if (f.kind && !f.kind.has(p.k)) return false;
  if (f.verification && !f.verification.has(p.v)) return false;
  if (f.access && !f.access.has(accessOf(p))) return false;
  if (f.staffed && !p.sf) return false;
  if (f.noBoat && p.bo) return false;
  if (f.climbable && !p.cl) return false;
  if (f.stay && !p.sy) return false;
  if (f.registered && !p.rg) return false;
  if (f.story && !p.st) return false;
  if (f.region && p.r !== f.region) return false;
  if (f.country && countryOfProps(p) !== f.country) return false;
  if (f.mine && f.mine.size > 0) {
    if (!checklist || !checklist.hasAny(p.i, f.mine)) return false;
  }
  return true;
}

export function applyFilters<T extends { properties: StationProps }>(features: readonly T[], f: Filters, checklist?: ChecklistLookup | null): T[] {
  return features.filter((x) => matches(x.properties, f, checklist));
}

/** How many filters differ from the defaults (shown on the phone "Filters (3)" button). */
export function activeFilterCount(f: Filters): number {
  let n = 0;
  for (const k of ['status', 'kind', 'verification', 'access'] as const) if (f[k]) n++;
  for (const k of ['staffed', 'noBoat', 'climbable', 'stay', 'registered', 'story'] as const) if (f[k]) n++;
  if (f.region || f.country) n++;
  if (f.mine && f.mine.size) n++;
  return n;
}

export type Facet = 'status' | 'kind' | 'verification' | 'access' | 'region';

function facetValue(p: StationProps, facet: Facet): string {
  switch (facet) {
    case 'status':
      return p.s;
    case 'kind':
      return p.k;
    case 'verification':
      return p.v;
    case 'access':
      return accessOf(p);
    case 'region':
      return p.r;
  }
}

/**
 * Counts per value of one facet, applying every OTHER filter. This is what "Active light (812)"
 * next to a checkbox means: how many you would see with it ticked.
 */
export function facetCounts(features: readonly { properties: StationProps }[], f: Filters, facet: Facet, checklist?: ChecklistLookup | null): Map<string, number> {
  // (the place select sets a region or a whole country: counting regions ignores both)
  const others: Filters = { ...f, [facet]: null, ...(facet === 'region' ? { country: null } : {}) };
  const counts = new Map<string, number>();
  for (const x of features) {
    if (!matches(x.properties, others, checklist)) continue;
    const key = facetValue(x.properties, facet);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
}

/**
 * Toggle one value of a multi-value filter. `all` is every value the UI offers. Returns null
 * (meaning "everything") when every offered value ends up selected.
 */
export function toggleValue(current: Set<string> | null, value: string, on: boolean, all: readonly string[]): Set<string> | null {
  const next = new Set(current ?? all);
  if (on) next.add(value);
  else next.delete(value);
  if (all.every((v) => next.has(v)) && next.size === all.length) return null;
  return next;
}

export function isSelected(current: Set<string> | null, value: string): boolean {
  return current === null || current.has(value);
}
