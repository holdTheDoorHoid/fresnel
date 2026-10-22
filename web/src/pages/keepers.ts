/**
 * /keepers/: search the people of the keepers index (DESIGN.md 3.6) by name, state, role and
 * station. The page is prerendered (the explanation, the letters, the form's frame); this loads
 * the index lazily, one file per surname initial (data/k/i/<L>.json, 15 to 60 KB each), and reads
 * every file only when the visitor filters without a name, or asks to search first names too.
 * The logic is in lib/people.ts (tested); this file is the DOM.
 */
import '../styles/pages.css';
import '../styles/keepers.css';
import { initCommon } from '../ui/common.ts';
import { formatCount } from '../lib/format.ts';
import {
  NO_FILTERS,
  chunkName,
  chunksNeeded,
  filterRows,
  filtersFromParams,
  filtersToParams,
  hasAnyFilter,
  queryWords,
  rowSortKey,
  stationLabels,
  yearsText,
  type Filters,
  type IndexChunk,
  type IndexRow,
  type KeeperManifest,
  type StationChoice,
} from '../lib/people.ts';
import { regionName } from '../lib/regions.ts';
import siteConfig from '../../site.config.json';

const base = import.meta.env.BASE_URL;
const PAGE = 100;

async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(`${base}data/k/${path}`);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return (await r.json()) as T;
}

const q = <T extends HTMLElement>(sel: string) => document.querySelector<T>(sel);

async function devFill(): Promise<KeeperManifest | null> {
  const main = document.getElementById('main')!;
  if (!main.innerHTML.includes('fr:keepers')) return null;
  const { renderKeepersMain } = await import('../render/people.ts');
  const manifest = await getJson<KeeperManifest>('index.json');
  const meta = await fetch(`${base}data/meta.json`).then((r) => r.json());
  const sources = new Map(meta.sources.map((s: { id: string }) => [s.id, s]));
  main.innerHTML = renderKeepersMain(manifest, { base, siteUrl: siteConfig.siteUrl, repo: siteConfig.repo, sources } as never).value;
  return manifest;
}

async function start(): Promise<void> {
  initCommon();
  const form = q<HTMLFormElement>('[data-keepers-form]');
  if (!form && !import.meta.env.DEV) return;
  let devManifest: KeeperManifest | null = null;
  if (import.meta.env.DEV) devManifest = await devFill();
  const formEl = q<HTMLFormElement>('[data-keepers-form]');
  if (!formEl) return;
  const status = q<HTMLElement>('[data-status]')!;
  const list = q<HTMLOListElement>('[data-list]')!;
  const more = q<HTMLButtonElement>('[data-more]')!;
  const everywhereNote = q<HTMLElement>('[data-everywhere]')!;
  const nameInput = q<HTMLInputElement>('#k-q')!;
  const stateSel = q<HTMLSelectElement>('#k-state')!;
  const roleSel = q<HTMLSelectElement>('#k-role')!;
  const stationInput = q<HTMLInputElement>('#k-station')!;
  const stationList = q<HTMLDataListElement>('#k-station-list')!;

  let manifest: KeeperManifest;
  try {
    manifest = devManifest ?? (await getJson<KeeperManifest>('index.json'));
  } catch {
    status.textContent = 'The index could not be loaded. Reload the page to try again.';
    return;
  }
  formEl.hidden = false;
  q('[data-letters]')!.hidden = false;
  status.hidden = false;
  const roleIds = manifest.roles.map((r) => r.id);
  const chunks = new Map<string, IndexRow[]>();
  let stations: StationChoice[] | null = null;
  let labels: string[] = [];
  let filters: Filters = filtersFromParams(new URLSearchParams(location.search));
  let found: IndexRow[] = [];
  let shown = 0;
  let token = 0;

  async function loadStations(): Promise<void> {
    if (stations) return;
    const f = await getJson<{ stations: [string, string, string][] }>('stations.json');
    stations = f.stations.map(([id, name, region]) => ({ id, name, region }));
    labels = stationLabels(stations);
    stationList.replaceChildren(...labels.map((l) => Object.assign(document.createElement('option'), { value: l })));
  }

  function syncInputs(): void {
    nameInput.value = filters.q;
    stateSel.value = filters.region;
    roleSel.value = filters.role;
    const i = stations ? stations.findIndex((s) => s.id === filters.station) : -1;
    stationInput.value = i >= 0 ? labels[i]! : '';
    for (const a of document.querySelectorAll<HTMLAnchorElement>('[data-letter]')) {
      if (a.dataset.letter === filters.letter && !filters.q.trim()) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    }
  }

  function describe(row: IndexRow): string {
    const [, , y0, y1, regs, roles] = row;
    const where = regs ? regs.split(' ').map((c) => regionName(c) || c).join(', ') : '';
    const what = roles.map((n) => roleIds[n]).filter(Boolean).map((r) => r!.charAt(0).toUpperCase() + r!.slice(1)).join(', ');
    return [yearsText(y0, y1), where, what].filter(Boolean).join(' · ');
  }

  function draw(): void {
    const frag = document.createDocumentFragment();
    for (const row of found.slice(shown, shown + PAGE)) {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `${base}k/${row[0]}/`;
      a.textContent = row[1];
      const meta = document.createElement('span');
      meta.className = 'k-meta';
      meta.textContent = describe(row);
      li.append(a, meta);
      frag.append(li);
    }
    list.append(frag);
    shown = Math.min(found.length, shown + PAGE);
    more.hidden = shown >= found.length;
    more.textContent = `Show ${Math.min(PAGE, found.length - shown)} more`;
  }

  async function run(): Promise<void> {
    const mine = ++token;
    syncInputs();
    const params = filtersToParams(filters);
    history.replaceState(null, '', params.toString() ? `?${params}` : location.pathname);
    const need = chunksNeeded(filters, Object.keys(manifest.letters));
    const words = queryWords(filters.q);
    everywhereNote.hidden = !(words.length === 1 && !filters.everywhere);
    list.replaceChildren();
    more.hidden = true;
    found = [];
    shown = 0;
    if (!need.length) {
      status.textContent = hasAnyFilter(filters) ? 'No keepers have a surname beginning with that letter.' : 'Choose a letter, or type a name, to see keepers.';
      return;
    }
    const missing = need.filter((l) => !chunks.has(l));
    if (missing.length) {
      status.textContent = missing.length > 3 ? 'Reading the index…' : 'Searching…';
      try {
        const got = await Promise.all(missing.map((l) => getJson<IndexChunk>(`i/${chunkName(l)}.json`)));
        got.forEach((c, i) => chunks.set(missing[i]!, c.rows));
      } catch {
        if (mine === token) status.textContent = 'Part of the index could not be loaded. Try again in a moment.';
        return;
      }
    }
    if (mine !== token) return;
    if (filters.station) await loadStations();
    const roleNumber = roleIds.indexOf(filters.role);
    const stationNumber = filters.station && stations ? stations.findIndex((s) => s.id === filters.station) : -1;
    const rows = need.flatMap((l) => chunks.get(l) ?? []);
    found = filterRows(rows, filters, roleNumber, stationNumber);
    if (need.length > 1 || words.length) found.sort((a, b) => (rowSortKey(a[1]) < rowSortKey(b[1]) ? -1 : 1));
    const n = found.length;
    status.textContent = n
      ? `${formatCount(n)} ${n === 1 ? 'person' : 'people'} found${n > PAGE ? `; showing the first ${PAGE}` : ''}.`
      : 'No one matches. Try fewer words, another spelling, or clear a filter. People whose service ran past 1960 are not in this index.';
    draw();
  }

  let timer = 0;
  function soon(): void {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => void run(), 140);
  }

  nameInput.addEventListener('input', () => {
    filters = { ...filters, q: nameInput.value, letter: '', everywhere: false };
    soon();
  });
  stateSel.addEventListener('change', () => {
    filters = { ...filters, region: stateSel.value };
    void run();
  });
  roleSel.addEventListener('change', () => {
    filters = { ...filters, role: roleSel.value };
    void run();
  });
  stationInput.addEventListener('focus', () => void loadStations());
  stationInput.addEventListener('input', () => {
    const i = labels.indexOf(stationInput.value);
    const id = i >= 0 ? stations![i]!.id : '';
    if (!stationInput.value) filters = { ...filters, station: '' };
    else if (id) filters = { ...filters, station: id };
    else return; // still typing
    void run();
  });
  more.addEventListener('click', () => draw());
  q<HTMLButtonElement>('[data-search-all]')!.addEventListener('click', () => {
    filters = { ...filters, everywhere: true };
    void run();
  });
  q<HTMLButtonElement>('[data-reset]')!.addEventListener('click', () => {
    filters = { ...NO_FILTERS };
    void run();
  });
  formEl.addEventListener('submit', (e) => e.preventDefault());
  q('[data-letters]')!.addEventListener('click', (e) => {
    const a = (e.target as HTMLElement).closest<HTMLAnchorElement>('[data-letter]');
    if (!a) return;
    e.preventDefault();
    filters = { ...filters, q: '', letter: a.dataset.letter!, everywhere: false };
    void run();
  });

  if (filters.station) await loadStations();
  void run();
}

void start();
