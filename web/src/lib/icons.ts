/**
 * Marker design. A marker's SHAPE says the station's status, so the map reads the same in
 * greyscale, in print and for colour-blind visitors; colour only repeats it.
 *
 *   status      glyph     shape                                             colour
 *   active      lit       a lit lamp: a sunburst with a bright core          lamp amber
 *   inactive    dark      the station standing, unlit: a solid silhouette    deep navy (pale in dark mode)
 *   ruins       broken    the silhouette broken off: a jagged stump          rust brown
 *   lost        ghost     a dashed hollow ring with a cross, drawn UNDER     grey
 *                         every standing marker
 *   relocated   moved     the silhouette with an arrow badge                 teal
 *   replica     copy      a hollow silhouette over its own offset outline    violet
 *   unknown     unknown   a ring with a question mark                        slate
 *
 * The silhouette says what stood there: a light tower (lighthouses, range, pier and harbor
 * lights), a ship (lightships and lightship stations) or a house with a lookout (life-saving
 * stations). The lamp, the ghost and the question mark are the same for every kind. A
 * life-saving station never had a light, so an active one ("in service") is an amber house
 * without the sunburst.
 *
 * One list of drawing parts per glyph and silhouette draws both the map markers (canvas, in the
 * browser) and the inline SVGs in the key, the filters, the badges and the pages. The SVGs paint
 * each part with a --mk-* token (base.css) so they follow the theme, with the light palette as
 * the fallback attribute; the canvas uses MARKER_PALETTE. test/markers.test.ts keeps the two
 * palettes equal.
 */

export type Glyph = 'lit' | 'dark' | 'broken' | 'ghost' | 'moved' | 'copy' | 'unknown';
export type Silhouette = 'tower' | 'ship' | 'house';
export type MarkerTheme = 'light' | 'dark';

export const GLYPHS: readonly Glyph[] = ['lit', 'dark', 'broken', 'ghost', 'moved', 'copy', 'unknown'];
export const SILHOUETTES: readonly Silhouette[] = ['tower', 'ship', 'house'];

const STATUS_GLYPH: Record<string, Glyph> = {
  active: 'lit',
  inactive: 'dark',
  ruins: 'broken',
  lost: 'ghost',
  relocated: 'moved',
  replica: 'copy',
  unknown: 'unknown',
};

/** The glyph a status draws; a status added to the data later draws the question mark. */
export function glyphFor(status: string): Glyph {
  return STATUS_GLYPH[status] ?? 'unknown';
}

export function silhouetteFor(kind: string): Silhouette {
  if (kind === 'lightship' || kind === 'lightship_station') return 'ship';
  if (kind === 'life_saving_station') return 'house';
  return 'tower';
}

/** The map image name of a glyph and silhouette ("fr-lit-tower"). Every pair has an image. */
export function iconName(glyph: Glyph, silhouette: Silhouette): string {
  return `fr-${glyph}-${silhouette}`;
}

/** Drawing order: lost lights under everything, active lights on top. */
export const GLYPH_ORDER: Record<Glyph, number> = { ghost: 0, unknown: 1, broken: 2, copy: 3, moved: 4, dark: 5, lit: 6 };

/* ---------- Palette ---------- */

export interface MarkerPalette {
  halo: string;
  lit: string;
  litEdge: string;
  litCore: string;
  dark: string;
  darkEdge: string;
  ruin: string;
  ruinEdge: string;
  ghost: string;
  moved: string;
  movedEdge: string;
  movedInk: string;
  copy: string;
  unknown: string;
}
export type PaintKey = keyof MarkerPalette;

/** Keep in step with the --mk-* tokens in src/styles/base.css (test/markers.test.ts checks). */
export const MARKER_PALETTE: Record<MarkerTheme, MarkerPalette> = {
  light: {
    halo: '#ffffff',
    lit: '#f2a900',
    litEdge: '#6b4300',
    litCore: '#fff7d6',
    dark: '#17324f',
    darkEdge: '#06121f',
    ruin: '#9a6237',
    ruinEdge: '#3e230f',
    ghost: '#5d6975',
    moved: '#17808f',
    movedEdge: '#08363d',
    movedInk: '#ffffff',
    copy: '#7048a8',
    unknown: '#4d6072',
  },
  dark: {
    halo: '#091522',
    lit: '#ffc23d',
    litEdge: '#3a2500',
    litCore: '#fffbe8',
    dark: '#c9d8e8',
    darkEdge: '#f4f8fb',
    ruin: '#e0a679',
    ruinEdge: '#2a160a',
    ghost: '#a2b0be',
    moved: '#6fd0de',
    movedEdge: '#06343b',
    movedInk: '#e9fbfd',
    copy: '#c6a8f0',
    unknown: '#b5c3d1',
  },
};

/** "litEdge" -> "--mk-lit-edge". */
export function tokenFor(key: PaintKey): string {
  return `--mk-${key.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`)}`;
}

/* ---------- Geometry, in a 24 x 24 box ---------- */

const SHAPE: Record<Silhouette, string> = {
  // a tapered tower with gallery, lantern and roof, on a plinth
  tower: 'M12 2.2L14.4 4.4V6.4H15.6V7.9H14.9L17 19.6H18.4V21.6H5.6V19.6H7L9.1 7.9H8.4V6.4H9.6V4.4Z',
  // a hull with a deckhouse and a mast carrying the lantern
  ship: 'M2.4 14.6H8.6V12H11.2V6.4H10.1V3.2H13.9V6.4H12.8V12H15.4V14.6H21.6L19.2 20.4H4.8Z',
  // a house with the lookout on its ridge
  house: 'M3 11.4L10.4 5.2V3.4H13.6V5.2L21 11.4V20.6H3Z',
};

const BROKEN: Record<Silhouette, string> = {
  tower: 'M7 19.6L8.72 10L10.4 12.2L11.9 9.2L13.6 11.8L15.28 10L17 19.6H18.4V21.6H5.6V19.6Z',
  ship: 'M2.4 14.6H9.2L10.3 11.2L12.7 12.6L12.1 14.6H21.6L19.2 20.4H4.8Z',
  house: 'M3 20.6V12.6L6.2 14.8L8.6 11.4L11.6 14L14.2 11L17.4 14.2L21 12.2V20.6Z',
};

/** A sunburst: `rays` points between radius `outer` and `inner`, centred in the box. */
function sunburst(rays: number, outer: number, inner: number): string {
  const pts: string[] = [];
  for (let i = 0; i < rays * 2; i++) {
    const r = i % 2 === 0 ? outer : inner;
    const a = (Math.PI * i) / rays - Math.PI / 2;
    pts.push(`${(12 + r * Math.cos(a)).toFixed(2)} ${(12 + r * Math.sin(a)).toFixed(2)}`);
  }
  return `M${pts.join('L')}Z`;
}
const SUN = sunburst(12, 11.2, 6.9);
const CROSS = 'M8.7 8.7L15.3 15.3M15.3 8.7L8.7 15.3';
const QUESTION = 'M9.5 9.9A2.6 2.6 0 1 1 13.3 12.2C12.4 12.7 12 13.2 12 14.1V14.7';
const ARROW = 'M15.8 17.6H20.6M18.6 15.5L20.8 17.6L18.6 19.7';

type Paint = PaintKey | 'none';

export type Part =
  | { type: 'path'; d: string; fill?: Paint; stroke?: Paint; width?: number; dash?: number[]; round?: boolean; fillOpacity?: number; dx?: number; dy?: number }
  | { type: 'circle'; cx: number; cy: number; r: number; fill?: Paint; stroke?: Paint; width?: number; dash?: number[]; fillOpacity?: number };

const HALO_W = 3.4;

function silhouetteParts(d: string, fill: Paint, stroke: PaintKey, width: number, dx = 0, dy = 0): Part[] {
  return [
    { type: 'path', d, fill: 'none', stroke: 'halo', width: HALO_W + width, dx, dy },
    { type: 'path', d, fill, stroke, width, dx, dy },
  ];
}

/** What to draw for a glyph on a silhouette, back to front. */
export function markerParts(glyph: Glyph, sil: Silhouette): Part[] {
  switch (glyph) {
    case 'lit':
      if (sil === 'house') return silhouetteParts(SHAPE.house, 'lit', 'litEdge', 1.3);
      return [
        { type: 'path', d: SUN, fill: 'none', stroke: 'halo', width: 3 },
        { type: 'path', d: SUN, fill: 'lit', stroke: 'litEdge', width: 1.1 },
        { type: 'circle', cx: 12, cy: 12, r: 3.3, fill: 'litCore', stroke: 'litEdge', width: 0.9 },
      ];
    case 'dark':
      return silhouetteParts(SHAPE[sil], 'dark', 'darkEdge', 1.1);
    case 'broken':
      return silhouetteParts(BROKEN[sil], 'ruin', 'ruinEdge', 1.1);
    case 'ghost':
      return [
        { type: 'circle', cx: 12, cy: 12, r: 8.4, fill: 'halo', fillOpacity: 0.72, stroke: 'halo', width: 4.2 },
        { type: 'circle', cx: 12, cy: 12, r: 8.4, fill: 'none', stroke: 'ghost', width: 2.1, dash: [2.7, 2.05] },
        { type: 'path', d: CROSS, fill: 'none', stroke: 'halo', width: 4.2, round: true },
        { type: 'path', d: CROSS, fill: 'none', stroke: 'ghost', width: 2.1, round: true },
      ];
    case 'moved':
      return [
        ...silhouetteParts(SHAPE[sil], 'moved', 'movedEdge', 1.1, -1.6, 0),
        { type: 'circle', cx: 18.4, cy: 17.6, r: 5.3, fill: 'halo' },
        { type: 'circle', cx: 18.4, cy: 17.6, r: 4.3, fill: 'movedEdge' },
        { type: 'path', d: ARROW, fill: 'none', stroke: 'movedInk', width: 1.7, round: true },
      ];
    case 'copy':
      return [
        ...silhouetteParts(SHAPE[sil], 'halo', 'copy', 1.2, 1.7, -1.1),
        ...silhouetteParts(SHAPE[sil], 'halo', 'copy', 2, -1.1, 0.8),
      ];
    case 'unknown':
      return [
        { type: 'circle', cx: 12, cy: 12, r: 8.5, fill: 'halo', stroke: 'halo', width: 4.2 },
        { type: 'circle', cx: 12, cy: 12, r: 8.5, fill: 'none', stroke: 'unknown', width: 2 },
        { type: 'path', d: QUESTION, fill: 'none', stroke: 'unknown', width: 2.2, round: true },
        { type: 'circle', cx: 12, cy: 17.2, r: 1.3, fill: 'unknown' },
      ];
  }
}

/* ---------- SVG (key, filters, badges, pages) ---------- */

function paintAttr(attr: 'fill' | 'stroke', paint: Paint | undefined): string {
  if (!paint) return attr === 'fill' ? ' fill="none"' : '';
  if (paint === 'none') return ` ${attr}="none"`;
  return ` ${attr}="${MARKER_PALETTE.light[paint]}"`;
}

function partSvg(p: Part): string {
  const style: string[] = [];
  if (p.fill && p.fill !== 'none') style.push(`fill:var(${tokenFor(p.fill)})`);
  if (p.stroke && p.stroke !== 'none') style.push(`stroke:var(${tokenFor(p.stroke)})`);
  let a = paintAttr('fill', p.fill) + paintAttr('stroke', p.stroke);
  if (p.width) a += ` stroke-width="${p.width}"`;
  if (p.dash) a += ` stroke-dasharray="${p.dash.join(' ')}"`;
  if (p.fillOpacity !== undefined) a += ` fill-opacity="${p.fillOpacity}"`;
  if (p.type === 'path') {
    a += p.round ? ' stroke-linecap="round" stroke-linejoin="round"' : ' stroke-linejoin="round"';
    if (p.dx || p.dy) a += ` transform="translate(${p.dx ?? 0} ${p.dy ?? 0})"`;
    return `<path d="${p.d}"${a} style="${style.join(';')}"/>`;
  }
  return `<circle cx="${p.cx}" cy="${p.cy}" r="${p.r}"${a} style="${style.join(';')}"/>`;
}

/** Inline SVG markup for a station's marker. Decorative: always pair it with a text label. */
export function markerSvg(status: string, kind: string, opts: { size?: number; className?: string } = {}): string {
  return glyphSvg(glyphFor(status), silhouetteFor(kind), opts);
}

export function glyphSvg(glyph: Glyph, sil: Silhouette, opts: { size?: number; className?: string } = {}): string {
  const size = opts.size ?? 22;
  const cls = `mk mk-${glyph}${opts.className ? ` ${opts.className}` : ''}`;
  return `<svg class="${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${markerParts(glyph, sil).map(partSvg).join('')}</svg>`;
}

/* ---------- Canvas (map markers; browser only) ---------- */

/** Draw a marker into a canvas context scaled so the 24-unit box fills `px`. */
export function drawMarker(ctx: CanvasRenderingContext2D, glyph: Glyph, sil: Silhouette, px: number, theme: MarkerTheme = 'light'): void {
  const c = MARKER_PALETTE[theme];
  const s = px / 24;
  for (const p of markerParts(glyph, sil)) {
    ctx.save();
    ctx.scale(s, s);
    if (p.type === 'path' && (p.dx || p.dy)) ctx.translate(p.dx ?? 0, p.dy ?? 0);
    let shape: Path2D;
    if (p.type === 'path') {
      shape = new Path2D(p.d);
    } else {
      shape = new Path2D();
      shape.arc(p.cx, p.cy, p.r, 0, Math.PI * 2);
    }
    if (p.fill && p.fill !== 'none') {
      ctx.globalAlpha = p.fillOpacity ?? 1;
      ctx.fillStyle = c[p.fill];
      ctx.fill(shape);
      ctx.globalAlpha = 1;
    }
    if (p.stroke && p.stroke !== 'none' && p.width) {
      ctx.strokeStyle = c[p.stroke];
      ctx.lineWidth = p.width;
      ctx.lineJoin = 'round';
      ctx.lineCap = p.type === 'path' && p.round ? 'round' : 'butt';
      ctx.setLineDash(p.dash ?? []);
      ctx.stroke(shape);
    }
    ctx.restore();
  }
}
