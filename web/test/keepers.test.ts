import { describe, expect, it } from 'vitest';
import type { Keeper } from '../src/lib/types.ts';
import { keepersTable, researchSourcesList, sortKeepers } from '../src/render/keepers.ts';
import { keepersSection } from '../src/render/station.ts';
import { contextFor, fixtureData } from './helpers.ts';

describe('the keepers roster', () => {
  const { records, meta } = fixtureData();
  const rec = records.get('us-me-example-head')!;
  const out = keepersTable(rec.keepers, rec.research_sources)!.value;

  it('comes from the research file through the pipeline', () => {
    expect(rec.keepers?.map((k) => k.name)).toEqual(['Joseph Example', 'Hannah Example', 'Samuel Sample', 'Unnamed assistant']);
  });

  it('has the columns Name, Role, Years, Note, Sources', () => {
    expect([...out.matchAll(/<th scope="col">([^<]+)<\/th>/g)].map((m) => m[1])).toEqual(['Name', 'Role', 'Years', 'Note', 'Sources']);
  });

  it('writes the role as the source gives it and the years plainly', () => {
    expect(out).toContain('Acting keeper');
    expect(out).toContain('1791–1795');
    expect(out).toContain('from 1855');
    expect(out).toContain('c. 1880 – 1884'); // years given as strings, the first one approximate
    expect(out).not.toMatch(/null|undefined|NaN/);
  });

  it('links each line to the research sources listed on the page', () => {
    expect(out).toContain('<a href="#rs-2" aria-label="Source 2">[2]</a>');
    const list = researchSourcesList(rec.research_sources)!.value;
    expect(list).toContain('<li id="rs-1">');
    expect(list).toContain('<li id="rs-2">');
    expect(list).toContain('Annual Report of the Lighthouse Board, 1855');
  });

  it('says plainly when there is no roster yet', () => {
    const other = records.get('ca-ns-fixture-island')!;
    expect(keepersTable(other.keepers, other.research_sources)).toBeNull();
    expect(keepersSection(other, contextFor(meta)).value).toContain('No roster of keepers has been compiled');
  });
});

describe('roster details', () => {
  it('orders lines by the first year, lines without years last', () => {
    const k: Keeper[] = [
      { name: 'C', from: null, to: null },
      { name: 'B', from: '1880-05-12', to: 1890 },
      { name: 'A', from: 1855 },
      { name: 'D', to: '1870' },
    ];
    expect(sortKeepers(k).map((x) => x.name)).toEqual(['A', 'D', 'B', 'C']);
  });

  it('shows a cite that is not in the source list without a dead link, and marks missing roles and sources', () => {
    const out = keepersTable([{ name: 'X', cite: [9] }, { name: 'Y' }], [{ n: 1, title: 'One' }])!.value;
    expect(out).toContain('[9]');
    expect(out).not.toContain('href="#rs-9"');
    expect(out).toContain('Not given');
    expect(out).toContain('None given');
  });

  it('escapes names and notes', () => {
    const out = keepersTable([{ name: '<script>x</script>', note: '<b>n</b>' }], [])!.value;
    expect(out).not.toContain('<script>');
    expect(out).not.toContain('<b>');
  });
});
