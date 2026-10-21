import { describe, expect, it } from 'vitest';
import { morseWords, parseCharacteristic, readCharacteristic } from '../src/lib/characteristic.ts';
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
    ['Q(3) W 10s', 'Three quick white flashes, repeated every 10 seconds'],
    ['Mo(A) W 8s', 'White flashes spelling the letter A in Morse code (short, long) every 8 seconds'],
    ['Al Fl W R 30s', 'Flashes alternating white and red, the pattern repeating every 30 seconds'],
    ['F W', 'A steady white light'],
    ['F R', 'A steady red light'],
    ['F Fl W 30s', 'A steady white light with a brighter flash every 30 seconds'],
    ['Fl Y 2.5s', 'One yellow flash every 2.5 seconds'],
  ])('%s', (raw, words) => expect(readCharacteristic(raw)).toBe(words));

  it('accepts the spellings sources use: dots, capitals, "Gp", spaces, a range after the period', () => {
    for (const raw of ['Fl.W.4s', 'FL W 4s', 'Fl W 4 s', 'Fl W 4sec', 'Fl W 4s 30m 24M']) expect(readCharacteristic(raw), raw).toBe('One white flash every 4 seconds');
    expect(readCharacteristic('Gp Fl(3) W 20s')).toBe('Three white flashes, repeated every 20 seconds');
    expect(readCharacteristic('Al.Fl.WR.30s')).toBe('Flashes alternating white and red, the pattern repeating every 30 seconds');
  });

  it('reads several colours without "Al" as coloured sectors', () => {
    expect(readCharacteristic('Fl WR 4s')).toBe('One flash every 4 seconds. It shows white or red depending on the direction you see it from (coloured sectors)');
    expect(parseCharacteristic('Oc WRG 10s')?.colours).toEqual(['W', 'R', 'G']);
  });

  it('returns the structure the light-at-night view will draw', () => {
    expect(parseCharacteristic('Fl(2) R 10s')).toEqual({ raw: 'Fl(2) R 10s', type: 'Fl', group: [2], morse: null, colours: ['R'], alternating: false, period: 10, tail: null, recorded: null, sectors: [], notes: [] });
    expect(parseCharacteristic('Mo(U) W 15s')).toMatchObject({ type: 'Mo', morse: 'U', period: 15 });
    expect(morseWords('U')).toBe('short, short, long');
  });

  it('leaves forms it does not cover unread, so the page shows them as given', () => {
    for (const raw of ['Al W 10s', 'R', 'inactive', 'decorative light', 'Fl W 400s', 'Q(6)+Fl W 15s', '', '   ', null, undefined]) expect(parseCharacteristic(raw as string), String(raw)).toBeNull();
  });
});

describe('the characteristic on a page', () => {
  it('shows the code and its reading, lower-cased after the colon', () => {
    expect(characteristicHtml('Fl W 4s')!.value).toBe('<span class="char-read"><code class="char">Fl W 4s</code>: one white flash every 4 seconds.</span>');
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
