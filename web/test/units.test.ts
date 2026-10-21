import { describe, expect, it } from 'vitest';
import { distanceFor, feetAndMetres, formatDate, formatYearish, lengthFor, metresAndFeet, nauticalMiles, yearSpan } from '../src/lib/format.ts';
import type { StationRecord } from '../src/lib/types.ts';
import { lightRows } from '../src/render/station.ts';
import { html } from '../src/lib/html.ts';

describe('heights: feet first in the US and its territories, metres first in Canada', () => {
  it('reads heights in the country\'s units, the other alongside', () => {
    expect(lengthFor('US', 24.4)).toBe('80 ft (24 m)');
    expect(lengthFor('CA', 24.4)).toBe('24 m (80 ft)');
    expect(feetAndMetres(30)).toBe('98 ft (30 m)');
    expect(metresAndFeet(43)).toBe('43 m (141 ft)');
    expect(lengthFor('US', 1234.5)).toBe('4,050 ft (1,235 m)');
    expect(lengthFor(null, 10)).toBe('33 ft (10 m)');
  });

  it('keeps a decimal when asked', () => {
    expect(feetAndMetres(7.5, 1)).toBe('25 ft (7.5 m)');
  });

  it('says nothing for a missing value, never "null" or "NaN"', () => {
    for (const v of [null, undefined, Number.NaN, Infinity]) {
      expect(lengthFor('US', v as number)).toBeNull();
      expect(nauticalMiles(v as number)).toBeNull();
    }
  });
});

describe('ranges and distances at sea: nautical miles everywhere, km alongside', () => {
  it('writes nmi with km', () => {
    expect(nauticalMiles(24)).toBe('24 nmi (44 km)');
    expect(nauticalMiles(5)).toBe('5 nmi (9.3 km)');
    expect(nauticalMiles(17.5)).toBe('17.5 nmi (32 km)');
  });

  it('shows the range the same way on a US and a Canadian page', () => {
    const rec = (country: string, region: string): StationRecord => ({
      id: `${country.toLowerCase()}-${region.toLowerCase()}-x`, name: 'X', region, country, kind: 'lighthouse', status: 'active', verification: 'facts',
      location: { lat: 44, lon: -63 }, light: { range_nm: 23, focal_height_m: 43 },
    });
    const text = (r: StationRecord) => Object.fromEntries(lightRows(r).map(([k, v]) => [k, html`${v}`.value]));
    expect(text(rec('US', 'ME')).Range).toContain('23 nmi (43 km)');
    expect(text(rec('CA', 'NS')).Range).toContain('23 nmi (43 km)');
    expect(text(rec('US', 'ME'))['Focal height']).toContain('141 ft (43 m)');
    expect(text(rec('CA', 'NS'))['Focal height']).toContain('43 m (141 ft)');
  });
});

describe('distances on land', () => {
  it('uses the country\'s units first', () => {
    expect(distanceFor('US', 820)).toBe('2,690 ft (820 m)');
    expect(distanceFor('CA', 820)).toBe('820 m (2,690 ft)');
    expect(distanceFor('US', 2400)).toBe('1.5 mi (2.4 km)');
    expect(distanceFor('CA', 24000)).toBe('24 km (15 mi)');
  });
});

describe('dates and years', () => {
  it('formats dates and partial dates', () => {
    expect(formatDate('2026-10-21')).toBe('21 Oct 2026');
    expect(formatDate('1880-05')).toBe('May 1880');
    expect(formatDate(null)).toBeNull();
    expect(formatYearish(1791)).toBe('1791');
    expect(formatYearish('1880')).toBe('1880');
    expect(formatYearish('1880-05-12')).toBe('12 May 1880');
    expect(formatYearish('sometime')).toBeNull();
    expect(formatYearish(null)).toBeNull();
  });

  it('writes a span of years plainly', () => {
    expect(yearSpan(1791, 1795)).toBe('1791–1795');
    expect(yearSpan('1880', '1880')).toBe('1880');
    expect(yearSpan(1855, null)).toBe('from 1855');
    expect(yearSpan(null, '1884')).toBe('until 1884');
    expect(yearSpan('1880-05-12', 1884)).toBe('12 May 1880 – 1884');
    expect(yearSpan(null, undefined)).toBe('Not recorded');
  });
});
