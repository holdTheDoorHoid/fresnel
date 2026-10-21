import { describe, expect, it } from 'vitest';
import { activeFilterCount, applyFilters, defaultFilters, facetCounts, isSelected, matches, toggleValue, type ChecklistLookup } from '../src/lib/filters.ts';
import type { Mark } from '../src/lib/checklist.ts';
import type { StationFeature, StationProps } from '../src/lib/types.ts';
import { STATUS_ORDER } from '../src/lib/vocab.ts';
import { countText } from '../src/lib/count.ts';

function f(p: Partial<StationProps> & { i: string }): StationFeature {
  return { type: 'Feature', geometry: { type: 'Point', coordinates: [-70, 43] }, properties: { n: p.i, r: 'ME', k: 'lighthouse', s: 'active', v: 'facts', ...p } };
}

const stations = [
  f({ i: 'us-me-a', s: 'active', a: 'public', cl: 1, rg: 1, st: 1 }),
  f({ i: 'us-me-b', s: 'lost', v: 'unverified' }),
  f({ i: 'us-ma-c', r: 'MA', s: 'inactive', k: 'lightship', a: 'public', sy: 1 }),
  f({ i: 'us-nj-d', r: 'NJ', s: 'ruins', k: 'life_saving_station', a: 'private' }),
  f({ i: 'ca-ns-e', r: 'NS', cc: 'CA', s: 'active', a: 'permission', sf: 'staffed', bo: 1 }),
];

const ids = (list: StationFeature[]) => list.map((x) => x.properties.i);

function checklist(marks: Record<string, Mark[]>): ChecklistLookup {
  return { hasAny: (id, want) => [...want].some((m) => marks[id]?.includes(m)) };
}

describe('filters', () => {
  it('shows everything by default', () => {
    expect(applyFilters(stations, defaultFilters())).toHaveLength(5);
    expect(activeFilterCount(defaultFilters())).toBe(0);
  });

  it('filters by status, kind, verification and access sets', () => {
    expect(ids(applyFilters(stations, { ...defaultFilters(), status: new Set(['lost', 'ruins']) }))).toEqual(['us-me-b', 'us-nj-d']);
    expect(ids(applyFilters(stations, { ...defaultFilters(), kind: new Set(['lightship']) }))).toEqual(['us-ma-c']);
    expect(ids(applyFilters(stations, { ...defaultFilters(), verification: new Set(['unverified']) }))).toEqual(['us-me-b']);
    // a station with no recorded access counts as "unknown"
    expect(ids(applyFilters(stations, { ...defaultFilters(), access: new Set(['unknown']) }))).toEqual(['us-me-b']);
    expect(ids(applyFilters(stations, { ...defaultFilters(), access: new Set(['private', 'permission']) }))).toEqual(['us-nj-d', 'ca-ns-e']);
  });

  it('an empty set shows nothing (every box unticked)', () => {
    expect(applyFilters(stations, { ...defaultFilters(), status: new Set() })).toHaveLength(0);
  });

  it('filters the switches and combines filters with AND', () => {
    expect(ids(applyFilters(stations, { ...defaultFilters(), climbable: true }))).toEqual(['us-me-a']);
    expect(ids(applyFilters(stations, { ...defaultFilters(), stay: true }))).toEqual(['us-ma-c']);
    expect(ids(applyFilters(stations, { ...defaultFilters(), staffed: true }))).toEqual(['ca-ns-e']);
    expect(ids(applyFilters(stations, { ...defaultFilters(), noBoat: true }))).toEqual(['us-me-a', 'us-me-b', 'us-ma-c', 'us-nj-d']);
    expect(ids(applyFilters(stations, { ...defaultFilters(), registered: true, story: true }))).toEqual(['us-me-a']);
    expect(activeFilterCount({ ...defaultFilters(), registered: true, story: true })).toBe(2);
  });

  it('filters by region and by country', () => {
    expect(ids(applyFilters(stations, { ...defaultFilters(), region: 'ME' }))).toEqual(['us-me-a', 'us-me-b']);
    expect(ids(applyFilters(stations, { ...defaultFilters(), country: 'CA' }))).toEqual(['ca-ns-e']);
    expect(applyFilters(stations, { ...defaultFilters(), country: 'US' })).toHaveLength(4);
  });

  it('filters by my checklist: any of the ticked marks', () => {
    const list = checklist({ 'us-me-b': ['visited'], 'us-ma-c': ['want'], 'ca-ns-e': ['visited', 'climbed'] });
    const mine = (m: Mark[]) => ({ ...defaultFilters(), mine: new Set(m) });
    expect(ids(applyFilters(stations, mine(['visited']), list))).toEqual(['us-me-b', 'ca-ns-e']);
    expect(ids(applyFilters(stations, mine(['climbed', 'want']), list))).toEqual(['us-ma-c', 'ca-ns-e']);
    // Without a checklist available, a checklist filter matches nothing rather than everything.
    expect(applyFilters(stations, mine(['visited']), null)).toHaveLength(0);
  });

  it('keeps new vocabulary values visible while a filter is "all"', () => {
    expect(matches(f({ i: 'us-me-z', s: 'some-new-status' }).properties, defaultFilters())).toBe(true);
  });

  it('toggleValue returns null when everything ends up selected', () => {
    const off = toggleValue(null, 'lost', false, STATUS_ORDER);
    expect(off).not.toBeNull();
    expect(isSelected(off, 'lost')).toBe(false);
    expect(isSelected(off, 'active')).toBe(true);
    expect(toggleValue(off, 'lost', true, STATUS_ORDER)).toBeNull();
  });

  it('facet counts apply every other filter but not their own', () => {
    const counts = facetCounts(stations, { ...defaultFilters(), status: new Set(['active']), country: 'US' }, 'status');
    expect(counts.get('active')).toBe(1);
    expect(counts.get('lost')).toBe(1);
    expect(facetCounts(stations, defaultFilters(), 'access').get('unknown')).toBe(1);
  });
});

describe('the count chip says what it counts', () => {
  it('names stations, and says when filters narrow them', () => {
    expect(countText(5, 5, false)).toEqual({ main: 'All 5 stations shown', sub: 'lighthouses, lightships and life-saving stations, standing or lost' });
    expect(countText(2, 2431, true)).toEqual({ main: '2 of 2,431 stations shown', sub: 'narrowed by your filters' });
    expect(countText(0, 5, true).main).toBe('No stations match your filters');
    expect(countText(0, 0, false).main).toBe('No stations loaded');
  });
});
