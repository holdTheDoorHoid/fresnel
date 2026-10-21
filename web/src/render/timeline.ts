/**
 * A station's short timeline: its dated events in order, each with its source, plus the dates
 * the record states elsewhere (the light's first and last years, each structure's year built)
 * when no event already says so. Undated events come last. Pure string rendering.
 */
import { html, type SafeHtml } from '../lib/html.ts';
import type { StationEvent, StationRecord } from '../lib/types.ts';
import { STRUCTURE_ROLE, eventLabel } from '../lib/vocab.ts';

export interface TimelineItem {
  year: number | null;
  label: string;
  note: string | null;
  from: string | null;
}

function structureName(s: NonNullable<StationRecord['structures']>[number]): string {
  return s.name || STRUCTURE_ROLE[s.role ?? ''] || 'Structure';
}

/** The items in order: by year, undated last, record order kept within a year. */
export function timelineItems(r: Pick<StationRecord, 'events' | 'light' | 'structures'>): TimelineItem[] {
  const events: StationEvent[] = (r.events ?? []).filter((e) => e && typeof e.event === 'string');
  const has = (kind: string, year: number) => events.some((e) => e.event === kind && e.year === year);
  // A pattern change with no note says what the pattern became (DESIGN.md 3.4, `characteristic`).
  const changedTo = (e: StationEvent) => {
    const c = (e as StationEvent & { characteristic?: unknown }).characteristic;
    return e.event === 'characteristic_changed' && typeof c === 'string' && c.trim() ? `To ${c.trim()}.` : null;
  };
  const items: TimelineItem[] = events.map((e) => ({ year: typeof e.year === 'number' ? e.year : null, label: eventLabel(e.event), note: e.note ?? changedTo(e), from: e.from ?? null }));
  const light = r.light;
  if (light && typeof light.first_lit === 'number' && !has('first_lit', light.first_lit)) {
    items.push({ year: light.first_lit, label: eventLabel('first_lit'), note: null, from: light.from ?? null });
  }
  if (light && typeof light.deactivated === 'number' && !has('deactivated', light.deactivated)) {
    items.push({ year: light.deactivated, label: eventLabel('deactivated'), note: null, from: light.from ?? null });
  }
  for (const s of r.structures ?? []) {
    if (typeof s.built !== 'number') continue;
    if (events.some((e) => e.year === s.built && ['built', 'rebuilt', 'replaced'].includes(e.event))) continue;
    items.push({ year: s.built, label: `Built: ${structureName(s).replace(/^./, (c) => c.toLowerCase())}`, note: null, from: s.from ?? null });
  }
  return items
    .map((it, i) => ({ it, i }))
    .sort((a, b) => (a.it.year ?? Infinity) - (b.it.year ?? Infinity) || a.i - b.i)
    .map((x) => x.it);
}

export function renderTimeline(r: Pick<StationRecord, 'events' | 'light' | 'structures'>, source: (from: string | null) => SafeHtml | string): SafeHtml {
  const items = timelineItems(r);
  if (!items.length) return html`<p class="muted">No dated events are recorded for this station yet.</p>`;
  return html`<ol class="timeline">${items.map(
    (it) => html`<li><span class="tl-year">${it.year ?? 'Date unknown'}</span>
      <span class="tl-body"><span class="tl-what">${it.label}</span>${it.note ? html`<span class="tl-note">${it.note}</span>` : ''}${source(it.from)}</span></li>`,
  )}</ol>`;
}
