/**
 * The keepers index in HTML (DESIGN.md 3.6): a person's page (/k/<id>/), the archive's roster on a
 * station page, and the shell of /keepers/. Pure functions returning escaped HTML, used by
 * scripts/prerender.ts at build time and by the dev pages in the browser.
 *
 * Wording rules: a name is joined to another only by the archive's own person record, and the page
 * says "possibly the same person as…" and nothing more where two records only share a name; the
 * archive is credited and linked on every page that shows its names; the archive's race and sex
 * fields are never shown (the pipeline does not even read them).
 */
import { formatCount, formatDate, yearOf, yearSpan } from '../lib/format.ts';
import { html, safeUrl, type SafeHtml } from '../lib/html.ts';
import { isPersonId, yearsText, type KeeperManifest, type PersonRecord, type PersonStint } from '../lib/people.ts';
import { regionName } from '../lib/regions.ts';
import { isStationId } from '../lib/station-id.ts';
import type { ArchiveLine, ArchivePlace, ArchiveRoster, StationRecord } from '../lib/types.ts';
import { INFO, externalLink, type RenderContext } from './common.ts';
import { researchSourceId } from './keepers.ts';

/** The archive's credit in the words the owner chose (DESIGN.md 3.6). */
export const ARCHIVE_NAME = 'U.S. Lighthouse Society’s Digital Archive';
export const ARCHIVE_SOURCE_LINE = 'Keepers listed by the U.S. Lighthouse Society’s Digital Archive, from the National Archives’ keeper registers.';
export const ARCHIVE_HOME = 'https://archives.uslhs.org/';

/** The same sentence with the archive linked, for pages that have no place or person link of their own to put beside it. */
export function archiveSentence(): SafeHtml {
  return html`Keepers listed by the ${externalLink(ARCHIVE_HOME, ARCHIVE_NAME)}, from the National Archives’ keeper registers.`;
}

export function personPath(id: string, ctx: Pick<RenderContext, 'base'>): string {
  return `${ctx.base}k/${id}/`;
}

export function personUrl(id: string, ctx: Pick<RenderContext, 'siteUrl'>): string {
  return `${ctx.siteUrl}k/${id}/`;
}

export function keepersPath(ctx: Pick<RenderContext, 'base'>): string {
  return `${ctx.base}keepers/`;
}

/* ---------- Roles and years, as the archive prints them ---------- */

function capitalise(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

/** The archive's own heading when it is not one of the standard seven ("Machinist", "USCG"), else our word ("Head keeper"). */
export function roleLabel(role: string | null | undefined, roleRaw?: string | null): string {
  const raw = (roleRaw ?? '').trim();
  if (raw) return raw;
  return capitalise((role ?? '').trim());
}

/**
 * The years as the archive prints them, in words: "1861–1864", "from at least 1909", "until 1911",
 * "1 Oct 1912 – 1913". The archive's "at least" stays: it marks a documented stretch, not a term.
 */
export function printedSpan(span: string | null | undefined): string {
  const s = (span ?? '').replace(/\s+/g, ' ').trim();
  const dated = (t: string) =>
    t
      .replace(/(\d{4})\.(\d{2})\.(\d{2})/g, (_m, y, mo, d) => formatDate(`${y}-${mo}-${d}`) ?? _m)
      .replace(/(\d{4})\.(\d{2})(?!\.)/g, (_m, y, mo) => formatDate(`${y}-${mo}`) ?? _m)
      .trim();
  const i = s.indexOf('-');
  if (i < 0) return s ? dated(s) : 'Not recorded';
  const a = dated(s.slice(0, i));
  const b = dated(s.slice(i + 1).split('-')[0] ?? '');
  if (a && b) return a === b ? a : `${a}${/[a-z]/i.test(a + b) && (a.includes(' ') || b.includes(' ')) ? ' – ' : '–'}${b}`;
  if (a) return `from ${a}`;
  if (b) return `until ${b}`;
  return 'Not recorded';
}

function stintYears(s: Pick<PersonStint, 'span' | 'from' | 'to' | 'from_approx' | 'to_approx' | 'src'>): string {
  if (s.src === 'uslhs' && s.span) return printedSpan(s.span);
  return yearSpan(s.from, s.to, s.from_approx === true, s.to_approx === true);
}

function lineYears(l: ArchiveLine): string {
  if (l.span) return printedSpan(l.span);
  return yearSpan(l.from, l.to, l.from_approx === true, l.to_approx === true);
}

/* ---------- The archive's roster on a station page ---------- */

function lineSortYear(l: ArchiveLine): number {
  return l.from ?? l.to ?? Infinity;
}

/** Roster lines in order of service: by the first year, lines with no year last, ties kept as printed. */
export function sortArchiveLines(lines: readonly ArchiveLine[]): ArchiveLine[] {
  return lines
    .map((l, i) => ({ l, i }))
    .sort((a, b) => lineSortYear(a.l) - lineSortYear(b.l) || (a.l.to ?? Infinity) - (b.l.to ?? Infinity) || a.i - b.i)
    .map((x) => x.l);
}

export function archiveTable(lines: readonly ArchiveLine[], ctx: Pick<RenderContext, 'base'>): SafeHtml {
  const rows = sortArchiveLines(lines.filter((l) => l && typeof l.name === 'string' && l.name.trim()));
  return html`<div class="table-wrap">
    <table class="keepers keepers-archive">
      <caption class="visually-hidden">Keepers of this station as the archive lists them, in order of service</caption>
      <thead><tr><th scope="col">Name</th><th scope="col">Role</th><th scope="col">Years</th></tr></thead>
      <tbody>${rows.map(
        (l) => html`<tr>
          <th scope="row" data-label="Name">${l.person && isPersonId(l.person) ? html`<a href="${personPath(l.person, ctx)}">${l.name}</a>` : l.name}</th>
          <td data-label="Role">${roleLabel(l.role, l.role_raw) || html`<span class="muted">Not given</span>`}</td>
          <td data-label="Years" class="years">${lineYears(l)}</td>
        </tr>`,
      )}</tbody>
    </table>
  </div>`;
}

/** What a station page says about the archive's roster: the roster itself when no research roster exists, else a note. */
export function archiveRosterBlock(r: Pick<StationRecord, 'archive_roster' | 'keepers'>, ctx: Pick<RenderContext, 'base'>): SafeHtml | null {
  const ar: ArchiveRoster | null | undefined = r.archive_roster;
  if (!ar || !ar.places?.length) return null;
  const checked = !!r.keepers?.length;
  if (checked) {
    const links = ar.places.map((p) => externalLink(p.url, p.name));
    return html`<p class="fine roster-note">The ${ARCHIVE_NAME} also lists ${formatCount(ar.count)} ${ar.count === 1 ? 'line' : 'lines'} for this station (${links.map((l, i) => html`${i ? ', ' : ''}${l}`)}), from the National Archives’ keeper registers. The roster above is the one that has been checked.</p>`;
  }
  const shown = ar.places.filter((p) => p.lines?.length);
  if (!shown.length) return null;
  const many = shown.length > 1;
  return html`<div class="roster-archive">
    <p class="roster-source"><span class="tag tag-unchecked">Not yet checked</span> ${ARCHIVE_SOURCE_LINE} A span marked “at least” is a stretch the archive documents, not always the whole term. Nobody has checked this roster against other sources yet. Each name with a page links to it.</p>
    ${shown.map((p) => archivePlace(p, many, ctx))}
  </div>`;
}

function archivePlace(p: ArchivePlace, heading: boolean, ctx: Pick<RenderContext, 'base'>): SafeHtml {
  return html`${heading ? html`<h3 class="h-small">${externalLink(p.url, p.name)} <span class="muted">(${formatCount(p.count)} ${p.count === 1 ? 'line' : 'lines'})</span></h3>` : html`<p class="fine roster-link">${externalLink(p.url, `${p.name} at the archive`)} · ${formatCount(p.count)} ${p.count === 1 ? 'line' : 'lines'}</p>`}
    ${archiveTable(p.lines ?? [], ctx)}`;
}

/** The credit line for the station page's "Sources and credits": the archive place pages the roster came from. */
export function archiveRosterCredit(r: Pick<StationRecord, 'archive_roster'>, ctx: Pick<RenderContext, 'sources'>): SafeHtml | null {
  const ar = r.archive_roster;
  if (!ar?.places?.length) return null;
  const info = ctx.sources.get('uslhs');
  return html`<h3 class="h-small" id="archive-roster-source">Keepers roster</h3>
    <p class="fine">${ARCHIVE_SOURCE_LINE} Place record${ar.places.length > 1 ? 's' : ''}: ${ar.places.map((p, i) => html`${i ? ', ' : ''}${externalLink(p.url, p.name)}`)}. ${info?.credit ?? ''} Facts only (names, roles, years): the archive’s text is not copied.</p>`;
}

/* ---------- A person's page ---------- */

function distinctPlaces(p: PersonRecord): string[] {
  const out: string[] = [];
  for (const s of p.stints) {
    const n = s.station_name || s.place_name;
    if (n && !out.includes(n)) out.push(n);
  }
  return out;
}

function listWords(items: string[]): string {
  if (items.length <= 1) return items[0] ?? '';
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`;
}

/** The first and last year anywhere in a person's stints. */
export function careerYears(p: Pick<PersonRecord, 'stints'>): [number | null, number | null] {
  const ys = p.stints.flatMap((s) => [yearOf(s.from), yearOf(s.to)]).filter((y): y is number => y !== null);
  return ys.length ? [Math.min(...ys), Math.max(...ys)] : [null, null];
}

/** "Listed at 3 stations in Maine and New Hampshire, 1861–1878." */
export function personSummary(p: PersonRecord): string {
  const places = distinctPlaces(p);
  const regions = [...new Set(p.stints.map((s) => s.region).filter((r): r is string => !!r))].map((c) => regionName(c) || c);
  const [y0, y1] = careerYears(p);
  const years = yearsText(y0, y1);
  const where = places.length === 1 ? places[0]! : `${places.length} places`;
  const inRegions = regions.length ? ` in ${listWords(regions)}` : '';
  return `Listed at ${where}${places.length === 1 ? '' : inRegions}${places.length === 1 && regions.length ? ` (${listWords(regions)})` : ''}${years ? `, ${years}` : ''}.`;
}

function stationCell(s: PersonStint, ctx: Pick<RenderContext, 'base'>): SafeHtml {
  const region = s.region ? regionName(s.region) || s.region : null;
  if (s.station && isStationId(s.station)) {
    return html`<a href="${ctx.base}s/${s.station}/">${s.station_name || s.station}</a>${region ? html`<span class="sub">${region}</span>` : ''}`;
  }
  const name = s.place_name || s.station_name || 'A place the archive lists';
  return html`${s.place_url ? externalLink(s.place_url, name) : name}${region ? html`<span class="sub">${region}</span>` : ''}<span class="sub">Not linked to a station page</span>`;
}

function sourceCell(s: PersonStint, ctx: Pick<RenderContext, 'base'>): SafeHtml {
  if (s.src === 'research') {
    const at = s.via || s.station;
    const nums = (s.cite ?? []).filter((n) => Number.isInteger(n));
    const cites = nums.length
      ? html`${nums.map((n, i) => html`${i ? ', ' : ''}${at && isStationId(at) ? html`<a href="${ctx.base}s/${at}/#${researchSourceId(n)}" aria-label="Source ${n}">[${n}]</a>` : html`[${n}]`}`)}`
      : '';
    return html`<span class="tag tag-checked">Checked</span> Fresnel research ${cites}`;
  }
  return html`<span class="tag tag-unchecked">Archive</span> ${s.place_url ? externalLink(s.place_url, s.place_name || 'archive record') : 'U.S. Lighthouse Society archive'}`;
}

function stintOrder(a: PersonStint, b: PersonStint): number {
  const ya = yearOf(a.from) ?? yearOf(a.to) ?? Infinity;
  const yb = yearOf(b.from) ?? yearOf(b.to) ?? Infinity;
  return ya - yb;
}

export function stintsTable(p: PersonRecord, ctx: Pick<RenderContext, 'base'>): SafeHtml {
  const rows = [...p.stints].sort(stintOrder);
  return html`<div class="table-wrap">
    <table class="keepers keepers-stints">
      <caption class="visually-hidden">Where ${p.name} is listed, in order of service</caption>
      <thead><tr><th scope="col">Station</th><th scope="col">Role</th><th scope="col">Years</th><th scope="col">Source</th></tr></thead>
      <tbody>${rows.map(
        (s) => html`<tr>
          <th scope="row" data-label="Station"><span class="cell">${stationCell(s, ctx)}</span></th>
          <td data-label="Role"><span class="cell">${roleLabel(s.role, s.role_raw) || html`<span class="muted">Not given</span>`}${s.note ? html`<span class="sub">${s.note}</span>` : ''}</span></td>
          <td data-label="Years" class="years">${stintYears(s)}</td>
          <td data-label="Source" class="cites"><span class="cell">${sourceCell(s, ctx)}</span></td>
        </tr>`,
      )}</tbody>
    </table>
  </div>`;
}

function possiblySection(p: PersonRecord, ctx: Pick<RenderContext, 'base'>): SafeHtml | null {
  const list = (p.possibly ?? []).filter((o) => o && isPersonId(o.id));
  if (!list.length) return null;
  return html`<p>The archive keeps ${list.length === 1 ? 'another record' : 'other records'} under this name, and the years and places fit one career. Nothing connects ${list.length === 1 ? 'it' : 'them'} to this one, so Fresnel keeps the pages apart and does not merge their stints.</p>
    <ul class="possibly">${list.map(
      (o) => html`<li><span class="p-lead">Possibly the same person as</span> <a href="${personPath(o.id, ctx)}">${o.name}</a>${yearsText(o.from, o.to) || o.places.length ? html`<span class="sub">${[yearsText(o.from, o.to), listWords(o.places)].filter(Boolean).join(' · ')}</span>` : ''}</li>`,
    )}</ul>`;
}

function historiesSection(p: PersonRecord, ctx: Pick<RenderContext, 'base'>): SafeHtml | null {
  const seen = new Set<string>();
  const items: SafeHtml[] = [];
  for (const s of [...p.stints].sort(stintOrder)) {
    if (!s.story || !s.station || seen.has(s.station) || !isStationId(s.station)) continue;
    seen.add(s.station);
    const name = s.station_name || s.station;
    items.push(
      html`<li><a href="${ctx.base}s/${s.station}/#history">The history of ${name}</a>${s.mentioned ? html`<span class="sub">The history mentions the name “${p.name}”</span>` : html`<span class="sub">The station where ${p.name} is listed; the history does not use the name</span>`}</li>`,
    );
  }
  if (!items.length) return null;
  return html`<ul class="links histories">${items}</ul>`;
}

export function personEditUrl(p: Pick<PersonRecord, 'id' | 'name' | 'stints'>, ctx: Pick<RenderContext, 'repo' | 'siteUrl'>): string {
  const first = p.stints.find((s) => s.station) ?? p.stints[0];
  const page = personUrl(p.id, ctx);
  const q = new URLSearchParams({
    template: 'edit.yml',
    title: `Edit: keeper ${p.name}`,
    station_id: first?.station ?? '',
    station_name: first?.station_name || first?.place_name || p.name,
    page_url: page,
    body: `Keeper: ${p.name}\nPage: ${page}\n\nWhat is wrong or missing, what is right, and how do you know?\n`,
  });
  return `https://github.com/${ctx.repo}/issues/new?${q.toString()}`;
}

export function renderPersonMain(p: PersonRecord, ctx: RenderContext): SafeHtml {
  const poss = possiblySection(p, ctx);
  const hist = historiesSection(p, ctx);
  const info = ctx.sources.get('uslhs');
  const research = p.stints.some((s) => s.src === 'research');
  const sections: { id: string; title: string; body: SafeHtml | null }[] = [
    {
      id: 'service',
      title: 'Where they served',
      body: html`${stintsTable(p, ctx)}
        ${p.check === 'far_overlap' ? html`<p class="notice tone-caution" role="note">${INFO}<span>Two of these stints overlap in time at places far apart. The archive files them under one record, so this page does too, but the record may hold more than one person.</span></p>` : ''}
        <p class="fine">Years are as the source prints them. “At least” marks a stretch the archive documents, not always the whole term.</p>`,
    },
    { id: 'possibly', title: 'Possibly the same person', body: poss },
    { id: 'histories', title: 'In the histories', body: hist },
    {
      id: 'sources',
      title: 'Sources and credits',
      body: html`<p>${archiveSentence()} ${p.stints.length > 1 ? 'This page puts the stints together only because the archive files them under one person record' : 'The archive keeps one record for this person'}${p.archive && safeUrl(p.archive) ? html`: ${externalLink(p.archive, 'the archive’s page for this person')}` : ''}. Two records with the same name are never joined.</p>
        ${research ? html`<p>Lines marked <span class="tag tag-checked">Checked</span> come from Fresnel’s own research, each with the sources listed on that station’s page.</p>` : ''}
        <p class="fine">${info?.credit ?? ARCHIVE_NAME}. Facts only (names, roles, years, places); the archive’s text is not copied. See <a href="${keepersPath(ctx)}#where">where the names come from and who is left out</a>, and <a href="${ctx.base}credits/">all sources and licences</a>.</p>`,
    },
  ];
  const shown = sections.filter((s): s is { id: string; title: string; body: SafeHtml } => !!s.body);
  return html`
  <nav class="crumbs" aria-label="Breadcrumb"><ol>
    <li><a href="${ctx.base}">Map</a></li>
    <li><a href="${keepersPath(ctx)}">Keepers</a></li>
    <li><span aria-current="page">${p.name}</span></li>
  </ol></nav>
  <header class="s-head p-head">
    <p class="eyebrow">Keepers index</p>
    <h1>${p.name}</h1>
    <p class="p-summary">${personSummary(p)}</p>
    <nav class="jump" aria-label="On this page"><ul>${shown.map((s) => html`<li><a href="#${s.id}">${s.title}</a></li>`)}</ul></nav>
  </header>
  <div class="p-main">${shown.map((s) => html`<section class="s-section" id="${s.id}" aria-labelledby="${s.id}-h"><h2 id="${s.id}-h">${s.title}</h2>${s.body}</section>`)}
    <p><a class="btn" href="${personEditUrl(p, ctx)}" rel="noopener">Suggest a correction<span class="visually-hidden"> (opens GitHub)</span></a></p>
  </div>`;
}

export function renderPersonHead(p: PersonRecord, ctx: RenderContext): SafeHtml {
  const places = distinctPlaces(p);
  const title = `${p.name}: listed at ${places.length === 1 ? places[0] : `${places.length} places`} · Fresnel`;
  const desc = `${personSummary(p)} Names, roles and years from the U.S. Lighthouse Society’s Digital Archive, from the National Archives’ keeper registers.`;
  const url = personUrl(p.id, ctx);
  return html`<title>${title}</title>
    <meta name="description" content="${desc}">
    <link rel="canonical" href="${url}">
    ${p.fixture ? html`<meta name="robots" content="noindex">` : ''}
    <meta property="og:type" content="profile">
    <meta property="og:site_name" content="Fresnel">
    <meta property="og:title" content="${p.name}">
    <meta property="og:description" content="${desc}">
    <meta property="og:url" content="${url}">`;
}

/* ---------- /keepers/ ---------- */

export function renderKeepersHead(ctx: RenderContext): SafeHtml {
  const desc = 'Search the keepers, assistants and crews of the lighthouses and life-saving stations of the United States, with every station each one served. Names, roles and years from the U.S. Lighthouse Society’s Digital Archive.';
  return html`<title>Keepers: the people who kept the lights · Fresnel</title>
    <meta name="description" content="${desc}">
    <link rel="canonical" href="${ctx.siteUrl}keepers/">`;
}

/** The index page's body: the explanation and the search form's frame. The script fills the results. */
export function renderKeepersMain(m: KeeperManifest, ctx: RenderContext): SafeHtml {
  const letters = Object.entries(m.letters);
  const roleLabelOf = (id: string) => capitalise(id);
  return html`
  <p class="eyebrow">Keepers</p>
  <h1>The people who kept the lights</h1>
  <p class="lede">${formatCount(m.total)} keepers, assistants and crew of the lighthouses, lightships and life-saving stations of the United States. Each has a page that lists every station the register puts them at, with the years.</p>
  <p class="counts-line">${formatCount(m.total)} people · ${formatCount(m.multi)} listed at more than one station · ${formatCount(m.stations)} stations</p>

  <section id="find" aria-labelledby="find-h" class="k-find">
    <h2 id="find-h">Find a keeper</h2>
    <form class="k-form" data-keepers-form role="search" hidden>
      <div class="k-field k-field-wide"><label for="k-q">Name</label><input id="k-q" name="q" type="search" autocomplete="off" spellcheck="false" placeholder="A surname, or first and last name"></div>
      <div class="k-field"><label for="k-state">State or territory</label><select id="k-state" name="state"><option value="">Any</option>${m.regions.map((r) => html`<option value="${r.code}">${r.name} (${formatCount(r.n)})</option>`)}</select></div>
      <div class="k-field"><label for="k-role">Role</label><select id="k-role" name="role"><option value="">Any</option>${m.roles.map((r) => html`<option value="${r.id}">${roleLabelOf(r.id)} (${formatCount(r.n)})</option>`)}</select></div>
      <div class="k-field k-field-wide"><label for="k-station">Station</label><input id="k-station" name="station" type="text" list="k-station-list" autocomplete="off" placeholder="Start typing a station’s name"><datalist id="k-station-list"></datalist></div>
      <div class="k-actions"><button type="button" class="btn btn-quiet" data-reset>Clear</button></div>
    </form>
    <noscript><p class="notice tone-caution" role="note">${INFO}<span>The search needs JavaScript. Without it, every station page lists its keepers, and each name with a page links to it.</span></p></noscript>
    <nav class="k-letters" aria-label="Browse by the first letter of the surname" data-letters hidden><ul>${letters.map(([l, n]) => html`<li><a href="?l=${encodeURIComponent(l)}" data-letter="${l}">${l}<span class="visually-hidden"> surnames</span><span class="k-n">${formatCount(n)}</span></a></li>`)}</ul></nav>
    <p class="k-status" role="status" aria-live="polite" data-status hidden>Choose a letter, or type a name, to see keepers.</p>
    <ol class="k-list" data-list aria-label="Keepers found"></ol>
    <p><button type="button" class="btn" data-more hidden>Show more</button></p>
    <p class="fine" data-everywhere hidden>A single word searches surnames that begin with it. <button type="button" class="linklike" data-search-all>Search first names too</button> (this reads the whole index).</p>
  </section>

  <section id="where" aria-labelledby="where-h">
    <h2 id="where-h">Where the names come from, and who is left out</h2>
    <p>${archiveSentence()} The archive gives each person one record, and a record may list service at many stations. A person’s page is that record: <strong>two people are never joined because their names match</strong>. Where two records share a name and their years and places fit one career, each page says “possibly the same person as…” and nothing more. Fresnel’s own research can add a stint to a person only when it names the same archive record, or cites a source that connects them.</p>
    <p><strong>People who may be alive have no page.</strong> Anyone whose recorded service begins in 1950 or later or ends after 1960, or whose record carries no year at all, is left out of this index${m.withheld ? html` (${formatCount(m.withheld)} people)` : ''}. They still appear, exactly as the archive prints them (name, role, years), in the roster of the station where they served.</p>
    <p><strong>The United States only, so far.</strong> The archive covers the United States, so this index has no Canadian keepers yet. Canadian keepers will come from the researched histories of the stations, each line with its source.</p>
    <p>Rosters from the archive are marked “Not yet checked”: they are transcriptions of registers, not research. A station whose roster has been researched shows that one instead, marked “Checked”, with a source on every line. Facts only (names, roles, years, places) are taken from the archive; its text is not copied. <a href="${ctx.base}credits/">All sources and licences</a>.</p>
  </section>`;
}

