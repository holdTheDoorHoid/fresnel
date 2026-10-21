/**
 * Small pieces shared by the station page, the map panel and the site pages: the render
 * context, URLs, icons, links, badges and notices. Pure functions returning escaped HTML.
 */
import { html, raw, safeUrl, type SafeHtml } from '../lib/html.ts';
import { markerSvg } from '../lib/icons.ts';
import type { AccessLabel } from '../lib/access.ts';
import type { SourceInfo, StationRecord } from '../lib/types.ts';
import { regionWithCountry, stationCountry } from '../lib/regions.ts';
import { statusWording } from '../lib/vocab.ts';

export interface RenderContext {
  /** Site base path, e.g. "/fresnel/". */
  base: string;
  /** Absolute site URL for canonical links, e.g. "https://…/fresnel/". */
  siteUrl: string;
  /** GitHub "owner/name" that receives edit suggestions and takedown requests. */
  repo: string;
  /** meta.json's sources by id, for titles, links and credit lines. */
  sources: Map<string, SourceInfo>;
  takedownEmail?: string | null;
  /** Where mirrored photos will be served; null until they are (photos are hotlinked meanwhile). */
  photosBase?: string | null;
}

/* ---------- URLs ---------- */

export function stationPath(id: string, ctx: Pick<RenderContext, 'base'>): string {
  return `${ctx.base}s/${id}/`;
}

export function stationUrl(id: string, ctx: Pick<RenderContext, 'siteUrl'>): string {
  return `${ctx.siteUrl}s/${id}/`;
}

export function mapLink(r: Pick<StationRecord, 'id' | 'location'>, ctx: Pick<RenderContext, 'base'>, zoom = 13): string {
  const { lat, lon } = r.location;
  return `${ctx.base}?at=${zoom}/${lat.toFixed(4)}/${lon.toFixed(4)}&s=${r.id}`;
}

/** "Maine, United States" / "Nova Scotia, Canada": the edit form's "Where" box. */
export function whereWords(r: Pick<StationRecord, 'region'> & { country?: string | null }): string {
  const c = stationCountry(r);
  const region = regionWithCountry(r.region);
  return c === 'US' ? `${region}, United States` : region;
}

/**
 * The "Suggest an edit" link: a GitHub issue on the project, opened on the edit form
 * (.github/ISSUE_TEMPLATE/edit.yml) with the station filled in. The title says the station and
 * its region ("Edit: Portland Head Light (Maine)"). Form fields are filled by their ids; `body`
 * carries the same for the plain issue page GitHub shows if the form is not available.
 */
export function editIssueUrl(r: Pick<StationRecord, 'id' | 'name' | 'region'> & { country?: string | null }, ctx: Pick<RenderContext, 'repo' | 'siteUrl'>, extra: Record<string, string> = {}): string {
  const page = stationUrl(r.id, ctx);
  const q = new URLSearchParams({
    template: 'edit.yml',
    title: `Edit: ${r.name} (${regionWithCountry(r.region)})`,
    station_id: r.id,
    station_name: r.name,
    where: whereWords(r),
    page_url: page,
    body: `Station: ${r.name}\nId: ${r.id}\nPage: ${page}\n\nWhat is wrong or missing, what is right, and how do you know?\n`,
    ...extra,
  });
  return `https://github.com/${ctx.repo}/issues/new?${q.toString()}`;
}

export function takedownIssueUrl(r: Pick<StationRecord, 'id' | 'name'> | null, ctx: Pick<RenderContext, 'repo' | 'siteUrl'>): string {
  const q = new URLSearchParams({ template: 'takedown.yml', title: r ? `Takedown: ${r.name}` : 'Takedown: ' });
  if (r) {
    q.set('station_id', r.id);
    q.set('page_url', stationUrl(r.id, ctx));
  }
  return `https://github.com/${ctx.repo}/issues/new?${q.toString()}`;
}

/* ---------- Icons ---------- */

export const EXT = raw('<svg class="ext-icon" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M9 2h5v5M14 2 7.5 8.5M12 9.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>');
export const WARN = raw('<svg class="notice-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M10 2.5 18.5 17h-17Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M10 8v4.2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="10" cy="14.6" r="1.1" fill="currentColor"/></svg>');
export const STOP = raw('<svg class="notice-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M6.7 2h6.6L18 6.7v6.6L13.3 18H6.7L2 13.3V6.7Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M6.5 10h7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>');
export const INFO = raw('<svg class="notice-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M10 9v5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="10" cy="6.1" r="1.1" fill="currentColor"/></svg>');
export const CHECK = raw('<svg class="notice-icon" width="16" height="16" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="m4.5 10.5 3.5 3.5 7.5-8" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
export const BOAT = raw('<svg class="notice-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M2 11.5h16l-2.6 4.5H4.6Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M10 3v8.5M10 3.6l5 6.4h-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M1.5 18.4c1.4 0 1.4-.9 2.8-.9s1.4.9 2.8.9 1.4-.9 2.9-.9 1.4.9 2.8.9 1.4-.9 2.8-.9 1.4.9 2.9.9" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>');
export const HOME = raw('<svg class="notice-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M3 9.3 10 3l7 6.3V17H3Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M8 17v-4.5h4V17" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>');

/** The icon for an access label: what it is about, at a glance; the words always follow. */
export function accessIcon(l: AccessLabel): SafeHtml {
  if (l.id === 'boat_only') return BOAT;
  if (l.id === 'staffed' || l.id === 'volunteer') return HOME;
  if (l.tone === 'ok') return CHECK;
  if (l.tone === 'stop') return STOP;
  if (l.tone === 'unknown') return INFO;
  return WARN;
}

export function externalLink(url: string | null | undefined, text: unknown, className = ''): SafeHtml {
  const safe = safeUrl(url);
  if (!safe) return html`${text}`;
  return html`<a href="${safe}" class="${className || null}" rel="noopener">${text}${EXT}<span class="visually-hidden"> (opens another site)</span></a>`;
}

export function statusIcon(status: string, kind: string, size = 20): SafeHtml {
  return raw(markerSvg(status, kind, { size, className: 'marker-icon' }));
}

/** The status badge: the map marker's shape and the status in words, never colour alone. */
export function statusBadge(r: { status: string; kind: string }): SafeHtml {
  const st = statusWording(r.status, r.kind);
  return html`<li class="badge badge-status status-${r.status}" title="${st.meaning}">${statusIcon(r.status, r.kind, 20)}<span>${st.label}</span></li>`;
}

export function unverifiedBadge(): SafeHtml {
  return html`<li class="badge badge-unverified" title="Not yet confirmed: no two independent sources agree on it, and nobody has checked it. Details may be wrong.">${WARN}<span>Unverified</span></li>`;
}

export function accessBadge(l: AccessLabel): SafeHtml {
  return html`<li class="badge badge-access tone-${l.tone}" title="${l.meaning}">${accessIcon(l)}<span>${l.label}</span></li>`;
}

/** A labelled notice for one access label (the prominent warning on pages and in the panel). */
export function accessNotice(l: AccessLabel, note?: string | null): SafeHtml {
  return html`<div class="notice tone-${l.tone}" role="note">${accessIcon(l)}<div>
    <p class="notice-title">${l.label}</p>
    <p>${l.meaning}${note ? html` ${note}` : ''}</p>
  </div></div>`;
}
