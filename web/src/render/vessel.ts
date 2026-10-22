/**
 * A lightship vessel's page (/v/<id>/) and the "Vessels" section of a lightship station's page.
 *
 * A vessel is a hull with a number (LV-112), the names it carried, the stations it served with the years, its
 * fate and, if it survives, its berth. The data is data/vessels/<id>.json with each station resolved to the
 * station's page (pipeline/site_vessels.py writes v/<id>.json). Pure functions returning escaped HTML, used by
 * scripts/prerender.ts, in the station page's own style.
 */
import { formatCoords, plainCoords, yearSpan } from '../lib/format.ts';
import { html, type SafeHtml } from '../lib/html.ts';
import { isStationId } from '../lib/station-id.ts';
import type { StationRecord, VesselLink, VesselPage } from '../lib/types.ts';
import { EXT, externalLink, stationPath, type RenderContext } from './common.ts';

export function vesselPath(id: string, ctx: Pick<RenderContext, 'base'>): string {
  return `${ctx.base}v/${id}/`;
}

export function vesselUrl(id: string, ctx: Pick<RenderContext, 'siteUrl'>): string {
  return `${ctx.siteUrl}v/${id}/`;
}

/** A vessel id is a hull number or a name: lower-case letters, digits and hyphens. */
export function isVesselId(id: unknown): id is string {
  return typeof id === 'string' && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id) && id.length <= 80;
}

/** "LV-112 Nantucket"; a vessel known only by its name is just that name; a hull with no name is its number. */
export function vesselName(v: Pick<VesselPage, 'hull' | 'names'> | Pick<VesselLink, 'hull' | 'names'>): string {
  const name = (v.names ?? []).find((n) => typeof n === 'string' && n.trim());
  return name && name.trim().toLowerCase() !== v.hull.toLowerCase() ? `${v.hull} ${name.trim()}` : v.hull;
}

/* ---------- Fate ---------- */

/** What became of the vessel, in Fresnel's own words (the Society's remark is not repeated). */
export function fateWords(v: Pick<VesselPage, 'fate' | 'berth'>): string {
  const { status, year, doubtful } = v.fate ?? {};
  const when = typeof year === 'number' ? ` in ${year}` : '';
  switch (status) {
    case 'survives':
      if (doubtful) return `The Society's record has her still in existence, but notes that she may have been scrapped${when}. Treat her survival as uncertain.`;
      return v.berth ? `She survives. Her berth is ${v.berth.name}.` : 'She survives, but no berth is recorded here yet.';
    case 'lost':
      return `Lost${when}.`;
    case 'scrapped':
      return `Scrapped${when}.`;
    case 'sold':
      return `Sold out of service${when}.`;
    default:
      return 'What became of her is not recorded here yet.';
  }
}

const FATE_LABEL: Record<string, string> = {
  survives: 'Survives',
  lost: 'Lost',
  scrapped: 'Scrapped',
  sold: 'Sold',
  unknown: 'Fate not recorded',
};

/* ---------- The "Vessels" section of a station page ---------- */

function stintYears(stints: VesselLink['stints']): string {
  const spans = (stints ?? []).map((s) => yearSpan(s.start ?? null, s.end ?? null)).filter((s) => s && s !== 'Not recorded');
  return spans.join(', ');
}

/** Null when the station has no vessel on record. */
export function vesselsSection(r: StationRecord, ctx: RenderContext): SafeHtml | null {
  const list = (r.vessels ?? []).filter((v) => v && isVesselId(v.id) && typeof v.hull === 'string');
  if (!list.length) return null;
  const served = list.filter((v) => v.role === 'served');
  const berth = list.filter((v) => v.role === 'berth');
  const years = (v: VesselLink) => stintYears(v.stints);
  return html`
    ${served.length
      ? html`<p>${served.length === 1 ? 'The lightship that served this station' : html`The ${served.length} lightships that served this station`}, in order of service:</p>
        <ul class="vessels">${served.map((v) => html`<li><a href="${vesselPath(v.id, ctx)}">${vesselName(v)}</a>${years(v) ? html` <span class="vessel-years">${years(v)}</span>` : ''}</li>`)}</ul>
        <p class="fine">Years are the ones the US Lighthouse Society's records give for each vessel at this station; a vessel may have left and come back.</p>`
      : ''}
    ${berth.length
      ? html`<p>${berth.length === 1 ? 'This is the berth of' : 'This is the berth of these vessels:'}</p>
        <ul class="vessels">${berth.map((v) => html`<li><a href="${vesselPath(v.id, ctx)}">${vesselName(v)}</a></li>`)}</ul>`
      : ''}`;
}

/* ---------- The vessel's page ---------- */

function careerTable(v: VesselPage, ctx: RenderContext): SafeHtml | null {
  const rows = (v.career ?? []).filter((c) => c && typeof c.station === 'string' && c.station.trim());
  if (!rows.length) return null;
  const sorted = rows.map((c, i) => ({ c, i })).sort((a, b) => (a.c.start ?? Infinity) - (b.c.start ?? Infinity) || a.i - b.i).map((x) => x.c);
  return html`<div class="table-wrap">
    <table class="career">
      <caption class="visually-hidden">Stations this vessel served, in order of the first year</caption>
      <thead><tr><th scope="col">Station</th><th scope="col">Years</th></tr></thead>
      <tbody>${sorted.map(
        (c) => html`<tr>
          <th scope="row" data-label="Station">${c.station_id && isStationId(c.station_id) ? html`<a href="${stationPath(c.station_id, ctx)}">${c.station}</a>` : c.station}</th>
          <td data-label="Years" class="years">${yearSpan(c.start ?? null, c.end ?? null)}</td>
        </tr>`,
      )}</tbody>
    </table>
  </div>`;
}

function berthSection(v: VesselPage, ctx: RenderContext): SafeHtml | null {
  const b = v.berth;
  if (!b || !isStationId(b.station_id)) return null;
  const hasPoint = typeof b.lat === 'number' && typeof b.lon === 'number';
  return html`<p>${v.fate?.status === 'survives' ? 'She lies at' : 'The hull or wreck is marked at'} <a href="${stationPath(b.station_id, ctx)}">${b.name}</a> on the Fresnel map.</p>
    ${b.note ? html`<p class="fine">${b.note.charAt(0).toUpperCase()}${b.note.slice(1)}.</p>` : ''}
    ${hasPoint ? html`<p class="coords-line"><span class="coords" data-coords="${plainCoords(b.lat!, b.lon!)}">${formatCoords(b.lat!, b.lon!)}</span></p>` : ''}`;
}

function vesselSources(v: VesselPage): SafeHtml {
  const list = (v.sources ?? []).filter((s) => s && s.url && s.label);
  return html`<h3 class="h-small" id="data-sources">Where the facts come from</h3>
    ${list.length
      ? html`<ol class="sources">${list.map((s) => html`<li><span class="src-title">${externalLink(s.url, s.label)}</span>${s.credit ? html`<span class="credit-line">${s.credit}</span>` : ''}</li>`)}</ol>`
      : html`<p class="muted">No sources recorded.</p>`}
    <p class="fine">Fresnel takes facts (hull numbers, years, stations) from these records, credits them here, and writes its own words.</p>`;
}

function vesselIssueUrl(v: VesselPage, ctx: Pick<RenderContext, 'repo' | 'siteUrl'>): string {
  const page = vesselUrl(v.id, ctx);
  const name = vesselName(v);
  const q = new URLSearchParams({
    template: 'edit.yml',
    title: `Edit: ${name} (lightship vessel)`,
    station_name: name,
    where: 'A lightship vessel (not a station)',
    page_url: page,
    body: `Vessel: ${name}\nPage: ${page}\n\nWhat is wrong or missing, what is right, and how do you know?\n`,
  });
  return `https://github.com/${ctx.repo}/issues/new?${q.toString()}`;
}

export function renderVesselMain(v: VesselPage, ctx: RenderContext): SafeHtml {
  const name = vesselName(v);
  const status = v.fate?.status ?? 'unknown';
  const other = [v.wal && v.wal !== v.hull ? `Coast Guard number ${v.wal}` : null, ...(v.names ?? []).slice(1).map((n) => `also called ${n}`)].filter(Boolean);
  const berth = berthSection(v, ctx);
  const served = (v.career ?? []).length;
  const facts: [string, unknown][] = [
    ['Hull number', v.hull],
    ...(v.wal ? ([['Coast Guard number', v.wal]] as [string, unknown][]) : []),
    ...(typeof v.built === 'number' ? ([['Built', v.built]] as [string, unknown][]) : []),
    ...(typeof v.retired === 'number' ? ([['Retired from lightship service', v.retired]] as [string, unknown][]) : []),
    ['Stations served', served ? String(served) : 'None recorded'],
    ['What became of her', fateWords(v)],
  ];
  const sections: [string, string, SafeHtml][] = [];
  if (berth) sections.push(['berth', 'Where she is now', berth]);
  sections.push([
    'career',
    'Career',
    careerTable(v, ctx) ?? html`<p class="muted">No stations are recorded for this vessel yet.</p>`,
  ]);
  sections.push(['facts', 'Facts', html`<dl class="kv kv-facts">${facts.map(([k, val]) => html`<div><dt>${k}</dt><dd>${val}</dd></div>`)}</dl>`]);
  sections.push(['sources', 'Sources and credits', vesselSources(v)]);
  return html`
  <nav class="crumbs" aria-label="Breadcrumb"><ol>
    <li><a href="${ctx.base}">Map</a></li>
    <li><span aria-current="page">${name}</span></li>
  </ol></nav>
  <header class="s-head">
    <p class="eyebrow">Lightship vessel${typeof v.built === 'number' ? ` · built ${v.built}` : ''}</p>
    <h1>${name}</h1>
    ${other.length ? html`<p class="aka">${other.join('; ')}</p>` : ''}
    <div class="notices"><p class="status-line"><strong>${FATE_LABEL[status] ?? FATE_LABEL.unknown}.</strong> ${fateWords(v)}</p></div>
    <nav class="jump" aria-label="On this page"><ul>${sections.map(([id, title]) => html`<li><a href="#${id}">${title}</a></li>`)}</ul></nav>
  </header>
  <div class="s-grid">
    <div class="s-main">${sections.map(([id, title, body]) => html`<section class="s-section" id="${id}" aria-labelledby="${id}-h"><h2 id="${id}-h">${title}</h2>${body}</section>`)}</div>
    <aside class="s-rail" aria-label="Corrections">
      <section class="card" aria-labelledby="edit-h">
        <h2 id="edit-h" class="h-card">Something wrong or missing?</h2>
        <p class="fine">Corrections and additions are welcome. This opens a short form on GitHub (a free account is needed) with this vessel already filled in.</p>
        <p><a class="btn" href="${vesselIssueUrl(v, ctx)}" rel="noopener">Suggest an edit${EXT}<span class="visually-hidden"> (opens GitHub)</span></a></p>
      </section>
    </aside>
  </div>`;
}

export function describeVessel(v: VesselPage): string {
  const served = (v.career ?? []).filter((c) => c.station).length;
  const built = typeof v.built === 'number' ? ` built in ${v.built}` : '';
  return `Lightship vessel ${vesselName(v)}${built}: ${served ? `${served} station${served === 1 ? '' : 's'} served with the years, ` : ''}what became of her${v.berth ? ' and where she lies today' : ''}, with sources.`;
}

export function renderVesselHead(v: VesselPage, ctx: RenderContext): SafeHtml {
  const name = vesselName(v);
  const desc = describeVessel(v);
  const url = vesselUrl(v.id, ctx);
  return html`<title>${name}: lightship vessel · Fresnel</title>
    <meta name="description" content="${desc}">
    <link rel="canonical" href="${url}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Fresnel">
    <meta property="og:title" content="${name}">
    <meta property="og:description" content="${desc}">
    <meta property="og:url" content="${url}">`;
}
