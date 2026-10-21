/** Site-wide fragments filled in at build time (and in dev, in the browser): the map key, the sources table, notices. */
import { html, raw, safeUrl, type SafeHtml } from '../lib/html.ts';
import { formatCount, formatDate } from '../lib/format.ts';
import { glyphSvg, type Glyph, type Silhouette } from '../lib/icons.ts';
import type { Meta } from '../lib/types.ts';

/** The status rows of the key, in the order of the filter: the shape, the words, what it means. */
export const KEY_STATUS: { status: string; glyph: Glyph; label: string; meaning: string }[] = [
  { status: 'active', glyph: 'lit', label: 'Active light', meaning: 'A lit lamp: the light still shines at night.' },
  { status: 'inactive', glyph: 'dark', label: 'Standing, light out', meaning: 'A solid, unlit shape: it stands, but shows no light.' },
  { status: 'ruins', glyph: 'broken', label: 'Ruins', meaning: 'A broken-off shape: only ruins or foundations are left.' },
  { status: 'lost', glyph: 'ghost', label: 'Lost', meaning: 'A dashed ring with a cross: gone, only the site is left. Drawn under the others.' },
  { status: 'relocated', glyph: 'moved', label: 'Moved', meaning: 'A shape with an arrow: moved, and shown where it stands now.' },
  { status: 'replica', glyph: 'copy', label: 'Replica', meaning: 'A hollow shape over its own outline: a copy, not the original.' },
  { status: 'unknown', glyph: 'unknown', label: 'Status unknown', meaning: 'A ring with a question mark: we do not know yet.' },
];

export const KEY_KIND: { silhouette: Silhouette; label: string }[] = [
  { silhouette: 'tower', label: 'A tower: lighthouses, and range, pier and harbor lights' },
  { silhouette: 'ship', label: 'A ship: lightships at their berths, and lightship stations at sea' },
  { silhouette: 'house', label: 'A house: life-saving stations (they had no light; one still in service is amber)' },
];

/**
 * The map key. The same markup appears on the map (the Key panel), in the filters and on the
 * About page, so it reads the same everywhere. `headingLevel` sets its two headings.
 */
export function mapKey(opts: { headingLevel?: 2 | 3 | 4; idPrefix?: string } = {}): SafeHtml {
  const h = opts.headingLevel ?? 3;
  const p = opts.idPrefix ?? 'key';
  const heading = (id: string, text: string) => raw(`<h${h} class="key-h" id="${p}-${id}">${text}</h${h}>`);
  return html`<div class="map-key">
    <div class="key-group">
      ${heading('status', 'The shape says the status')}
      <ul class="key-list" aria-labelledby="${p}-status">${KEY_STATUS.map(
        (k) => html`<li>${raw(glyphSvg(k.glyph, 'tower', { size: 26 }))}<span><strong>${k.label}.</strong> ${k.meaning}</span></li>`,
      )}</ul>
    </div>
    <div class="key-group">
      ${heading('kind', 'The silhouette says what it is')}
      <ul class="key-list" aria-labelledby="${p}-kind">${KEY_KIND.map((k) => html`<li>${raw(glyphSvg('dark', k.silhouette, { size: 26 }))}<span>${k.label}</span></li>`)}</ul>
      <p class="fine">The lamp, the dashed ring and the question mark look the same for every kind. Colour only repeats what the shape says, so the map reads the same in any colour vision and in print. Numbered circles are groups of nearby stations: zoom in or select one to spread them out.</p>
    </div>
  </div>`;
}

/** The Credits page's table: every data source with its licence, credit line and counts. */
export function sourcesRows(meta: Pick<Meta, 'sources'>): SafeHtml {
  if (!meta.sources.length) return html`<tr><td colspan="5" class="muted">No sources are listed yet.</td></tr>`;
  return html`${meta.sources.map((s) => {
    const url = safeUrl(s.url);
    return html`<tr id="source-${s.id}">
      <th scope="row">${url ? html`<a href="${url}" rel="noopener">${s.title}</a>` : s.title}${s.retrieved ? html`<span class="sub">Retrieved ${formatDate(s.retrieved)}</span>` : ''}</th>
      <td>${s.license ?? 'Not stated'}</td>
      <td class="credit-line">${s.credit ?? s.title}</td>
      <td class="num" data-label="Records">${typeof s.records === 'number' ? formatCount(s.records) : '–'}</td>
      <td class="num" data-label="Stations">${typeof s.stations === 'number' ? formatCount(s.stations) : '–'}</td>
    </tr>`;
  })}`;
}

export function fixtureBanner(meta: Pick<Meta, 'fixtures'>): SafeHtml {
  if (!meta.fixtures) return html``;
  return html`<p class="fixture-banner" role="note"><strong>Sample data.</strong> This site is showing a few invented test entries while the real station database is being built. Do not plan a trip from them.</p>`;
}

export function takedownEmail(email: string | null | undefined): SafeHtml {
  if (!email || !/^[^@\s"<>]+@[^@\s"<>]+$/.test(email)) return html``;
  return html`<p>Prefer not to use GitHub? Email <a href="mailto:${email}">${email}</a> with the same details.</p>`;
}

/** "7 stations: 2 active lights, …" for the About page's lede, from meta.json. */
export function countsLine(meta: Pick<Meta, 'counts'>): string {
  const c = meta.counts;
  const parts = [`${formatCount(c.total)} stations on the map`];
  if (c.stories) parts.push(`${formatCount(c.stories)} with a written history`);
  if (c.rosters) parts.push(`${formatCount(c.rosters)} with a keepers roster`);
  return parts.join(', ') + '.';
}
