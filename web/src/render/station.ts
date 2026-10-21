/**
 * The station page and the map's side panel. Pure functions returning escaped HTML, used by
 * scripts/prerender.ts at build time (one static page per station) and by the map in the
 * browser, so both say the same thing in the same words.
 *
 * The page is built from SECTIONS, an ordered list: practical first (visit, climb, stay), then
 * the facts, the timeline, the history and its keepers, photos, disagreements, related stations
 * and the sources. A section that has nothing to say returns null and is left out (and out of
 * the "On this page" links). A new section is one entry in the list.
 */
import { formatCoords, formatDate, distanceFor, distanceMetres, lengthFor, nauticalMiles, plainCoords, yesNo } from '../lib/format.ts';
import { html, isSafeStoryHtml, raw, safeUrl, type SafeHtml } from '../lib/html.ts';
import { accessLabels, isProminent } from '../lib/access.ts';
import { parseCharacteristic, describeCharacteristic } from '../lib/characteristic.ts';
import { MARKS, MARK_LABELS } from '../lib/checklist.ts';
import { placeLine, regionName, regionWithCountry, stationCountry } from '../lib/regions.ts';
import { isStationId } from '../lib/station-id.ts';
import type { Conflict, StationProps, StationRecord, Structure } from '../lib/types.ts';
import {
  ATON,
  LENS_ORDER,
  LENS_STATUS,
  LENS_TYPE,
  MATERIAL,
  OWNERSHIP,
  REGISTER_NAMES,
  RELATION,
  SETTING,
  STAFFING,
  STAY_TYPE,
  STRUCTURE_ROLE,
  STRUCTURE_STATUS,
  STRUCTURE_TYPE,
  hasLight,
  kindWording,
  lookup,
  statusWording,
  verificationWording,
} from '../lib/vocab.ts';
import {
  EXT,
  INFO,
  WARN,
  accessBadge,
  accessNotice,
  editIssueUrl,
  externalLink,
  mapLink,
  stationPath,
  stationUrl,
  statusBadge,
  statusIcon,
  takedownIssueUrl,
  unverifiedBadge,
  type RenderContext,
} from './common.ts';
import { keepersTable, researchSourcesList } from './keepers.ts';
import { renderTimeline } from './timeline.ts';

export type { RenderContext } from './common.ts';

/* ---------- Sources: short names and links ---------- */

const SHORT_SOURCE: Record<string, string> = {
  wikidata: 'Wikidata',
  osm: 'OpenStreetMap',
  enc: 'NOAA charts',
  uscg: 'USCG Light List',
  ccg: 'Canadian List of Lights',
  nrhp: 'National Register',
  research: 'Fresnel research',
};

export function sourceShortName(id: string | null | undefined, ctx: Pick<RenderContext, 'sources'>): string {
  if (!id) return 'unknown source';
  return SHORT_SOURCE[id] ?? ctx.sources.get(id)?.title ?? id;
}

function sourceRef(from: string | null | undefined, r: StationRecord, ctx: RenderContext): SafeHtml | string {
  if (!from) return '';
  const listed = (r.sources ?? []).some((s) => s.source === from);
  return html`<span class="tl-src">Source: ${listed ? html`<a href="#src-${from}">${sourceShortName(from, ctx)}</a>` : sourceShortName(from, ctx)}</span>`;
}

/* ---------- Header pieces ---------- */

export function kindPlace(r: Pick<StationRecord, 'kind' | 'county' | 'region' | 'country'>): string {
  return `${kindWording(r.kind).label} · ${placeLine(r)}`;
}

/** True when a station's structure is gone or broken, so there is nothing to climb or enter. */
function isGone(status: string): boolean {
  return status === 'lost' || status === 'ruins';
}

/**
 * The badges under the name. On a page, an access label that also gets its own notice right
 * below (`withProminent: false`) is left out of the badges, so it is said once; the map panel
 * keeps them all as badges.
 */
export function badges(r: StationRecord, opts: { withProminent?: boolean } = {}): SafeHtml {
  const labels = accessLabels(r).filter((l) => opts.withProminent !== false || !isProminent(l));
  const ver = verificationWording(r.verification);
  return html`<ul class="badges" aria-label="Status and access">
    ${statusBadge(r)}
    ${r.verification === 'unverified' ? unverifiedBadge() : html`<li class="badge badge-ver ver-${r.verification}" title="${ver.meaning}"><span>${ver.label}</span></li>`}
    ${labels.map((l) => accessBadge(l))}
    ${r.fixture ? html`<li class="badge badge-fixture"><span>Sample entry</span></li>` : ''}
  </ul>`;
}

export function unverifiedNotice(r: StationRecord, ctx: RenderContext): SafeHtml {
  if (r.verification !== 'unverified') return html``;
  return html`<div class="notice tone-caution" role="note">${WARN}<div>
    <p class="notice-title">Unverified entry</p>
    <p>No two independent sources agree on this entry yet, and nobody has checked it, so details may be wrong. If you know better, <a href="${editIssueUrl(r, ctx)}">suggest an edit</a>.</p>
  </div></div>`;
}

/** "Lost: Gone… Swept away by ice in 1918." under the title, for every status but a plain active light. */
export function statusLine(r: StationRecord): SafeHtml {
  const st = statusWording(r.status, r.kind);
  if (r.status === 'active' && !r.status_note) return html``;
  return html`<p class="status-meaning">${statusIcon(r.status, r.kind, 18)} <span><strong>${st.label}.</strong> ${st.meaning}${r.status_note ? html` ${r.status_note}` : ''}</span></p>`;
}

/* ---------- Visit, climb & stay ---------- */

function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return 'the provider’s site';
  }
}

function stayBlock(r: StationRecord): SafeHtml {
  const s = r.stay;
  if (!s || typeof s !== 'object' || !Object.values(s).some((v) => v !== null && v !== undefined && v !== '')) {
    return html`<p class="muted">No overnight stays are recorded here.</p>`;
  }
  const type = lookup(STAY_TYPE, s.type) ?? 'Somewhere to stay';
  const url = safeUrl(s.url);
  const rows: [string, unknown][] = [
    ['Run by', s.provider],
    ['Season', s.season],
  ];
  const shown = rows.filter(([, v]) => v);
  return html`<div class="stay-card">
    <p class="stay-type"><strong>${type}.</strong> ${s.note ?? ''}</p>
    ${shown.length ? html`<dl class="kv kv-stay">${shown.map(([k, v]) => html`<div><dt>${k}</dt><dd>${v}</dd></div>`)}</dl>` : ''}
    ${url ? html`<p class="stay-link"><a class="btn btn-primary" href="${url}" rel="noopener">See it on ${hostOf(url)}${EXT}<span class="visually-hidden"> (opens another site)</span></a></p>` : ''}
    <p class="fine">${s.checked ? `Checked ${formatDate(s.checked)}. ` : ''}Seasons, prices and rules change: confirm with the provider before you plan a stay.</p>
  </div>`;
}

export function visitSection(r: StationRecord): SafeHtml {
  const v = r.visit ?? {};
  const labels = accessLabels(r);
  const gone = isGone(r.status);
  let lead: SafeHtml | string = '';
  if (r.status === 'lost') lead = html`<p class="lede"><strong>Lost: only the site is left.</strong> There is nothing standing to visit or climb${r.access?.level === 'public' ? ', though you may be able to visit the place where it stood' : ''}.</p>`;
  else if (r.status === 'ruins') lead = html`<p class="lede"><strong>Ruins only.</strong> There is no tower to climb.</p>`;
  else if (r.status === 'relocated') lead = html`<p class="lede"><strong>Moved.</strong> The structure now stands somewhere else; see the timeline and related stations for where.</p>`;
  else if (r.kind === 'lightship_station') lead = html`<p class="lede"><strong>A place at sea.</strong> Lightships were anchored here; there is nothing to visit at the spot itself.</p>`;

  const rows: [string, unknown][] = [];
  rows.push(['Getting there', v.boat_only === true ? html`<strong>By boat only.</strong>` : v.boat_only === false ? 'Reachable without a boat' : 'Not recorded']);
  if (!gone) rows.push(['Grounds open to visitors?', yesNo(v.grounds_open, 'Yes', 'No')]);
  if (!gone && hasLight(r.kind) && r.kind !== 'lightship_station') rows.push([r.kind === 'lightship' ? 'Can you go aboard?' : 'Can you climb it?', yesNo(v.climbable, 'Yes', 'No')]);
  if (!gone && v.museum !== null && v.museum !== undefined) rows.push(['Museum', yesNo(v.museum, 'Yes', 'No')]);
  if (v.tours) rows.push(['Tours', v.tours]);
  if (v.passport_stamp !== null && v.passport_stamp !== undefined) rows.push(['Passport stamp', yesNo(v.passport_stamp, 'Yes', 'No')]);
  if (r.staffing?.status && r.staffing.status !== 'unknown') {
    const s = STAFFING[r.staffing.status] ?? r.staffing.status;
    rows.push(['Keepers', r.staffing.as_of ? `${s} (as of ${r.staffing.as_of})` : s]);
  }
  if (v.note) rows.push(['Note', v.note]);

  const prominent = labels.filter(isProminent);
  const plain = labels.filter((l) => !isProminent(l));
  return html`${lead}
    <h3 class="h-small">Access</h3>
    ${prominent.length ? html`<p class="access-line">${prominent.map((l, i) => html`${i ? ' · ' : ''}<strong>${l.label}</strong>`)}. See the ${prominent.length > 1 ? 'warnings' : 'warning'} at the top of this page.</p>` : ''}
    ${plain.map((l) => html`<p class="access-line tone-${l.tone}"><strong>${l.label}.</strong> ${l.meaning}${!prominent.length && r.access?.note ? html` ${r.access.note}` : ''}</p>`)}
    <dl class="kv">${rows.map(([k, val]) => html`<div><dt>${k}</dt><dd>${val}</dd></div>`)}</dl>
    <h3 class="h-small">Stay</h3>
    ${stayBlock(r)}`;
}

/* ---------- Facts ---------- */

function hasConflict(r: StationRecord, ...fields: string[]): boolean {
  return (r.conflicts ?? []).some((c) => fields.includes(c.field));
}

function disagree(r: StationRecord, ...fields: string[]): SafeHtml | string {
  return hasConflict(r, ...fields) ? html` <a class="disagree" href="#conflicts">sources disagree</a>` : '';
}

/** The light's characteristic as charted, with its plain reading (or the raw string when it is in a form we do not read). */
export function characteristicHtml(raw: string | null | undefined, opts: { lost?: boolean } = {}): SafeHtml | null {
  if (!raw || !raw.trim()) return null;
  const c = parseCharacteristic(raw);
  const asWas = opts.lost ? html`<span class="sub">As last recorded.</span>` : '';
  if (!c) return html`<code class="char">${raw.trim()}</code><span class="sub">As the source writes it.</span>${asWas}`;
  const reading = describeCharacteristic(c);
  return html`<span class="char-read"><code class="char">${c.raw}</code>: ${reading.charAt(0).toLowerCase() + reading.slice(1)}.</span>${asWas}`;
}

function lensText(r: StationRecord): SafeHtml | null {
  const l = r.light?.lens;
  if (!l || !Object.values(l).some(Boolean)) return null;
  const type = lookup(LENS_TYPE, l.type);
  const order = l.order ? LENS_ORDER[l.order] ?? `Order ${l.order}` : null;
  const what = [order && type === 'Fresnel lens' ? `${order.split(' (')[0]} Fresnel lens` : type, order && type !== 'Fresnel lens' ? order : null].filter(Boolean).join(', ');
  const status = lookup(LENS_STATUS, l.status);
  const where = l.where ? (l.status === 'on_display' ? `${status}: ${l.where}` : `${status ?? ''}${status ? '. ' : ''}${l.where}`) : status;
  return html`${what || 'Lens'}${where ? html`<span class="sub">${where}</span>` : ''}`;
}

export function lightRows(r: StationRecord): [string, unknown][] {
  const L = r.light;
  if (!L) return [];
  const country = stationCountry(r);
  const rows: [string, unknown][] = [];
  const ch = characteristicHtml(L.characteristic, { lost: r.status !== 'active' });
  if (ch) rows.push(['Light', html`${ch}${disagree(r, 'light.characteristic')}`]);
  if (typeof L.first_lit === 'number') rows.push(['First lit', html`${L.first_lit}${disagree(r, 'light.first_lit')}`]);
  if (typeof L.deactivated === 'number') rows.push(['Light went out', html`${L.deactivated}${disagree(r, 'light.deactivated')}`]);
  const fh = lengthFor(country, L.focal_height_m);
  if (fh) rows.push(['Focal height', html`${fh}<span class="sub">The height of the light above the water.</span>${disagree(r, 'light.focal_height_m')}`]);
  const range = nauticalMiles(L.range_nm);
  if (range) rows.push(['Range', html`${range}<span class="sub">How far out it ${r.status === 'active' ? 'can' : 'could'} be seen in clear weather, as charted.</span>${disagree(r, 'light.range_nm')}`]);
  const lens = lensText(r);
  if (lens) rows.push(['Lens', lens]);
  if (L.fog_signal) rows.push(['Fog signal', L.fog_signal.replace(/^./, (c) => c.toUpperCase())]);
  return rows;
}

function structureLine(s: Structure, r: StationRecord): SafeHtml {
  const country = stationCountry(r);
  const role = lookup(STRUCTURE_ROLE, s.role);
  const title = s.name ? (role && role !== s.name ? `${s.name} (${role.toLowerCase()})` : s.name) : role ?? 'Structure';
  const type = s.type && s.type !== 'other' ? STRUCTURE_TYPE[s.type] : null;
  const bits: (string | SafeHtml)[] = [];
  if (type) bits.push(html`<abbr title="${type.meaning}">${type.label}</abbr>`);
  const material = lookup(MATERIAL, s.material);
  if (material) bits.push(bits.length ? material.toLowerCase() : material);
  if (typeof s.built === 'number') bits.push(`built ${s.built}`);
  const h = lengthFor(country, s.height_m);
  if (h) bits.push(`${h} tall`);
  const status = s.status ? STRUCTURE_STATUS[s.status] ?? s.status : null;
  const apart = s.location && typeof s.location.lat === 'number' && typeof s.location.lon === 'number' ? s.location : null;
  const away = apart ? distanceMetres(r.location.lat, r.location.lon, apart.lat, apart.lon) : null;
  return html`<li class="structure">
    <span class="st-head"><strong>${title}</strong>${status ? html` <span class="st-status st-${s.status}">${status}</span>` : ''}</span>
    ${bits.length ? html`<span class="st-facts">${bits.map((b, i) => html`${i ? ' · ' : ''}${b}`)}</span>` : ''}
    ${apart ? html`<span class="sub">Stands apart from the station’s pin: <span class="coords" data-coords="${plainCoords(apart.lat, apart.lon)}">${formatCoords(apart.lat, apart.lon)}</span>${away !== null && away >= 1 ? `, ${distanceFor(country, away)} away` : ''}.</span>` : ''}
    ${s.note ? html`<span class="sub">${s.note}</span>` : ''}
  </li>`;
}

export function structuresList(r: StationRecord): SafeHtml | null {
  const list = (r.structures ?? []).filter((s) => s && typeof s === 'object');
  if (!list.length) return null;
  return html`<ul class="structures">${list.map((s) => structureLine(s, r))}</ul>`;
}

function registersList(r: StationRecord): SafeHtml | null {
  const regs = (r.registers ?? []).filter((g) => g && g.register);
  if (!regs.length) return null;
  return html`<ul class="plain">${regs.map((g) => {
    const name = REGISTER_NAMES[g.register] ?? g.register;
    const label = html`${name}${g.number ? html` <span class="reg-num">${g.number}</span>` : ''}`;
    const url = safeUrl(g.url);
    return html`<li>${url ? html`<a href="${url}" rel="noopener">${label}</a>` : label}</li>`;
  })}</ul>`;
}

function atonList(r: StationRecord): SafeHtml | null {
  const a = r.aton ?? {};
  const rows = (Object.keys(ATON) as (keyof typeof a)[]).filter((k) => a[k]).map((k) => [ATON[k]!, a[k]!] as const);
  if (!rows.length) return null;
  return html`<ul class="plain">${rows.map(([w, v]) => html`<li><abbr title="${w.meaning}">${w.label}</abbr>: <code>${v}</code></li>`)}</ul>`;
}

export function factsSection(r: StationRecord): SafeHtml {
  const kind = kindWording(r.kind);
  const ver = verificationWording(r.verification);
  const light = lightRows(r);
  const station: [string, unknown][] = [
    ['Kind', html`${kind.label}${kind.meaning ? html`<span class="sub">${kind.meaning}</span>` : ''}${disagree(r, 'kind')}`],
    ['Status', html`<span class="with-icon">${statusIcon(r.status, r.kind, 18)}${statusWording(r.status, r.kind).label}</span>${disagree(r, 'status')}`],
  ];
  const setting = lookup(SETTING, r.setting);
  if (setting || r.water) station.push(['Setting', [setting, r.water].filter(Boolean).join(', ')]);
  station.push(['Location', placeLine(r)]);
  station.push(['Coordinates', html`<span class="coords" data-coords="${plainCoords(r.location.lat, r.location.lon)}">${formatCoords(r.location.lat, r.location.lon)}</span>${r.location.precision && r.location.precision !== 'exact' ? ` (${r.location.precision})` : ''}${disagree(r, 'location')}`]);
  if (r.agency) station.push(['Run by', r.agency]);
  const own = lookup(OWNERSHIP, r.ownership);
  if (own && r.ownership !== 'unknown') station.push(['Owner', own]);
  const structures = structuresList(r);
  const regs = registersList(r);
  const aton = atonList(r);
  const noLight = !hasLight(r.kind);
  return html`
    ${light.length
      ? html`<h3 class="h-small">The light</h3><dl class="kv kv-facts">${light.map(([k, v]) => html`<div><dt>${k}</dt><dd>${v}</dd></div>`)}</dl>`
      : noLight ? '' : html`<h3 class="h-small">The light</h3><p class="muted">No details of the light are recorded yet.</p>`}
    <h3 class="h-small">The station</h3>
    <dl class="kv kv-facts">${station.map(([k, v]) => html`<div><dt>${k}</dt><dd>${v}</dd></div>`)}</dl>
    <h3 class="h-small">Structures</h3>
    ${structures ?? html`<p class="muted">No structures are recorded yet.</p>`}
    ${regs ? html`<h3 class="h-small">Heritage registers</h3>${regs}` : ''}
    ${aton ? html`<h3 class="h-small">Light list numbers</h3>${aton}` : ''}
    <h3 class="h-small">This entry</h3>
    <dl class="kv kv-facts">
      <div><dt>Checked?</dt><dd>${ver.label}<span class="sub">${ver.meaning}${r.updated ? ` Updated ${formatDate(r.updated)}.` : ''}</span></dd></div>
      <div><dt>Fresnel id</dt><dd><code>${r.id}</code></dd></div>
    </dl>`;
}

/* ---------- Timeline ---------- */

export function timelineSection(r: StationRecord, ctx: RenderContext): SafeHtml {
  return renderTimeline(r, (from) => sourceRef(from, r, ctx));
}

/* ---------- History ---------- */

/** "Researched 21 Oct 2026, fact-checked." above a researched story. */
export function researchStamp(r: StationRecord): SafeHtml | string {
  const s = r.research;
  if (!s?.researched) return '';
  const when = formatDate(s.researched) ?? s.researched;
  if (s.verdict === 'pass' || s.verdict === 'fixed') return html`<p class="research-stamp">Researched ${when}, fact-checked${s.checked ? ` ${formatDate(s.checked)}` : ''}.</p>`;
  if (s.verdict === 'fail') return html`<p class="research-stamp">Researched ${when}. The fact-check found problems; a revised version is on its way.</p>`;
  return html`<p class="research-stamp">Researched ${when}. Not yet fact-checked.</p>`;
}

const CHAPTER_ID = /^s-[a-z0-9-]+$/;

export function chapterList(r: StationRecord): SafeHtml | string {
  const chapters = (r.chapters ?? []).filter((c) => c && CHAPTER_ID.test(c.id) && c.title);
  if (chapters.length < 2) return '';
  return html`<nav class="chapters" aria-labelledby="chapters-h"><h3 id="chapters-h" class="h-small">In this history</h3>
    <ol>${chapters.map((c) => html`<li><a href="#${c.id}">${c.title}</a></li>`)}</ol></nav>`;
}

/**
 * One or two plain sentences built only from the record's fields, for a station with no
 * written history yet. Never prose beyond what the fields say.
 */
export function recordSummary(r: StationRecord): string {
  const kind = kindWording(r.kind).label.toLowerCase();
  const was = isGone(r.status);
  const article = /^[aeiou]/.test(kind) ? 'an' : 'a';
  let s = `${r.name} ${was ? 'was' : 'is'} ${article} ${kind} in ${placeLine(r)}.`;
  const L = r.light;
  const lit = typeof L?.first_lit === 'number' ? L.first_lit : null;
  const out = typeof L?.deactivated === 'number' ? L.deactivated : null;
  if (lit && out) s += ` Its light was first lit in ${lit} and went out in ${out}.`;
  else if (lit) s += ` Its light was first lit in ${lit}${r.status === 'active' ? ' and still shines' : ''}.`;
  else if (out) s += ` Its light went out in ${out}.`;
  if (r.status_note) s += ` ${r.status_note.trim().replace(/([^.!?])$/, '$1.')}`;
  return s;
}

export function historySection(r: StationRecord, ctx: RenderContext): SafeHtml {
  if (r.story_html) {
    if (!isSafeStoryHtml(r.story_html)) {
      return html`<p class="notice tone-caution">This station’s history could not be shown because it contains markup we do not allow. It has been flagged for a fix.</p>`;
    }
    return html`${researchStamp(r)}${chapterList(r)}<div class="prose story">${raw(r.story_html)}</div>
      <p class="fine">Every factual sentence is footnoted. Passages about the period in general (“On most stations of the period…”) are marked as general and cited to a history of the service; they are never presented as having happened here.</p>`;
  }
  return html`<p class="no-story">No history has been written for this station yet. Histories are being researched station by station, from the Lighthouse Board and Life-Saving Service reports, keeper registers, heritage nominations and old newspapers.</p>
    <div class="record-summary"><p class="h-small">From the record, not a researched history</p><p>${recordSummary(r)}</p></div>
    <p class="muted">Know something about its history, or have a source? <a href="${editIssueUrl(r, ctx)}">Tell us</a>.</p>`;
}

/* ---------- Keepers ---------- */

export function keepersSection(r: StationRecord, ctx: RenderContext): SafeHtml {
  const table = keepersTable(r.keepers, r.research_sources);
  if (!table) {
    return html`<p class="muted">No roster of keepers has been compiled for this station yet. Know a keeper’s name and years, with a source? <a href="${editIssueUrl(r, ctx)}">Tell us</a>.</p>`;
  }
  return html`<p>Everyone the sources name as keeping this ${r.kind === 'life_saving_station' ? 'station' : 'light'}, with the role as the source gives it. Each line cites the sources listed under <a href="#research-sources">Research sources</a>.</p>${table}`;
}

/* ---------- Photos ---------- */

function isHttps(url: string | null | undefined): boolean {
  const safe = safeUrl(url);
  return !!safe && /^https:\/\//i.test(safe);
}

/**
 * Photos are not mirrored yet: each shows its thumbnail hotlinked from its source (https only,
 * since an https page cannot embed plain http), with the credit and a link to its page.
 */
export function photosSection(r: StationRecord, ctx: RenderContext): SafeHtml | null {
  const photos = (r.photos ?? []).filter((p) => p && (p.thumb_url || p.url || p.source_url));
  if (!photos.length) return null;
  return html`<div class="photos">${photos.map((p) => {
    const source = safeUrl(p.source_url);
    const shown = isHttps(p.thumb_url) ? safeUrl(p.thumb_url) : isHttps(p.url) ? safeUrl(p.url) : null;
    const full = safeUrl(p.url) ?? source;
    const credit = html`<span class="credit-line">Photo: ${p.credit ?? 'credit unknown'}${p.license ? html` · ${p.license}` : ''}${source ? html` · ${externalLink(source, 'source')}` : ''}</span>`;
    const caption = p.caption || p.year ? html`<span class="cap">${[p.caption?.replace(/[\s.]+$/, ''), p.year ? `(${p.year})` : null].filter(Boolean).join(' ')}</span>` : '';
    const alt = p.caption ? p.caption : `Photo of ${r.name}${p.year ? `, ${p.year}` : ''}`;
    return html`<figure class="photo">
      ${shown
        ? html`<a href="${full ?? shown}" rel="noopener"><img src="${shown}" alt="${alt}" loading="lazy" decoding="async" referrerpolicy="no-referrer"></a>`
        : html`<a class="photo-link" href="${full ?? '#'}" rel="noopener">View the photo at its source${EXT}</a>`}
      <figcaption>${caption}${credit}</figcaption>
    </figure>`;
  })}</div>
  <p class="fine">Photos keep their own rights and are shown with credit, loaded from where they are published. Is one of these yours? You can <a href="${takedownIssueUrl(r, ctx)}">ask for a different credit or for removal</a>.</p>`;
}

/* ---------- Conflicts ---------- */

const FIELD_WORDS: Record<string, string> = {
  location: 'the location',
  status: 'its status',
  kind: 'what kind of station it is',
  name: 'the name',
  'light.first_lit': 'the year the light was first lit',
  'light.deactivated': 'the year the light went out',
  'light.characteristic': 'the light’s pattern',
  'light.focal_height_m': 'the focal height',
  'light.range_nm': 'the range',
  built: 'the year it was built',
  height_m: 'the height',
};

function conflictValue(field: string, value: unknown, country: string): string {
  if (value && typeof value === 'object' && 'lat' in value && 'lon' in value) {
    const v = value as { lat: unknown; lon: unknown };
    if (typeof v.lat === 'number' && typeof v.lon === 'number') return formatCoords(v.lat, v.lon);
  }
  if (value === null || value === undefined || value === '') return 'no value';
  if (field === 'status' && typeof value === 'string') return statusWording(value).label;
  if (field === 'kind' && typeof value === 'string') return kindWording(value).label;
  if (typeof value === 'number' && /(_m|height)$/.test(field)) return lengthFor(country, value) ?? String(value);
  if (typeof value === 'number' && field.endsWith('range_nm')) return nauticalMiles(value) ?? String(value);
  if (typeof value === 'object') return JSON.stringify(value).slice(0, 120);
  return String(value);
}

export function conflictSentence(c: Conflict, r: StationRecord, ctx: RenderContext): SafeHtml {
  const values = (c.values ?? []).filter(Boolean);
  const country = stationCountry(r);
  const what = FIELD_WORDS[c.field] ?? `the ${c.field.replace(/^light\./, 'light’s ').replace(/_m$/, '').replace(/[._]/g, ' ')}`;
  let headline = html`Sources disagree on ${what}.`;
  if (c.field === 'location') {
    let d = typeof c.distance_m === 'number' ? c.distance_m : null;
    const pts = values.map((v) => v.value as { lat?: number; lon?: number });
    if (d === null && pts.length >= 2 && typeof pts[0]?.lat === 'number' && typeof pts[1]?.lat === 'number' && typeof pts[0]?.lon === 'number' && typeof pts[1]?.lon === 'number') {
      d = distanceMetres(pts[0].lat, pts[0].lon, pts[1].lat, pts[1].lon);
    }
    if (d !== null) headline = html`Sources disagree on the location, by ${distanceFor(country, d)}.`;
  }
  const list = values.map((v) => html`<li><span class="src">${sourceShortName(v.source, ctx)}:</span> ${conflictValue(c.field, v.value, country)}</li>`);
  const usedFrom = c.field === 'location' && r.location.from ? html`<p class="fine">The map uses the position from ${sourceShortName(r.location.from, ctx)}.</p>` : '';
  return html`<li class="conflict"><p class="conflict-head">${headline}</p>${list.length ? html`<ul class="plain">${list}</ul>` : ''}${c.note ? html`<p>${c.note}</p>` : ''}${usedFrom}</li>`;
}

export function conflictsSection(r: StationRecord, ctx: RenderContext): SafeHtml | null {
  const cs = (r.conflicts ?? []).filter((c) => c && c.field);
  if (!cs.length) return null;
  return html`<p>We show disagreements between sources instead of quietly picking one. If you know which is right, please <a href="${editIssueUrl(r, ctx)}">tell us</a>.</p>
    <ul class="conflicts">${cs.map((c) => conflictSentence(c, r, ctx))}</ul>`;
}

/* ---------- Related stations ---------- */

export function relatedSection(r: StationRecord, ctx: RenderContext): SafeHtml | null {
  const rel = (r.related ?? []).filter((x) => x && isStationId(x.id) && x.id !== r.id);
  if (!rel.length) return null;
  return html`<ul class="related">${rel.map((x) => html`<li><span class="rel-kind">${lookup(RELATION, x.relation) ?? 'Related'}:</span> <a href="${stationPath(x.id, ctx)}">${x.name || x.id}</a></li>`)}</ul>`;
}

/* ---------- Sources and credits ---------- */

const FIELD_NAMES: Record<string, string> = {
  location: 'location',
  name: 'name',
  other_names: 'other names',
  kind: 'kind',
  status: 'status',
  light: 'the light',
  structures: 'structures',
  registers: 'register numbers',
  aton: 'light list numbers',
  events: 'dates',
  county: 'county',
  access: 'access',
  visit: 'visiting details',
  stay: 'places to stay',
  staffing: 'staffing',
  photos: 'photos',
  links: 'links',
  agency: 'agency',
  ownership: 'owner',
};

export function sourcesSection(r: StationRecord, ctx: RenderContext): SafeHtml {
  // One entry per source, with every field it gave (a source may give two records).
  const bySource = new Map<string, Set<string>>();
  for (const s of r.sources ?? []) {
    if (!s || typeof s.source !== 'string') continue;
    const set = bySource.get(s.source) ?? new Set<string>();
    for (const f of s.fields ?? []) set.add(f === 'county' && stationCountry(r) !== 'US' ? 'district' : FIELD_NAMES[f] ?? f.replace(/_/g, ' '));
    bySource.set(s.source, set);
  }
  const links = (r.links ?? []).filter((l) => l && safeUrl(l.url));
  const photos = (r.photos ?? []).filter((p) => p && (p.credit || p.source_url));
  const research = researchSourcesList(r.research_sources);
  return html`
    <h3 class="h-small" id="data-sources">Where the facts come from</h3>
    ${bySource.size
      ? html`<ol class="sources">${[...bySource].map(([id, fields]) => {
          const info = ctx.sources.get(id);
          const title = info?.title ?? id;
          return html`<li id="src-${id}">
            <span class="src-title">${info?.url ? externalLink(info.url, title) : title}</span>
            ${fields.size ? html`<span class="src-fields">Gave us: ${[...fields].join(', ')}</span>` : ''}
            <span class="credit-line">${info?.credit ?? title}${info?.license ? html` · ${info.license}` : ''}${info?.retrieved ? html` · retrieved ${formatDate(info.retrieved)}` : ''}</span>
          </li>`;
        })}</ol>`
      : html`<p class="muted">No sources recorded.</p>`}
    ${research ? html`<h3 class="h-small" id="research-sources">Research sources</h3><p class="fine">The sources the history’s research and the keepers roster cite, by number.</p>${research}` : ''}
    ${photos.length ? html`<h3 class="h-small">Photo credits</h3><ul class="plain credits-list">${photos.map((p) => html`<li>${p.caption ? html`${p.caption}: ` : ''}${p.credit ?? 'credit unknown'}${p.license ? ` (${p.license})` : ''}${safeUrl(p.source_url) ? html` · ${externalLink(p.source_url, 'source')}` : ''}</li>`)}</ul>` : ''}
    ${links.length ? html`<h3 class="h-small">More about this station elsewhere</h3><ul class="links">${links.map((l) => html`<li>${externalLink(l.url, l.label || l.url)}</li>`)}</ul>` : ''}
    <p class="fine">Fresnel takes facts (places, dates, numbers, names) from these sources, credits them here, and writes its own words. See <a href="${ctx.base}credits/">all sources and licences</a>.</p>`;
}

/* ---------- Checklist ---------- */

export function checklistButtons(id: string): SafeHtml {
  return html`<div class="checklist-buttons" data-checklist="${id}" role="group" aria-label="My checklist">
    ${MARKS.map((m) => html`<button type="button" class="chip-toggle" data-mark="${m}" aria-pressed="false" disabled><span class="tick" aria-hidden="true"></span>${MARK_LABELS[m]}</button>`)}
  </div>`;
}

/* ---------- The page ---------- */

export interface StationSection {
  id: string;
  title: string;
  /** Null: nothing to say, so the section and its link are left out. */
  render: (r: StationRecord, ctx: RenderContext) => SafeHtml | null;
}

export const SECTIONS: readonly StationSection[] = [
  { id: 'visit', title: 'Visit, climb and stay', render: (r) => visitSection(r) },
  { id: 'facts', title: 'Facts', render: (r) => factsSection(r) },
  { id: 'timeline', title: 'Timeline', render: timelineSection },
  { id: 'history', title: 'History', render: historySection },
  { id: 'keepers', title: 'Keepers', render: (r, ctx) => (r.kind === 'lightship_station' && !r.keepers?.length ? null : keepersSection(r, ctx)) },
  { id: 'photos', title: 'Photos', render: photosSection },
  { id: 'conflicts', title: 'Where sources disagree', render: conflictsSection },
  { id: 'related', title: 'Related stations', render: relatedSection },
  { id: 'sources', title: 'Sources and credits', render: sourcesSection },
];

function sectionHtml(s: StationSection, body: SafeHtml): SafeHtml {
  return html`<section class="s-section" id="${s.id}" aria-labelledby="${s.id}-h"><h2 id="${s.id}-h">${s.title}</h2>${body}</section>`;
}

export function renderStationMain(r: StationRecord, ctx: RenderContext, sections: readonly StationSection[] = SECTIONS): SafeHtml {
  const other = (r.other_names ?? []).filter((n) => typeof n === 'string' && n.trim());
  const rendered = sections.map((s) => ({ s, body: s.render(r, ctx) })).filter((x): x is { s: StationSection; body: SafeHtml } => !!x.body);
  const labels = accessLabels(r);
  const prominent = labels.filter(isProminent);
  return html`
  <nav class="crumbs" aria-label="Breadcrumb"><ol>
    <li><a href="${ctx.base}">Map</a></li>
    <li><a href="${ctx.base}?region=${r.region}">${regionName(r.region) || r.region}</a></li>
    <li><span aria-current="page">${r.name}</span></li>
  </ol></nav>
  <header class="s-head">
    <p class="eyebrow">${kindPlace(r)}</p>
    <h1>${r.name}</h1>
    ${other.length ? html`<p class="aka">Also known as ${other.join('; ')}</p>` : ''}
    ${badges(r, { withProminent: false })}
    <div class="notices">
      ${prominent.map((l, i) => accessNotice(l, i === 0 ? r.access?.note : null))}
      ${unverifiedNotice(r, ctx)}
      ${statusLine(r)}
    </div>
    <nav class="jump" aria-label="On this page"><ul>${rendered.map(({ s }) => html`<li><a href="#${s.id}">${s.title}</a></li>`)}<li><a href="#mine">My checklist</a></li></ul></nav>
  </header>
  <div class="s-grid">
    <div class="s-main">${rendered.map(({ s, body }) => sectionHtml(s, body))}</div>
    <aside class="s-rail" aria-label="Map, your checklist and corrections">
      <section class="card card-map" aria-labelledby="where-h">
        <h2 id="where-h" class="h-card">Where it is</h2>
        <p>${placeLine(r)}</p>
        <p class="coords-line"><span class="coords" data-coords="${plainCoords(r.location.lat, r.location.lon)}">${formatCoords(r.location.lat, r.location.lon)}</span></p>
        <p><a class="btn btn-primary" href="${mapLink(r, ctx)}">Show on the Fresnel map</a></p>
      </section>
      <section class="card" id="mine" aria-labelledby="mine-h">
        <h2 id="mine-h" class="h-card">My checklist</h2>
        ${checklistButtons(r.id)}
        <p class="fine" data-checklist-note>Saved only in this browser. Nothing is sent anywhere. Marking “Climbed” or “Stayed” also marks “Visited”.</p>
        <p class="fine warn-text" data-checklist-problem hidden></p>
        <p><button type="button" class="btn btn-quiet" data-open-checklist-dialog>Download or import my checklist</button></p>
        <noscript><p class="fine">Turn on JavaScript to use the checklist.</p></noscript>
      </section>
      <section class="card" aria-labelledby="edit-h">
        <h2 id="edit-h" class="h-card">Something wrong or missing?</h2>
        <p class="fine">Corrections and additions are welcome. This opens a short form on GitHub (a free account is needed) with this station already filled in.</p>
        <p><a class="btn" href="${editIssueUrl(r, ctx)}" rel="noopener">Suggest an edit${EXT}<span class="visually-hidden"> (opens GitHub)</span></a></p>
      </section>
    </aside>
  </div>`;
}

export function describeStation(r: StationRecord): string {
  const st = statusWording(r.status, r.kind).label;
  const kind = kindWording(r.kind).label.toLowerCase();
  let d = `${st}: ${kind} in ${placeLine(r)}`;
  if (typeof r.light?.first_lit === 'number') d += `, first lit ${r.light.first_lit}`;
  d += '. Visiting and access, the light, its history and keepers, with sources.';
  return d;
}

export function renderStationHead(r: StationRecord, ctx: RenderContext): SafeHtml {
  const title = `${r.name}: ${kindWording(r.kind).label.toLowerCase()} in ${regionWithCountry(r.region)} · Fresnel`;
  const desc = describeStation(r);
  const url = stationUrl(r.id, ctx);
  return html`<title>${title}</title>
    <meta name="description" content="${desc}">
    <link rel="canonical" href="${url}">
    ${r.fixture ? html`<meta name="robots" content="noindex">` : ''}
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Fresnel">
    <meta property="og:title" content="${r.name}">
    <meta property="og:description" content="${desc}">
    <meta property="og:url" content="${url}">`;
}

/* ---------- Map side panel ---------- */

export function renderPanel(r: StationRecord, ctx: RenderContext, opts: { hiddenByFilters?: boolean } = {}): SafeHtml {
  const labels = accessLabels(r);
  const prominent = labels.filter(isProminent);
  const L = r.light;
  const country = stationCountry(r);
  const rows: [string, unknown][] = [];
  const ch = characteristicHtml(L?.characteristic, { lost: r.status !== 'active' });
  if (ch) rows.push(['Light', ch]);
  const years = typeof L?.first_lit === 'number' ? (typeof L.deactivated === 'number' ? `${L.first_lit} to ${L.deactivated}` : r.status === 'active' ? `Since ${L.first_lit}` : `First lit ${L.first_lit}`) : null;
  if (years) rows.push(['Lit', years]);
  const fh = lengthFor(country, L?.focal_height_m);
  if (fh) rows.push(['Focal height', fh]);
  const range = nauticalMiles(L?.range_nm);
  if (range) rows.push(['Range', range]);
  const tower = (r.structures ?? []).find((s) => s && (s.role === 'tower' || s.role === 'front_range') && s.status === 'standing') ?? (r.structures ?? [])[0];
  if (tower) {
    const type = tower.type && STRUCTURE_TYPE[tower.type] ? STRUCTURE_TYPE[tower.type]!.label : null;
    const bits = [type, lookup(MATERIAL, tower.material), typeof tower.built === 'number' ? `built ${tower.built}` : null, lengthFor(country, tower.height_m)].filter((b): b is string => !!b).map((b, i) => (i ? b.charAt(0).toLowerCase() + b.slice(1) : b));
    if (bits.length) rows.push([lookup(STRUCTURE_ROLE, tower.role) ?? 'Structure', bits.join(', ')]);
  }
  const v = r.visit ?? {};
  const visit: string[] = [];
  if (!isGone(r.status)) {
    if (v.grounds_open === true) visit.push('Grounds open');
    if (v.grounds_open === false) visit.push('Grounds not open');
    if (v.climbable === true) visit.push(r.kind === 'lightship' ? 'You can go aboard' : 'You can climb it');
    if (v.museum === true) visit.push('Museum');
  }
  if (r.stay && typeof r.stay === 'object' && r.stay.type) visit.push(`Stay: ${lookup(STAY_TYPE, r.stay.type)}`);
  return html`
    <p class="eyebrow">${kindPlace(r)}</p>
    <h2 id="panel-title" tabindex="-1">${r.name}</h2>
    ${badges(r)}
    ${opts.hiddenByFilters ? html`<p class="notice tone-unknown" role="note">${INFO}<span>Your filters hide this station on the map. <button type="button" class="linklike" data-action="reset-filters">Reset filters</button></span></p>` : ''}
    ${prominent.map((l, i) => accessNotice(l, i === 0 ? r.access?.note : null))}
    ${statusLine(r)}
    ${r.verification === 'unverified' ? html`<p class="fine warn-text">Unverified: not yet confirmed by two sources, not yet checked.</p>` : ''}
    ${visit.length ? html`<p class="panel-visit">${visit.join(' · ')}</p>` : ''}
    ${rows.length ? html`<dl class="kv kv-panel">${rows.map(([k, val]) => html`<div><dt>${k}</dt><dd>${val}</dd></div>`)}</dl>` : ''}
    ${checklistButtons(r.id)}
    <p class="panel-actions"><a class="btn btn-primary" href="${stationPath(r.id, ctx)}">Open the full page<span class="visually-hidden">: ${r.name}</span></a></p>
    <p class="fine">${r.story_html ? 'Its history, keepers, ' : 'Visiting details, '}facts, sources and “Suggest an edit” are on the full page.</p>`;
}

/** Shown at once from the map point while the full record loads. */
export function renderPanelStub(p: StationProps, ctx: RenderContext, message: string): SafeHtml {
  return html`
    <p class="eyebrow">${kindPlace({ kind: p.k, county: p.c ?? null, region: p.r, country: p.cc ?? null })}</p>
    <h2 id="panel-title" tabindex="-1">${p.n}</h2>
    <ul class="badges">${statusBadge({ status: p.s, kind: p.k })}${p.v === 'unverified' ? unverifiedBadge() : ''}</ul>
    <p class="muted" role="status">${message}</p>
    <p class="panel-actions"><a class="btn" href="${stationPath(p.i, ctx)}">Open the full page</a></p>`;
}
