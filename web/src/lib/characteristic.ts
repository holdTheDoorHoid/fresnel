/**
 * Light characteristics: the abbreviation a chart or the Light List prints for a light's
 * pattern ("Fl W 4s", "Fl(2) R 10s", "Oc W 4s", "Iso G 6s", "Q R", "Mo(A) W 8s",
 * "Al Fl W R 30s", "F W"), read into a structure and into plain words: "Fl W 4s" -> "One white
 * flash every 4 seconds". lib/pattern.ts turns the structure into a timed on/off pattern.
 *
 * Notation covered (IALA, the USCG Light List, the Canadian List of Lights): F, Fl, LFl, Oc,
 * Iso, Q, VQ, UQ, IQ, IVQ, IUQ, Mo(X), F Fl, groups "(2)" and composite groups "(2+1)", the old
 * "Gp" prefix, a quick group followed by a long flash ("Q(6)+LFl"), "Al" for alternating
 * colours, colours W R G Y Bu Or (several letters without "Al" mean coloured sectors), and a
 * period in seconds. Heights and ranges printed after the period ("30m 24M") are ignored.
 *
 * Real records are messier, so `readLight` also reads, and says that it read:
 *  - spellings: dots and commas ("Fl.W.4s", "Fl W, 6s"), "FL", "FI" (a capital i for the l),
 *    "L Fl", "Alt", "QF" / "QFl" (old "quick flashing"), "4 sec", "4 s", "2 minutes";
 *  - "FF": the French "feu fixe", a fixed light (and "FF W, Fl W 60s" is a fixed light varied by
 *    a flash);
 *  - words: "fixed white varied by a flash every 90 seconds", "flashing W 2.5s", "5 s R flash",
 *    "28 s on, 2 s off", "Alternating R and G 24 s", "Alt W 5s, R 5s", "Fl alternately R and W,
 *    interval between Fl 10s", "continuous revolving W with a 90 s interval", "Feu fixe";
 *  - sector clauses: "R sector", "with two R sectors", "(R sector)", "R sector 045° to 135°",
 *    "dark sector", "obscured from 158° to 318°", "avec F W (secteur)";
 *  - several lights or dates in one record: "F R (rear); F W (front)", "F G (along range line)
 *    <br>Fl W 4s (passing light)", "F W (original); Fl W with two R sectors (current)",
 *    "F R (initially F W)", "F W (1901)", "Fl W 6s (c1965)", "(as of 1941)".
 *
 * Anything else is left unread: the page shows the text as the source writes it. Nothing is
 * guessed silently: every reading that needed a decision carries a note in plain words.
 */

export type LightType = 'F' | 'FFl' | 'Fl' | 'LFl' | 'Oc' | 'Iso' | 'Q' | 'VQ' | 'UQ' | 'IQ' | 'IVQ' | 'IUQ' | 'Mo';

/** A coloured or dark sector named in the record. Bearings are true, from seaward, when given. */
export interface Sector {
  /** "R", "W", ... or "dark" for an obscured sector. */
  colour: string;
  from: number | null;
  to: number | null;
  /** "two R sectors": 2; 0 for "R sectors" (more than one, number not said); null for one. */
  count: number | null;
}

/** Durations the record itself gives, in seconds (otherwise lib/pattern.ts uses conventions). */
export interface Recorded {
  flash?: number;
  light?: number;
  dark?: number;
  /** Alternating lights: how long each colour shows, in the colours' order. */
  perColour?: number[];
}

export interface Characteristic {
  raw: string;
  type: LightType;
  /** Flashes or eclipses per group: [2] for "(2)", [2, 1] for "(2+1)"; null for single. */
  group: number[] | null;
  /** The Morse letter of a Mo(X) light. */
  morse: string | null;
  /** "W", "R", "G", "Y", "Bu", "Or", in the order given; empty when the record gives none. */
  colours: string[];
  /** "Al": the colours alternate. Several colours without it are sectors. */
  alternating: boolean;
  /** Seconds for one full cycle; null when not given. */
  period: number | null;
  /** "Q(6)+LFl": a long flash follows the group of quick flashes. */
  tail: 'LFl' | null;
  recorded: Recorded | null;
  /** Sectors the text names besides its colour letters ("R sector", "dark sector"). */
  sectors: Sector[];
  /** Decisions the reader made, in plain words ("'FF' read as the French 'feu fixe'..."). */
  notes: string[];
}

/** One light in a record, with what the record says about which light or when. */
export interface ReadLight {
  c: Characteristic;
  /** Which light of the station: "front", "rear", "passing light", "along the range line". */
  role: string | null;
  /** When the record dates it. `order` sorts eras: earlier < 0 < later. */
  era: { label: string; year: number | null; approx: boolean; order: number } | null;
  /** Other things the record says about this light ("Visible only along the range line"). */
  notes: string[];
}

export interface LightReading {
  raw: string;
  /** The lights read from the text, in its order; empty when nothing could be read. */
  lights: ReadLight[];
  /** Parts of the text that were not used, as given. */
  leftovers: string[];
}

const COLOUR_WORDS: Record<string, string> = { W: 'white', R: 'red', G: 'green', Y: 'yellow', BU: 'blue', OR: 'orange', DARK: 'dark' };
const COLOUR_CODE: Record<string, string> = { W: 'W', R: 'R', G: 'G', Y: 'Y', BU: 'Bu', OR: 'Or' };
const WORD_TO_CODE: Record<string, string> = {
  white: 'W', red: 'R', green: 'G', yellow: 'Y', blue: 'Bu', orange: 'Or',
  blanc: 'W', blanche: 'W', rouge: 'R', vert: 'G', verte: 'G', jaune: 'Y',
};

export function colourWord(code: string): string {
  return COLOUR_WORDS[code.toUpperCase()] ?? code;
}

const TYPES: [RegExp, LightType][] = [
  [/^F\s*Fl\b/i, 'FFl'],
  [/^(?:Gp\s*)?L\s*Fl\b/i, 'LFl'],
  [/^(?:Gp\s*)?Fl\b/i, 'Fl'],
  [/^(?:Gp\s*)?Occ?\b/i, 'Oc'],
  [/^Iso\b/i, 'Iso'],
  [/^IUQ\b/i, 'IUQ'],
  [/^IVQ\b/i, 'IVQ'],
  [/^IQ\b/i, 'IQ'],
  [/^UQ\b/i, 'UQ'],
  [/^VQ\b/i, 'VQ'],
  [/^Q\b/i, 'Q'],
  [/^F\b/i, 'F'],
];

// \b does not work after ")" or before "(", so the group and Morse forms are matched on their own.
const TYPE_BEFORE_GROUP: [RegExp, LightType][] = [
  [/^F\s*Fl(?=\s*\()/i, 'FFl'],
  [/^(?:Gp\s*)?L\s*Fl(?=\s*\()/i, 'LFl'],
  [/^(?:Gp\s*)?Fl(?=\s*\()/i, 'Fl'],
  [/^(?:Gp\s*)?Occ?(?=\s*\()/i, 'Oc'],
  [/^IUQ(?=\s*\()/i, 'IUQ'],
  [/^IVQ(?=\s*\()/i, 'IVQ'],
  [/^IQ(?=\s*\()/i, 'IQ'],
  [/^UQ(?=\s*\()/i, 'UQ'],
  [/^VQ(?=\s*\()/i, 'VQ'],
  [/^Q(?=\s*\()/i, 'Q'],
];

const NUM = String.raw`(\d+(?:\.\d+)?)`;
const ALT = String.raw`Al(?:ternating|t)?`;
const C = String.raw`(?:Bu|Or|W|R|G|Y)`;
const COUNT_WORDS: Record<string, number> = { one: 1, two: 2, three: 3, four: 4, a: 1, an: 1 };

function blank(): Omit<Characteristic, 'raw' | 'type'> {
  return { group: null, morse: null, colours: [], alternating: false, period: null, tail: null, recorded: null, sectors: [], notes: [] };
}

/** Colour words to letters, seconds and minutes to "Ns", "every" before a number dropped. */
function normaliseWords(s: string): string {
  return s
    .replace(/\b(white|red|green|yellow|blue|orange|blanc|blanche|rouge|verte?|jaune)\b/gi, (m) => WORD_TO_CODE[m.toLowerCase()]!)
    .replace(new RegExp(String.raw`${NUM}\s*-?\s*(?:minutes?|mins?)(?![a-z])`, 'gi'), (_, n: string) => `${Number(n) * 60}s`)
    .replace(new RegExp(String.raw`${NUM}\s*-?\s*(?:seconds?|secs?|s)(?![a-z])`, 'gi'), '$1s')
    .replace(/\bgroup[- ]flashing\b/gi, 'Fl')
    .replace(/\bquick[- ]flashing\b/gi, 'Q')
    .replace(/\bflashing\b/gi, 'Fl')
    .replace(/\bflash(?:es)?\b/gi, 'Fl')
    .replace(/\boccult(?:ing)?\b/gi, 'Oc')
    .replace(/\bisophase\b/gi, 'Iso')
    .replace(/\bfixed\b/gi, 'F')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Notation clean-up: dots, "FI", "QF", "Alt", "((1))". */
function normaliseNotation(s: string, notes: string[]): string {
  // "Fl.W.4s" -> "Fl W 4s"; keep the decimal point of a period ("2.5s").
  s = s.replace(/(\d)\.(\d)/g, '$1\u0000$2').replace(/\./g, ' ').replace(/\u0000/g, '.');
  s = s.replace(/\bFI(?=[\s(\d]|$)/g, 'Fl'); // a capital i for the l
  s = s.replace(/\bQ\s*F(?:l|I)?(?=\s|$)/g, 'Q'); // "QF W", "QFl W", "Q F W": quick flashing
  s = s.replace(/\bAlt\b/gi, 'Al');
  s = s.replace(/\(\s*\(\s*([\d+\s]+)\s*\)\s*\)/g, '($1)');
  s = s.replace(/\bevery\s+(?=\d)/gi, '');
  s = s.replace(/\s+/g, ' ').trim();
  if (/^FF\b/.test(s)) {
    s = s.replace(/^FF\b/, 'F');
    if (!/\bFl\b/i.test(s)) notes.push('“FF” is read as the French “feu fixe”: a fixed light.');
  }
  // "F W, Fl W 60s", "F W with W Fl 120s", "F W with Fl 90s": a fixed light varied by a flash.
  s = s.replace(new RegExp(String.raw`^F\s+(${C}+)\s*(?:,|\bwith\b)?\s*(?:${C}+\s+)?Fl\b\s*(?:(${C}+)\b)?\s*`, 'i'), (_, a: string) => `F Fl ${a} `);
  return s.replace(/\s+/g, ' ').trim();
}

/** Whole-phrase readings of records written in words. Returns notation, or null. */
function prose(s: string, rec: Recorded, notes: string[]): string | null {
  let m: RegExpExecArray | null;
  if ((m = new RegExp(String.raw`^${NUM}s on,? ${NUM}s off$`, 'i').exec(s))) {
    const on = Number(m[1]);
    const off = Number(m[2]);
    rec.light = on;
    rec.dark = off;
    return `${on > off ? 'Oc' : on < off ? 'Fl' : 'Iso'} ${on + off}s`;
  }
  if ((m = new RegExp(String.raw`^${NUM}s Fl every ${NUM}s$`, 'i').exec(s))) {
    rec.flash = Number(m[1]);
    return `Fl ${m[2]}s`;
  }
  if ((m = new RegExp(String.raw`^${NUM}s (${C}) Fl$`, 'i').exec(s))) return `Fl ${m[2]} ${m[1]}s`;
  if ((m = new RegExp(String.raw`^(${C}) Fl every ${NUM}s(.*)$`, 'i').exec(s))) return `Fl ${m[1]} ${m[2]}s${m[3]}`;
  if ((m = new RegExp(String.raw`^Fl (${C}),? (?:1|one|a) Fl every ${NUM}s$`, 'i').exec(s))) return `Fl ${m[1]} ${m[2]}s`;
  if ((m = new RegExp(String.raw`^Fl alternately (${C}) and (${C}),? interval between Fl ${NUM}s$`, 'i').exec(s))) {
    const gap = Number(m[3]);
    notes.push(`The record gives ${gap} seconds between flashes, so one ${colourWord(m[1]!)} and one ${colourWord(m[2]!)} flash take ${gap * 2} seconds.`);
    return `Al Fl ${m[1]} ${m[2]} ${gap * 2}s`;
  }
  if ((m = new RegExp(String.raw`^${ALT} (${C}) and (${C}) ${NUM}s$`, 'i').exec(s))) return `Al ${m[1]} ${m[2]} ${m[3]}s`;
  if ((m = new RegExp(String.raw`^${ALT} (${C}) ${NUM}s, (${C}) ${NUM}s$`, 'i').exec(s))) {
    rec.perColour = [Number(m[2]), Number(m[4])];
    return `Al ${m[1]} ${m[3]} ${Number(m[2]) + Number(m[4])}s`;
  }
  if ((m = new RegExp(String.raw`^(?:continuous )?revolving (${C}) with an? ${NUM}s interval$`, 'i').exec(s))) {
    notes.push('Old light lists called a light with a turning lens “revolving”: it showed a flash each time a panel of the lens passed, so it is read as a flashing light.');
    return `Fl ${m[1]} ${m[2]}s`;
  }
  if ((m = new RegExp(String.raw`^F (${C}) varied by (?:an? |one |single )?(?:(${C}) )?Fl every ${NUM}s$`, 'i').exec(s))) return `F Fl ${m[1]} ${m[3]}s`;
  if ((m = new RegExp(String.raw`^F (${C}) varied by (?:a )?group of (\d) (?:(${C}) )?Fl every ${NUM}s$`, 'i').exec(s))) return `F Fl(${m[2]}) ${m[1]} ${m[4]}s`;
  if ((m = /^Feu fixe(?: d['’]alignement)?(?: (\w+))?$/i.exec(s))) {
    if (/alignement/i.test(s)) notes.push('“Feu fixe d’alignement” is French for a fixed range light.');
    const col = m[1] ? WORD_TO_CODE[m[1].toLowerCase()] ?? null : null;
    return col ? `F ${col}` : 'F';
  }
  return null;
}

const SECTOR_RE = new RegExp(
  String.raw`^(?:with\s+)?(?:(\d+|one|two|three|four|several)\s+)?((?:${C}|dark)(?:\s*(?:and|,|&)\s*(?:${C}|dark))*)\s+sectors?(?:\s+(?:covers?|covering)\s+([^,]+?))?(?:\s+(?:from\s+)?(\d{1,3})\s*°?\s*(?:to|-|–)\s*(\d{1,3})\s*°?)?$`,
  'i',
);

/** "R sector", "with two R sectors", "R sector 045° to 135°", "dark sector": the sectors, or null. */
function sectorClause(text: string): Sector[] | null {
  const t = text.trim().replace(/^[,(-]\s*|\s*[)]$/g, '').trim();
  const m = SECTOR_RE.exec(t);
  if (!m) {
    const ob = /^obscured\s+(?:from\s+)?(\d{1,3})\s*°?\s*(?:to|-|–)\s*(\d{1,3})\s*°?$/i.exec(t);
    if (ob) return [{ colour: 'dark', from: Number(ob[1]), to: Number(ob[2]), count: null }];
    const fr = new RegExp(String.raw`^avec\s+(?:F\s+)?(${C})(?:\s*\(?\s*secteurs?\s*\)?)?$`, 'i').exec(t);
    if (fr) return [{ colour: COLOUR_CODE[fr[1]!.toUpperCase()]!, from: null, to: null, count: null }];
    return null;
  }
  const countWord = m[1]?.toLowerCase();
  // 0: more than one, how many not said ("R sectors", "several R sectors").
  const plural = /sectors\b/i.test(t) ? 0 : null;
  const count = countWord ? (COUNT_WORDS[countWord] ?? (/^\d+$/.test(countWord) ? Number(countWord) : plural)) : plural;
  const colours = m[2]!.split(/\s*(?:and|,|&)\s*/i).map((c) => (c.toLowerCase() === 'dark' ? 'dark' : COLOUR_CODE[c.toUpperCase()]!));
  const from = m[4] ? Number(m[4]) : null;
  const to = m[5] ? Number(m[5]) : null;
  return colours.map((colour) => ({ colour, from, to, count: colours.length === 1 || count === 0 ? count : null }));
}

/** Clauses after the characteristic: sectors, "visible on the range line only", or nothing usable. */
function clauses(rest: string, c: Characteristic, lightNotes: string[]): string | null {
  let leftover = '';
  for (const part of rest.split(/\s*,\s*|\s+-\s+|\s+(?=with\b)/i)) {
    const p = part.trim().replace(/^-\s*/, '');
    if (!p) continue;
    const sec = sectorClause(p);
    if (sec) {
      c.sectors.push(...sec);
      const covers = /covers?\s+(.+?)\s*\)?$/i.exec(p);
      if (covers) lightNotes.push(`The ${colourWord(sec[0]!.colour)} sector covers ${covers[1]!.replace(/^the\s+/i, 'the ')}.`);
      continue;
    }
    if (/^(?:visible\s+)?(?:on|along)\s+(?:the\s+)?range\s+line(?:\s+only)?$|^visible\s+(?:only\s+)?(?:on|along)\s+(?:the\s+)?range\s+line$/i.test(p)) {
      lightNotes.push('It can be seen only along the range line.');
      continue;
    }
    if (/^light$/i.test(p)) continue;
    leftover += (leftover ? ', ' : '') + p;
  }
  return leftover || null;
}

/** Read one characteristic in notation (after `normaliseWords` / `prose`). */
function core(text: string, rec: Recorded, notes: string[], lightNotes: string[]): { c: Characteristic; leftover: string | null } | null {
  const original = text;
  let s = normaliseNotation(text, notes);
  const c: Characteristic = { raw: original, type: 'F', ...blank(), notes };

  const al = /^Al\b\s*/i.exec(s);
  if (al) {
    c.alternating = true;
    s = s.slice(al[0].length);
  }

  let type: LightType | null = null;
  const mo = /^Mo\s*\(\s*([A-Za-z0-9])\s*\)/.exec(s);
  if (mo) {
    type = 'Mo';
    c.morse = mo[1]!.toUpperCase();
    s = s.slice(mo[0].length);
  } else {
    for (const [re, t] of [...TYPE_BEFORE_GROUP, ...TYPES]) {
      const m = re.exec(s);
      if (m) {
        type = t;
        s = s.slice(m[0].length);
        break;
      }
    }
  }
  if (!type) {
    // "Al WR 10s": alternating colours with no type word.
    if (!c.alternating) return null;
    type = 'Fl';
    notes.push('The record does not say whether the light flashes or shows steadily between its colour changes. It is drawn as alternating flashes, as most US and Canadian alternating lights are rotating beacons.');
  }
  c.type = type;

  const g = /^\s*\(\s*(\d+(?:\s*\+\s*\d+)*)\s*\)/.exec(s);
  if (g) {
    const group = g[1]!.split('+').map((n) => Number(n.trim()));
    if (group.some((n) => !Number.isInteger(n) || n < 1 || n > 20)) return null;
    c.group = group.length === 1 && group[0] === 1 ? null : group;
    s = s.slice(g[0].length);
  }
  const tail = /^\s*\+\s*L\s*Fl\b/i.exec(s);
  if (tail) {
    if (!['Q', 'VQ', 'UQ'].includes(type) || !c.group || c.group.length !== 1) return null;
    c.tail = 'LFl';
    s = s.slice(tail[0].length);
  }
  if (/^\s*\+/.test(s)) return null; // another composite form: not covered

  // Colours: "W", "W R", "WR", "W/R", "WRG", "Bu"; one letter may be written in lower case.
  for (;;) {
    const m = /^\s*(?:[/,]|\band\b)?\s*((?:Bu|Or|[WRGY])+|[wrgy])(?![A-Za-z])(?!\s+sectors?\b)/.exec(s);
    if (!m) break;
    for (const code of m[1]!.match(/Bu|Or|[WRGYwrgy]/g) ?? []) {
      const k = COLOUR_CODE[code.toUpperCase()]!;
      if (!c.colours.includes(k)) c.colours.push(k);
    }
    s = s.slice(m[0].length);
  }

  const p = /^\s*,?\s*(\d+(?:\.\d+)?)\s*s(?![a-z])/i.exec(s) ?? /^\s*,?\s*(\d+(?:\.\d+)?)\s*(?=,|$)/.exec(s);
  if (p) {
    const period = Number(p[1]);
    if (!(period > 0 && period <= 120)) return null;
    if (!/s\s*$/i.test(p[0])) notes.push(`The record gives the period as “${p[1]}” with no unit; it is read as seconds.`);
    s = s.slice(p[0].length);
    if (type === 'F' && !c.alternating) {
      notes.push(`The record adds a period (${seconds(period)}), but a fixed light has none. It may be a fixed light varied by a flash; it is drawn as a steady light.`);
    } else c.period = period;
  }

  // Heights and ranges printed after the period ("30m 24M", "101ft").
  s = s.replace(/^(?:\s*\d+(?:\.\d+)?\s*(?:m|ft|M|NM|nm|nmi)(?![a-z]))+/, '').trim();
  let leftover: string | null = null;
  if (s) {
    // Anything after must be a clause (comma, "with", dash, parenthesis), else the record is not read.
    if (!/^(?:[,(-]|with\b|avec\b|light\b)/i.test(s)) return null;
    leftover = clauses(s.replace(/^light\b\s*/i, ''), c, lightNotes);
  }
  if (c.alternating && c.colours.length < 2) return null;
  if (rec.flash || rec.light || rec.dark || rec.perColour) c.recorded = { ...rec };
  return { c, leftover };
}

/** Parenthesised words after a characteristic: a date, an era, which light, a sector, durations. */
type Label =
  | { kind: 'year'; year: number; approx: boolean; asOf: boolean }
  | { kind: 'era'; word: string; order: number }
  | { kind: 'earlier'; text: string }
  | { kind: 'role'; role: string }
  | { kind: 'sector'; sectors: Sector[]; text: string }
  | { kind: 'durations'; perColour: number[]; colours: string[] }
  | { kind: 'note'; text: string };

const ERA_WORDS: Record<string, number> = {
  original: -1, originally: -1, initial: -1, initially: -1, first: -1, formerly: -1, former: -1, earlier: -1, old: -1,
  current: 1, currently: 1, now: 1, present: 1, today: 1, later: 1, modern: 1,
};

function label(text: string): Label {
  const t = text.trim();
  let m: RegExpExecArray | null;
  if ((m = /^(?:(c\.?|ca\.?|circa|about)\s*)?(1[6-9]\d\d|20\d\d)$/i.exec(t))) return { kind: 'year', year: Number(m[2]), approx: !!m[1], asOf: false };
  if ((m = /^as\s+of\s+(1[6-9]\d\d|20\d\d)$/i.exec(t))) return { kind: 'year', year: Number(m[1]), approx: false, asOf: true };
  if (Object.hasOwn(ERA_WORDS, t.toLowerCase())) return { kind: 'era', word: t.toLowerCase(), order: ERA_WORDS[t.toLowerCase()]! };
  if ((m = /^(?:initially|originally|formerly|at first)\s+(.+)$/i.exec(t))) return { kind: 'earlier', text: m[1]! };
  if (/^(front|rear|upper|lower)$/i.test(t)) return { kind: 'role', role: t.toLowerCase() };
  if (/^passing\s+light$/i.test(t)) return { kind: 'role', role: 'passing light' };
  if (/^(?:along\s+(?:the\s+)?)?range\s+line$/i.test(t)) return { kind: 'role', role: 'along the range line' };
  const words = normaliseWords(t);
  const sec = sectorClause(words);
  if (sec) return { kind: 'sector', sectors: sec, text: words };
  if (/^secteurs?$/i.test(t)) return { kind: 'note', text: '' };
  if ((m = new RegExp(String.raw`^(${C})\s+${NUM}s\s*,\s*(${C})\s+${NUM}s$`, 'i').exec(words))) {
    return { kind: 'durations', perColour: [Number(m[2]), Number(m[4])], colours: [COLOUR_CODE[m[1]!.toUpperCase()]!, COLOUR_CODE[m[3]!.toUpperCase()]!] };
  }
  return { kind: 'note', text: t };
}

/** Pull "(...)" labels out of a segment, leaving group and Morse brackets ("Fl(2)", "Mo(A)") in place. */
function extractLabels(seg: string): { text: string; labels: Label[] } {
  const labels: Label[] = [];
  const text = seg.replace(/\(([^()]*)\)/g, (whole, inner: string, offset: number) => {
    const before = seg.slice(0, offset);
    if (/^\s*\d{1,2}(?:\s*\+\s*\d{1,2})*\s*$/.test(inner)) return whole; // a group: "(2)", "(2+1)"
    if (/\bMo\s*$/i.test(before) && /^\s*[A-Za-z0-9]\s*$/.test(inner)) return whole; // Morse letter
    labels.push(label(inner));
    return ' ';
  });
  return { text: text.replace(/\s+/g, ' ').trim(), labels };
}

function readSegment(seg: string): { light: ReadLight | null; leftover: string | null; labels: Label[] } {
  const { text, labels } = extractLabels(seg);
  const notes: string[] = [];
  const lightNotes: string[] = [];
  const rec: Recorded = {};
  const words = normaliseWords(text.replace(/[\s,.;:]+$/, ''));
  if (!words) return { light: null, leftover: null, labels };
  const notation = prose(words, rec, notes) ?? words;
  const got = core(notation, rec, notes, lightNotes);
  if (!got) return { light: null, leftover: text || null, labels };
  got.c.raw = seg.trim().replace(/[\s,;]+$/, '');
  return { light: { c: got.c, role: null, era: null, notes: lightNotes }, leftover: got.leftover, labels };
}

function applyLabels(light: ReadLight, labels: Label[], extra: ReadLight[], leftovers: string[]): void {
  const c = light.c;
  for (const l of labels) {
    switch (l.kind) {
      case 'year':
        light.era = { label: l.asOf ? `as recorded in ${l.year}` : `${l.approx ? 'about ' : ''}${l.year}`, year: l.year, approx: l.approx, order: 0 };
        break;
      case 'era':
        light.era = { label: l.word, year: null, approx: false, order: l.order };
        break;
      case 'role':
        light.role = l.role;
        break;
      case 'sector':
        c.sectors.push(...l.sectors);
        if (/cover/i.test(l.text)) {
          const covers = /covers?\s+(.+)$/i.exec(l.text);
          if (covers) light.notes.push(`The ${colourWord(l.sectors[0]!.colour)} sector covers ${covers[1]}.`);
        }
        break;
      case 'durations':
        if (c.alternating && c.colours.join() === l.colours.join()) c.recorded = { ...(c.recorded ?? {}), perColour: l.perColour };
        else leftovers.push(l.colours.map((k, i) => `${k} ${l.perColour[i]}s`).join(', '));
        break;
      case 'earlier': {
        // "(initially F W)": a full earlier characteristic; "(originally W)": the same light in another colour.
        const r = readSegment(l.text);
        let earlier: Characteristic | null = r.light?.c ?? null;
        if (!earlier) {
          const cols = normaliseWords(l.text).match(/^((?:Bu|Or|[WRGY])+)$/);
          if (cols) earlier = { ...c, raw: `${c.raw.replace(/\s*\(.*$/, '')} (${l.text})`, colours: (cols[1]!.match(/Bu|Or|[WRGY]/g) ?? []).map((k) => COLOUR_CODE[k]!), sectors: [], notes: [] };
        }
        if (earlier) {
          if (!light.era) light.era = { label: 'later', year: null, approx: false, order: 1 };
          extra.push({ c: { ...earlier, raw: l.text }, role: light.role, era: { label: 'at first', year: null, approx: false, order: -1 }, notes: [] });
        } else leftovers.push(l.text);
        break;
      }
      case 'note':
        if (l.text) light.notes.push(l.text.replace(/^./, (ch) => ch.toUpperCase()).replace(/([^.])$/, '$1.'));
        break;
    }
  }
}

/** Notes that are whole parts of a record ("obscured from 158° to 318°", "emergency light..."). */
function noteFromPart(part: string, to: ReadLight): boolean {
  const { text, labels } = extractLabels(part);
  const sec = sectorClause(normaliseWords(text));
  if (sec) {
    to.c.sectors.push(...sec);
    for (const l of labels) if (l.kind === 'year' && !to.era) to.era = { label: l.asOf ? `as recorded in ${l.year}` : String(l.year), year: l.year, approx: l.approx, order: 0 };
    return true;
  }
  const t = part.trim();
  if (/^emergency light\b/i.test(t)) {
    to.notes.push(`${t.replace(/\s+/g, ' ').replace(/\s*\.\s*\)/g, ')').replace(/([^.])$/, '$1.')}`.replace(/^./, (ch) => ch.toUpperCase()));
    return true;
  }
  if (/^(illuminated|dark sectors?|visible|obscured|shown)\b/i.test(t)) {
    const date = labels.find((l) => l.kind === 'year');
    if (date && date.kind === 'year' && !to.era) to.era = { label: date.asOf ? `as recorded in ${date.year}` : String(date.year), year: date.year, approx: date.approx, order: 0 };
    to.notes.push(text.replace(/^./, (ch) => ch.toUpperCase()).replace(/([^.])$/, '$1.'));
    return true;
  }
  return false;
}

/** Undo artefacts seen in the records: "obscuR" and "Ruced" (a "red" -> "R" replacement upstream), "Flevery". */
function repair(raw: string): string {
  return raw
    .replace(/obscuR/g, 'obscured')
    .replace(/\bRuced\b/g, 'reduced')
    .replace(/Flevery/g, 'Fl every')
    .replace(/&nbsp;/gi, ' ');
}

/** Read a record's characteristic text into one or more lights. */
export function readLight(raw: string | null | undefined): LightReading {
  const text = typeof raw === 'string' ? raw.trim() : '';
  const out: LightReading = { raw: text, lights: [], leftovers: [] };
  if (!text || text.length > 300) return out;
  const parts = repair(text).split(/<br\s*\/?>|;/i).map((p) => p.trim()).filter(Boolean);
  for (const part of parts) {
    const r = readSegment(part);
    if (r.light) {
      const extra: ReadLight[] = [];
      applyLabels(r.light, r.labels, extra, out.leftovers);
      out.lights.push(r.light, ...extra);
      if (r.leftover) {
        if (!noteFromPart(r.leftover, r.light)) out.leftovers.push(r.leftover);
      }
    } else {
      const last = out.lights.at(-1);
      if (!(last && noteFromPart(part, last))) out.leftovers.push(part);
    }
  }
  // A light whose only words are notes and no pattern is not a reading.
  return out;
}

/**
 * Read one characteristic written in a single form; null when it is empty, in a form this does
 * not cover, or several lights (use `readLight` for those).
 */
export function parseCharacteristic(raw: string | null | undefined): Characteristic | null {
  const r = readLight(raw);
  return r.lights.length === 1 && !r.leftovers.length ? r.lights[0]!.c : null;
}

const NUMBER_WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
function count(n: number): string {
  return NUMBER_WORDS[n] ?? String(n);
}
function seconds(p: number): string {
  const v = Number.isInteger(p) ? String(p) : String(Number(p.toFixed(2)));
  return `${v} ${p === 1 ? 'second' : 'seconds'}`;
}
function capitalise(s: string): string {
  return s ? s[0]!.toUpperCase() + s.slice(1) : s;
}

const MORSE: Record<string, string> = {
  A: '.-', B: '-...', C: '-.-.', D: '-..', E: '.', F: '..-.', G: '--.', H: '....', I: '..', J: '.---',
  K: '-.-', L: '.-..', M: '--', N: '-.', O: '---', P: '.--.', Q: '--.-', R: '.-.', S: '...', T: '-',
  U: '..-', V: '...-', W: '.--', X: '-..-', Y: '-.--', Z: '--..',
  '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
};

/** ".-" for Morse A; null for a letter not in the table. */
export function morseCode(letter: string): string | null {
  return MORSE[letter.toUpperCase()] ?? null;
}

/** "short, long" for Morse A. */
export function morseWords(letter: string): string | null {
  const code = morseCode(letter);
  return code ? [...code].map((ch) => (ch === '.' ? 'short' : 'long')).join(', ') : null;
}

function list(names: string[], joiner: 'and' | 'or'): string {
  if (names.length <= 1) return names[0] ?? '';
  return names.length === 2 ? `${names[0]} ${joiner} ${names[1]}` : `${names.slice(0, -1).join(', ')} ${joiner} ${names.at(-1)}`;
}

/** The colours a visitor may see, depending on direction: the colour letters plus any coloured sectors. */
export function sectorColours(c: Characteristic): string[] {
  if (c.alternating) return [];
  const out = [...c.colours];
  for (const s of c.sectors) if (s.colour !== 'dark' && !out.includes(s.colour)) out.push(s.colour);
  return out.length > 1 ? out : [];
}

/**
 * The colour words: "white"; "alternating white and red"; with sectors, the colours and a note
 * returned separately ("white or red", sectors = true).
 */
function colourPhrase(c: Characteristic): { words: string; sectors: boolean } {
  const names = c.colours.map(colourWord);
  if (names.length === 0) return { words: '', sectors: false };
  if (names.length === 1) return { words: names[0]!, sectors: false };
  if (c.alternating) return { words: list(names, 'and'), sectors: false };
  return { words: list(names, 'or'), sectors: true };
}

/** "two white flashes", "three quick red flashes", "white flashes in a group of two then one". */
function groupWords(group: number[], adjective: string, noun: string, colour: string): string {
  const desc = [adjective, colour].filter(Boolean).join(' ');
  if (group.length === 1) {
    const n = group[0]!;
    return `${count(n)} ${desc ? `${desc} ` : ''}${n === 1 ? noun : `${noun}es`}`;
  }
  return `${desc ? `${desc} ` : ''}${noun}es in a group of ${group.map(count).join(' then ')}`;
}

function bearing(n: number): string {
  return `${String(n).padStart(3, '0')}°`;
}

function sectorWords(c: Characteristic): string {
  const coloured = c.sectors.filter((s) => s.colour !== 'dark');
  const dark = c.sectors.filter((s) => s.colour === 'dark');
  let text = '';
  if (coloured.length) {
    const parts = coloured.map((s) =>
      s.from !== null && s.to !== null
        ? `${colourWord(s.colour)} from ${bearing(s.from)} to ${bearing(s.to)}`
        : s.count === 0 ? `${colourWord(s.colour)} sectors` : s.count && s.count > 1 ? `${count(s.count)} ${colourWord(s.colour)} sectors` : `a ${colourWord(s.colour)} sector`,
    );
    const names = [...new Set(coloured.map((s) => colourWord(s.colour)))];
    text += coloured.some((s) => s.from !== null)
      ? `. It shows ${parts.join(' and ')} (bearings from seaward)`
      : `. It has ${parts.join(' and ')}: from some directions it shows ${list(names, 'or')} instead`;
  }
  if (dark.length) {
    const d = dark.filter((s) => s.from !== null && s.to !== null);
    text += d.length
      ? `. It cannot be seen from ${d.map((s) => `${bearing(s.from!)} to ${bearing(s.to!)}`).join(' or ')} (bearings from seaward)`
      : '. From some directions it cannot be seen (a dark sector)';
  }
  return text;
}

/** Plain words for a parsed characteristic: "One white flash every 4 seconds". */
export function describeCharacteristic(c: Characteristic): string {
  const { words: col, sectors } = colourPhrase(c);
  const alt = c.alternating;
  // Alternating colours are said once, at the end ("alternating white and red").
  const colour = alt || sectors ? '' : col;
  const lead = colour ? `${colour} ` : '';
  const every = c.period ? ` every ${seconds(c.period)}` : '';
  const repeated = c.period ? `, repeated every ${seconds(c.period)}` : '';
  const cycle = c.period ? `, the pattern repeating every ${seconds(c.period)}` : '';
  let text: string;
  switch (c.type) {
    case 'F':
      text = alt ? `A steady light that changes colour, ${col} in turn${cycle}` : `A steady ${lead}light`;
      break;
    case 'FFl':
      text = c.group
        ? `A steady ${lead}light with ${groupWords(c.group, 'brighter', 'flash', '')}${repeated}`
        : `A steady ${lead}light with a brighter flash${every}`;
      break;
    case 'Fl':
      if (alt) text = `${c.group ? `${capitalise(groupWords(c.group, '', 'flash', ''))},` : 'Flashes'} alternating ${col}${cycle}`;
      else if (c.group) text = `${capitalise(groupWords(c.group, '', 'flash', colour))}${repeated}`;
      else text = c.period ? `One ${lead}flash${every}` : `A flashing ${lead}light (how often is not recorded)`;
      break;
    case 'LFl':
      text = c.group
        ? `${capitalise(groupWords(c.group, 'long', 'flash', colour))}${repeated}`
        : c.period ? `One long ${lead}flash${every}` : `A long-flashing ${lead}light`;
      text += ' (a long flash lasts 2 seconds or more)';
      break;
    case 'Oc': {
      const n = c.group?.length === 1 ? c.group[0]! : 1;
      const times = c.group && c.group.length > 1 ? `in groups of ${c.group.map(count).join(' then ')}` : n === 1 ? 'once' : n === 2 ? 'twice' : `${count(n)} times`;
      text = c.period
        ? `A steady ${lead}light that goes dark ${times}${every}; it is on for longer than it is off`
        : `A steady ${lead}light that goes dark ${n > 1 || (c.group && c.group.length > 1) ? `${times} ` : ''}at intervals (how often is not recorded); it is on for longer than it is off`;
      break;
    }
    case 'Iso':
      text = c.period
        ? `${capitalise(lead)}${lead ? 'light' : 'Light'} and darkness of equal length: ${seconds(c.period / 2)} on, ${seconds(c.period / 2)} off`
        : `${capitalise(lead)}${lead ? 'light' : 'Light'} and darkness of equal length`;
      break;
    case 'Q':
    case 'VQ':
    case 'UQ': {
      const speed = c.type === 'Q' ? 'quick' : c.type === 'VQ' ? 'very quick' : 'ultra-quick';
      const rate = c.type === 'Q' ? 'about 60 a minute' : c.type === 'VQ' ? 'about 120 a minute' : '160 or more a minute';
      if (c.group && c.tail) text = `${capitalise(groupWords(c.group, speed, 'flash', colour))} followed by a long flash${repeated}`;
      else if (c.group) text = `${capitalise(groupWords(c.group, speed, 'flash', colour))}${repeated}`;
      else text = `${capitalise(speed)} ${lead}flashes, ${rate}, without a pause`;
      break;
    }
    case 'IQ':
    case 'IVQ':
    case 'IUQ':
      text = `${capitalise(c.type === 'IQ' ? 'quick' : c.type === 'IVQ' ? 'very quick' : 'ultra-quick')} ${lead}flashes broken by a dark pause${repeated}`;
      break;
    case 'Mo': {
      const m = c.morse ? morseWords(c.morse) : null;
      text = `${capitalise(`${lead}flashes`)} spelling the letter ${c.morse} in Morse code${m ? ` (${m})` : ''}${every}`;
      break;
    }
  }
  if (alt && c.type !== 'F' && c.type !== 'Fl') text += `, alternating ${col}`;
  if (sectors) text += `. It shows ${col} depending on the direction you see it from (coloured sectors)`;
  if (c.sectors.length) text += sectorWords(c);
  const r = c.recorded;
  const asides: string[] = [];
  if (r?.light !== undefined && r.dark !== undefined) asides.push(`${seconds(r.light)} on, ${seconds(r.dark)} off, as recorded`);
  else if (r?.flash !== undefined) asides.push(`each flash ${seconds(r.flash)}, as recorded`);
  if (r?.perColour && c.colours.length === r.perColour.length) asides.push(`${c.colours.map((k, i) => `${colourWord(k)} ${seconds(r.perColour![i]!)}`).join(', ')}, as recorded`);
  if (!c.colours.length) asides.push('its colour is not recorded');
  if (asides.length) text += ` (${asides.join('; ')})`;
  return text;
}

function lightLead(l: ReadLight): string {
  const who = l.role ? capitalise(l.role) : '';
  const when = l.era ? (/^\d{4}$/.test(l.era.label) ? `In ${l.era.label}` : capitalise(l.era.label)) : '';
  return [who, when].filter(Boolean).join(', ');
}

/** Plain words for a whole record: one light, or each light with its role or date. */
export function describeReading(r: LightReading): string | null {
  if (!r.lights.length) return null;
  if (r.lights.length === 1 && !r.lights[0]!.role && !r.lights[0]!.era) {
    const l = r.lights[0]!;
    return [describeCharacteristic(l.c), ...l.notes].join('. ').replace(/\.\./g, '.');
  }
  return r.lights
    .map((l) => {
      const lead = lightLead(l);
      const words = describeCharacteristic(l.c);
      const body = lead ? `${lead}: ${words.charAt(0).toLowerCase()}${words.slice(1)}` : words;
      return [body, ...l.notes].join('. ');
    })
    .join('. ')
    .replace(/\.\./g, '.');
}

/** Plain words for a characteristic string, or null when it is not in a covered form. */
export function readCharacteristic(raw: string | null | undefined): string | null {
  const c = parseCharacteristic(raw);
  return c ? describeCharacteristic(c) : null;
}
