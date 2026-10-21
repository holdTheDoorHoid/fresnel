/**
 * The keepers roster (DESIGN.md 3.6): every keeper, assistant and (on lightships) master and
 * crew member the research names, with the role as the source gives it, the years, a note and
 * the sources each line rests on. The roster comes from the research file, never from the prose.
 * Sources link to the research sources listed under "Sources and credits" (#rs-<n>).
 */
import { html, type SafeHtml } from '../lib/html.ts';
import { formatDate, yearOf, yearSpan } from '../lib/format.ts';
import type { Keeper, ResearchSource } from '../lib/types.ts';
import { externalLink } from './common.ts';

export function researchSourceId(n: number): string {
  return `rs-${n}`;
}

/** Roster lines in order of service: by the first year, lines with no year last, ties kept as given. */
export function sortKeepers(keepers: readonly Keeper[]): Keeper[] {
  return keepers
    .map((k, i) => ({ k, i, y: yearOf(k.from) ?? yearOf(k.to) }))
    .sort((a, b) => (a.y ?? Infinity) - (b.y ?? Infinity) || a.i - b.i)
    .map((x) => x.k);
}

function citeLinks(cite: readonly number[] | null | undefined, known: Set<number>): SafeHtml | string {
  const nums = [...new Set((cite ?? []).filter((n) => Number.isInteger(n)))];
  if (!nums.length) return html`<span class="muted">None given</span>`;
  return html`${nums.map((n, i) => html`${i ? ', ' : ''}${known.has(n) ? html`<a href="#${researchSourceId(n)}" aria-label="Source ${n}">[${n}]</a>` : html`[${n}]`}`)}`;
}

/** The roster table, or null when there is no roster. */
export function keepersTable(keepers: readonly Keeper[] | null | undefined, sources: readonly ResearchSource[] | null | undefined): SafeHtml | null {
  const rows = sortKeepers((keepers ?? []).filter((k) => k && typeof k.name === 'string' && k.name.trim()));
  if (!rows.length) return null;
  const known = new Set((sources ?? []).map((s) => s.n));
  return html`<div class="table-wrap">
    <table class="keepers">
      <caption class="visually-hidden">Keepers of this station, in order of service</caption>
      <thead><tr><th scope="col">Name</th><th scope="col">Role</th><th scope="col">Years</th><th scope="col">Note</th><th scope="col">Sources</th></tr></thead>
      <tbody>${rows.map(
        (k) => html`<tr>
          <th scope="row" data-label="Name">${k.name}</th>
          <td data-label="Role">${k.role || html`<span class="muted">Not given</span>`}</td>
          <td data-label="Years" class="years">${yearSpan(k.from, k.to)}</td>
          <td data-label="Note">${k.note || ''}</td>
          <td data-label="Sources" class="cites">${citeLinks(k.cite, known)}</td>
        </tr>`,
      )}</tbody>
    </table>
  </div>`;
}

/** The research sources the roster and the research cite, numbered as they are cited. */
export function researchSourcesList(sources: readonly ResearchSource[] | null | undefined): SafeHtml | null {
  const list = (sources ?? []).filter((s) => Number.isInteger(s.n)).sort((a, b) => a.n - b.n);
  if (!list.length) return null;
  return html`<ul class="research-sources">${list.map((s) => {
    const title = s.title || 'Untitled source';
    const bits = [s.publisher, s.date].filter(Boolean).join(', ');
    const accessed = s.accessed ? formatDate(s.accessed) : null;
    return html`<li id="${researchSourceId(s.n)}"><span class="rs-n">[${s.n}]</span> ${s.url ? externalLink(s.url, title) : html`<cite>${title}</cite>`}${bits ? html`. ${bits}` : ''}${accessed ? html` (accessed ${accessed})` : ''}.</li>`;
  })}</ul>`;
}
