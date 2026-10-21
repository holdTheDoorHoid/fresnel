/**
 * A light's characteristic as a timed pattern: what is lit, in which colour, from which second
 * to which, over one period. The strip diagram and the night scene both draw from it.
 *
 * Most records give only the notation ("Fl(2) W 15s"): how long each flash or eclipse lasts is
 * not written down. Those durations are drawn with the conventions below, within the limits of
 * IALA Recommendation R0110 (Rhythmic Characters of Lights on Aids to Navigation) and the USCG
 * Light List's rates, and every pattern lists, in plain words, which of its durations are
 * conventional rather than recorded (`conventions`). A duration the record does give
 * ("28 s on, 2 s off", "0.5 s flash") is used as given.
 *
 *  - Flash: 0.5 s, or a quarter of the period when that is shorter (R0110: a flash is under 2 s
 *    and the dark after it at least three times as long).
 *  - Groups: 1 s between the flashes of a group of two, 1.5 s for three or more, twice that
 *    between the parts of a composite group ("2+1"), and the dark after the group at least three
 *    times the gap inside it (R0110). When the period is too short for that, everything is scaled
 *    down to fit; when even that leaves flashes too short to tell apart, the pattern is not drawn.
 *  - Long flash: 2 s, the shortest long flash (R0110: 2 s or more).
 *  - Occulting: the eclipse is a quarter of the period, at most 2 s; in a group, 1 s eclipses with
 *    1 s of light between them.
 *  - Isophase: half the period lit, half dark (that is its definition).
 *  - Quick: 60 a minute (the US Light List rate; R0110 allows 50 to 79), very quick 120 a minute
 *    (80 to 159), ultra-quick 160 a minute (160 or more); each flash 0.3 of its cycle.
 *    Interrupted quick: quick flashes for three quarters of the period, then dark.
 *  - Morse: short flash 0.5 s, long flash 1.5 s (three times the short, as in Morse code),
 *    0.5 s between them.
 *  - Fixed and flashing: the steady light drawn at 40 % of the flash's brightness.
 *  - Alternating: the colours evenly spaced through the period, in the order written.
 *  - No period recorded: a period is chosen only to show the rhythm (5 s for a flash...), and the
 *    pattern says so; the strip then has no time scale.
 */
import { colourWord, morseCode, type Characteristic } from './characteristic.ts';

export interface Phase {
  /** Seconds from the start of the period. */
  start: number;
  dur: number;
  /** "W", "R"...; null = dark. */
  colour: string | null;
  /** 0..1: 1 for a flash or a steady light, 0.4 for the steady part of a fixed-and-flashing light. */
  level: number;
}

export interface Pattern {
  /** Seconds in one cycle as drawn. */
  period: number;
  /** False when the record gives no period and one was chosen to show the rhythm. */
  periodRecorded: boolean;
  /** A fixed light: no rhythm at all. */
  steady: boolean;
  /** Contiguous phases covering [0, period), dark ones included. */
  phases: Phase[];
  /** Plain words, one line for each duration that is a convention, not a record. */
  conventions: string[];
  /** False when the record gives no colour and the light is drawn white. */
  colourRecorded: boolean;
  /** The most times the light comes on within any one second (for the flashing warning). */
  flashRate: number;
}

export type PatternResult = { ok: true; pattern: Pattern } | { ok: false; reason: string };

export const CONVENTION = {
  flash: 0.5,
  gapPair: 1.0,
  gapGroup: 1.5,
  longFlash: 2.0,
  ocEclipseMax: 2.0,
  ocGroupEclipse: 1.0,
  ocGroupLight: 1.0,
  quickPerMinute: { Q: 60, VQ: 120, UQ: 160 } as Record<string, number>,
  quickDuty: 0.3,
  morseShort: 0.5,
  morseLong: 1.5,
  morseGap: 0.5,
  fixedLevel: 0.4,
  /** Shortest flash drawn after scaling to fit; shorter means the record cannot be drawn. */
  minFlash: 0.08,
} as const;

/** Display periods for a light whose record gives none. */
const UNRECORDED_PERIOD: Partial<Record<string, number>> = { Fl: 5, LFl: 10, Oc: 6, Iso: 4, FFl: 10, Mo: 8, IQ: 10, IVQ: 10, IUQ: 10 };

function s(n: number): string {
  return `${Number(n.toFixed(2))} s`;
}

interface Lit {
  start: number;
  dur: number;
  colour: string;
  level: number;
}

/** Fill the dark gaps between lit spans (sorted, non-overlapping) to cover [0, period). */
function toPhases(lit: Lit[], period: number, base: { colour: string; level: number } | null): Phase[] {
  const out: Phase[] = [];
  let t = 0;
  const gap = (until: number) => {
    if (until - t > 1e-6) out.push({ start: t, dur: until - t, colour: base ? base.colour : null, level: base ? base.level : 0 });
  };
  for (const l of [...lit].sort((a, b) => a.start - b.start)) {
    gap(l.start);
    out.push({ start: l.start, dur: l.dur, colour: l.colour, level: l.level });
    t = l.start + l.dur;
  }
  gap(period);
  return out;
}

/** Times the light brightens (dark to lit, or steady to flash) within any one-second window. */
export function flashRate(phases: Phase[], period: number): number {
  const onsets: number[] = [];
  for (let k = 0; k < 3; k++) {
    phases.forEach((p, i) => {
      const prev = phases[(i - 1 + phases.length) % phases.length]!;
      if (p.level > prev.level + 1e-6 || (p.colour !== prev.colour && p.colour && p.level >= prev.level)) onsets.push(p.start + k * period);
    });
  }
  onsets.sort((a, b) => a - b);
  let best = 0;
  for (let i = 0; i < onsets.length; i++) {
    let j = i;
    while (j < onsets.length && onsets[j]! < onsets[i]! + 1 - 1e-9) j++;
    best = Math.max(best, j - i);
  }
  return best;
}

/**
 * Flashes (or eclipses) in groups: each element `el` long, `gap` between elements of a part,
 * `between` between parts, the rest of the period after. Scales down when the period is short.
 * Returns the element start times and their length, or null when they cannot fit.
 */
function groupLayout(parts: number[], period: number, el: number, gap: number, between: number, restMin: number): { starts: number[]; el: number; scaled: boolean } | null {
  const n = parts.reduce((a, b) => a + b, 0);
  const inner = parts.reduce((a, b) => a + (b - 1), 0);
  const total = n * el + inner * gap + (parts.length - 1) * between;
  let k = 1;
  if (period - total < restMin) k = period / (total + restMin);
  if (el * k < CONVENTION.minFlash) return null;
  const starts: number[] = [];
  let t = 0;
  parts.forEach((m, pi) => {
    for (let i = 0; i < m; i++) {
      starts.push(t);
      t += el * k + (i < m - 1 ? gap * k : 0);
    }
    if (pi < parts.length - 1) t += between * k;
  });
  return { starts, el: el * k, scaled: k < 1 };
}

const TOO_SHORT = (what: string, period: number) =>
  `${what.replace(/^./, (ch) => ch.toUpperCase())} cannot fit in ${Number(period.toFixed(2))} second${period === 1 ? '' : 's'} with gaps the eye could tell apart, so the record may be miswritten; the pattern is not drawn.`;

/** The timed pattern of a characteristic, seen in `colour` (a sector's colour) when given. */
export function lightPattern(c: Characteristic, opts: { colour?: string } = {}): PatternResult {
  const conventions: string[] = [];
  const colourRecorded = c.colours.length > 0 || !!opts.colour;
  const main = opts.colour ?? c.colours[0] ?? 'W';
  if (!colourRecorded) conventions.push('Colour: not recorded; drawn white.');
  const colours = c.alternating ? c.colours : [main];
  const rec = c.recorded ?? {};

  let period = c.period;
  let periodRecorded = period !== null;
  const done = (lit: Lit[], p: number, base: { colour: string; level: number } | null = null, steady = false): PatternResult => {
    const phases = toPhases(lit, p, base);
    return { ok: true, pattern: { period: p, periodRecorded, steady, phases, conventions, colourRecorded, flashRate: steady ? 0 : flashRate(phases, p) } };
  };
  const needPeriod = (fallback: number) => {
    if (period === null) {
      period = fallback;
      periodRecorded = false;
      conventions.push(`Period: not recorded; drawn as ${s(fallback)} only to show the rhythm.`);
    }
    return period;
  };

  // Steady lights.
  if (c.type === 'F') {
    if (c.alternating) {
      const P = needPeriod(colours.length * 3);
      const durs = rec.perColour?.length === colours.length ? rec.perColour : colours.map(() => P / colours.length);
      if (!rec.perColour) conventions.push('Each colour: drawn for an equal share of the period (not recorded).');
      let t = 0;
      const lit = colours.map((col, i) => {
        const l = { start: t, dur: durs[i]!, colour: col, level: 1 };
        t += durs[i]!;
        return l;
      });
      return done(lit, t);
    }
    periodRecorded = false;
    return done([{ start: 0, dur: 4, colour: main, level: 1 }], 4, null, true);
  }

  const quick = (type: string) => CONVENTION.quickPerMinute[type.replace(/^I/, '')];

  // Quick, very quick and ultra-quick lights, continuous, grouped, interrupted.
  if (['Q', 'VQ', 'UQ', 'IQ', 'IVQ', 'IUQ'].includes(c.type)) {
    const base = c.type.replace(/^I/, '');
    const rate = quick(c.type)!;
    let cycle = 60 / rate;
    const name = base === 'Q' ? 'Quick' : base === 'VQ' ? 'Very quick' : 'Ultra-quick';
    const allowed = base === 'Q' ? '50 to 79' : base === 'VQ' ? '80 to 159' : '160 or more';
    const f = () => cycle * CONVENTION.quickDuty;
    const rateNote = () => conventions.push(`${name} flashes: drawn at ${rate} a minute${base === 'Q' ? ' (the US Light List rate)' : ''}, each ${s(f())}; IALA allows ${allowed} a minute.`);
    if (c.type === base && !c.group) {
      // Continuous. A period close to one cycle is the cycle itself ("Q R 1s").
      if (period !== null && period >= cycle * 0.7 && period <= cycle * 1.3) {
        cycle = period;
        conventions.push(`${name} flashes: one every ${s(cycle)} as recorded, each ${s(f())} (not recorded).`);
      } else {
        if (period !== null) conventions.push(`The record gives ${s(period)}, which is not one ${name.toLowerCase()} cycle; it is drawn as continuous ${name.toLowerCase()} flashes.`);
        rateNote();
      }
      periodRecorded = true;
      return done([{ start: 0, dur: f(), colour: main, level: 1 }], cycle);
    }
    const P = needPeriod(10);
    rateNote();
    const lit: Lit[] = [];
    if (c.type !== base) {
      // Interrupted: quick flashes, then a dark pause.
      const n = c.group?.[0] ?? Math.max(2, Math.floor((P * 0.75) / cycle));
      if (!c.group) conventions.push('The dark pause: drawn as a quarter of the period (not recorded).');
      if (n * cycle > P - cycle) return { ok: false, reason: TOO_SHORT(`${n} ${name.toLowerCase()} flashes and a pause`, P) };
      for (let i = 0; i < n; i++) lit.push({ start: i * cycle, dur: f(), colour: main, level: 1 });
      return done(lit, P);
    }
    const n = c.group!.reduce((a, b) => a + b, 0);
    const tailLen = c.tail ? CONVENTION.longFlash : 0;
    if (n * cycle + tailLen + cycle > P) return { ok: false, reason: TOO_SHORT(`${n} ${name.toLowerCase()} flashes`, P) };
    for (let i = 0; i < n; i++) lit.push({ start: i * cycle, dur: f(), colour: main, level: 1 });
    if (c.tail) {
      lit.push({ start: n * cycle, dur: tailLen, colour: main, level: 1 });
      conventions.push(`Long flash: drawn at ${s(tailLen)}, the shortest long flash IALA allows.`);
    }
    return done(lit, P);
  }

  if (c.type === 'Iso') {
    const P = needPeriod(UNRECORDED_PERIOD.Iso!);
    if (c.alternating) {
      const sub = P / colours.length;
      conventions.push('Colours: drawn in turn, evenly through the period (not recorded).');
      return done(colours.map((col, i) => ({ start: i * sub, dur: sub / 2, colour: col, level: 1 })), P);
    }
    return done([{ start: 0, dur: P / 2, colour: main, level: 1 }], P);
  }

  if (c.type === 'Oc') {
    const P = needPeriod(UNRECORDED_PERIOD.Oc!);
    if (rec.light !== undefined && rec.dark !== undefined) return done([{ start: 0, dur: rec.light, colour: main, level: 1 }], rec.light + rec.dark);
    const parts = c.group ?? [1];
    const subs = c.alternating ? colours : [main];
    const sub = P / subs.length;
    if (c.alternating) conventions.push('Colours: drawn in turn, evenly through the period (not recorded).');
    if (parts.length === 1 && parts[0] === 1) {
      const e = Math.min(sub / 4, CONVENTION.ocEclipseMax);
      conventions.push(`Eclipse: not recorded; drawn at ${s(e)} (light is longer than dark in an occulting light).`);
      return done(subs.map((col, i) => ({ start: i * sub, dur: sub - e, colour: col, level: 1 })), P);
    }
    // Groups of eclipses at the end of each sub-period, light between them.
    const layout = groupLayout(parts, sub, CONVENTION.ocGroupEclipse, CONVENTION.ocGroupLight, CONVENTION.ocGroupLight * 2, CONVENTION.ocGroupLight * 3);
    if (!layout) return { ok: false, reason: TOO_SHORT(`${parts.join('+')} eclipses`, sub) };
    conventions.push(`Eclipses: drawn at ${s(layout.el)} with ${s(layout.el)} of light between them (not recorded).`);
    const lit: Lit[] = [];
    subs.forEach((col, i) => {
      const t0 = i * sub;
      const groupLen = layout.starts.at(-1)! + layout.el;
      const offset = sub - groupLen;
      let t = 0;
      for (const st of layout.starts) {
        lit.push({ start: t0 + t, dur: offset + st - t, colour: col, level: 1 });
        t = offset + st + layout.el;
      }
    });
    return done(lit, P);
  }

  if (c.type === 'Mo') {
    const P = needPeriod(UNRECORDED_PERIOD.Mo!);
    const code = c.morse ? morseCode(c.morse) : null;
    if (!code) return { ok: false, reason: `The Morse letter “${c.morse ?? ''}” is not one this page can spell out.` };
    const { morseShort: dot, morseLong: dash, morseGap: gap } = CONVENTION;
    const total = [...code].reduce((a, ch) => a + (ch === '.' ? dot : dash), 0) + (code.length - 1) * gap;
    const k = total + 3 * gap > P ? P / (total + 3 * gap) : 1;
    if (dot * k < CONVENTION.minFlash) return { ok: false, reason: TOO_SHORT(`The Morse letter ${c.morse}`, P) };
    conventions.push(`Morse: short flash ${s(dot * k)}, long flash ${s(dash * k)}, ${s(gap * k)} between them (not recorded).`);
    const lit: Lit[] = [];
    let t = 0;
    for (const ch of code) {
      const d = (ch === '.' ? dot : dash) * k;
      lit.push({ start: t, dur: d, colour: main, level: 1 });
      t += d + gap * k;
    }
    return done(lit, P);
  }

  // Flashing, long-flashing, and fixed-and-flashing lights.
  const long = c.type === 'LFl';
  const fixedBase = c.type === 'FFl';
  const P = needPeriod(UNRECORDED_PERIOD[c.type] ?? 5);
  const parts = c.group ?? [1];
  const many = parts.reduce((a, b) => a + b, 0);
  const alternatingSplit = c.alternating && (parts.length === 1 && parts[0] === 1);
  const subs = alternatingSplit ? colours : [null];
  const sub = P / subs.length;
  if (alternatingSplit) {
    conventions.push(
      rec.perColour?.length === colours.length
        ? `Colours: each shows for the time recorded (${colours.map((col, i) => `${colourWord(col)} ${s(rec.perColour![i]!)}`).join(', ')}), a flash at the start of each.`
        : 'Colours: drawn in turn, evenly through the period (not recorded).',
    );
  }
  const subStarts = alternatingSplit && rec.perColour?.length === colours.length ? rec.perColour.reduce<number[]>((a, _d, i) => [...a, i ? a[i - 1]! + rec.perColour![i - 1]! : 0], []) : subs.map((_, i) => i * sub);
  const span = (i: number) => (alternatingSplit && rec.perColour?.length === colours.length ? rec.perColour[i]! : sub);

  let el: number;
  if (rec.flash !== undefined) el = rec.flash;
  else if (long) {
    el = Math.min(CONVENTION.longFlash, span(0) / 2);
    conventions.push(`Long flash: drawn at ${s(el)}, the shortest long flash IALA allows (2 s or more).`);
  } else el = Math.min(CONVENTION.flash, span(0) / 4);

  const lit: Lit[] = [];
  if (many === 1) {
    if (rec.flash === undefined && !long) conventions.push(`Flash: not recorded; drawn at ${s(el)} (IALA: under 2 s, with the dark at least three times as long).`);
    subs.forEach((col, i) => lit.push({ start: subStarts[i]!, dur: el, colour: col ?? main, level: 1 }));
  } else {
    const gap = long ? CONVENTION.longFlash : Math.max(...parts) >= 3 ? CONVENTION.gapGroup : CONVENTION.gapPair;
    const layout = groupLayout(parts, P, el, gap, gap * 2, gap * 3);
    if (!layout) return { ok: false, reason: TOO_SHORT(`${many} flashes`, P) };
    const word = long ? 'Long flashes' : 'Flashes';
    conventions.push(`${word} in the group: drawn at ${s(layout.el)}, ${s(layout.el * (gap / el))} apart${parts.length > 1 ? `, twice that between the parts of the group` : ''} (not recorded${layout.scaled ? '; shortened to fit the period' : ''}).`);
    // Alternating groups: a colour per part when the parts match the colours, else per flash in turn.
    const perPart = c.alternating && parts.length === colours.length;
    if (c.alternating) conventions.push(perPart ? 'Colours: one for each part of the group, in the order written (not recorded).' : 'Colours: flash by flash in turn (not recorded).');
    let idx = 0;
    parts.forEach((m, pi) => {
      for (let i = 0; i < m; i++, idx++) {
        const col = c.alternating ? (perPart ? colours[pi]! : colours[idx % colours.length]!) : main;
        lit.push({ start: layout.starts[idx]!, dur: layout.el, colour: col, level: 1 });
      }
    });
  }
  if (fixedBase) {
    conventions.push(`The steady light: drawn at ${Math.round(CONVENTION.fixedLevel * 100)} % of the flash's brightness (not recorded).`);
    return done(lit, P, { colour: main, level: CONVENTION.fixedLevel });
  }
  return done(lit, P);
}

/** Is the light lit at time `t` (seconds, any value), and how brightly and in what colour. */
export function phaseAt(p: Pattern, t: number): Phase {
  const x = ((t % p.period) + p.period) % p.period;
  for (const ph of p.phases) if (x >= ph.start && x < ph.start + ph.dur) return ph;
  return p.phases.at(-1)!;
}

/** "light 0.5 s, dark 3.5 s": the phases in words, for screen readers and the strip's caption. */
export function phaseWords(p: Pattern): string {
  if (p.steady) return 'Lit all the time.';
  return `${p.phases
    .map((ph) => `${ph.colour === null ? 'dark' : ph.level < 1 ? `${colourWord(ph.colour)}, dimmer` : colourWord(ph.colour)} ${s(ph.dur)}`)
    .join(', ')}${p.periodRecorded ? '' : ' (period not recorded)'}.`;
}
