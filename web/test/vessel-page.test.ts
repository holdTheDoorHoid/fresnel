/**
 * The lightship vessel page, the "Lightship vessels" section on a station's page and the "stations we can't place yet"
 * page (pipeline/site_vessels.py writes their data). Data here is written by hand in the shape the pipeline writes.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import type { StationRecord, UnplacedFile, UnplacedStation, VesselLink, VesselPage } from '../src/lib/types.ts';
import { commonReason, renderUnplacedHead, renderUnplacedMain, rowId, suggestLocationUrl } from '../src/render/unplaced.ts';
import { fateWords, isVesselId, renderVesselHead, renderVesselMain, vesselName, vesselsSection } from '../src/render/vessel.ts';
import { positionBasis } from '../src/render/station.ts';
import { contextFor } from './helpers.ts';

const ctx = contextFor({ sources: [] });
const text = (h: string) => h.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
const noJunk = (out: string) => {
  expect(text(out)).not.toMatch(/\b(null|undefined|NaN)\b|\[object/);
  expect(out).not.toMatch(/="(null|undefined)"/);
};

const nantucket: VesselPage = {
  id: 'lv-112',
  hull: 'LV-112',
  wal: 'WAL-534',
  names: ['Nantucket'],
  built: 1936,
  retired: 1975,
  fate: { status: 'survives', year: null, existing: true },
  berth: { station_id: 'us-ma-lightship-nantucket', name: 'United States lightship Nantucket', lat: 42.36115, lon: -71.03523 },
  career: [
    { station: 'Nantucket Shoals', station_id: 'us-ma-nantucket-shoals', start: 1936, end: 1942 },
    { station: 'Examination Vessel WWII', station_id: null, start: 1942, end: 1945 },
    { station: 'Nantucket Shoals', station_id: 'us-ma-nantucket-shoals', start: 1945, end: 1958 },
  ],
  sources: [{ label: 'US Lighthouse Society Digital Archive: LV-112 (vessel record)', url: 'https://archives.uslhs.org/node/4156', credit: 'U.S. Lighthouse Society Digital Archive: facts only, with a link' }],
};
const lost: VesselPage = { id: 'lv-71', hull: 'LV-71', wal: null, names: [], built: 1897, retired: 1918, fate: { status: 'lost', year: 1918 }, berth: null, career: [], sources: [] };

describe('vessel names and fates', () => {
  it('names a vessel by hull number and name, without repeating a name that is the hull', () => {
    expect(vesselName(nantucket)).toBe('LV-112 Nantucket');
    expect(vesselName(lost)).toBe('LV-71');
    expect(vesselName({ hull: 'Kewaunee', names: ['Kewaunee'] })).toBe('Kewaunee');
  });

  it('says what became of each vessel in plain words', () => {
    expect(fateWords(nantucket)).toBe('She survives. Her berth is United States lightship Nantucket.');
    expect(fateWords(lost)).toBe('Lost in 1918.');
    expect(fateWords({ fate: { status: 'scrapped', year: 1950 }, berth: null })).toBe('Scrapped in 1950.');
    expect(fateWords({ fate: { status: 'survives' }, berth: null })).toBe('She survives, but no berth is recorded here yet.');
    expect(fateWords({ fate: { status: 'unknown' }, berth: null })).toMatch(/not recorded/);
    expect(fateWords({ fate: { status: 'survives', year: 2013, doubtful: true }, berth: null })).toMatch(/uncertain/);
  });

  it('accepts only ids a page address can hold', () => {
    for (const ok of ['lv-112', 'wlv-604', 'kewaunee', 'lv-zz']) expect(isVesselId(ok), ok).toBe(true);
    for (const bad of ['', 'LV-112', '../x', 'a b', 'lv--1', null, 7]) expect(isVesselId(bad), String(bad)).toBe(false);
  });
});

describe('the vessel page', () => {
  it('shows the career with each station linked when it has a page, the berth, the fate and the sources', () => {
    const out = renderVesselMain(nantucket, ctx).value;
    noJunk(out);
    expect(out).toContain('<h1>LV-112 Nantucket</h1>');
    expect(out).toContain('href="/fresnel/s/us-ma-nantucket-shoals/"');
    expect(out).toContain('href="/fresnel/s/us-ma-lightship-nantucket/"');
    expect(text(out)).toContain('Examination Vessel WWII');
    expect(out).not.toContain('us-null'); // a station with no page is plain text
    expect(text(out)).toContain('1936–1942');
    expect(text(out)).toContain('Coast Guard number WAL-534');
    expect(out).toContain('https://archives.uslhs.org/node/4156');
    expect(out).toContain('id="career"');
    expect(out).toContain('id="berth"');
    // every "On this page" link points at a section that is there
    const jump = out.slice(out.indexOf('<nav class="jump"'), out.indexOf('</nav>', out.indexOf('<nav class="jump"')));
    for (const m of jump.matchAll(/href="#([a-z-]+)"/g)) expect(out, m[1]).toContain(`id="${m[1]}"`);
  });

  it('lists the career in order of the first year, whatever order the record is in', () => {
    const shuffled = { ...nantucket, career: [...nantucket.career].reverse() };
    const out = renderVesselMain(shuffled, ctx).value;
    expect(out.indexOf('1936–1942')).toBeLessThan(out.indexOf('1942–1945'));
    expect(out.indexOf('1942–1945')).toBeLessThan(out.indexOf('1945–1958'));
  });

  it('copes with a vessel with no career, no berth and no sources', () => {
    const out = renderVesselMain(lost, ctx).value;
    noJunk(out);
    expect(text(out)).toContain('No stations are recorded for this vessel yet');
    expect(out).not.toContain('id="berth"');
    expect(text(out)).toContain('Lost in 1918');
  });

  it('has a head with a canonical address and offers an edit on GitHub', () => {
    const head = renderVesselHead(nantucket, ctx).value;
    expect(head).toContain('<title>LV-112 Nantucket: lightship vessel · Fresnel</title>');
    expect(head).toContain('rel="canonical" href="https://example.org/fresnel/v/lv-112/"');
    expect(renderVesselMain(nantucket, ctx).value).toContain('https://github.com/holdTheDoorHoid/fresnel/issues/new?template=edit.yml');
  });

  it('escapes a hostile name', () => {
    const out = renderVesselMain({ ...nantucket, names: ['<script>alert(1)</script>'] }, ctx).value + renderVesselHead({ ...nantucket, names: ['<img onerror=x>'] }, ctx).value;
    expect(out).not.toContain('<script>alert');
    expect(out).not.toContain('<img onerror');
  });
});

describe('the vessels on a station page', () => {
  const station = (vessels: VesselLink[] | null): StationRecord => ({ id: 'us-ma-nantucket-shoals', vessels }) as StationRecord;
  const served: VesselLink = { id: 'lv-112', hull: 'LV-112', names: ['Nantucket'], role: 'served', stints: [{ start: 1936, end: 1942 }, { start: 1945, end: 1958 }] };

  it('leaves the section out when the station has no vessel', () => {
    expect(vesselsSection(station(null), ctx)).toBeNull();
    expect(vesselsSection(station([]), ctx)).toBeNull();
  });

  it('lists the vessels that served the station with their years, each linked to its page', () => {
    const out = vesselsSection(station([served, { ...served, id: 'lv-66', hull: 'LV-66', names: [], stints: [{ start: 1896, end: 1907 }] }]), ctx)!.value;
    noJunk(out);
    expect(out).toContain('href="/fresnel/v/lv-112/"');
    expect(text(out)).toContain('LV-112 Nantucket 1936–1942, 1945–1958');
    expect(text(out)).toContain('The 2 lightships that served this station');
  });

  it('says a surviving vessel lies at its berth', () => {
    const out = vesselsSection(station([{ ...served, role: 'berth', stints: [] }]), ctx)!.value;
    expect(text(out)).toContain('This is the berth of');
    expect(out).toContain('href="/fresnel/v/lv-112/"');
  });

  it('skips a link with an id a page address cannot hold', () => {
    expect(vesselsSection(station([{ ...served, id: '../x' }]), ctx)).toBeNull();
  });
});

describe('how an approximate position is explained', () => {
  const at = (from: string | null, note: string | null) => ({ location: { lat: 41.5, lon: -69.9, from, note } });

  it('says a computed position was worked out, and quotes the words it was worked from', () => {
    const out = positionBasis(at('computed', 'Light List 1900: 4 miles SE. by E. from Monomoy Point Light-House'))!.value;
    expect(text(out)).toContain('Worked out from a description');
    expect(text(out)).toContain('4 miles SE. by E. from Monomoy Point Light-House');
  });

  it('quotes the printed source of a position that was read, and says nothing when there is no note', () => {
    expect(text(positionBasis(at('lightship_stations', 'Position printed in the Light List 1900'))!.value)).toBe('Position printed in the Light List 1900');
    expect(positionBasis(at('wikidata', null))).toBeNull();
  });
});

describe('the page of stations we can’t place yet', () => {
  const lightship = (name: string, extra: Partial<UnplacedStation> = {}): UnplacedStation => ({
    key: `lightship_stations:${name.toLowerCase().replace(/\W+/g, '-')}`,
    kind: 'lightship_station',
    name,
    other_names: [],
    region: 'NJ',
    country: 'US',
    first: 1908,
    last: 1967,
    reason: 'no Light List, report or Bulletin entry read gives a position for this station',
    suggest: true,
    vessels: [{ id: 'lv-87', hull: 'LV-87' }],
    ...extra,
  });
  const file: UnplacedFile = {
    note: '',
    count: 4,
    stations: [
      lightship('Ambrose Channel', { where: 'Ambrose Channel' }),
      lightship('Barnegat'),
      lightship('Staten Island Depot', { region: 'NY', suggest: false, reason: 'a depot where lightships were kept, not a mooring', vessels: [], first: null, last: null }),
      { ...lightship('Nome Life-Saving Station'), kind: 'life_saving_station', region: 'AK', vessels: [], reason: 'no position could be read cleanly' },
    ],
  };

  it('lists each station with its region, years and why it has no position', () => {
    const out = renderUnplacedMain(file, ctx).value;
    noJunk(out);
    expect(out).toContain('<h1>Stations we can’t place yet</h1>');
    expect(text(out)).toContain('Ambrose Channel');
    expect(text(out)).toContain('New Jersey');
    expect(text(out)).toContain('1908–1967');
    expect(text(out)).toContain('Not found in the sources read.');
    expect(text(out)).toContain('A depot where lightships were kept, not a mooring.');
    expect(out).toContain('id="lightships"');
    expect(out).toContain('id="life-saving"');
    expect(out).toContain('href="/fresnel/v/lv-87/"');
  });

  it('states the reason most rows share once, above the table', () => {
    expect(commonReason(file.stations.filter((s) => s.kind === 'lightship_station'))).toMatch(/^no Light List/);
    expect(commonReason([file.stations[0]!])).toBeNull();
    expect(text(renderUnplacedMain(file, ctx).value)).toContain('Why most have no position: No Light List, report or Bulletin entry read gives a position for this station.');
  });

  it('gives each station that has a mooring a pre-filled Suggest a location link, and a depot none', () => {
    const out = renderUnplacedMain(file, ctx).value;
    expect(out.match(/issues\/new\?template=edit\.yml/g)).toHaveLength(3); // the two moorings and the life-saving station, not the depot
    expect(text(out)).toContain('Not a mooring');
    const url = new URL(suggestLocationUrl(file.stations[0]!, ctx));
    expect(url.searchParams.get('template')).toBe('edit.yml');
    expect(url.searchParams.get('title')).toBe('Location: Ambrose Channel (New Jersey)');
    expect(url.searchParams.get('station_name')).toBe('Ambrose Channel');
    expect(url.searchParams.get('where')).toBe('New Jersey, United States');
    expect(url.searchParams.get('page_url')).toBe('https://example.org/fresnel/unplaced/');
    expect(url.searchParams.get('body')).toContain('Please do not guess');
  });

  it('opens only form fields the edit form has', () => {
    const dir = resolve(import.meta.dirname, '../../.github/ISSUE_TEMPLATE');
    const ids = [...readFileSync(resolve(dir, 'edit.yml'), 'utf8').matchAll(/^\s+id: ([a-z_]+)$/gm)].map((m) => m[1]);
    for (const s of file.stations) {
      for (const key of new URL(suggestLocationUrl(s, ctx)).searchParams.keys()) if (!['template', 'title', 'body'].includes(key)) expect(ids, key).toContain(key);
    }
  });

  it('copes with a station with no region and gives every row an anchor', () => {
    const odd = lightship('Wreck of the Joliet', { region: null, first: 1912, last: 1912 });
    noJunk(renderUnplacedMain({ ...file, stations: [odd] }, ctx).value);
    expect(new URL(suggestLocationUrl(odd, ctx)).searchParams.get('where')).toBe('United States');
    expect(rowId(odd)).toBe('u-lightship-stations-wreck-of-the-joliet');
  });

  it('has a head with a canonical address', () => {
    expect(renderUnplacedHead(file, ctx).value).toContain('rel="canonical" href="https://example.org/fresnel/unplaced/"');
  });

  it('escapes a hostile name', () => {
    const out = renderUnplacedMain({ ...file, stations: [lightship('<script>alert(1)</script>')] }, ctx).value;
    expect(out).not.toContain('<script>alert');
  });
});
