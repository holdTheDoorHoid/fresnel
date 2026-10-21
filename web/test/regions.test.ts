/**
 * lib/regions.ts mirrors pipeline/regions.py (DESIGN.md 3.3). These tests run the Python module
 * and check the two agree: the names, the countries, the territories, the listing order, the
 * "Nova Scotia, Canada" wording and how a local unit is written.
 */
import { describe, expect, it } from 'vitest';
import {
  COUNTRY_NAMES, COUNTRY_ORDER, REGIONS, REGION_WORDS, US_TERRITORIES, countryOf, localUnitLabel, placeLine, regionGroups, regionKind, regionName, regionWithCountry, stationCountry,
} from '../src/lib/regions.ts';
import { python } from './helpers.ts';

const UNIT_CASES: [string | null, string | null, string | null][] = [
  ['US', 'ME', 'Cumberland'],
  ['US', 'ME', 'Cumberland County'],
  ['US', 'LA', 'Plaquemines'],
  ['US', 'AK', 'Nome'],
  ['US', 'AK', 'Juneau'],
  ['US', 'AK', 'Kenai Peninsula Borough'],
  ['US', 'AK', 'Aleutians West'],
  ['US', 'PR', 'Cabo Rojo'],
  ['US', 'GU', 'Piti'],
  ['US', 'AS', 'Eastern District'],
  ['US', 'DC', 'Washington'],
  ['US', 'VA', 'Norfolk/Virginia Beach'],
  ['US', 'NY', 'Fishers Island'],
  ['CA', 'NS', 'Halifax County'],
  ['CA', 'BC', 'Capital Regional District'],
  [null, 'NS', 'Lunenburg'],
  ['US', 'ME', ''],
  ['US', 'ME', null],
];

const py = JSON.parse(
  python(`
import json, regions, build_site_data
from collections import Counter
cases = json.loads(sys.stdin.read())
print(json.dumps({
  "names": regions.REGION_NAMES,
  "country": regions.REGION_COUNTRY,
  "territories": list(regions.US_TERRITORIES),
  "country_names": regions.COUNTRY_NAMES,
  "order": regions.COUNTRY_ORDER,
  "words": {k: list(v) for k, v in regions.REGION_WORDS.items()},
  "with_country": {c: regions.region_with_country(c) for c in regions.REGION_NAMES},
  "units": [regions.local_unit_label(c, r, u) for c, r, u in cases],
  "listing": build_site_data.regions_meta(Counter())["countries"],
}))
`, JSON.stringify(UNIT_CASES)),
) as {
  names: Record<string, string>;
  country: Record<string, string>;
  territories: string[];
  country_names: Record<string, string>;
  order: string[];
  words: Record<string, string[]>;
  with_country: Record<string, string>;
  units: (string | null)[];
  listing: { code: string; name: string; regions: { code: string; name: string; territory: boolean }[] }[];
};

describe('regions agree with pipeline/regions.py', () => {
  it('has the same codes and names', () => {
    expect(REGIONS).toEqual(py.names);
  });

  it('puts every code in the same country', () => {
    for (const code of Object.keys(py.names)) expect(countryOf(code), code).toBe(py.country[code]);
  });

  it('has the same territories, countries, order and region words', () => {
    expect([...US_TERRITORIES]).toEqual(py.territories);
    expect(COUNTRY_NAMES).toEqual(py.country_names);
    expect([...COUNTRY_ORDER]).toEqual(py.order);
    expect(Object.fromEntries(Object.entries(REGION_WORDS).map(([k, v]) => [k, [...v]]))).toEqual(py.words);
  });

  it('writes every region the same way ("Puerto Rico", "Nova Scotia, Canada")', () => {
    for (const code of Object.keys(py.names)) expect(regionWithCountry(code), code).toBe(py.with_country[code]);
    expect(regionWithCountry('PR')).toBe('Puerto Rico');
    expect(regionWithCountry('GU')).toBe('Guam');
    expect(regionWithCountry('NS')).toBe('Nova Scotia, Canada');
  });

  it('writes local units the same way', () => {
    expect(UNIT_CASES.map(([c, r, u]) => localUnitLabel(c, r, u))).toEqual(py.units);
    expect(localUnitLabel('US', 'ME', 'Cumberland')).toBe('Cumberland County');
    expect(localUnitLabel('US', 'LA', 'Plaquemines')).toBe('Plaquemines Parish');
    expect(localUnitLabel('US', 'AK', 'Nome')).toBe('Nome Census Area');
    expect(localUnitLabel('US', 'AK', 'Juneau')).toBe('Juneau Borough');
    expect(localUnitLabel('US', 'PR', 'Cabo Rojo')).toBe('Cabo Rojo');
    expect(localUnitLabel('CA', 'NS', 'Halifax County')).toBe('Halifax County');
  });

  it('lists regions in the order the pipeline lists them (states, then territories, then Canada)', () => {
    const groups = regionGroups();
    expect(groups.map((g) => g.country)).toEqual(py.listing.map((c) => c.code));
    for (const [i, g] of groups.entries()) {
      expect(g.regions.map((r) => [r.code, r.name, r.territory])).toEqual(py.listing[i]!.regions.map((r) => [r.code, r.name, r.territory]));
    }
  });
});

describe('region words on the site', () => {
  it('names a station\'s place with its local unit and region', () => {
    expect(placeLine({ county: 'Cumberland', region: 'ME' })).toBe('Cumberland County, Maine');
    expect(placeLine({ county: 'Cabo Rojo', region: 'PR' })).toBe('Cabo Rojo, Puerto Rico');
    expect(placeLine({ county: 'Halifax County', region: 'NS', country: 'CA' })).toBe('Halifax County, Nova Scotia, Canada');
    expect(placeLine({ county: null, region: 'GU' })).toBe('Guam');
  });

  it('knows a station\'s country from its fields or its region', () => {
    expect(stationCountry({ region: 'NS' })).toBe('CA');
    expect(stationCountry({ region: 'CA' })).toBe('US'); // California: Canada is a country, never a region code
    expect(stationCountry({ r: 'PR' })).toBe('US');
    expect(stationCountry({ cc: 'CA', r: 'BC' })).toBe('CA');
  });

  it('says what kind of region it is', () => {
    expect(regionKind('ME')).toBe('state');
    expect(regionKind('PR')).toBe('territory');
    expect(regionKind('NS')).toBe('province');
    expect(regionKind('NU')).toBe('territory');
    expect(regionName('ZZ')).toBe('ZZ');
    expect(regionName(null)).toBe('');
  });

  it('only lists the regions asked for', () => {
    const g = regionGroups(['NS', 'PR', 'ME', 'AK']);
    expect(g.map((x) => x.regions.map((r) => r.code))).toEqual([['AK', 'ME', 'PR'], ['NS']]);
  });
});
