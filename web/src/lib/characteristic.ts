/**
 * Light characteristics: the abbreviation a chart or the Light List prints for a light's
 * pattern ("Fl W 4s", "Fl(2) R 10s", "Oc W 4s", "Iso G 6s", "Q R", "Mo(A) W 8s",
 * "Al Fl W R 30s", "F W"), read into a structure and into plain words: "Fl W 4s" -> "One white
 * flash every 4 seconds".
 *
 * Covers the common Light List / IALA forms: F, Fl, LFl, Oc, Iso, Q, VQ, UQ, IQ, IVQ, Mo(X),
 * F Fl, with groups "(2)" and "(2+1)", the old "Gp" prefix, "Al" for alternating colours,
 * colours W R G Y Bu Or (several letters without "Al" mean sectors), and a period in seconds.
 * Dots and spacing vary between sources ("Fl.W.4s", "Fl (2) W 20s"); a height or range printed
 * after the period ("30m 24M") is ignored. Anything else (composite forms such as
 * "Q(6)+LFl W 15s") is left unread: `parseCharacteristic` returns null and the page shows the
 * raw string as given. The later "light at night" view draws from the same structure.
 */

export type LightType = 'F' | 'FFl' | 'Fl' | 'LFl' | 'Oc' | 'Iso' | 'Q' | 'VQ' | 'UQ' | 'IQ' | 'IVQ' | 'Mo';

export interface Characteristic {
  raw: string;
  type: LightType;
  /** Flashes or eclipses per group: [2] for "(2)", [2, 1] for "(2+1)"; null for single. */
  group: number[] | null;
  /** The Morse letter of a Mo(X) light. */
  morse: string | null;
  /** "W", "R", "G", "Y", "Bu", "Or", in the order given. */
  colours: string[];
  /** "Al": the colours alternate. Several colours without it are sectors. */
  alternating: boolean;
  /** Seconds for one full cycle; null when not given. */
  period: number | null;
}

const COLOUR_WORDS: Record<string, string> = { W: 'white', R: 'red', G: 'green', Y: 'yellow', BU: 'blue', OR: 'orange' };
const COLOUR_CODE: Record<string, string> = { W: 'W', R: 'R', G: 'G', Y: 'Y', BU: 'Bu', OR: 'Or' };

const TYPES: [RegExp, LightType][] = [
  [/^F\s*Fl\b/i, 'FFl'],
  [/^(?:Gp\s*)?L\s*Fl\b/i, 'LFl'],
  [/^(?:Gp\s*)?Fl\b/i, 'Fl'],
  [/^(?:Gp\s*)?Occ?\b/i, 'Oc'],
  [/^Iso\b/i, 'Iso'],
  [/^IVQ\b/i, 'IVQ'],
  [/^IQ\b/i, 'IQ'],
  [/^UQ\b/i, 'UQ'],
  [/^VQ\b/i, 'VQ'],
  [/^Q\b/i, 'Q'],
  [/^F\b/i, 'F'],
];

// \b does not work after ")" or before "(", so the group and Morse forms are matched on their own.
const TYPE_BEFORE_GROUP: [RegExp, LightType][] = [
  [/^(?:Gp\s*)?L\s*Fl(?=\s*\()/i, 'LFl'],
  [/^(?:Gp\s*)?Fl(?=\s*\()/i, 'Fl'],
  [/^(?:Gp\s*)?Occ?(?=\s*\()/i, 'Oc'],
  [/^IVQ(?=\s*\()/i, 'IVQ'],
  [/^IQ(?=\s*\()/i, 'IQ'],
  [/^VQ(?=\s*\()/i, 'VQ'],
  [/^Q(?=\s*\()/i, 'Q'],
];

/** Read a characteristic; null when it is empty or in a form this does not cover. */
export function parseCharacteristic(raw: string | null | undefined): Characteristic | null {
  if (typeof raw !== 'string') return null;
  const original = raw.trim();
  if (!original || original.length > 80) return null;
  // "Fl.W.4s" -> "Fl W 4s"; keep the decimal point of a period ("2.5s").
  let s = original.replace(/(\d)\.(\d)/g, '$1\u0000$2').replace(/\./g, ' ').replace(/\u0000/g, '.').replace(/\s+/g, ' ').trim();

  let alternating = false;
  const al = /^Alt?\b\s*/i.exec(s);
  if (al) {
    alternating = true;
    s = s.slice(al[0].length);
  }

  let type: LightType | null = null;
  let morse: string | null = null;
  const mo = /^Mo\s*\(\s*([A-Za-z0-9])\s*\)/.exec(s);
  if (mo) {
    type = 'Mo';
    morse = mo[1]!.toUpperCase();
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
    // "Al W R": alternating with no type word is a fixed light that changes colour.
    if (alternating) type = 'F';
    else return null;
  }

  let group: number[] | null = null;
  const g = /^\s*\(\s*(\d+(?:\s*\+\s*\d+)*)\s*\)/.exec(s);
  if (g) {
    group = g[1]!.split('+').map((n) => Number(n.trim()));
    if (group.some((n) => !Number.isInteger(n) || n < 1 || n > 20)) return null;
    if (group.length === 1 && group[0] === 1) group = null;
    s = s.slice(g[0].length);
  }
  if (/^\s*\+/.test(s)) return null; // a composite such as Q(6)+LFl: not covered

  // Colours: "W", "W R", "WR", "W/R", "WRG", "Bu"; one letter may be written in lower case.
  const colours: string[] = [];
  for (;;) {
    const c = /^\s*[/,]?\s*((?:Bu|Or|[WRGY])+|[wrgy])(?![A-Za-z])/.exec(s);
    if (!c) break;
    for (const code of c[1]!.match(/Bu|Or|[WRGYwrgy]/g) ?? []) {
      const k = COLOUR_CODE[code.toUpperCase()]!;
      if (!colours.includes(k)) colours.push(k);
    }
    s = s.slice(c[0].length);
  }

  let period: number | null = null;
  const p = /^\s*(\d+(?:\.\d+)?)\s*(?:s|secs?|seconds?)(?![a-z])/i.exec(s);
  if (p) {
    period = Number(p[1]);
    if (!(period > 0 && period <= 120)) return null;
    s = s.slice(p[0].length);
  }

  // Heights and ranges printed after the period ("30m 24M", "101ft"), or a parenthesised note.
  const rest = s.replace(/\s*\d+(?:\.\d+)?\s*(?:m|ft|M|NM|nm|nmi)(?![a-z])/g, '').replace(/\s*\([^)]*\)/g, '').trim();
  if (rest) return null;
  if (alternating && colours.length < 2) return null;

  return { raw: original, type, group, morse, colours, alternating, period };
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
};

/** "short, long" for Morse A. */
export function morseWords(letter: string): string | null {
  const code = MORSE[letter.toUpperCase()];
  return code ? [...code].map((c) => (c === '.' ? 'short' : 'long')).join(', ') : null;
}

/**
 * The colour words: "white"; "alternating white and red"; with sectors, the colours and a note
 * returned separately ("white or red", sectors = true).
 */
function colourPhrase(c: Characteristic): { words: string; sectors: boolean } {
  const names = c.colours.map((k) => COLOUR_WORDS[k.toUpperCase()] ?? k);
  if (names.length === 0) return { words: '', sectors: false };
  if (names.length === 1) return { words: names[0]!, sectors: false };
  const list = names.length === 2 ? `${names[0]} and ${names[1]}` : `${names.slice(0, -1).join(', ')} and ${names.at(-1)}`;
  if (c.alternating) return { words: list, sectors: false };
  const or = names.length === 2 ? `${names[0]} or ${names[1]}` : `${names.slice(0, -1).join(', ')} or ${names.at(-1)}`;
  return { words: or, sectors: true };
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
      text = `A steady ${lead}light with a brighter flash${every}`;
      break;
    case 'Fl':
      if (alt) text = `${c.group ? capitalise(groupWords(c.group, '', 'flash', '')) : 'Flashes'} alternating ${col}${cycle}`;
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
      text = `A steady ${lead}light that goes dark ${times}${every}; it is on for longer than it is off`;
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
      text = c.group
        ? `${capitalise(groupWords(c.group, speed, 'flash', colour))}${repeated}`
        : `${capitalise(speed)} ${lead}flashes, ${rate}, without a pause`;
      break;
    }
    case 'IQ':
    case 'IVQ':
      text = `${capitalise(c.type === 'IQ' ? 'quick' : 'very quick')} ${lead}flashes broken by a dark pause${repeated}`;
      break;
    case 'Mo': {
      const m = c.morse ? morseWords(c.morse) : null;
      text = `${capitalise(`${lead}flashes`)} spelling the letter ${c.morse} in Morse code${m ? ` (${m})` : ''}${every}`;
      break;
    }
  }
  if (alt && c.type !== 'F' && c.type !== 'Fl') text += `, alternating ${col}`;
  if (sectors) text += `. It shows ${col} depending on the direction you see it from (coloured sectors)`;
  return text;
}

/** Plain words for a characteristic string, or null when it is not in a covered form. */
export function readCharacteristic(raw: string | null | undefined): string | null {
  const c = parseCharacteristic(raw);
  return c ? describeCharacteristic(c) : null;
}
