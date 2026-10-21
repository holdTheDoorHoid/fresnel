/**
 * The filter panel. Each status and kind option shows the marker it draws, and each count says
 * how many stations you would see with it ticked (every other filter applied).
 */
import { MARKS, MARK_LABELS, type Mark } from '../lib/checklist.ts';
import { formatCount } from '../lib/format.ts';
import { facetCounts, isSelected, matches, toggleValue, type ChecklistLookup, type Facet, type Filters } from '../lib/filters.ts';
import { html, raw, type SafeHtml } from '../lib/html.ts';
import { glyphSvg, markerSvg, silhouetteFor } from '../lib/icons.ts';
import type { StationFeature } from '../lib/types.ts';
import { ACCESS, ACCESS_ORDER, KIND, KIND_ORDER, STATUS, STATUS_ORDER, VERIFICATION, VERIFICATION_ORDER } from '../lib/vocab.ts';
import { COUNTRY_NAMES, regionGroups, regionName } from '../lib/regions.ts';
import { BOAT, HOME } from '../render/common.ts';

export interface FilterPanelDeps {
  root: HTMLElement;
  features: () => readonly StationFeature[];
  filters: () => Filters;
  checklist: ChecklistLookup & { counts(): Record<Mark, number> };
  onChange: (next: Filters) => void;
}

function option(name: string, value: string, label: string, icon: SafeHtml | string, hint?: string): SafeHtml {
  return html`<label class="opt">
    <input type="checkbox" name="${name}" value="${value}">
    <span class="opt-icon">${typeof icon === 'string' ? raw(icon) : icon}</span>
    <span class="opt-label">${label}${hint ? html`<span class="opt-hint">${hint}</span>` : ''}</span>
    <span class="opt-count" data-count="${name}:${value}"></span>
  </label>`;
}

function multiFieldset(facet: Facet, legend: string, body: SafeHtml, help?: string): SafeHtml {
  return html`<fieldset class="fs" data-facet="${facet}">
    <legend>${legend}</legend>
    ${help ? html`<p class="fs-help">${help}</p>` : ''}
    ${body}
    <button type="button" class="linklike fs-all" data-all="${facet}" hidden>Show all again</button>
  </fieldset>`;
}

const ICON_CLIMB = raw('<svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M5 18V4M15 18V4M5 7h10M5 11h10M5 15h10" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>');
const ICON_STAY = raw('<svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M2.5 15V6M2.5 11.5h15V15M17.5 11.5V9.5a2 2 0 0 0-2-2H9v4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/><circle cx="5.8" cy="9" r="1.6" fill="currentColor"/></svg>');
const ICON_REG = raw('<svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M5 2.5h10v15l-5-3.4-5 3.4Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>');
const ICON_STORY = raw('<svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M10 5.2C8.4 3.9 5.8 3.5 2.5 3.8v11.6c3.3-.3 5.9.1 7.5 1.4 1.6-1.3 4.2-1.7 7.5-1.4V3.8c-3.3-.3-5.9.1-7.5 1.4Zm0 0v11.6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>');

const SWITCHES: { name: string; key: 'climbable' | 'stay' | 'noBoat' | 'staffed' | 'registered' | 'story'; label: string; hint: string; icon: SafeHtml }[] = [
  { name: 'climbable', key: 'climbable', label: 'Only towers you can climb', hint: 'As recorded; hours and seasons vary', icon: ICON_CLIMB },
  { name: 'stay', key: 'stay', label: 'Only places you can stay', hint: 'Rentals, inns, hostels, keeper programs', icon: ICON_STAY },
  { name: 'noboat', key: 'noBoat', label: 'Hide stations reached only by boat', hint: 'Islands, reefs and offshore towers', icon: BOAT },
  { name: 'staffed', key: 'staffed', label: 'Only stations where keepers live', hint: 'Working lightstations and resident volunteer keepers', icon: HOME },
  { name: 'registered', key: 'registered', label: 'Only stations on a heritage register', hint: 'National Register, heritage lighthouses', icon: ICON_REG },
  { name: 'story', key: 'story', label: 'Only stations with a written history', hint: 'Researched and footnoted', icon: ICON_STORY },
];

export function renderFilterPanel(d: FilterPanelDeps): () => void {
  const regions = [...new Set(d.features().map((f) => f.properties.r))];

  d.root.innerHTML = html`
    ${multiFieldset(
      'status',
      'Status',
      html`${STATUS_ORDER.map((s) => option('status', s, STATUS[s]?.label ?? s, markerSvg(s, 'lighthouse', { size: 22 })))}`,
      'The marker’s shape shows this.',
    )}
    ${multiFieldset(
      'kind',
      'What it is',
      html`${KIND_ORDER.map((k) => option('kind', k, KIND[k]?.label ?? k, glyphSvg('dark', silhouetteFor(k), { size: 22 })))}`,
      'The silhouette shows this.',
    )}
    <fieldset class="fs">
      <legend>Visiting</legend>
      ${SWITCHES.slice(0, 4).map((s) => html`<label class="opt"><input type="checkbox" name="${s.name}" value="1"><span class="opt-icon">${s.icon}</span><span class="opt-label">${s.label}<span class="opt-hint">${s.hint}</span></span><span class="opt-count" data-count="${s.name}"></span></label>`)}
    </fieldset>
    ${multiFieldset(
      'access',
      'Access',
      html`${ACCESS_ORDER.map((a) => option('access', a, ACCESS[a]?.label ?? a, '', a === 'unknown' ? 'Nothing recorded yet' : undefined))}`,
      'Every station is on the map at its real position; these say whether you may go in.',
    )}
    <div class="fs fs-select">
      <label for="f-region" class="fs-label">State, territory or province</label>
      <select id="f-region" name="region">
        <option value="">Everywhere</option>
        ${regionGroups(regions).map((g) => html`<optgroup label="${g.name}">
          <option value="@${g.country}">All of ${g.country === 'US' ? 'the United States' : g.name}</option>
          ${g.regions.map((r) => html`<option value="${r.code}">${r.name}</option>`)}
        </optgroup>`)}
      </select>
    </div>
    <fieldset class="fs">
      <legend>History</legend>
      ${SWITCHES.slice(4).map((s) => html`<label class="opt"><input type="checkbox" name="${s.name}" value="1"><span class="opt-icon">${s.icon}</span><span class="opt-label">${s.label}<span class="opt-hint">${s.hint}</span></span><span class="opt-count" data-count="${s.name}"></span></label>`)}
    </fieldset>
    ${multiFieldset(
      'verification',
      'How well checked',
      html`${VERIFICATION_ORDER.map((v) => option('verification', v, VERIFICATION[v]?.label ?? v, '', VERIFICATION[v]?.meaning))}`,
    )}
    <fieldset class="fs">
      <legend>My checklist</legend>
      <p class="fs-help">Show only stations you marked in this browser. Leave all unticked to show everything.</p>
      ${MARKS.map((m) => html`<label class="opt"><input type="checkbox" name="mine" value="${m}"><span class="opt-icon"></span><span class="opt-label">${MARK_LABELS[m]}</span><span class="opt-count" data-count="mine:${m}"></span></label>`)}
      <button type="button" class="linklike" data-open-checklist-dialog>Download or import my checklist</button>
    </fieldset>
    <div class="fs-actions">
      <button type="button" class="btn btn-quiet" data-reset-filters>Reset all filters</button>
    </div>
    <p class="fine fs-credit">Station data from many sources: see <a href="${import.meta.env.BASE_URL}credits/">sources and credits</a>.</p>
  `.value;

  const root = d.root;
  root.addEventListener('change', (e) => {
    const input = e.target as HTMLInputElement | HTMLSelectElement;
    const checked = (input as HTMLInputElement).checked;
    const f: Filters = { ...d.filters() };
    const sw = SWITCHES.find((s) => s.name === input.name);
    if (sw) {
      f[sw.key] = checked;
      d.onChange(f);
      return;
    }
    switch (input.name) {
      case 'status':
        f.status = toggleValue(f.status, input.value, checked, STATUS_ORDER);
        break;
      case 'kind':
        f.kind = toggleValue(f.kind, input.value, checked, KIND_ORDER);
        break;
      case 'verification':
        f.verification = toggleValue(f.verification, input.value, checked, VERIFICATION_ORDER);
        break;
      case 'access':
        f.access = toggleValue(f.access, input.value, checked, ACCESS_ORDER);
        break;
      case 'region':
        // "@CA": a whole country; a code: one state, territory or province
        f.country = input.value.startsWith('@') ? input.value.slice(1) : null;
        f.region = input.value && !input.value.startsWith('@') ? input.value : null;
        break;
      case 'mine': {
        const next = new Set(f.mine ?? []);
        if (checked) next.add(input.value as Mark);
        else next.delete(input.value as Mark);
        f.mine = next.size ? next : null;
        break;
      }
      default:
        return;
    }
    d.onChange(f);
  });
  root.addEventListener('click', (e) => {
    const all = (e.target as Element).closest<HTMLElement>('[data-all]');
    if (!all) return;
    const facet = all.dataset.all as 'status' | 'kind' | 'verification' | 'access';
    d.onChange({ ...d.filters(), [facet]: null });
    root.querySelector<HTMLInputElement>(`fieldset[data-facet="${facet}"] input`)?.focus();
  });

  const FACETS: { facet: 'status' | 'kind' | 'verification' | 'access'; order: readonly string[] }[] = [
    { facet: 'status', order: STATUS_ORDER },
    { facet: 'kind', order: KIND_ORDER },
    { facet: 'verification', order: VERIFICATION_ORDER },
    { facet: 'access', order: ACCESS_ORDER },
  ];

  /** Sync checkboxes and counts with the current filters. */
  return function sync(): void {
    const f = d.filters();
    const feats = d.features();
    const set = (name: string, value: string, on: boolean) => {
      const el = root.querySelector<HTMLInputElement>(`input[name="${name}"][value="${value}"]`);
      if (el) el.checked = on;
    };
    for (const { facet, order } of FACETS) {
      for (const v of order) set(facet, v, isSelected(f[facet], v));
      const btn = root.querySelector<HTMLElement>(`[data-all="${facet}"]`);
      if (btn) btn.hidden = f[facet] === null;
    }
    for (const s of SWITCHES) set(s.name, '1', f[s.key]);
    for (const m of MARKS) set('mine', m, !!f.mine?.has(m));
    const sel = root.querySelector<HTMLSelectElement>('#f-region');
    if (sel) {
      if (f.region && !sel.querySelector(`option[value="${f.region}"]`)) {
        sel.insertAdjacentHTML('beforeend', html`<option value="${f.region}">${regionName(f.region)} (no stations yet)</option>`.value);
      }
      sel.value = f.region ?? (f.country ? `@${f.country}` : '');
    }

    const write = (key: string, n: number) => {
      const el = root.querySelector(`[data-count="${key}"]`);
      if (el) el.textContent = formatCount(n);
    };
    for (const { facet, order } of FACETS) {
      const counts = facetCounts(feats, f, facet, d.checklist);
      for (const v of order) write(`${facet}:${v}`, counts.get(v) ?? 0);
    }
    const regionCounts = facetCounts(feats, f, 'region', d.checklist);
    if (sel) {
      const byCountry = new Map<string, number>();
      for (const g of regionGroups(regionCounts.keys())) byCountry.set(g.country, g.regions.reduce((a, r) => a + (regionCounts.get(r.code) ?? 0), 0));
      for (const opt of sel.options) {
        if (!opt.value) continue;
        if (opt.value.startsWith('@')) {
          const c = opt.value.slice(1);
          opt.textContent = `All of ${c === 'US' ? 'the United States' : COUNTRY_NAMES[c] ?? c} (${formatCount(byCountry.get(c) ?? 0)})`;
          continue;
        }
        opt.textContent = `${regionName(opt.value)} (${formatCount(regionCounts.get(opt.value) ?? 0)})`;
      }
    }
    const countWith = (patch: Partial<Filters>) => feats.filter((x) => matches(x.properties, { ...f, ...patch }, d.checklist)).length;
    for (const s of SWITCHES) {
      // "Hide boat-only": how many it hides; the others: how many you would see.
      if (s.key === 'noBoat') write(s.name, feats.filter((x) => x.properties.bo && matches(x.properties, { ...f, noBoat: false }, d.checklist)).length);
      else write(s.name, countWith({ [s.key]: true }));
    }
    for (const m of MARKS) write(`mine:${m}`, d.checklist.counts()[m]);
  };
}
