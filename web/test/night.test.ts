/**
 * The light at night: timed patterns (lib/pattern.ts), the sighting physics (lib/sighting.ts),
 * a light's eras (lib/light-history.ts), the station-page section and its live readout
 * (render/night.ts), and the map's range rings (map/reach.ts).
 */
import { describe, expect, it } from 'vitest';
import { parseCharacteristic } from '../src/lib/characteristic.ts';
import { distanceMetres } from '../src/lib/format.ts';
import { eventCharacteristics, lightEras } from '../src/lib/light-history.ts';
import { CONVENTION, lightPattern, phaseAt, phaseWords, type Pattern } from '../src/lib/pattern.ts';
import {
  DEFAULT_EYE_M,
  LOOM_MIN_RANGE_NM,
  R_EFF,
  brightnessRatio,
  circleRing,
  defaultDistanceNm,
  dipRad,
  elevationRad,
  geographicRangeNm,
  horizonNm,
  luminousRangeNm,
  ringRangeNm,
  sight,
} from '../src/lib/sighting.ts';
import type { StationRecord } from '../src/lib/types.ts';
import { reachCollection } from '../src/map/reach.ts';
import { nightData, nightSection, sightingWords } from '../src/render/night.ts';
import { renderStationMain } from '../src/render/station.ts';
import { stripSvg } from '../src/render/strip.ts';
import { contextFor, fixtureData } from './helpers.ts';

function pattern(raw: string, colour?: string): Pattern {
  const c = parseCharacteristic(raw);
  if (!c) throw new Error(`unread: ${raw}`);
  const res = lightPattern(c, colour ? { colour } : {});
  if (!res.ok) throw new Error(res.reason);
  return res.pattern;
}
/** [colour or null, duration] for each phase, rounded. */
const shape = (p: Pattern) => p.phases.map((ph) => [ph.colour, Number(ph.dur.toFixed(3))]);

describe('timed patterns', () => {
  it('a single flash: 0.5 s, the rest dark, and says the length is a convention', () => {
    const p = pattern('Fl W 4s');
    expect(shape(p)).toEqual([['W', 0.5], [null, 3.5]]);
    expect(p.period).toBe(4);
    expect(p.periodRecorded).toBe(true);
    expect(p.conventions.join()).toContain('Flash: not recorded; drawn at 0.5 s');
    expect(shape(pattern('Fl R 1.5s'))).toEqual([['R', 0.375], [null, 1.125]]); // a quarter of a short period
  });

  it('groups: 1 s apart for two, 1.5 s for three or more, the dark after at least three times the gap', () => {
    expect(shape(pattern('Fl(2) W 15s'))).toEqual([['W', 0.5], [null, 1], ['W', 0.5], [null, 13]]);
    expect(shape(pattern('Fl(3) W 12s'))).toEqual([['W', 0.5], [null, 1.5], ['W', 0.5], [null, 1.5], ['W', 0.5], [null, 7.5]]);
    // composite: twice the gap between the parts; scaled down when the period is short
    const c = pattern('Fl(2+1) G 6s');
    const lit = c.phases.filter((ph) => ph.colour);
    expect(lit).toHaveLength(3);
    const gaps = c.phases.filter((ph) => !ph.colour).map((ph) => ph.dur);
    expect(gaps[1]! / gaps[0]!).toBeCloseTo(2, 6);
    expect(gaps[2]!).toBeGreaterThanOrEqual(gaps[0]! * 3 - 1e-9);
    expect(c.conventions.join()).toContain('shortened to fit the period');
  });

  it('long flashes, occulting, isophase', () => {
    expect(shape(pattern('LFl W 10s'))).toEqual([['W', 2], [null, 8]]);
    expect(shape(pattern('Oc W 4s'))).toEqual([['W', 3], [null, 1]]);
    expect(shape(pattern('Oc W 20s'))).toEqual([['W', 18], [null, 2]]);
    expect(shape(pattern('Oc(2) W 10s'))).toEqual([['W', 7], [null, 1], ['W', 1], [null, 1]]);
    expect(shape(pattern('Iso G 6s'))).toEqual([['G', 3], [null, 3]]);
    expect(shape(pattern('28 s on, 2 s off'))).toEqual([['W', 28], [null, 2]]);
    expect(pattern('28 s on, 2 s off').conventions).toEqual(['Colour: not recorded; drawn white.']);
  });

  it('quick lights at the Light List rates, groups and the south-cardinal long flash', () => {
    expect(shape(pattern('Q R'))).toEqual([['R', 0.3], [null, 0.7]]);
    expect(shape(pattern('VQ G'))).toEqual([['G', 0.15], [null, 0.35]]);
    expect(pattern('Q R 1s').conventions.join()).toContain('one every 1 s as recorded');
    const q6 = pattern('Q(6)+LFl W 15s');
    const lit = q6.phases.filter((ph) => ph.colour);
    expect(lit.map((ph) => Number(ph.dur.toFixed(2)))).toEqual([0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 2]);
    expect(q6.period).toBe(15);
    expect(pattern('Q W').flashRate).toBe(1);
    expect(pattern('VQ W').flashRate).toBe(2);
    expect(pattern('UQ W').flashRate).toBe(3); // 160 a minute: still no more than three a second
    expect(pattern('IQ W 12s').phases.filter((ph) => ph.colour)).toHaveLength(9);
  });

  it('Morse: short 0.5 s, long 1.5 s, 0.5 s between', () => {
    expect(shape(pattern('Mo(U) W 20s'))).toEqual([['W', 0.5], [null, 0.5], ['W', 0.5], [null, 0.5], ['W', 1.5], [null, 16.5]]);
    expect(shape(pattern('Mo(A) Y 8s'))).toEqual([['Y', 0.5], [null, 0.5], ['Y', 1.5], [null, 5.5]]);
  });

  it('fixed and flashing: the steady light dimmer than the flash', () => {
    const p = pattern('F Fl W 30s');
    expect(p.phases.map((ph) => [ph.colour, ph.level])).toEqual([['W', 1], ['W', CONVENTION.fixedLevel]]);
    expect(p.flashRate).toBe(1);
  });

  it('alternating colours: evenly through the period, or for the time recorded; per part of a composite group', () => {
    expect(shape(pattern('Al Fl W R 30s'))).toEqual([['W', 0.5], [null, 14.5], ['R', 0.5], [null, 14.5]]);
    expect(pattern('Alt W 5s, R 5s').phases.map((ph) => [ph.colour, ph.start])).toEqual([['W', 0], [null, 0.5], ['R', 5], [null, 5.5]]);
    const umpqua = pattern('Al.Fl(2+1) WR 15s');
    expect(umpqua.phases.filter((ph) => ph.colour).map((ph) => ph.colour)).toEqual(['W', 'W', 'R']);
    expect(umpqua.conventions.join()).toContain('one for each part of the group');
  });

  it('sectors: the colour the visitor picks', () => {
    expect(shape(pattern('Fl W 6s, R sector', 'R'))).toEqual([['R', 0.5], [null, 5.5]]);
    expect(shape(pattern('Fl WR 5s', 'R'))[0]).toEqual(['R', 0.5]);
  });

  it('steady lights, and lights with no period', () => {
    const f = pattern('F G');
    expect(f.steady).toBe(true);
    expect(f.flashRate).toBe(0);
    const fl = pattern('Fl W');
    expect(fl.periodRecorded).toBe(false);
    expect(fl.period).toBe(5);
    expect(fl.conventions.join()).toContain('Period: not recorded; drawn as 5 s only to show the rhythm');
  });

  it('refuses a pattern that cannot fit, and says why', () => {
    const res = lightPattern(parseCharacteristic('Fl(6) W 1s')!);
    expect(res.ok).toBe(false);
    expect(!res.ok && res.reason).toContain('cannot fit in 1 second');
  });

  it('tells the phase at any time, and says the phases in words', () => {
    const p = pattern('Fl W 4s');
    expect(phaseAt(p, 0.2).colour).toBe('W');
    expect(phaseAt(p, 1).colour).toBeNull();
    expect(phaseAt(p, 8.3).colour).toBe('W');
    expect(phaseAt(p, -3.8).colour).toBe('W');
    expect(phaseWords(p)).toBe('white 0.5 s, dark 3.5 s.');
  });

  it('draws the strip to scale, repeating short periods', () => {
    const svg = stripSvg(pattern('Fl W 4s'), { id: 't' }).value;
    expect(svg).toContain('data-period="4"');
    expect(svg).toContain('data-span="8"'); // two periods fill the strip
    expect(svg).toContain('<title id="t-t">2 periods of 4 seconds, the first in full colour. One period: white 0.5 s, dark 3.5 s.</title>');
    expect(stripSvg(pattern('Fl W'), { id: 'u' }).value).not.toContain('>0 s<'); // no time scale without a period
  });
});

describe('sighting physics', () => {
  it('geographic range: 2.08 × (√H + √h) nautical miles', () => {
    expect(horizonNm(3)).toBeCloseTo(3.603, 3);
    expect(geographicRangeNm(31, 3)).toBeCloseTo(2.08 * (Math.sqrt(31) + Math.sqrt(3)), 9);
    expect(geographicRangeNm(31, 3)).toBeCloseTo(15.18, 2);
  });

  it('the vertical angles agree: the light meets the horizon exactly at the geographic range', () => {
    const H = 31;
    const h = 3;
    const D = geographicRangeNm(H, h);
    expect(elevationRad(H, h, D) + dipRad(h)).toBeCloseTo(0, 9);
    expect(elevationRad(H, h, D * 0.9) + dipRad(h)).toBeGreaterThan(0);
    expect(elevationRad(H, h, D * 1.1) + dipRad(h)).toBeLessThan(0);
    expect(R_EFF).toBeCloseTo(7.42e6, -4);
  });

  it('luminous range: the charted range in 10-mile visibility, farther in clear air, short in fog', () => {
    expect(brightnessRatio(19, 19, 10)).toBeCloseTo(1, 9);
    expect(luminousRangeNm(19, 10)).toBeCloseTo(19, 3);
    expect(luminousRangeNm(19, 20)).toBeGreaterThan(25);
    expect(luminousRangeNm(19, 3)).toBeLessThan(9);
    expect(luminousRangeNm(19, 0.5)).toBeLessThan(2);
    expect(brightnessRatio(19, 9, 10)).toBeCloseTo((19 / 9) ** 2 * 0.05 ** (0.9 - 1.9), 6);
  });

  it('says whether the light is seen, too faint, or below the horizon', () => {
    const base = { focalM: 31, nominalNm: 19, eyeM: 3, visibility: 'normal' as const };
    expect(sight({ ...base, distanceNm: 9 }).state).toBe('seen');
    expect(sight({ ...base, distanceNm: 9, visibility: 'fog' }).state).toBe('too_faint');
    const far = sight({ ...base, distanceNm: 17 });
    expect(far.state).toBe('below_horizon');
    expect(far.loom).toBeGreaterThan(0); // 19 nmi is a powerful light, and it would be bright enough at 17
    expect(sight({ ...base, nominalNm: LOOM_MIN_RANGE_NM - 1, distanceNm: 17 }).loom).toBe(0);
    expect(sight({ ...base, distanceNm: 40 }).loom).toBe(0); // past its luminous range too
    expect(sight({ ...base, distanceNm: 15.1 }).dipping).toBe(true);
    const s = sight({ ...base, distanceNm: 9 });
    expect(s.visibleNm).toBeCloseTo(15.18, 2);
    expect(s.limit).toBe('horizon');
  });

  it('works with only one of the figures, and says which is unknown', () => {
    const noRange = sight({ focalM: 31, nominalNm: null, eyeM: 3, distanceNm: 9, visibility: 'normal' });
    expect(noRange).toMatchObject({ state: 'unknown', ratio: null, aboveHorizon: true, limit: 'horizon' });
    const noHeight = sight({ focalM: null, nominalNm: 12, eyeM: 3, distanceNm: 9, visibility: 'normal' });
    expect(noHeight).toMatchObject({ state: 'seen', aboveHorizon: null, geographicNm: null, limit: 'brightness' });
    expect(sight({ focalM: null, nominalNm: null, eyeM: 3, distanceNm: 9, visibility: 'normal' })).toMatchObject({ state: 'unknown', visibleNm: null, limit: null });
  });

  it('the ring: the smaller of the charted range and the horizon', () => {
    expect(ringRangeNm(31, 19, 3)).toEqual({ nm: geographicRangeNm(31, 3), limit: 'horizon' });
    expect(ringRangeNm(31, 12, 3)).toEqual({ nm: 12, limit: 'range' });
    expect(ringRangeNm(null, 12, 3)).toEqual({ nm: 12, limit: 'range' });
    expect(ringRangeNm(31, null, 3)?.limit).toBe('horizon');
    expect(ringRangeNm(null, null, 3)).toBeNull();
    const ring = circleRing(43.6, -70.2, 10);
    expect(ring[0]).toEqual(ring.at(-1));
    for (const [lon, lat] of ring.slice(0, 10)) expect(distanceMetres(43.6, -70.2, lat, lon) / 1852).toBeCloseTo(10, 1);
  });

  it('starts the visitor at a typical approach, inside the visible range', () => {
    expect(defaultDistanceNm(15.2)).toBe(9);
    expect(defaultDistanceNm(4)).toBe(2.5);
    expect(defaultDistanceNm(40)).toBe(10);
    expect(defaultDistanceNm(null)).toBe(5);
  });
});

describe('the words under the scene', () => {
  const ctx = { distanceNm: 9, eyeM: 3, visibility: 'normal' as const, country: 'US', past: false, drawable: true, dark: false };
  const base = { focalM: 31, nominalNm: 19, eyeM: 3, visibility: 'normal' as const };
  it('says plainly when the light is below the horizon', () => {
    const w = sightingWords(sight({ ...base, distanceNm: 25 }), { ...ctx, distanceNm: 25 });
    expect(w).toContain('From 25 nmi (46 km) away');
    expect(w).toContain('the light is below your horizon');
    expect(w).toContain('Nothing of it can be seen.');
  });
  it('names the loom', () => expect(sightingWords(sight({ ...base, distanceNm: 17 }), { ...ctx, distanceNm: 17 })).toContain('its loom'));
  it('says how bright, in times the faintest light', () => {
    const w = sightingWords(sight({ ...base, distanceNm: 9 }), ctx);
    expect(w).toContain('about 89 times the faintest light');
    expect(w).toContain('Here it can be seen out to about 15.2 nmi (28 km), where it drops below your horizon.');
  });
  it('uses metres first in Canada, and the past tense for a light no longer lit', () => {
    const w = sightingWords(sight({ ...base, distanceNm: 9 }), { ...ctx, country: 'CA', past: true });
    expect(w).toContain('eye 3 m (10 ft)');
    expect(w).toContain('the light was above your horizon');
  });
  it('never claims a range it does not know', () => {
    const w = sightingWords(sight({ ...base, nominalNm: null, distanceNm: 9 }), ctx);
    expect(w).toContain('How bright it is (its charted range) is not recorded');
    expect(w).toContain('it drops below your horizon at 15.2 nmi (28 km), however bright it is');
    expect(w).not.toContain('can be seen out to');
    const none = sightingWords(sight({ ...base, focalM: null, nominalNm: null, distanceNm: 9 }), ctx);
    expect(none).toContain('Neither its height nor its range is recorded');
    expect(none).not.toContain('9 nmi');
  });
  it('dark sectors and too-faint lights', () => {
    expect(sightingWords(sight({ ...base, distanceNm: 9 }), { ...ctx, dark: true })).toContain('cannot be seen at all');
    expect(sightingWords(sight({ ...base, distanceNm: 9, visibility: 'fog' }), { ...ctx, visibility: 'fog' })).toContain('too faint to see');
  });
});

describe('a light’s eras', () => {
  const { records, meta, geo } = fixtureData();
  const ctx = contextFor(meta);
  const rec = (id: string) => records.get(id)!;
  const base = (light: Partial<NonNullable<StationRecord['light']>>, status = 'active', events: StationRecord['events'] = []) => ({ status, light: { first_lit: null, deactivated: null, characteristic: null, focal_height_m: null, range_nm: null, ...light }, events });

  it('from characteristic_changed events: the pattern, and the range where recorded', () => {
    const eras = lightEras(rec('us-me-example-head'));
    expect(eras.map((e) => [e.short, e.reading.raw, e.nominalNm, e.rangeFrom, e.past])).toEqual([
      ['1791–1883', 'F W', null, 'none', true],
      ['1883–1958', 'Fl W 30s', 16, 'era', true],
      ['1958–today', 'Fl W 4s', 24, 'station', false],
    ]);
    // an earlier era borrows today's height, and says so
    expect(eras[0]!.focalFrom).toBe('station');
    expect(eras.at(-1)!.label).toBe('From 1958 to today, as charted');
  });

  it('reads the new pattern from an event note when no field gives it', () => {
    expect(eventCharacteristics({ year: 1902, event: 'characteristic_changed', note: 'Changed from F W to Fl W 10s.' })).toEqual({ prev: 'F W', next: 'Fl W 10s' });
    expect(eventCharacteristics({ year: 1902, event: 'characteristic_changed', note: 'Fl(2) W 20s' })).toEqual({ prev: null, next: 'Fl(2) W 20s' });
    expect(eventCharacteristics({ year: 1902, event: 'characteristic_changed', note: 'A new lens.' })).toEqual({ prev: null, next: null });
    const eras = lightEras(base({ characteristic: 'Fl W 4s', first_lit: 1850 }, 'active', [{ year: 1902, event: 'characteristic_changed', note: 'A new lens.' }]));
    expect(eras[0]!.note).toContain('pattern from 1850 to 1902 is not recorded');
  });

  it('from the characteristic text itself', () => {
    const fb = lightEras(base({ characteristic: 'F W (original); Fl W with two R sectors (current)', deactivated: 1925 }, 'inactive'));
    expect(fb.map((e) => [e.short, e.reading.lights.length, e.past])).toEqual([['Original', 1, true], ['Until 1925', 1, true]]);
    expect(fb.at(-1)!.label).toBe('As it was when last lit (the light went out in 1925)');
    const later = lightEras(base({ characteristic: 'F R (initially F W)' }));
    expect(later.map((e) => e.short)).toEqual(['At first', 'Today']);
  });

  it('one era otherwise: today, or as it was when last lit, or as last recorded', () => {
    expect(lightEras(base({ characteristic: 'Fl W 4s' }))[0]!.label).toBe('Today, as charted');
    expect(lightEras(base({ characteristic: 'F R', deactivated: 1933 }, 'lost'))[0]).toMatchObject({ label: 'As it was when last lit (the light went out in 1933)', lastLit: true, past: true });
    expect(lightEras(base({ characteristic: 'F W (1901)' }, 'lost'))[0]!.label).toBe('As it was when last lit (pattern recorded in 1901)');
    expect(lightEras(base({ characteristic: 'F W (1901)', deactivated: 1931 }, 'lost'))[0]!.label).toBe('As it was when last lit (the light went out in 1931; pattern recorded in 1901)');
    expect(lightEras(base({ characteristic: 'Fl W 6s (c1965)' }, 'unknown'))[0]!.label).toBe('As last recorded (whether it is still lit is not known; pattern recorded about 1965)');
    expect(lightEras(base({ characteristic: 'Fl W 6s' }, 'unknown'))[0]!.label).toContain('whether it is still lit is not known');
  });

  it('the station page section, for every fixture with a light', () => {
    for (const r of records.values()) {
      const out = nightSection(r, ctx);
      if (r.kind === 'life_saving_station' || !r.light) expect(out, r.id).toBeNull();
      else expect(out, r.id).not.toBeNull();
    }
    const page = renderStationMain(rec('us-me-example-head'), ctx).value;
    expect(page).toContain('<section class="s-section" id="night"');
    expect(page.indexOf('id="facts"')).toBeLessThan(page.indexOf('id="night"'));
    expect(page.indexOf('id="night"')).toBeLessThan(page.indexOf('id="timeline"'));
    const night = nightSection(rec('us-me-example-head'), ctx)!.value;
    expect(night).toContain('From 1958 to today, as charted');
    expect(night).toContain('The record also gives 2 earlier patterns: choose the year below.');
    expect(night).toContain('class="strip-svg"');
    expect(night).toContain('Flash: not recorded; drawn at 0.5 s');
    expect(night).toContain('A guide, not a navigation aid.');
    expect(night.match(/not a navigation aid/g)).toHaveLength(1);
    // the data for the scene: an attribute, not a script
    const m = /data-night="([^"]+)"/.exec(night)!;
    const data = JSON.parse(m[1]!.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&'));
    expect(data).toEqual(JSON.parse(JSON.stringify(nightData(rec('us-me-example-head'), ctx))));
    expect(data.events).toHaveLength(2);
  });

  it('says what is missing rather than assuming it', () => {
    const lightship = nightSection(rec('us-ma-example-shoals-lightship-station'), ctx)!.value;
    expect(lightship).toContain('As it was when last lit (the light went out in 1983)');
    expect(lightship).toContain('Its focal height (the height of the light above the water) is not recorded');
    expect(lightship).not.toContain('How far out it');
    const vessel = nightSection(rec('us-ma-fixture-lightship'), ctx)!.value;
    expect(vessel).toContain('Nothing is recorded yet about this light’s pattern, its height or its range');
    const unread = nightSection(rec('us-gu-sample-point'), ctx)!.value;
    expect(unread).toContain('<code class="char">Al W 10s</code>');
    expect(unread).toContain('this page cannot read it');
    expect(unread).not.toContain('class="strip-svg"');
  });

  it('metres first in Canada', () => {
    const out = nightSection(rec('ca-ns-fixture-island'), ctx)!.value;
    expect(out).toContain('eye 3 m (10 ft) above the water');
  });

  it('the map: rings for the lights whose height or range is recorded', () => {
    const withData = geo.features.filter((f) => f.properties.k !== 'life_saving_station' && (f.properties.fh || f.properties.rn));
    expect(withData.length).toBeGreaterThan(3);
    const head = geo.features.find((f) => f.properties.i === 'us-me-example-head')!;
    expect(head.properties).toMatchObject({ fh: 30, rn: 24 });
    const rings = reachCollection(geo.features, DEFAULT_EYE_M);
    expect(rings.features).toHaveLength(withData.length);
    expect(rings.features.at(-1)!.properties.lit).toBe(1); // lit lights draw last, on top
    const r = rings.features.find((f) => f.properties.i === 'us-me-example-head')!;
    expect(r.properties).toMatchObject({ nm: Number(geographicRangeNm(30, 3).toFixed(1)), limit: 'horizon', lit: 1 });
  });
});
