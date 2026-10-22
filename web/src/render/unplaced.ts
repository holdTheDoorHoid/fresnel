/**
 * The "stations we can't place yet" page (/unplaced/): the lightship and life-saving stations that the sources name and
 * no source gives a position for, so they are not on the map. Each row says why, and carries a pre-filled "Suggest a
 * location" link to the GitHub edit form. A position is only ever added from a source that gives one (a Light List
 * entry, a report, a chart); a guess is never placed.
 */
import { yearSpan } from '../lib/format.ts';
import { html, type SafeHtml } from '../lib/html.ts';
import { regionName, regionWithCountry } from '../lib/regions.ts';
import type { UnplacedFile, UnplacedStation } from '../lib/types.ts';
import { vesselName, vesselPath } from './vessel.ts';
import { EXT, type RenderContext } from './common.ts';

export function unplacedUrl(ctx: Pick<RenderContext, 'siteUrl'>): string {
  return `${ctx.siteUrl}unplaced/`;
}

const GROUPS: { kind: string; id: string; title: string; what: string }[] = [
  { kind: 'lightship_station', id: 'lightships', title: 'Lightship stations', what: 'Places where a lightship was moored to mark a shoal, a channel or a harbor approach.' },
  { kind: 'life_saving_station', id: 'life-saving', title: 'Life-saving stations', what: 'Stations of the US Life-Saving Service and the houses of refuge on the Florida coast.' },
];

/** A row's anchor: the source key is stable and already URL-safe once its colon is dropped. */
export function rowId(s: Pick<UnplacedStation, 'key'>): string {
  return `u-${s.key.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`;
}

/** The "Suggest a location" link: the edit form, opened with the station's name and the question to answer. */
export function suggestLocationUrl(s: UnplacedStation, ctx: Pick<RenderContext, 'repo' | 'siteUrl'>): string {
  const where = s.region ? (s.country === 'US' ? `${regionName(s.region) || s.region}, United States` : regionWithCountry(s.region)) : 'United States';
  const kind = s.kind === 'lightship_station' ? 'lightship station' : 'life-saving station';
  const q = new URLSearchParams({
    template: 'edit.yml',
    title: `Location: ${s.name} (${s.region ? regionWithCountry(s.region) || s.region : 'United States'})`,
    station_name: s.name,
    where,
    page_url: unplacedUrl(ctx),
    body:
      `Station: ${s.name} (${kind}, not on the map yet)\nWhere: ${where}\nPage: ${unplacedUrl(ctx)}\n\n` +
      'Where was it? Give a latitude and longitude, or a bearing and distance from a named light, and say where you read it ' +
      '(a Light List, a chart, a report, a book). Please do not guess: a position is only added from a source.\n',
  });
  return `https://github.com/${ctx.repo}/issues/new?${q.toString()}`;
}

/** The reason most rows of a group share; a row then says it only if its own reason differs. */
export function commonReason(items: readonly UnplacedStation[]): string | null {
  const counts = new Map<string, number>();
  for (const s of items) counts.set(s.reason, (counts.get(s.reason) ?? 0) + 1);
  let best: string | null = null;
  let n = 0;
  for (const [reason, c] of counts) if (c > n || (c === n && best !== null && reason < best)) [best, n] = [reason, c];
  return best !== null && n > 1 ? best : null;
}

function sentence(s: string): string {
  const t = s.trim().replace(/\.$/, '');
  return t ? `${t.charAt(0).toUpperCase()}${t.slice(1)}.` : '';
}

function sortRows(items: readonly UnplacedStation[]): UnplacedStation[] {
  const region = (s: UnplacedStation) => (s.region ? regionName(s.region) || s.region : '~');
  return [...items].sort((a, b) => a.country.localeCompare(b.country) || region(a).localeCompare(region(b)) || a.name.localeCompare(b.name));
}

function row(s: UnplacedStation, common: string | null, ctx: RenderContext): SafeHtml {
  const years = s.first || s.last ? yearSpan(s.first, s.last) : '';
  const why = common !== null && s.reason === common ? 'Not found in the sources read.' : sentence(s.reason);
  const others = (s.other_names ?? []).filter(Boolean);
  return html`<tr id="${rowId(s)}">
    <th scope="row" data-label="Station">${s.name}${others.length ? html`<span class="sub">Also known as ${others.join('; ')}</span>` : ''}${s.where ? html`<span class="sub">Described as: ${s.where}</span>` : ''}${s.vessels.length ? html`<span class="sub">Vessels: ${s.vessels.map((v, i) => html`${i ? ', ' : ''}<a href="${vesselPath(v.id, ctx)}">${vesselName({ hull: v.hull, names: [] })}</a>`)}</span>` : ''}</th>
    <td data-label="Region">${s.region ? regionWithCountry(s.region) || s.region : html`<span class="muted">Not given</span>`}</td>
    <td data-label="Years" class="years">${years || html`<span class="muted">Not recorded</span>`}</td>
    <td data-label="Why no position">${why}</td>
    <td data-label="Help" class="suggest">${s.suggest ? html`<a href="${suggestLocationUrl(s, ctx)}" rel="noopener">Suggest a location${EXT}<span class="visually-hidden"> for ${s.name} (opens GitHub)</span></a>` : html`<span class="muted">Not a mooring</span>`}</td>
  </tr>`;
}

export function renderUnplacedMain(file: UnplacedFile, ctx: RenderContext): SafeHtml {
  const groups = GROUPS.map((g) => ({ ...g, items: sortRows((file.stations ?? []).filter((s) => s.kind === g.kind)) })).filter((g) => g.items.length);
  const total = groups.reduce((n, g) => n + g.items.length, 0);
  return html`
  <nav class="crumbs" aria-label="Breadcrumb"><ol>
    <li><a href="${ctx.base}">Map</a></li>
    <li><span aria-current="page">Stations we can’t place yet</span></li>
  </ol></nav>
  <header class="s-head">
    <p class="eyebrow">Open questions</p>
    <h1>Stations we can’t place yet</h1>
    <p class="lede">${total} stations that the records name but that no source we have read gives a position for. They are not on the map, because Fresnel never places a station by guesswork. If you know where one was, a Light List entry, a chart or a report that gives a position, a bearing and distance from a named light, <em>Suggest a location</em> opens the edit form with the station already filled in.</p>
    <nav class="jump" aria-label="On this page"><ul>${groups.map((g) => html`<li><a href="#${g.id}">${g.title} (${g.items.length})</a></li>`)}<li><a href="#how">How a position is found</a></li></ul></nav>
  </header>
  <div class="s-grid s-grid-wide">
    <div class="s-main">
      ${groups.map((g) => {
        const common = commonReason(g.items);
        return html`<section class="s-section" id="${g.id}" aria-labelledby="${g.id}-h">
          <h2 id="${g.id}-h">${g.title}</h2>
          <p>${g.what}</p>
          ${common ? html`<p class="fine"><strong>Why most have no position:</strong> ${sentence(common)}</p>` : ''}
          <div class="table-wrap">
            <table class="gaps">
              <caption class="visually-hidden">${g.title} with no position yet</caption>
              <thead><tr><th scope="col">Station</th><th scope="col">Region</th><th scope="col">Years</th><th scope="col">Why no position</th><th scope="col">Help</th></tr></thead>
              <tbody>${g.items.map((s) => row(s, common, ctx))}</tbody>
            </table>
          </div>
        </section>`;
      })}
      <section class="s-section" id="how" aria-labelledby="how-h">
        <h2 id="how-h">How a position is found</h2>
        <p>A position comes only from a source that gives one: a latitude and longitude printed in a Light List, a Light-House Board report or a Lighthouse Service Bulletin, or a bearing and distance from a named light (“4 miles SE. by E. ¼ E. from Monomoy Point Light-House”), worked out from that light’s own position. A worked-out position is marked <em>approximate</em> and <em>computed</em> on the station’s page, with the words it was worked from.</p>
        <p>The stations here were not found in the Light Lists, reports and bulletins read so far. Many were kept after 1900 in Light Lists that were not read, or before 1850 in no list at all.</p>
        <p class="fine">The facts about each station (years, vessels) come from the US Lighthouse Society’s records and the Life-Saving Service’s annual reports; see <a href="${ctx.base}credits/">all sources and licences</a>.</p>
      </section>
    </div>
  </div>`;
}

export function renderUnplacedHead(file: UnplacedFile, ctx: RenderContext): SafeHtml {
  const desc = `${file.count} lightship and life-saving stations the records name but no source places: why each has no position yet, and how to suggest one.`;
  const url = unplacedUrl(ctx);
  return html`<title>Stations we can’t place yet · Fresnel</title>
    <meta name="description" content="${desc}">
    <link rel="canonical" href="${url}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Fresnel">
    <meta property="og:title" content="Stations we can’t place yet">
    <meta property="og:description" content="${desc}">
    <meta property="og:url" content="${url}">`;
}
