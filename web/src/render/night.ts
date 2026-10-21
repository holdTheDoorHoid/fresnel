/**
 * "The light at night" on a station page (DESIGN.md section 4): the light's pattern in words and
 * as a strip diagram, what is recorded and what is a convention, how far out it can be seen,
 * how that is worked out, and a host for the browser's night scene and mini-map
 * (ui/night.ts), which read the same record from the JSON in the host's data-night attribute.
 *
 * Without JavaScript the page still says everything but the moving picture: the strip, the
 * ranges at two eye heights, the assumptions.
 */
import { describeReading, sectorColours, colourWord, type ReadLight } from '../lib/characteristic.ts';
import { lengthFor, nauticalMiles } from '../lib/format.ts';
import { html, type SafeHtml } from '../lib/html.ts';
import { lightEras, type LightEra } from '../lib/light-history.ts';
import { lightPattern, type PatternResult } from '../lib/pattern.ts';
import { stationCountry } from '../lib/regions.ts';
import { DEFAULT_EYE_M, NOMINAL_VISIBILITY_NM, LOOM_MIN_RANGE_NM, RANGE_COEFF, VISIBILITY, VISIBILITY_ORDER, horizonNm, ringRangeNm, sight } from '../lib/sighting.ts';
import type { StationRecord } from '../lib/types.ts';
import { hasLight } from '../lib/vocab.ts';
import { editIssueUrl, type RenderContext } from './common.ts';
import { stripCaption, stripSvg } from './strip.ts';

/** What the browser's scene needs, written into the page as JSON. */
export interface NightData {
  id: string;
  name: string;
  country: string;
  lat: number;
  lon: number;
  status: string;
  light: StationRecord['light'];
  events: NonNullable<StationRecord['events']>;
  /** Other sources' values where sources disagree, for the visitor to choose between. */
  alt: { focal: { source: string; value: number }[]; characteristic: { source: string; value: string }[] };
  sources: Record<string, string>;
}

const SOURCE_NAMES: Record<string, string> = { wikidata: 'Wikidata', osm: 'OpenStreetMap', enc: 'NOAA charts', uscg: 'USCG Light List', ccg: 'Canadian List of Lights' };

export function sourceName(id: string, ctx?: Pick<RenderContext, 'sources'>): string {
  return SOURCE_NAMES[id] ?? ctx?.sources.get(id)?.title ?? id;
}

export function nightData(r: StationRecord, ctx?: Pick<RenderContext, 'sources'>): NightData {
  const conflicts = r.conflicts ?? [];
  const values = (field: string) => conflicts.find((c) => c?.field === field)?.values ?? [];
  const focal = values('light.focal_height_m').filter((v): v is { source: string; value: number } => typeof v?.value === 'number' && v.value > 0);
  const chars = values('light.characteristic').filter((v): v is { source: string; value: string } => typeof v?.value === 'string' && !!v.value.trim());
  const sources: Record<string, string> = {};
  for (const v of [...focal, ...chars]) sources[v.source] = sourceName(v.source, ctx);
  if (r.light?.from) sources[r.light.from] = sourceName(r.light.from, ctx);
  return {
    id: r.id,
    name: r.name,
    country: stationCountry(r),
    lat: r.location.lat,
    lon: r.location.lon,
    status: r.status,
    light: r.light ?? null,
    events: (r.events ?? []).filter((e) => e && e.event === 'characteristic_changed'),
    alt: { focal, characteristic: chars },
    sources,
  };
}

/** The ways one light can be seen: each sector colour, a dark sector, or just the light. */
export interface LightView {
  colour: string | null;
  dark: boolean;
  label: string;
}

export function viewsOf(l: ReadLight): LightView[] {
  const cols = sectorColours(l.c);
  const views: LightView[] = cols.length ? cols.map((k) => ({ colour: k, dark: false, label: `In the ${colourWord(k)} sector` })) : [{ colour: null, dark: false, label: '' }];
  const dark = l.c.sectors.filter((s) => s.colour === 'dark');
  if (dark.length) {
    const b = dark.find((s) => s.from !== null && s.to !== null);
    if (views.length === 1 && !views[0]!.label) views[0]!.label = 'Where it shows';
    views.push({ colour: null, dark: true, label: b ? `In the dark sector (${b.from}° to ${b.to}°)` : 'In a dark sector' });
  }
  return views;
}

export function patternFor(l: ReadLight, v: LightView): PatternResult {
  return lightPattern(l.c, v.colour ? { colour: v.colour } : {});
}

function lightName(l: ReadLight): string {
  return l.role ? `The ${l.role}` : 'The light';
}

/** Strips for every light of an era and every sector of each. */
function strips(era: LightEra, idBase: string): SafeHtml {
  const many = era.reading.lights.length > 1;
  return html`${era.reading.lights.map((l, li) => {
    const views = viewsOf(l).filter((v) => !v.dark);
    return html`${views.map((v, vi) => {
      const res = patternFor(l, v);
      const label = [many ? lightName(l) : '', v.label].filter(Boolean).join(', ');
      if (!res.ok) return html`<p class="notice tone-caution" role="note">${label ? `${label}: ` : ''}${res.reason}</p>`;
      return html`<figure class="strip">
        ${label ? html`<figcaption class="strip-label">${label}</figcaption>` : ''}
        ${stripSvg(res.pattern, { label, id: `${idBase}-${li}-${vi}` })}
        <p class="strip-cap fine">${stripCaption(res.pattern)}</p>
      </figure>`;
    })}`;
  })}`;
}

/** Plain lines: which durations are conventions, and the reader's own notes. */
export function conventionLines(era: LightEra): string[] {
  const out = new Set<string>();
  for (const l of era.reading.lights) {
    for (const n of l.c.notes) out.add(n);
    for (const v of viewsOf(l).filter((x) => !x.dark)) {
      const res = patternFor(l, v);
      if (res.ok) for (const c of res.pattern.conventions) out.add(c);
    }
  }
  return [...out];
}

function eyeWords(country: string, m: number, what: string): string {
  return `${what} (eye ${lengthFor(country, m)} above the water)`;
}

/** "Visible to about 15.2 nmi (28 km): there it drops below your horizon." */
export function rangeRow(focal: number | null, nominal: number | null, eye: number): { value: SafeHtml; sub: string } | null {
  const ring = ringRangeNm(focal, nominal, eye);
  if (!ring) return null;
  const geo = focal !== null ? horizonNm(focal) + horizonNm(eye) : null;
  if (focal !== null && nominal !== null) {
    return {
      value: html`About ${nauticalMiles(ring.nm)}`,
      sub: ring.limit === 'horizon'
        ? `There it drops below your horizon. Its charted range, ${nauticalMiles(nominal)}, is farther: it is bright enough, the horizon is the limit.`
        : `Beyond that it is too faint (its charted range). Its horizon is farther, ${nauticalMiles(geo)}.`,
    };
  }
  if (focal !== null) return { value: html`Over the horizon to ${nauticalMiles(geo)}`, sub: 'Its charted range (how bright it is) is not recorded, so it may have been too faint to see that far.' };
  return { value: html`${nauticalMiles(nominal)}, its charted range`, sub: 'Its focal height is not recorded, so where it drops below the horizon cannot be worked out.' };
}

function missingLines(era: LightEra): string[] {
  const out: string[] = [];
  if (!era.reading.raw) out.push('Its pattern (the characteristic) is not recorded, so it cannot be shown flashing.');
  else if (!era.reading.lights.length) out.push('Its pattern is recorded in a form this page cannot read (shown above as the source writes it), so it is not drawn.');
  if (era.focalM === null) out.push('Its focal height (the height of the light above the water) is not recorded, so where it drops below the horizon cannot be worked out.');
  if (era.nominalNm === null) out.push(era.past && !era.lastLit ? 'Its range at that time is not recorded, so how bright it looked cannot be worked out.' : 'Its charted range is not recorded, so how bright it looks from a distance cannot be worked out.');
  return out;
}

function howItWorks(era: LightEra, country: string): SafeHtml {
  const H = era.focalM;
  const eye = DEFAULT_EYE_M;
  return html`<details class="night-how">
    <summary>How this view is worked out</summary>
    <div class="prose-small">
      <p><strong>The horizon.</strong> The earth curves away, so a light drops out of sight below the horizon at its <em>geographic range</em>: about 2.08 × (√H + √h) nautical miles, with H the height of the light above the water and h the height of your eye, both in metres. The 2.08 allows for the usual bending of light by the air (standard refraction).${H !== null ? html` For this light, H = ${lengthFor(country, H)}; from a small boat’s deck (h = ${lengthFor(country, eye)}): 2.08 × (√${Number(H.toFixed(1))} + √${eye}) ≈ ${nauticalMiles(horizonNm(H) + horizonNm(eye))}.` : ''}</p>
      <p><strong>Brightness.</strong> A light’s charted (nominal) range is how far it can be seen at night when the air is clear enough to see ${NOMINAL_VISIBILITY_NM} nautical miles. The page works out how bright it looks at other distances and in other weather with Allard’s law: brightness falls with the square of the distance and is dimmed by the air in between, so that at the charted range, in ${NOMINAL_VISIBILITY_NM}-mile visibility, it is just bright enough to see. The visibility choices are ${VISIBILITY_ORDER.map((v) => `${VISIBILITY[v].label.toLowerCase()} (${VISIBILITY[v].nm} nautical miles)`).join(', ')}.</p>
      <p><strong>What you see is the nearer of the two limits.</strong> The ring on the map is the same distance: the smaller of the horizon and the charted range, from your chosen eye height.</p>
      <p><strong>The loom.</strong> A powerful light (charted range ${LOOM_MIN_RANGE_NM} nautical miles or more) below your horizon can still light the air above it, a faint glow sailors call the loom. It is shown only when the light would be bright enough to see if the horizon were not in the way, and it fades as you go farther. Its strength is a sketch, not a measurement.</p>
      <p><strong>The picture.</strong> A moonless night. Angles are true: from a boat, a light miles away sits almost on the horizon line, because the height of a tower is tiny at that distance. The naked-eye view is 40° wide; the binocular view is 7°, about what a 7×50 marine binocular shows. Brightness is drawn on a scale of steps (each tenfold increase a step brighter). A screen cannot show a real light’s glare, so a near light looks dimmer than in life, and the faintest lights may look plainer than they would at sea, where you have to know where to look.</p>
      <p><strong>Durations.</strong> Most records give only the abbreviation, not how long each flash or eclipse lasts. Those are drawn by convention, within IALA’s rules for light rhythms, and the list above says which.</p>
      <p>The geographic range uses the factor ${RANGE_COEFF} of the US Light List and Bowditch. The two limits are worked out the same way for every light; where the record is missing a figure, the page says so instead of assuming one.</p>
    </div>
  </details>`;
}

function guideNotice(): SafeHtml {
  return html`<p class="night-guide"><strong>A guide, not a navigation aid.</strong> This is a drawing of what the record says, to show what the light was like. Never use it to find your way at sea: use current official charts and the Light List or List of Lights.</p>`;
}

function conflictNote(r: StationRecord, ctx: RenderContext): SafeHtml | string {
  const data = nightData(r, ctx);
  const country = data.country;
  const bits: SafeHtml[] = [];
  if (data.alt.focal.length > 1) {
    const vals = data.alt.focal.map((v) => `${lengthFor(country, v.value)} (${sourceName(v.source, ctx)})`);
    const [a, b] = [...data.alt.focal].sort((x, y) => x.value - y.value);
    const feet = a && b && Math.abs(b.value / a.value - 1 / 0.3048) < 0.1;
    bits.push(html`<li>Sources disagree on its focal height: ${vals.join(' or ')}.${feet ? ' The larger figure is the smaller one in feet, so it was probably written in feet by mistake.' : ''} The view uses the figure in the facts above; you can switch it below.</li>`);
  }
  if (data.alt.characteristic.length > 1) {
    bits.push(html`<li>Sources give different patterns: ${data.alt.characteristic.map((v, i) => html`${i ? ' or ' : ''}<code class="char">${v.value}</code> (${sourceName(v.source, ctx)})`)}. One may be an older pattern or a sector. The view shows the first; you can switch it below.</li>`);
  }
  return bits.length ? html`<ul class="night-conflicts notice tone-caution" role="note">${bits}</ul>` : '';
}

export function nightSection(r: StationRecord, ctx: RenderContext): SafeHtml | null {
  if (!hasLight(r.kind) || !r.light) return null;
  const eras = lightEras(r);
  const era = eras.at(-1);
  if (!era) return null;
  const country = stationCountry(r);
  const nothing = !era.reading.raw && era.focalM === null && era.nominalNm === null && eras.length === 1;
  if (nothing) {
    return html`<p class="muted">Nothing is recorded yet about this light’s pattern, its height or its range, so it cannot be shown at night. Know them, with a source? <a href="${editIssueUrl(r, ctx)}">Tell us</a>.</p>`;
  }
  const words = describeReading(era.reading);
  const readable = era.reading.lights.length > 0;
  const missing = missingLines(era);
  const conventions = readable ? conventionLines(era) : [];
  const lightNotes = era.reading.lights.flatMap((l) => l.notes);
  const sightable = era.focalM !== null || era.nominalNm !== null;
  const row = (eye: number, what: string) => {
    const v = rangeRow(era.focalM, era.nominalNm, eye);
    return v ? html`<div><dt>${eyeWords(country, eye, what)}</dt><dd>${v.value}<span class="sub">${v.sub}</span></dd></div>` : '';
  };
  const s0 = sight({ focalM: era.focalM, nominalNm: era.nominalNm, eyeM: DEFAULT_EYE_M, distanceNm: 1, visibility: 'normal' });
  return html`
    <p class="night-era"><span class="night-era-tag${era.past ? ' is-past' : ''}">${era.label}</span>${eras.length > 1 ? html` <span class="fine">The record also gives ${eras.length - 1 === 1 ? 'an earlier pattern' : `${eras.length - 1} earlier patterns`}; choose a year below.</span>` : ''}</p>
    ${readable
      ? html`<p class="night-words">${era.reading.lights.length === 1 && !era.reading.lights[0]!.role ? html`<code class="char">${era.reading.lights[0]!.c.raw}</code>: ` : ''}${(words ?? '').replace(/^./, (ch) => (era.reading.lights.length === 1 && !era.reading.lights[0]!.role ? ch.toLowerCase() : ch))}.</p>`
      : era.reading.raw ? html`<p class="night-words"><code class="char">${era.reading.raw}</code> <span class="sub">As the source writes it: this page cannot read it as a light’s pattern.</span></p>` : ''}
    ${era.reading.leftovers.length && readable ? html`<p class="fine">The record also says: ${era.reading.leftovers.map((t, i) => html`${i ? '; ' : ''}“${t}”`)} (not used in the drawing).</p>` : ''}
    ${conflictNote(r, ctx)}
    <div class="night-live" data-night="${JSON.stringify(nightData(r, ctx))}" hidden></div>
    <noscript><p class="fine">Turn on JavaScript to see the light flashing at sea, at a distance you choose.</p></noscript>
    ${readable ? html`<h3 class="h-small">The pattern over one period</h3>${strips(era, `strip-${r.id}`)}` : ''}
    ${conventions.length || lightNotes.length
      ? html`<h3 class="h-small">Recorded, and drawn by convention</h3><ul class="night-notes">${[...lightNotes, ...conventions].map((t) => html`<li>${t}</li>`)}</ul>`
      : ''}
    ${missing.length ? html`<h3 class="h-small">Not recorded</h3><ul class="night-notes night-missing">${missing.map((t) => html`<li>${t}</li>`)}</ul>` : ''}
    ${sightable
      ? html`<h3 class="h-small">How far out it ${era.past ? 'could' : 'can'} be seen</h3>
        <dl class="kv kv-facts night-ranges">${row(DEFAULT_EYE_M, 'From a small boat’s deck')}${row(15, 'From a ship’s bridge')}</dl>
        <p class="fine">On a clear night, in the ${NOMINAL_VISIBILITY_NM}-nautical-mile visibility the charted range assumes.${s0.geographicNm !== null && s0.luminousNm !== null ? '' : ' Only one of the two limits is known, so the real distance may be shorter.'}</p>
        <div class="night-map-wrap" data-night-map hidden></div>`
      : ''}
    ${guideNotice()}
    ${howItWorks(era, country)}`;
}

/** A short line for the map panel: "Seen from a small boat out to about 15 nmi". */
export function reachLine(r: StationRecord): string | null {
  const L = r.light;
  if (!L || !hasLight(r.kind)) return null;
  const ring = ringRangeNm(L.focal_height_m, L.range_nm, DEFAULT_EYE_M);
  if (!ring) return null;
  return `${r.status === 'active' ? 'Seen' : 'Could be seen'} from a small boat’s deck out to about ${nauticalMiles(ring.nm)}`;
}

