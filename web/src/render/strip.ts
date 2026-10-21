/**
 * The strip diagram of a light's pattern: one period drawn to scale on a time line, lit spans in
 * the light's colour and dark spans in night blue, the way charts and light lists teach a
 * characteristic. Short periods repeat, paler, so the rhythm shows. Pure string rendering,
 * used by the prerendered page and redrawn in the browser when the visitor changes the light.
 */
import { colourWord } from '../lib/characteristic.ts';
import { html, raw, type SafeHtml } from '../lib/html.ts';
import { phaseWords, type Pattern } from '../lib/pattern.ts';

/** Physical light colours (not theme colours: a red light is red on any page). */
export const LIGHT_RGB: Record<string, string> = {
  W: '#fff4d6',
  R: '#ff4a3d',
  G: '#3ee07a',
  Y: '#ffd43b',
  Bu: '#5a9bff',
  Or: '#ff9a2e',
};
export const NIGHT = '#0b1622';

const VIEW_W = 600;
const BAR_X = 8;
const BAR_W = VIEW_W - 16;

function fmt(n: number): string {
  return String(Number(n.toFixed(2)));
}

function tickStep(span: number): number {
  if (span <= 3) return 0.5;
  if (span <= 12) return 1;
  if (span <= 30) return 2;
  if (span <= 60) return 5;
  return 10;
}

let uid = 0;

/** One strip. `label` names it when there are several ("In the red sector"). */
export function stripSvg(p: Pattern, opts: { label?: string; id?: string } = {}): SafeHtml {
  const id = opts.id ?? `strip-${++uid}`;
  const repeats = p.steady || !p.periodRecorded ? 1 : Math.min(6, Math.max(1, Math.ceil(6 / p.period)));
  const span = p.period * repeats;
  const x = (t: number) => BAR_X + (t / span) * BAR_W;
  const barY = 10;
  const barH = 30;
  const rects: string[] = [];
  for (let k = 0; k < repeats; k++) {
    for (const ph of p.phases) {
      const x0 = x(ph.start + k * p.period);
      const w = Math.max(0.8, x(ph.start + ph.dur + k * p.period) - x0);
      const fill = ph.colour ? LIGHT_RGB[ph.colour] ?? LIGHT_RGB.W! : NIGHT;
      const h = ph.colour && ph.level < 1 ? barH * 0.55 : barH;
      if (ph.colour && ph.level < 1) rects.push(`<rect x="${fmt(x0)}" y="${barY}" width="${fmt(w)}" height="${barH}" fill="${NIGHT}"/>`);
      rects.push(`<rect x="${fmt(x0)}" y="${fmt(barY + (barH - h))}" width="${fmt(w)}" height="${fmt(h)}" fill="${fill}"${k ? ' opacity="0.5"' : ''}/>`);
    }
  }
  const ticks: string[] = [];
  if (p.periodRecorded && !p.steady) {
    const step = tickStep(span);
    for (let t = 0; t <= span + 1e-6; t += step) {
      const tx = fmt(x(t));
      const major = Math.abs(t / p.period - Math.round(t / p.period)) < 1e-6;
      ticks.push(`<line x1="${tx}" x2="${tx}" y1="${barY + barH}" y2="${barY + barH + (major ? 7 : 4)}" stroke="currentColor" stroke-width="${major ? 1.4 : 1}"/>`);
    }
    const labels = [0, p.period, ...(repeats > 1 ? [span] : [])];
    for (const t of labels) {
      const anchor = t === 0 ? 'start' : t === span ? 'end' : 'middle';
      ticks.push(`<text x="${fmt(x(t))}" y="${barY + barH + 20}" text-anchor="${anchor}" font-size="12" fill="currentColor">${fmt(t)} s</text>`);
    }
  }
  const periodMark = p.periodRecorded && !p.steady && repeats > 1
    ? `<line x1="${fmt(x(p.period))}" x2="${fmt(x(p.period))}" y1="${barY - 5}" y2="${barY + barH + 7}" stroke="currentColor" stroke-width="1.6"/>`
    : '';
  const words = phaseWords(p);
  const title = p.steady ? 'Lit all the time, no rhythm.' : `${repeats > 1 ? `${repeats} periods of ${fmt(p.period)} seconds, the first in full colour. ` : ''}One period: ${words}`;
  const h = p.periodRecorded && !p.steady ? 66 : 46;
  return html`<svg class="strip-svg" viewBox="0 0 ${VIEW_W} ${h}" role="img" aria-labelledby="${id}-t" data-period="${fmt(p.period)}" data-span="${fmt(span)}" data-x0="${BAR_X}" data-w="${BAR_W}" preserveAspectRatio="xMinYMin meet">
    <title id="${id}-t">${opts.label ? `${opts.label}: ` : ''}${title}</title>
    <rect x="${BAR_X - 1}" y="${barY - 1}" width="${BAR_W + 2}" height="${barH + 2}" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.35"/>
    ${raw(rects.join(''))}${raw(ticks.join(''))}${raw(periodMark)}
    <line class="strip-head" x1="${BAR_X}" x2="${BAR_X}" y1="${barY - 6}" y2="${barY + barH + 6}" stroke="currentColor" stroke-width="2" visibility="hidden"/>
  </svg>`;
}

/** The caption under the strip: what one period holds, to scale or not. */
export function stripCaption(p: Pattern): string {
  if (p.steady) return 'A steady light: lit all the time, with no rhythm to draw.';
  const lit = p.phases.filter((ph) => ph.colour && ph.level >= 1);
  const colours = [...new Set(lit.map((ph) => ph.colour!))].map(colourWord);
  const scale = p.periodRecorded ? `One period of ${fmt(p.period)} seconds, drawn to scale` : 'How often it repeats is not recorded, so the strip has no time scale';
  return `${scale}: ${colours.join(' and ')} light in colour, darkness in night blue.`;
}
