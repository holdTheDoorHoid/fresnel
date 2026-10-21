import { readFileSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { describeReading, morseWords, parseCharacteristic, readCharacteristic, readLight, sectorColours } from '../src/lib/characteristic.ts';
import { lightPattern } from '../src/lib/pattern.ts';
import { characteristicHtml } from '../src/render/station.ts';

describe('reading a light characteristic', () => {
  it.each([
    ['Fl W 4s', 'One white flash every 4 seconds'],
    ['Fl(2) R 10s', 'Two red flashes, repeated every 10 seconds'],
    ['Fl (2) W 20s', 'Two white flashes, repeated every 20 seconds'],
    ['Fl(2+1) G 15s', 'Green flashes in a group of two then one, repeated every 15 seconds'],
    ['LFl W 10s', 'One long white flash every 10 seconds (a long flash lasts 2 seconds or more)'],
    ['Oc W 4s', 'A steady white light that goes dark once every 4 seconds; it is on for longer than it is off'],
    ['Oc(2) W 8s', 'A steady white light that goes dark twice every 8 seconds; it is on for longer than it is off'],
    ['Iso G 6s', 'Green light and darkness of equal length: 3 seconds on, 3 seconds off'],
    ['Q R', 'Quick red flashes, about 60 a minute, without a pause'],
    ['VQ G', 'Very quick green flashes, about 120 a minute, without a pause'],
    ['UQ W', 'Ultra-quick white flashes, 160 or more a minute, without a pause'],
    ['Q(3) W 10s', 'Three quick white flashes, repeated every 10 seconds'],
    ['Q(6)+LFl W 15s', 'Six quick white flashes followed by a long flash, repeated every 15 seconds'],
    ['IQ W 15s', 'Quick white flashes broken by a dark pause, repeated every 15 seconds'],
    ['Mo(A) W 8s', 'White flashes spelling the letter A in Morse code (short, long) every 8 seconds'],
    ['Al Fl W R 30s', 'Flashes alternating white and red, the pattern repeating every 30 seconds'],
    ['F W', 'A steady white light'],
    ['F R', 'A steady red light'],
    ['F Fl W 30s', 'A steady white light with a brighter flash every 30 seconds'],
    ['Fl Y 2.5s', 'One yellow flash every 2.5 seconds'],
    ['Fl W', 'A flashing white light (how often is not recorded)'],
    ['Fl 5s', 'One flash every 5 seconds (its colour is not recorded)'],
  ])('%s', (raw, words) => expect(readCharacteristic(raw)).toBe(words));

  it('accepts the spellings sources use: dots, capitals, "Gp", spaces, a range after the period', () => {
    for (const raw of ['Fl.W.4s', 'FL W 4s', 'Fl W 4 s', 'Fl W 4sec', 'Fl W 4 sec', 'Fl W, 4s', 'Fl W 4s,', 'FI W 4s', 'Fl W 4s 30m 24M', 'flashing W 4s', 'flashing white every 4 seconds']) {
      expect(readCharacteristic(raw), raw).toBe('One white flash every 4 seconds');
    }
    expect(readCharacteristic('Gp Fl(3) W 20s')).toBe('Three white flashes, repeated every 20 seconds');
    expect(readCharacteristic('Al.Fl.WR.30s')).toBe('Flashes alternating white and red, the pattern repeating every 30 seconds');
    expect(readCharacteristic('L Fl W 10s')).toBe(readCharacteristic('LFl W 10s'));
    expect(readCharacteristic('Fl((1)) R 2.5s')).toBe('One red flash every 2.5 seconds');
    for (const raw of ['QF W', 'QFI W', 'Q F W']) expect(readCharacteristic(raw), raw).toBe('Quick white flashes, about 60 a minute, without a pause');
  });

  it('reads several colours without "Al" as coloured sectors', () => {
    expect(readCharacteristic('Fl WR 4s')).toBe('One flash every 4 seconds. It shows white or red depending on the direction you see it from (coloured sectors)');
    expect(parseCharacteristic('Oc WRG 10s')?.colours).toEqual(['W', 'R', 'G']);
    expect(parseCharacteristic('Fl W/R 10s')?.colours).toEqual(['W', 'R']);
  });

  it('reads sector clauses, with bearings when the record gives them', () => {
    expect(readCharacteristic('FI W 6s, R sector')).toBe('One white flash every 6 seconds. It has a red sector: from some directions it shows red instead');
    expect(readCharacteristic('Fl W 6s with two R sectors')).toBe('One white flash every 6 seconds. It has two red sectors: from some directions it shows red instead');
    expect(readCharacteristic('FI W 6s, R sectors')).toContain('It has red sectors');
    expect(readCharacteristic('Fl W 6s (R sector)')).toContain('a red sector');
    expect(readCharacteristic('Oc W 4s, R sector 045° to 135°')).toBe('A steady white light that goes dark once every 4 seconds; it is on for longer than it is off. It shows red from 045° to 135° (bearings from seaward)');
    expect(parseCharacteristic('Oc W 4s, R sector 045° to 135°')!.sectors).toEqual([{ colour: 'R', from: 45, to: 135, count: null }]);
    expect(readCharacteristic('Fl R, dark sector')).toContain('From some directions it cannot be seen (a dark sector)');
    expect(sectorColours(parseCharacteristic('F W, R sector')!)).toEqual(['W', 'R']);
    expect(sectorColours(parseCharacteristic('Al Fl WR 10s')!)).toEqual([]);
  });

  it('reads records written in words, and says what it decided', () => {
    expect(readCharacteristic('fixed white varied by a flash every 90 seconds')).toBe('A steady white light with a brighter flash every 90 seconds');
    expect(readCharacteristic('F W with W Fl every 2 minutes')).toBe('A steady white light with a brighter flash every 120 seconds');
    expect(readCharacteristic('FF W, FI W 60s')).toBe('A steady white light with a brighter flash every 60 seconds');
    expect(readCharacteristic('5 s R flash')).toBe('One red flash every 5 seconds');
    expect(readCharacteristic('28 s on, 2 s off')).toBe('A steady light that goes dark once every 30 seconds; it is on for longer than it is off (28 seconds on, 2 seconds off, as recorded; its colour is not recorded)');
    expect(parseCharacteristic('28 s on, 2 s off')!.recorded).toEqual({ light: 28, dark: 2 });
    expect(parseCharacteristic('0.5-s Flevery 9.5s')).toMatchObject({ type: 'Fl', period: 9.5, recorded: { flash: 0.5 } });
    const alt = parseCharacteristic('Fl alternately R and W, interval between Fl 10s')!;
    expect(alt).toMatchObject({ type: 'Fl', alternating: true, colours: ['R', 'W'], period: 20 });
    expect(alt.notes.join()).toContain('10 seconds between flashes');
    expect(parseCharacteristic('Alt W 5s, R 5s')).toMatchObject({ alternating: true, colours: ['W', 'R'], period: 10, recorded: { perColour: [5, 5] } });
    expect(parseCharacteristic('Alternating R and G 24 s (R 12s , G 12s)')).toMatchObject({ colours: ['R', 'G'], period: 24, recorded: { perColour: [12, 12] } });
    const rev = parseCharacteristic('continuous revolving W with a 90 s interval')!;
    expect(rev).toMatchObject({ type: 'Fl', period: 90 });
    expect(rev.notes.join()).toContain('revolving');
    expect(parseCharacteristic('FF W')!.notes.join()).toContain('feu fixe');
    expect(parseCharacteristic("Feu fixe d'alignement")).toMatchObject({ type: 'F', colours: [] });
    expect(parseCharacteristic('Fl W 5')!.notes.join()).toContain('no unit');
    // "Al WR" with a period: read as flashes, and the reading says so
    const nauset = parseCharacteristic('Al WR 10s')!;
    expect(nauset).toMatchObject({ type: 'Fl', alternating: true, period: 10 });
    expect(nauset.notes.join()).toContain('drawn as alternating flashes');
    // a fixed light with a period: drawn steady, with a warning
    const fp = parseCharacteristic('F W 30s')!;
    expect(fp).toMatchObject({ type: 'F', period: null });
    expect(fp.notes.join()).toContain('a fixed light has none');
  });

  it('reads records with several lights, eras and notes', () => {
    const range = readLight('F R (rear); F W (front)');
    expect(range.lights.map((l) => [l.role, l.c.colours[0]])).toEqual([['rear', 'R'], ['front', 'W']]);
    expect(describeReading(range)).toBe('Rear: a steady red light. Front: a steady white light');
    const passing = readLight('F G (along range line)<br>Fl W 4s (passing light)');
    expect(passing.lights.map((l) => l.role)).toEqual(['along the range line', 'passing light']);
    const eras = readLight('F W (original); Fl W with two R sectors (current)');
    expect(eras.lights.map((l) => [l.era?.label, l.era?.order, l.c.type])).toEqual([['original', -1, 'F'], ['current', 1, 'Fl']]);
    const initially = readLight('F R (initially F W)');
    expect(initially.lights.map((l) => [l.era?.label, l.c.colours[0]])).toEqual([['later', 'R'], ['at first', 'W']]);
    expect(readLight('F R (originally W)').lights.map((l) => l.c.colours[0])).toEqual(['R', 'W']);
    expect(readLight('F W (1901)').lights[0]!.era).toMatchObject({ year: 1901, approx: false });
    expect(readLight('Fl W 6s (c1965)').lights[0]!.era).toMatchObject({ year: 1965, approx: true, label: 'about 1965' });
    const obscured = readLight('Fl W 6s.<br> obscuR from 158° to 318°');
    expect(obscured.lights[0]!.c.sectors).toEqual([{ colour: 'dark', from: 158, to: 318, count: null }]);
    expect(describeReading(obscured)).toContain('It cannot be seen from 158° to 318°');
    const emergency = readLight('Fl W 10s.<br> emergency light (Fl W 6s.) of Ruced intensity when main light is extinguished');
    expect(emergency.lights).toHaveLength(1);
    expect(emergency.lights[0]!.notes[0]).toBe('Emergency light (Fl W 6s) of reduced intensity when main light is extinguished.');
    const dated = readLight('Fl R, dark sector; illuminated 307° of the horizon; dark sectors lying towards shore (as of 1941)');
    expect(dated.lights[0]!.era).toMatchObject({ year: 1941, label: 'as recorded in 1941' });
    expect(dated.leftovers).toEqual([]);
    expect(readLight('W Flevery 6 s (R sector covers the shoal)').lights[0]!.notes).toEqual(['The red sector covers the shoal.']);
    expect(readCharacteristic('F W - visible on Range line only')).toBe('A steady white light'); // the note is the light's, below
    expect(describeReading(readLight('F W - visible on Range line only'))).toBe('A steady white light. It can be seen only along the range line.');
    expect(describeReading(readLight('F R avec F W (secteur)'))).toContain('It has a white sector');
  });

  it('returns the structure the light-at-night view will draw', () => {
    expect(parseCharacteristic('Fl(2) R 10s')).toEqual({ raw: 'Fl(2) R 10s', type: 'Fl', group: [2], morse: null, colours: ['R'], alternating: false, period: 10, tail: null, recorded: null, sectors: [], notes: [] });
    expect(parseCharacteristic('Mo(U) W 15s')).toMatchObject({ type: 'Mo', morse: 'U', period: 15 });
    expect(parseCharacteristic('Q(6)+LFl W 15s')).toMatchObject({ type: 'Q', group: [6], tail: 'LFl', period: 15 });
    expect(morseWords('U')).toBe('short, short, long');
  });

  it('leaves forms it does not cover unread, so the page shows them as given', () => {
    for (const raw of ['Al W 10s', 'R', 'inactive', 'decorative light', 'Fl W 400s', 'Q(6)+Fl W 15s', 'Fl W 4s Q', '', '   ', null, undefined]) {
      expect(parseCharacteristic(raw as string), String(raw)).toBeNull();
    }
  });
});

describe('the characteristic on a page', () => {
  it('shows the code and its reading, lower-cased after the colon', () => {
    expect(characteristicHtml('Fl W 4s')!.value).toBe('<span class="char-read"><code class="char">Fl W 4s</code>: one white flash every 4 seconds.</span>');
  });

  it('reads records with several lights, each with its role', () => {
    expect(characteristicHtml('F R (rear); F W (front)')!.value).toContain('Rear: a steady red light. Front: a steady white light.');
  });

  it('falls back to the raw string, and says so', () => {
    const out = characteristicHtml('Al W 10s')!.value;
    expect(out).toContain('<code class="char">Al W 10s</code>');
    expect(out).toContain('As the source writes it.');
  });

  it('marks the pattern of a light that is out as the last one recorded', () => {
    expect(characteristicHtml('F W', { lost: true })!.value).toContain('As last recorded.');
    expect(characteristicHtml(null)).toBeNull();
    expect(characteristicHtml('  ')).toBeNull();
  });
});

/* ---------- Every characteristic the stations carry ---------- */

const STATIONS = resolve(import.meta.dirname, '../../data/stations');

function realCharacteristics(): Map<string, number> {
  const out = new Map<string, number>();
  for (const dir of readdirSync(STATIONS)) {
    for (const f of readdirSync(join(STATIONS, dir))) {
      const r = JSON.parse(readFileSync(join(STATIONS, dir, f), 'utf8')) as { light?: { characteristic?: string | null } | null };
      const c = r.light?.characteristic;
      if (c) out.set(c, (out.get(c) ?? 0) + 1);
    }
  }
  return out;
}

describe('every characteristic in data/stations', () => {
  const real = realCharacteristics();

  it('reads them all except the few that are not light patterns', () => {
    const unread = [...real.keys()].filter((c) => !readLight(c).lights.length).sort();
    expect(unread).toEqual(['Al W 10s', 'R', 'current decorative light', 'decorative light', 'inactive']);
    const stations = [...real.values()].reduce((a, b) => a + b, 0);
    const read = [...real].filter(([c]) => readLight(c).lights.length).reduce((a, [, n]) => a + n, 0);
    expect(stations - read).toBe(7);
  });

  it('leaves nothing of a read record unexplained', () => {
    const leftovers = [...real.keys()].flatMap((c) => (readLight(c).lights.length ? readLight(c).leftovers : []));
    expect(leftovers).toEqual([]);
  });

  it('gives every reading a timed pattern, or a reason it cannot be drawn', () => {
    const fails: string[] = [];
    for (const c of real.keys()) {
      for (const l of readLight(c).lights) {
        const colours = sectorColours(l.c);
        for (const colour of colours.length ? colours : [undefined]) {
          const res = lightPattern(l.c, colour ? { colour } : {});
          if (!res.ok) {
            expect(res.reason.length, c).toBeGreaterThan(20);
            fails.push(c);
            continue;
          }
          const p = res.pattern;
          let t = 0;
          for (const ph of p.phases) {
            expect(ph.start, c).toBeCloseTo(t, 6);
            expect(ph.dur, c).toBeGreaterThan(0);
            t += ph.dur;
          }
          expect(t, c).toBeCloseTo(p.period, 6);
          expect(p.phases.some((ph) => ph.colour), c).toBe(true);
          if (l.c.period && !p.steady && l.c.type !== 'Q') expect(p.period, c).toBeCloseTo(l.c.period, 6);
        }
      }
    }
    // Six flashes in one second cannot be drawn apart: the record is probably miswritten.
    expect([...new Set(fails)]).toEqual(['Fl(6) W 1s']);
  });
});
