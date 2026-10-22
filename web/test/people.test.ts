/**
 * The keepers index (DESIGN.md 3.6): the shared name rules (the same as pipeline/keepers.py), the
 * /keepers/ search logic, and the pages as the fixtures render them: a person's page, the archive's
 * roster on a station page, the living-people cut-off, and "possibly the same person as".
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  NO_FILTERS,
  chunkName,
  chunksNeeded,
  filterRows,
  filtersFromParams,
  filtersToParams,
  foldName,
  isPersonId,
  letterOf,
  rowMatches,
  rowSortKey,
  stationLabels,
  surnameOf,
  yearsText,
  type Filters,
  type IndexRow,
  type PersonRecord,
} from '../src/lib/people.ts';
import { archiveRosterBlock, personEditUrl, personSummary, printedSpan, renderKeepersMain, renderPersonHead, renderPersonMain, roleLabel, sortArchiveLines } from '../src/render/people.ts';
import { keepersSection, renderStationMain } from '../src/render/station.ts';
import { keepersTable } from '../src/render/keepers.ts';
import { contextFor, fixtureData, python, WEB } from './helpers.ts';

const data = fixtureData();
const ctx = contextFor(data.meta);
const text = (h: string) => h.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
const person = (id: string) => data.keepers.people.get(id)!;
const personPage = (id: string) => renderPersonMain(person(id), ctx).value;
const stationPage = (id: string) => renderStationMain(data.records.get(id)!, ctx).value;

describe('names are folded the way the pipeline folds them', () => {
  const names = ['Joshua F. Strout', "Pat O'Brien", 'Édouard Ünger', 'William K. Herriage, Jr.', 'Patrick "Luney" Looney', 'Jacob Brankhorst (Brankport)', 'Maria Mestre de los Dolores Andreu', 'Sherman', '123', 'Mrs. John Peterson'];

  it('agrees with pipeline/keepers.py on the folded name, the surname and the index letter', () => {
    const py = JSON.parse(python(`import json, keepers as k\nprint(json.dumps([[k.norm_name(n), k.surname_and_given(n)[0], k.letter_of(n)] for n in json.loads(input())]))`, JSON.stringify(names))) as string[][];
    names.forEach((n, i) => {
      expect([foldName(n), surnameOf(n), letterOf(n)], n).toEqual(py[i]);
    });
  });

  it('puts a surname in its chunk and a non-letter in "other"', () => {
    expect(letterOf('Joshua F. Strout')).toBe('S');
    expect(letterOf('123')).toBe('#');
    expect(chunkName('#')).toBe('other');
    expect(chunkName('S')).toBe('S');
  });

  it('sets a nickname and a trailing Jr. aside from the surname', () => {
    expect(surnameOf('William K. Herriage, Jr.')).toBe('herriage');
    expect(surnameOf('Albert (Allie) L. Davis')).toBe('davis');
  });

  it('accepts archive slugs and research ids, nothing that could break out of an address', () => {
    for (const ok of ['joshua-f-strout', 'charles-h-davis-0', 'us-me-example-head--joseph-example']) expect(isPersonId(ok), ok).toBe(true);
    for (const bad of ['', 'Joshua', 'a b', '../x', 'a/b', 'x--', '-x', 'a--b', 'x'.repeat(200)]) expect(isPersonId(bad), bad).toBe(false);
  });

  it('writes years plainly', () => {
    expect(yearsText(1861, 1878)).toBe('1861–1878');
    expect(yearsText(1861, 1861)).toBe('1861');
    expect(yearsText(1861, null)).toBe('from 1861');
    expect(yearsText(null, 1878)).toBe('until 1878');
    expect(yearsText(null, null)).toBe('');
  });
});

describe('the /keepers/ search', () => {
  const rows: IndexRow[] = [
    ['joshua-f-strout', 'Joshua F. Strout', 1869, 1904, 'ME', [1], [0]],
    ['joseph-w-strout', 'Joseph W. Strout', 1904, 1928, 'ME', [1], [0]],
    ['sam-smith', 'Sam Smith', 1850, 1860, 'MA NH', [0, 2], [1, 2]],
  ];
  const f = (over: Partial<Filters>): Filters => ({ ...NO_FILTERS, ...over });

  it('reads the chunk of a surname initial, or the initials of every word of a longer name', () => {
    const letters = ['A', 'J', 'S'];
    expect(chunksNeeded(f({ q: 'strout' }), letters)).toEqual(['S']);
    expect(chunksNeeded(f({ q: 'joshua strout' }), letters)).toEqual(['J', 'S']);
    expect(chunksNeeded(f({ q: 'Strout, Joshua' }), letters)).toEqual(['J', 'S']);
    expect(chunksNeeded(f({ q: 'zed' }), letters)).toEqual([]);
  });

  it('reads one letter when browsing, and every chunk only when it must', () => {
    const letters = ['A', 'J', 'S'];
    expect(chunksNeeded(f({ letter: 'J' }), letters)).toEqual(['J']);
    expect(chunksNeeded(f({ letter: 'Q' }), letters)).toEqual([]);
    expect(chunksNeeded(f({ region: 'ME' }), letters)).toEqual(letters);
    expect(chunksNeeded(f({ q: 'joshua', everywhere: true }), letters)).toEqual(letters);
    expect(chunksNeeded(NO_FILTERS, letters)).toEqual([]);
  });

  it('matches every typed word to the start of a word of the name', () => {
    expect(filterRows(rows, f({ q: 'str' }), -1, -1).map((r) => r[0])).toEqual(['joshua-f-strout', 'joseph-w-strout']);
    expect(filterRows(rows, f({ q: 'jos strout' }), -1, -1).map((r) => r[0])).toEqual(['joshua-f-strout', 'joseph-w-strout']);
    expect(filterRows(rows, f({ q: 'joshua strout' }), -1, -1).map((r) => r[0])).toEqual(['joshua-f-strout']);
    expect(filterRows(rows, f({ q: 'SMITH' }), -1, -1).map((r) => r[0])).toEqual(['sam-smith']);
    expect(filterRows(rows, f({ q: 'trout' }), -1, -1)).toEqual([]);
  });

  it('filters by state, role and station', () => {
    expect(filterRows(rows, f({ region: 'NH' }), -1, -1).map((r) => r[0])).toEqual(['sam-smith']);
    expect(filterRows(rows, f({ region: 'MA' }), -1, -1).map((r) => r[0])).toEqual(['sam-smith']);
    expect(filterRows(rows, f({ role: 'x' }), 2, -1).map((r) => r[0])).toEqual(['sam-smith']);
    expect(filterRows(rows, f({ station: 's' }), -1, 0).map((r) => r[0])).toEqual(['joshua-f-strout', 'joseph-w-strout']);
    expect(rowMatches(rows[0]!, f({ region: 'ME', role: 'x', station: 's' }), 1, 0)).toBe(true);
    expect(rowMatches(rows[0]!, f({ region: 'ME', role: 'x', station: 's' }), 1, 1)).toBe(false);
  });

  it('sorts by surname, then the rest of the name', () => {
    const sorted = [...rows].sort((a, b) => (rowSortKey(a[1]) < rowSortKey(b[1]) ? -1 : 1)).map((r) => r[0]);
    expect(sorted).toEqual(['sam-smith', 'joseph-w-strout', 'joshua-f-strout']);
  });

  it('keeps the search in the address, and ignores anything odd in it', () => {
    const state = f({ q: 'strout', region: 'ME', role: 'head keeper', station: 'us-me-portland-head' });
    expect(filtersFromParams(filtersToParams(state))).toEqual(state);
    expect(filtersFromParams(new URLSearchParams('l=s&state=<b>&q=' + 'x'.repeat(500)))).toMatchObject({ letter: 'S', region: '' });
    expect(filtersFromParams(new URLSearchParams('l=%3Cscript%3E')).letter).toBe('');
  });

  it('names a station once, and adds its id only where two stations share a name', () => {
    const labels = stationLabels([
      { id: 'us-me-a', name: 'Alpha Light', region: 'ME' },
      { id: 'us-me-b', name: 'Beta Light', region: 'ME' },
      { id: 'us-me-b-2', name: 'Beta Light', region: 'ME' },
    ]);
    expect(labels).toEqual(['Alpha Light (ME)', 'Beta Light (ME, us-me-b)', 'Beta Light (ME, us-me-b-2)']);
  });
});

describe('the keepers index the pipeline wrote for the fixtures', () => {
  const m = data.keepers.manifest;

  it('counts the people, those at more than one place and those left out', () => {
    expect(m.total).toBe(data.keepers.people.size);
    expect(m.total).toBe(8);
    expect(m.multi).toBe(4);
    expect(m.withheld).toBe(2); // the report's two, and the research puts nobody else past the cut-off
    expect(Object.keys(m.letters)).toEqual(['E', 'F', 'S']);
    expect(Object.values(m.letters).reduce((a, b) => a + b, 0)).toBe(m.total);
  });

  it('has a chunk per letter, rows of the documented shape, sorted by surname', () => {
    const rows = data.keepers.chunks.S!.rows as IndexRow[];
    expect(rows.map((r) => r[0])).toEqual(['ezra-sample', 'ezra-sample-0', 'ezra-sample-1', 'mary-sample', 'samuel-sample']);
    const [id, name, y0, y1, regions, roles, stations] = rows[4]!;
    expect([id, name, y0, y1, regions]).toEqual(['samuel-sample', 'Samuel Sample', 1855, 1866, 'ME NC']);
    expect(roles.map((n) => m.roles[n]!.id)).toEqual(['head keeper', 'first assistant']);
    expect(stations.map((i) => data.keepers.stations[i]![0]).sort()).toEqual(['us-me-example-head', 'us-nc-example-shoal']);
  });

  it('lists only stations a published person served at, by name', () => {
    expect(data.keepers.stations.map((s) => s[0]).sort()).toEqual(['ca-ns-fixture-island', 'us-me-example-head', 'us-nc-example-shoal', 'us-wa-example-spit']);
  });

  it('keeps the search index small: no chunk holds more than its letter', () => {
    for (const [letter, chunk] of Object.entries(data.keepers.chunks)) {
      expect(chunk.letter).toBe(letter);
      expect(chunk.rows.length).toBe(m.letters[letter]);
    }
  });
});

describe('one person, several stations', () => {
  const out = personPage('jonas-example');

  it('is one page with a stint for each station, linked, in order of service', () => {
    expect(out.indexOf('Example Shoal Light')).toBeLessThan(out.indexOf('Example Spit Lighthouse'));
    expect(out).toContain('<a href="/fresnel/s/us-nc-example-shoal/">Example Shoal Light</a>');
    expect(out).toContain('<a href="/fresnel/s/us-wa-example-spit/">Example Spit Lighthouse</a>');
    expect(out).toContain('1862–1870');
    expect(out).toContain('1871–1880');
    expect(personSummary(person('jonas-example'))).toBe('Listed at 2 places in North Carolina and Washington, 1862–1880.');
  });

  it('gives the source line of each stint and links the archive record', () => {
    expect(out).toContain('tag-unchecked');
    expect(out).toContain('href="https://archives.uslhs.org/places/example-shoal"');
    expect(out).toContain('Keepers listed by the U.S. Lighthouse Society’s Digital Archive, from the National Archives’ keeper registers.');
    expect(out).toContain('href="https://archives.uslhs.org/people/jonas-example"');
    expect(out).toContain('U.S. Lighthouse Society Digital Archive');
  });

  it('says the stints are joined by the archive’s record, never by the name', () => {
    expect(text(out)).toContain('puts the stints together only because the archive files them under one person record');
    expect(text(personPage('mary-sample'))).not.toContain('puts the stints together');
    expect(text(out)).toContain('Two records with the same name are never joined');
  });

  it('shows no race or sex, and only the columns Station, Role, Years, Source', () => {
    expect([...out.matchAll(/<th scope="col">([^<]+)<\/th>/g)].map((x) => x[1])).toEqual(['Station', 'Role', 'Years', 'Source']);
    expect(text(out)).not.toMatch(/\b(race|sex|gender|ethnic)/i);
  });

  it('links back to the index and offers a correction', () => {
    expect(out).toContain('<a href="/fresnel/keepers/">Keepers</a>');
    expect(personEditUrl(person('jonas-example'), ctx)).toContain('template=edit.yml');
    expect(new URL(personEditUrl(person('jonas-example'), ctx)).searchParams.get('title')).toBe('Edit: keeper Jonas Example');
  });

  it('a stint at a place with no station page is a plain archive place, said so', () => {
    const lars = personPage('lars-fixture');
    expect(lars).toContain('Sample Buoy Depot');
    expect(lars).toContain('Not linked to a station page');
    expect(lars).toContain('Machinist'); // the archive's own heading, as printed
  });
});

describe('same name, different records', () => {
  it('two records stay two pages, and the pair that fits says "possibly the same person as"', () => {
    const a = personPage('ezra-sample');
    expect(a).toContain('Possibly the same person as');
    expect(a).toContain('<a href="/fresnel/k/ezra-sample-0/">Ezra Sample</a>');
    expect(a).toContain('1886–1892');
    expect(a).not.toContain('/fresnel/k/ezra-sample-1/'); // a different era, in a different state: nothing is said
    expect(text(a)).toContain('Nothing connects it to this one');
    expect(personPage('ezra-sample-0')).toContain('<a href="/fresnel/k/ezra-sample/">Ezra Sample</a>');
  });

  it('a record with no fitting twin says nothing about the name', () => {
    expect(personPage('ezra-sample-1')).not.toContain('Possibly the same person');
    expect(person('ezra-sample-1').possibly).toBeUndefined();
  });

  it('the stints of the two records are never merged', () => {
    expect(person('ezra-sample').stints).toHaveLength(1);
    expect(person('ezra-sample-0').stints).toHaveLength(1);
    expect(person('ezra-sample').stints[0]!.station).toBe('us-nc-example-shoal');
  });
});

describe('research joins a person only by the archive record or a cited connection', () => {
  it('a line that names the archive record adds a checked stint, with its sources linked, and keeps the archive’s other stint', () => {
    const out = personPage('samuel-sample');
    expect(out).toContain('tag-checked');
    expect(out).toContain('href="/fresnel/s/us-me-example-head/#rs-2"');
    expect(out).toContain('tag-unchecked');
    expect(person('samuel-sample').stints.map((s) => s.src)).toEqual(['research', 'uslhs']);
  });

  it('service elsewhere with a cite makes a research person with both stations, on the other station’s page too', () => {
    const p = person('us-me-example-head--joseph-example');
    expect(p.source).toBe('research');
    expect(p.stints.map((s) => s.station)).toEqual(['us-me-example-head', 'ca-ns-fixture-island']);
    const out = renderPersonMain(p, ctx).value;
    expect(out).toContain('<a href="/fresnel/s/ca-ns-fixture-island/">Fixture Island Lighthouse</a>');
    expect(out).toContain('href="/fresnel/s/us-me-example-head/#rs-2"');
    expect(p.fixture).toBe(true);
  });

  it('a research line with no connection has no page', () => {
    expect(data.keepers.people.has('us-me-example-head--hannah-example')).toBe(false);
    const rec = data.records.get('us-me-example-head')!;
    expect(rec.keepers!.find((k) => k.name === 'Hannah Example')!.person).toBeUndefined();
  });
});

describe('the living-people cut-off', () => {
  it('people whose service begins in 1950 or later have no page and no entry, in the data or the index', () => {
    expect(data.keepers.people.has('alex-present')).toBe(false);
    expect(data.keepers.people.has('pat-coastguard')).toBe(false);
    const rows = Object.values(data.keepers.chunks).flatMap((c) => c.rows);
    expect(rows.map((r) => String(r[1])).join('|')).not.toMatch(/Alex Present|Pat Coastguard/);
    expect(JSON.stringify(data.keepers.manifest)).not.toMatch(/Alex Present|Pat Coastguard/);
  });

  it('but they stay in the roster table of their station, as the archive prints them, with no link', () => {
    const out = stationPage('us-nc-example-shoal');
    expect(out).toContain('<th scope="row" data-label="Name">Alex Present</th>');
    expect(out).toContain('1962–1975');
    expect(out).toContain('<th scope="row" data-label="Name">Pat Coastguard</th>');
    expect(out).toContain('USCG');
    expect(out).toContain('at least 1980 – 1985');
    expect(out).not.toMatch(/href="[^"]*alex-present/);
  });

  it('and the index page says who is left out and why', () => {
    const out = text(renderKeepersMain(data.keepers.manifest, ctx).value);
    expect(out).toContain('People who may be alive have no page.');
    expect(out).toContain('begins in 1950 or later or ends after 1960');
    expect(out).toContain('(2 people)');
    expect(out).toContain('exactly as the archive prints them');
  });
});

describe('the archive’s roster on a station page', () => {
  const out = stationPage('us-nc-example-shoal');

  it('shows the roster when there is no research roster, credited, linked and marked as not yet checked', () => {
    expect(out).toContain('Keepers listed by the U.S. Lighthouse Society’s Digital Archive, from the National Archives’ keeper registers.');
    expect(out).toContain('tag-unchecked');
    expect(out).toContain('Not yet checked');
    expect(out).toContain('href="https://archives.uslhs.org/places/example-shoal"');
    expect(out).toContain('Example Shoal at the archive');
    expect(out).toContain('id="archive-roster-source"'); // and again under Sources and credits
  });

  it('lists the lines in order of service with the columns Name, Role, Years (no sources column, no race or sex)', () => {
    const table = out.slice(out.indexOf('<table class="keepers keepers-archive">'), out.indexOf('</table>', out.indexOf('<table class="keepers keepers-archive">')));
    expect([...table.matchAll(/<th scope="col">([^<]+)<\/th>/g)].map((x) => x[1])).toEqual(['Name', 'Role', 'Years']);
    const names = [...table.matchAll(/data-label="Name">(?:<a[^>]*>)?([^<]+)/g)].map((x) => x[1]);
    expect(names).toEqual(['Samuel Sample', 'Jonas Example', 'Mary Sample', 'Ezra Sample', 'Lars Fixture', 'Alex Present', 'Pat Coastguard']);
    expect(text(table)).not.toMatch(/\b(race|sex|gender)\b/i);
  });

  it('links each name that has a person page, and only those', () => {
    expect(out).toContain('<a href="/fresnel/k/jonas-example/">Jonas Example</a>');
    expect(out).toContain('<a href="/fresnel/k/samuel-sample/">Samuel Sample</a>');
    expect(out).toContain('<a href="/fresnel/k/ezra-sample/">Ezra Sample</a>');
    expect((out.match(/href="\/fresnel\/k\//g) ?? []).length).toBe(5);
  });

  it('a research roster takes precedence, is marked checked, and the archive is a one-line note', () => {
    const head = stationPage('us-me-example-head');
    expect(head).toContain('<span class="tag tag-checked">Checked</span>');
    expect(head).not.toContain('Not yet checked');
    expect(head).not.toContain('keepers-archive');
    expect(head).toContain('The roster above is the one that has been checked.');
    expect(head).toContain('href="https://archives.uslhs.org/places/example-head"');
    expect(head).toContain('<a href="/fresnel/k/samuel-sample/">Samuel Sample</a>');
    expect(head).toContain('<a href="/fresnel/k/us-me-example-head--joseph-example/">Joseph Example</a>');
    expect(head).not.toMatch(/<a href="[^"]*">Hannah Example/);
  });

  it('a station with neither still says so plainly', () => {
    const other = data.records.get('ca-ns-fixture-island')!;
    expect(keepersSection(other, ctx).value).toContain('No roster of keepers has been compiled');
    expect(other.archive_roster).toBeUndefined();
  });

  it('the data a station carries leaves the lines out when a checked roster exists', () => {
    expect(data.records.get('us-me-example-head')!.archive_roster!.places[0]!.lines).toBeUndefined();
    expect(data.records.get('us-nc-example-shoal')!.archive_roster!.places[0]!.lines).toHaveLength(7);
  });
});

describe('words and years as the archive prints them', () => {
  it('writes a printed span in words and keeps “at least”', () => {
    expect(printedSpan('1861-1864')).toBe('1861–1864');
    expect(printedSpan('1861-1861')).toBe('1861');
    expect(printedSpan('at least 1950-1951')).toBe('at least 1950 – 1951');
    expect(printedSpan('at least 1909-')).toBe('from at least 1909');
    expect(printedSpan('-1911')).toBe('until 1911');
    expect(printedSpan('-')).toBe('Not recorded');
    expect(printedSpan('')).toBe('Not recorded');
    expect(printedSpan('1912.10.01-1913')).toBe('1 Oct 1912 – 1913');
  });

  it('shows the archive’s own heading when it is not a standard one, else our word', () => {
    expect(roleLabel('head keeper')).toBe('Head keeper');
    expect(roleLabel('other', 'Machinist')).toBe('Machinist');
    expect(roleLabel(null, null)).toBe('');
  });

  it('orders roster lines by the first year, lines with no year last, ties as printed', () => {
    const lines = [{ name: 'C' }, { name: 'B', from: 1880, to: 1890 }, { name: 'A', from: 1855 }, { name: 'D', to: 1870 }, { name: 'B2', from: 1880, to: 1885 }];
    expect(sortArchiveLines(lines).map((l) => l.name)).toEqual(['A', 'D', 'B2', 'B', 'C']);
  });
});

describe('what a page must never do', () => {
  const evil: PersonRecord = {
    id: 'evil-name',
    name: '<script>alert(1)</script>',
    source: 'uslhs',
    archive: 'javascript:alert(1)',
    stints: [{ src: 'uslhs', place_name: '<img src=x onerror=1>', place_url: 'javascript:alert(2)', role: '<b>x</b>', span: '1900-1901', region: 'ME' }],
    possibly: [{ id: 'bad id!', name: '<i>x</i>', from: 1, to: 2, places: [] }],
  };

  it('escapes names, places and roles, and refuses an unsafe address', () => {
    const out = renderPersonMain(evil, ctx).value + renderPersonHead(evil, ctx).value;
    expect(out).not.toContain('<script>');
    expect(out).not.toContain('<img');
    expect(out).not.toContain('<b>x');
    expect(out).not.toContain('javascript:');
    expect(out).not.toContain('bad id');
  });

  it('never prints null, undefined or NaN, for any person the fixtures hold', () => {
    for (const id of data.keepers.people.keys()) {
      const out = text(renderPersonMain(person(id), ctx).value + renderPersonHead(person(id), ctx).value);
      expect(out, id).not.toMatch(/\b(null|undefined|NaN)\b|\[object/);
    }
  });

  it('marks a sample person’s page noindex, and a real one’s not', () => {
    expect(renderPersonHead(person('jonas-example'), ctx).value).toContain('name="robots" content="noindex"');
    expect(renderPersonHead({ ...person('jonas-example'), fixture: false }, ctx).value).not.toContain('noindex');
  });

  it('an archive roster block with a link to nothing in it is left out, not printed empty', () => {
    expect(archiveRosterBlock({ archive_roster: { count: 0, places: [{ name: 'X', url: 'https://archives.uslhs.org/places/x', count: 0, lines: [] }] }, keepers: null }, ctx)).toBeNull();
    expect(archiveRosterBlock({ archive_roster: null, keepers: null }, ctx)).toBeNull();
  });

  it('only a person with a page is linked from a research roster', () => {
    const out = keepersTable([{ name: 'A', person: 'a-b' }, { name: 'B', person: '../x' }, { name: 'C' }], [], { base: '/fresnel/' })!.value;
    expect(out).toContain('<a href="/fresnel/k/a-b/">A</a>');
    expect(out).not.toContain('../x');
    expect(out).not.toContain('<a href="/fresnel/k/undefined');
    expect(keepersTable([{ name: 'A', person: 'a-b' }], [])!.value).not.toContain('/k/a-b/'); // without a base there is no link
  });
});

describe('the /keepers/ page', () => {
  const out = renderKeepersMain(data.keepers.manifest, ctx).value;

  it('gives the counts, the form, the letters and the explanation', () => {
    const t = text(out);
    expect(t).toContain('8 people · 4 listed at more than one station · 4 stations');
    expect(out).toContain('data-keepers-form');
    expect(out).toContain('<label for="k-q">Name</label>');
    expect(out).toContain('<label for="k-state">State or territory</label>');
    expect(out).toContain('<label for="k-role">Role</label>');
    expect(out).toContain('<label for="k-station">Station</label>');
    expect(out).toContain('data-letter="S"');
    expect(t).toContain('Keepers listed by the U.S. Lighthouse Society’s Digital Archive, from the National Archives’ keeper registers.');
  });

  it('says where the names come from, that two people are never joined by name, and what “possibly” means', () => {
    const t = text(out);
    expect(t).toContain('two people are never joined because their names match');
    expect(t).toContain('“possibly the same person as…” and nothing more');
    expect(t).toContain('cites a source that connects them');
  });

  it('says plainly that Canada has no keepers here yet', () => {
    expect(text(out)).toContain('The archive covers the United States, so this index has no Canadian keepers yet.');
  });

  it('works without JavaScript as far as it can: the form, the letters and the status line wait for the script, and a notice says why', () => {
    expect(out).toMatch(/<form class="k-form" data-keepers-form role="search" hidden>/);
    expect(out).toMatch(/<nav class="k-letters"[^>]* data-letters hidden>/);
    expect(out).toMatch(/<p class="k-status"[^>]* data-status hidden>/);
    expect(out).toContain('<noscript>');
  });

  it('is linked from the header on every page', () => {
    const header = readFileSync(join(WEB, 'src/partials/header.html'), 'utf8');
    expect(header).toContain('<a href="{{base}}keepers/" data-nav="keepers">Keepers</a>');
  });

  it('is an entry of the build, with the person-page template', () => {
    const vite = readFileSync(join(WEB, 'vite.config.ts'), 'utf8');
    expect(vite).toContain("keepers: resolve(root, 'keepers/index.html')");
    expect(vite).toContain("person: resolve(root, 'person.html')");
    expect(vite).toContain("if (path.includes('keepers')) return 'keepers';");
    expect(renderKeepersMain({ ...data.keepers.manifest, withheld: 0 }, ctx).value).not.toContain('people)');
  });
});
