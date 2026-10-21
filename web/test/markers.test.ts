import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { GLYPHS, GLYPH_ORDER, MARKER_PALETTE, SILHOUETTES, glyphFor, iconName, markerParts, markerSvg, silhouetteFor, tokenFor, type PaintKey } from '../src/lib/icons.ts';
import { KEY_STATUS, mapKey } from '../src/render/site.ts';
import { KIND_ORDER, STATUS_ORDER } from '../src/lib/vocab.ts';
import { ICON_EXPR, SORT_EXPR } from '../src/map/layers.ts';

const baseCss = readFileSync(resolve(import.meta.dirname, '../src/styles/base.css'), 'utf8');

/** Just enough of MapLibre's expression language to evaluate the map layer's icon and sort expressions. */
type Expr = unknown;
function evaluate(e: Expr, props: Record<string, unknown>): unknown {
  if (!Array.isArray(e)) return e;
  const [op, ...args] = e as [string, ...Expr[]];
  if (op === 'get') return props[args[0] as string];
  if (op === 'concat') return args.map((a) => evaluate(a, props)).join('');
  if (op === 'match') {
    const input = evaluate(args[0], props);
    for (let i = 1; i + 1 < args.length; i += 2) {
      const label = args[i];
      if (Array.isArray(label) ? label.includes(input) : label === input) return evaluate(args[i + 1], props);
    }
    return evaluate(args.at(-1), props);
  }
  throw new Error(`unsupported operator ${op}`);
}

/** The --mk-* tokens in base.css as [light, dark]. */
function tokens(): Map<string, [string, string]> {
  const out = new Map<string, [string, string]>();
  for (const m of baseCss.matchAll(/(--mk-[a-z-]+):\s*light-dark\((#[0-9a-f]{6}),\s*(#[0-9a-f]{6})\)/g)) out.set(m[1]!, [m[2]!, m[3]!]);
  return out;
}

describe('marker palette', () => {
  it('matches the --mk-* tokens in base.css, light and dark', () => {
    const t = tokens();
    for (const key of Object.keys(MARKER_PALETTE.light) as PaintKey[]) {
      const token = tokenFor(key);
      expect(t.get(token), token).toBeDefined();
      expect(MARKER_PALETTE.light[key], `${token} light`).toBe(t.get(token)![0]);
      expect(MARKER_PALETTE.dark[key], `${token} dark`).toBe(t.get(token)![1]);
    }
  });

  it('paints inline markers with the tokens, so they follow the theme', () => {
    const svg = markerSvg('active', 'lighthouse');
    const used = new Set([...svg.matchAll(/var\((--mk-[a-z-]+)\)/g)].map((m) => m[1]!));
    expect(used.size).toBeGreaterThan(1);
    for (const u of used) expect(tokens().has(u), u).toBe(true);
    expect(svg).toContain('aria-hidden="true"');
  });
});

describe('status by shape', () => {
  /** A marker's geometry, without colour: what is left in greyscale. */
  const shape = (status: string, kind = 'lighthouse') =>
    JSON.stringify(markerParts(glyphFor(status), silhouetteFor(kind)).map((p) => (p.type === 'path' ? [p.d, p.dash ?? null, p.dx ?? 0, p.dy ?? 0] : [p.cx, p.cy, p.r, p.dash ?? null])));

  it('draws every status with a different shape', () => {
    for (const kind of ['lighthouse', 'lightship', 'life_saving_station']) {
      const shapes = STATUS_ORDER.map((s) => shape(s, kind));
      // a life-saving station never had a light: "in service" is the house itself, in amber
      if (kind === 'life_saving_station') expect(new Set(shapes).size).toBe(STATUS_ORDER.length - 1);
      else expect(new Set(shapes).size, kind).toBe(STATUS_ORDER.length);
    }
  });

  it('draws lost lights as a dashed ring with a cross, unlike any standing marker', () => {
    const lost = markerParts('ghost', 'tower');
    expect(lost.some((p) => p.type === 'circle' && p.dash)).toBe(true);
    for (const g of GLYPHS.filter((x) => x !== 'ghost')) expect(markerParts(g, 'tower').some((p) => p.dash), g).toBe(false);
  });

  it('draws lost lights under standing ones, and active lights on top', () => {
    const order = Object.entries(GLYPH_ORDER).sort((a, b) => a[1] - b[1]).map(([g]) => g);
    expect(order[0]).toBe('ghost');
    expect(order.at(-1)).toBe('lit');
    // the map layer sorts by the same numbers
    for (const s of STATUS_ORDER) expect(evaluate(SORT_EXPR, { s }), s).toBe(GLYPH_ORDER[glyphFor(s)]);
  });

  it('has a map image for every glyph and silhouette, named as the map layer asks for them', () => {
    const names = GLYPHS.flatMap((g) => SILHOUETTES.map((s) => iconName(g, s)));
    expect(new Set(names).size).toBe(GLYPHS.length * SILHOUETTES.length);
    expect(names).toContain('fr-ghost-ship');
    // the map layer picks the same image the key and the pages draw
    for (const s of STATUS_ORDER) for (const k of KIND_ORDER) expect(evaluate(ICON_EXPR, { s, k }), `${s} ${k}`).toBe(iconName(glyphFor(s), silhouetteFor(k)));
    expect(evaluate(ICON_EXPR, { s: 'something-new', k: 'something-new' })).toBe('fr-unknown-tower');
  });

  it('draws an unknown new status as the question mark', () => {
    expect(glyphFor('something-new')).toBe('unknown');
    expect(silhouetteFor('something-new')).toBe('tower');
  });
});

describe('the map key', () => {
  it('explains every status, in the filters\' order, with its own shape', () => {
    expect(KEY_STATUS.map((k) => k.status)).toEqual(STATUS_ORDER);
    for (const k of KEY_STATUS) expect(k.glyph).toBe(glyphFor(k.status));
    const key = mapKey().value;
    for (const k of KEY_STATUS) expect(key).toContain(`<strong>${k.label}.</strong>`);
    expect(key).toContain('Drawn under the others');
  });

  it('explains the silhouettes', () => {
    const key = mapKey().value;
    for (const t of ['A tower', 'A ship', 'A house']) expect(key).toContain(t);
  });
});
