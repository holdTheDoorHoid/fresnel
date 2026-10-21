/**
 * A light's eras: the characteristic (and, where recorded, the height and range) it showed in
 * each period of its life, for the year selector of "The light at night".
 *
 * Where eras come from:
 *  - `characteristic_changed` events (DESIGN.md 3.4). Each starts an era in its year. The event
 *    gives the new pattern in `characteristic` (or, failing that, in its note: "Fl W 4s",
 *    "changed to Fl W 4s", "from F W to Fl W 4s"), the old one in `previous_characteristic`
 *    (or the note's "from ... to ..."), and may give that era's `focal_height_m` and `range_nm`.
 *  - Dates and era words inside the characteristic text itself: "F W (original); Fl W ...
 *    (current)", "F R (initially F W)", "F W (1901)" (lib/characteristic.ts reads them).
 *  - Otherwise one era: the light as charted today, or, for a light that is out or gone, as it
 *    was when last lit.
 *
 * Height and range: an era uses its own figures when the record gives them. The latest era uses
 * the station's charted figures. An earlier era borrows the station's focal height (the tower
 * may well have been the same; the page says it is borrowed) but never its range: lamps and
 * lenses changed, so an old light's brightness is unknown unless recorded.
 */
import { readLight, type LightReading } from './characteristic.ts';
import type { StationEvent, StationRecord } from './types.ts';

export interface LightEra {
  id: string;
  /** "Today, as charted", "As it was when last lit (it went out in 1931)", "1883 to 1958". */
  label: string;
  /** For the selector: "Today", "Until 1931", "1883–1958", "Original". */
  short: string;
  from: number | null;
  to: number | null;
  reading: LightReading;
  focalM: number | null;
  nominalNm: number | null;
  /** Where the height came from: this era's record, borrowed from today's, or not recorded. */
  focalFrom: 'era' | 'station' | 'none';
  rangeFrom: 'era' | 'station' | 'none';
  /** The light no longer shows this: an earlier era, or the last era of a light that is out. */
  past: boolean;
  /** The station's light is out or gone and this is the last pattern it showed. */
  lastLit: boolean;
  /** Text about the era the visitor should read (the record's note, a gap before it). */
  note: string | null;
}

/** The parts of a station record the eras are worked out from. */
export type EraInput = Pick<StationRecord, 'light' | 'events' | 'status'>;

type ChangeEvent = StationEvent & { characteristic?: string | null; previous_characteristic?: string | null; focal_height_m?: number | null; range_nm?: number | null };

function finite(v: unknown): v is number {
  return typeof v === 'number' && Number.isFinite(v) && v > 0;
}

const norm = (s: string | null | undefined) => (s ?? '').replace(/[\s.]+/g, '').toLowerCase();

/** The new and old patterns an event gives, from its fields or its note. */
export function eventCharacteristics(e: ChangeEvent): { next: string | null; prev: string | null } {
  let next = typeof e.characteristic === 'string' && e.characteristic.trim() ? e.characteristic.trim() : null;
  let prev = typeof e.previous_characteristic === 'string' && e.previous_characteristic.trim() ? e.previous_characteristic.trim() : null;
  const note = (e.note ?? '').trim();
  if (note && (!next || !prev)) {
    const both = /\bfrom\s+(.+?)\s+to\s+(.+?)\.?$/i.exec(note);
    if (both) {
      prev ??= readLight(both[1]).lights.length ? both[1]!.trim() : null;
      next ??= readLight(both[2]).lights.length ? both[2]!.trim() : null;
    } else if (!next) {
      const to = /\bto\s+(.+?)\.?$/i.exec(note);
      if (to && readLight(to[1]).lights.length) next = to[1]!.trim();
      else if (readLight(note).lights.length) next = note;
    }
  }
  return { next, prev };
}

/** "Today, as charted" / "As it was when last lit" for the latest era, by the station's status. */
function finalWords(r: EraInput): { label: string; short: string; lastLit: boolean; past: boolean } {
  const out = typeof r.light?.deactivated === 'number' ? r.light.deactivated : null;
  if (r.status === 'active' && out === null) return { label: 'Today, as charted', short: 'Today', lastLit: false, past: false };
  if (['inactive', 'lost', 'ruins', 'relocated'].includes(r.status) || out !== null) {
    return {
      label: `As it was when last lit${out !== null ? ` (the light went out in ${out})` : ''}`,
      short: out !== null ? `Until ${out}` : 'When last lit',
      lastLit: true,
      past: true,
    };
  }
  if (r.status === 'replica') return { label: 'As recorded for this replica', short: 'As recorded', lastLit: false, past: false };
  return { label: 'As last recorded (whether it is still lit is not known)', short: 'Last recorded', lastLit: false, past: false };
}

function filtered(reading: LightReading, keep: (i: number) => boolean): LightReading {
  return { raw: reading.raw, lights: reading.lights.filter((_, i) => keep(i)), leftovers: reading.leftovers };
}

/** The eras of a station's light, oldest first. Empty when the station has no light record. */
export function lightEras(r: EraInput): LightEra[] {
  const L = r.light;
  if (!L) return [];
  const focal = finite(L.focal_height_m) ? L.focal_height_m : null;
  const range = finite(L.range_nm) ? L.range_nm : null;
  const firstLit = typeof L.first_lit === 'number' ? L.first_lit : null;
  const fin = finalWords(r);
  const current = readLight(L.characteristic);
  const changes = (r.events ?? [])
    .filter((e): e is ChangeEvent => !!e && e.event === 'characteristic_changed' && typeof e.year === 'number')
    .sort((a, b) => a.year! - b.year!);

  const era = (p: Partial<LightEra> & Pick<LightEra, 'id' | 'label' | 'short' | 'reading'>, own: { focal?: number | null; range?: number | null }, latest: boolean): LightEra => {
    const f = finite(own.focal) ? own.focal : null;
    const g = finite(own.range) ? own.range : null;
    return {
      from: null,
      to: null,
      past: !latest || fin.past,
      lastLit: latest && fin.lastLit,
      note: null,
      ...p,
      focalM: f ?? focal,
      focalFrom: f !== null ? 'era' : focal !== null ? 'station' : 'none',
      nominalNm: g ?? (latest ? range : null),
      rangeFrom: g !== null ? 'era' : latest && range !== null ? 'station' : 'none',
    };
  };

  if (changes.length) {
    const eras: LightEra[] = [];
    const first = eventCharacteristics(changes[0]!);
    if (first.prev) {
      const y = changes[0]!.year!;
      eras.push(era({ id: 'era-0', label: firstLit !== null ? `From ${firstLit} to ${y}` : `Before ${y}`, short: firstLit !== null ? `${firstLit}–${y}` : `Before ${y}`, from: firstLit, to: y, reading: readLight(first.prev) }, {}, false));
    }
    changes.forEach((e, i) => {
      const { next } = eventCharacteristics(e);
      const to = changes[i + 1]?.year ?? null;
      const last = i === changes.length - 1;
      const sameAsCurrent = last && (!next || norm(next) === norm(L.characteristic));
      const reading = next ? readLight(next) : sameAsCurrent ? current : readLight(null);
      if (last && sameAsCurrent) {
        const end = typeof L.deactivated === 'number' ? L.deactivated : null;
        const label = fin.lastLit
          ? `From ${e.year} until the light went out${end !== null ? ` in ${end}` : ''}: as it was when last lit`
          : r.status === 'active' ? `From ${e.year} to today, as charted` : `From ${e.year}: ${fin.label.charAt(0).toLowerCase()}${fin.label.slice(1)}`;
        const short = fin.lastLit ? (end !== null ? `${e.year}–${end}` : `From ${e.year}`) : r.status === 'active' ? `${e.year}–today` : `From ${e.year}`;
        eras.push(era({ id: `era-${i + 1}`, label, short, from: e.year!, to: end, reading, note: e.note ?? null }, { focal: e.focal_height_m, range: e.range_nm }, true));
      } else {
        eras.push(era({ id: `era-${i + 1}`, label: to !== null ? `From ${e.year} to ${to}` : `From ${e.year}`, short: to !== null ? `${e.year}–${to}` : `From ${e.year}`, from: e.year!, to, reading, note: next ? (e.note ?? null) : `The record says the pattern changed in ${e.year} but does not say to what.` }, { focal: e.focal_height_m, range: e.range_nm }, false));
      }
    });
    const lastEra = eras.at(-1)!;
    if (lastEra.past && !lastEra.lastLit && current.lights.length) {
      // The record's charted pattern is not the last change's: show it as the latest era, its start not recorded.
      eras.push(era({ id: `era-${eras.length}`, label: fin.label, short: fin.short, reading: current }, {}, true));
    }
    if (!first.prev && firstLit !== null && firstLit < changes[0]!.year!) {
      eras[0]!.note = [`Its pattern from ${firstLit} to ${changes[0]!.year} is not recorded.`, eras[0]!.note].filter(Boolean).join(' ');
    }
    return eras;
  }

  // Eras written into the characteristic itself.
  const dated = current.lights.map((l, i) => ({ l, i })).filter(({ l }) => l.era);
  if (dated.length && current.lights.length > 1) {
    const orders = [...new Set(dated.map(({ l }) => l.era!.order))].sort((a, b) => a - b);
    const eras: LightEra[] = [];
    orders.forEach((o, k) => {
      const latest = k === orders.length - 1;
      const members = new Set(current.lights.map((l, i) => ({ l, i })).filter(({ l }) => (l.era ? l.era.order === o : latest)).map(({ i }) => i));
      const first = current.lights[[...members][0]!]!;
      // A light that is out: its "current" pattern was the last one it showed.
      const word = fin.lastLit && first.era?.label === 'current' ? 'later' : first.era?.label ?? 'later';
      const label = word.replace(/^./, (ch) => ch.toUpperCase());
      const plainLatest = word === 'current' || word === 'later';
      eras.push(era({ id: `era-${k}`, label: latest ? (plainLatest ? fin.label : `${label}: ${fin.label.replace(/^./, (ch) => ch.toLowerCase())}`) : label, short: latest && plainLatest ? fin.short : label, reading: filtered(current, (i) => members.has(i)), from: first.era?.year ?? null }, {}, latest));
    });
    return eras;
  }
  const one = current.lights.length === 1 ? current.lights[0]! : null;
  const when = one?.era?.year ? `pattern recorded ${one.era.approx ? 'about' : 'in'} ${one.era.year}` : '';
  const label = !when ? fin.label : fin.label.endsWith(')') ? `${fin.label.slice(0, -1)}; ${when})` : `${fin.label} (${when})`;
  return [era({ id: 'era-0', label, short: fin.short, reading: current }, {}, true)];
}
