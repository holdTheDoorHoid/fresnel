/** The map page: wires data, map, filters, search, key, side panel, checklist and URL state. */
import 'maplibre-gl/dist/maplibre-gl.css';
import '../styles/map.css';
import { Map as MlMap, Popup, setWorkerUrl, type GeoJSONSource, type MapLayerMouseEvent } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

import { activeFilterCount, applyFilters, defaultFilters, type Filters } from '../lib/filters.ts';
import { formatCount } from '../lib/format.ts';
import { html } from '../lib/html.ts';
import { resolveRedirect } from '../lib/redirects.ts';
import { buildIndex, type SearchEntry } from '../lib/search.ts';
import type { Meta, SourceInfo, StationCollection, StationFeature, StationProps } from '../lib/types.ts';
import { parseState, serializeState, type AppState } from '../lib/urlstate.ts';
import { DEFAULT_VIEW } from '../lib/views.ts';
import { countText } from '../lib/count.ts';
import { kindWording, statusWording } from '../lib/vocab.ts';
import { countryOf } from '../lib/regions.ts';
import { stationPath, type RenderContext } from '../render/common.ts';
import { bindChecklistButtons, getChecklist, initChecklistDialog, loadRedirects } from '../ui/checklist-ui.ts';
import { initCommon } from '../ui/common.ts';
import { effectiveTheme, onThemeChange } from '../ui/theme.ts';
import siteConfig from '../../site.config.json';
import { addControls, initJump } from './controls.ts';
import { renderFilterPanel } from './filters-ui.ts';
import { initKeyPanel } from './key-ui.ts';
import { L_CLUSTERS, L_POINTS, SRC, installOverlays, stations } from './layers.ts';
import { initReach, reach, type ReachControl } from './reach.ts';
import { Panel } from './panel.ts';
import { initSearch } from './search-ui.ts';
import { loadBaseStyle } from './style.ts';

const BASE = import.meta.env.BASE_URL;
const PHONE = matchMedia('(max-width: 899px)');

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return (await res.json()) as T;
}

async function main(): Promise<void> {
  initCommon();
  setWorkerUrl(workerUrl);

  const state: AppState = parseState(location.search);
  const checklist = getChecklist();
  initChecklistDialog(checklist);

  const countEl = $('count');
  const filtersEl = $('filters');
  const filtersBody = $('filters-body');
  const openFiltersBtn = $<HTMLButtonElement>('open-filters');
  const showResultsBtn = $<HTMLButtonElement>('show-results');
  const filterCountEl = $('filter-count');
  const mapMessage = $('map-message');
  const mapbox = document.querySelector<HTMLElement>('.mapbox')!;
  const searchEl = document.querySelector<HTMLElement>('.search')!;

  let features: StationFeature[] = [];
  let byId = new Map<string, StationFeature>();
  let shownIds = new Set<string>();
  let index: SearchEntry[] = [];
  let collection: StationCollection = { type: 'FeatureCollection', features: [] };
  let map: MlMap | null = null;
  let viewTouched = !!state.view;

  const ctx: RenderContext = { base: BASE, siteUrl: siteConfig.siteUrl, repo: siteConfig.repo, sources: new Map() };

  /* ---------- URL ---------- */
  let urlTimer = 0;
  const writeUrl = () => {
    clearTimeout(urlTimer);
    urlTimer = window.setTimeout(() => {
      if (map && viewTouched) {
        const c = map.getCenter();
        state.view = { zoom: map.getZoom(), lat: c.lat, lon: c.lng };
      }
      history.replaceState(history.state, '', location.pathname + serializeState(state) + location.hash);
    }, 200);
  };

  /* ---------- Key (always one click away) ---------- */
  let reachCtl: ReachControl | null = null;
  const keyPanel = initKeyPanel({
    button: $<HTMLButtonElement>('open-key'),
    panel: $('key-panel'),
    body: $('key-panel-body'),
    closeBtn: $<HTMLButtonElement>('close-key'),
    wide: () => !PHONE.matches,
    onToggle: (open) => {
      if (open && reachCtl?.isOpen) reachCtl.close();
    },
  });

  initJump($('jump'), () => map);

  /* ---------- Light ranges (the light at night's rings) ---------- */
  let shownFeatures: StationFeature[] = [];
  reachCtl = initReach({
    host: $('reach'),
    country: () => state.filters.country ?? countryOf(state.filters.region) ?? 'US',
    eye: () => state.reach,
    counts: () => ({ rings: reach.count, lights: shownFeatures.filter((f) => f.properties.k !== 'life_saving_station').length }),
    onChange: (eye) => {
      state.reach = eye;
      reach.set(shownFeatures, eye);
      reachCtl?.sync();
      writeUrl();
    },
    onOpen: () => {
      if (keyPanel.isOpen) keyPanel.hide();
    },
  });

  /* ---------- Panel ---------- */
  const panel = new Panel({
    el: $('panel'),
    body: $('panel-body'),
    closeBtn: $<HTMLButtonElement>('panel-close'),
    ctx,
    isHiddenByFilters: (id) => features.length > 0 && !shownIds.has(id),
    onRender: (root) => bindChecklistButtons(root, checklist),
    onClose: () => {
      state.selected = null;
      stations.setSelection(null);
      writeUrl();
    },
  });

  const select = (id: string, opts: { fly: boolean; focus: boolean }) => {
    const f = byId.get(id);
    state.selected = id;
    // Where the key and the details would crowd the map (phones, narrow windows), the details win.
    if (keyPanel.isOpen && window.innerWidth < 1280) keyPanel.hide();
    void panel.open(id, f?.properties ?? null, { focus: opts.focus });
    if (map && f) {
      const coords = f.geometry.coordinates;
      stations.setSelection(coords);
      const cover = panel.coverage();
      const padding = { top: PHONE.matches ? 80 : 40, left: 40, right: 40 + cover.right, bottom: 40 + cover.bottom };
      if (opts.fly) {
        viewTouched = true;
        map.flyTo({ center: coords, zoom: Math.max(map.getZoom(), 11), padding, essential: true });
      } else {
        // Don't leave the station you just picked hidden under the panel or the search box.
        const p = map.project(coords);
        const box = map.getContainer();
        const hidden = p.x < padding.left - 20 || p.y < padding.top - 20 || p.x > box.clientWidth - padding.right + 20 || p.y > box.clientHeight - padding.bottom + 20;
        if (hidden) map.easeTo({ center: coords, padding, duration: 500 });
      }
    }
    writeUrl();
  };

  /* ---------- Filters ---------- */
  let syncFilters = () => {};
  const update = () => {
    const shown = applyFilters(features, state.filters, checklist);
    shownIds = new Set(shown.map((f) => f.properties.i));
    collection = { type: 'FeatureCollection', features: shown };
    stations.setData(collection);
    shownFeatures = shown;
    reach.set(shown, state.reach);
    reachCtl?.sync();
    const active = activeFilterCount(state.filters);
    const t = countText(shown.length, features.length, active > 0);
    countEl.innerHTML = html`<span class="count-main">${t.main}</span>${t.sub ? html`<span class="count-sub">: ${t.sub}</span>` : ''}`.value;
    countEl.classList.toggle('is-empty', shown.length === 0 && features.length > 0);
    filterCountEl.textContent = active ? ` (${active})` : '';
    $('reset-map').hidden = active === 0;
    showResultsBtn.textContent = shown.length === 0 ? 'No stations match: close' : `Show ${formatCount(shown.length)} station${shown.length === 1 ? '' : 's'}`;
    syncFilters();
    panel.refresh();
    writeUrl();
  };
  const setFilters = (f: Filters) => {
    state.filters = f;
    update();
  };

  document.addEventListener('click', (e) => {
    const t = e.target as Element;
    if (t.closest('[data-reset-filters], [data-action="reset-filters"]')) setFilters(defaultFilters());
  });

  /* ---------- Phone filter sheet ---------- */
  const setSheet = (open: boolean) => {
    filtersEl.toggleAttribute('data-open', open);
    openFiltersBtn.setAttribute('aria-expanded', String(open));
    for (const el of [mapbox, searchEl, $('panel')]) el.inert = open;
    if (open) filtersEl.querySelector<HTMLElement>('.filters-close')?.focus();
    else openFiltersBtn.focus();
  };
  openFiltersBtn.addEventListener('click', () => setSheet(true));
  for (const b of filtersEl.querySelectorAll('[data-close-filters]')) b.addEventListener('click', () => setSheet(false));
  PHONE.addEventListener('change', () => {
    if (!PHONE.matches && filtersEl.hasAttribute('data-open')) setSheet(false);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || document.querySelector('dialog[open]')) return;
    if (filtersEl.hasAttribute('data-open')) setSheet(false);
    else if (panel.isOpen && !(e.target as Element).closest?.('.search')) panel.close();
  });

  /* ---------- Search ---------- */
  initSearch({
    input: $<HTMLInputElement>('q'),
    list: $<HTMLUListElement>('q-results'),
    status: $('q-status'),
    index: () => index,
    onPick: (entry) => {
      if (!map) {
        location.href = stationPath(entry.props.i, ctx);
        return;
      }
      select(entry.props.i, { fly: true, focus: true });
    },
  });

  /* ---------- Checklist ---------- */
  checklist.subscribe(() => {
    bindChecklistButtons(document, checklist);
    if (state.filters.mine) update();
    else syncFilters();
  });

  /* ---------- Data (in parallel with the base map; neither waits for the other) ---------- */
  const dataTask = (async (): Promise<boolean> => {
    let geo: StationCollection;
    let meta: Meta | null;
    try {
      [geo, meta] = await Promise.all([getJson<StationCollection>('data/stations.geojson'), getJson<Meta>('data/meta.json').catch(() => null)]);
    } catch (err) {
      console.error(err);
      countEl.textContent = 'Could not load the stations';
      mapMessage.hidden = false;
      mapMessage.textContent = 'The list of stations could not be loaded. Check your connection and reload the page.';
      filtersBody.innerHTML = '<p class="muted">Filters are unavailable until the stations load.</p>';
      return false;
    }
    features = geo.features;
    byId = new Map(features.map((f) => [f.properties.i, f]));
    index = buildIndex(features);
    if (meta) {
      ctx.sources = new Map<string, SourceInfo>(meta.sources.map((s) => [s.id, s]));
      if (meta.fixtures) $('fixture-banner').hidden = false;
    }
    $<HTMLInputElement>('q').placeholder = `Search ${formatCount(features.length)} stations, e.g. Portland Head`;
    syncFilters = renderFilterPanel({ root: filtersBody, features: () => features, filters: () => state.filters, checklist, onChange: setFilters });
    update();
    return true;
  })();

  /* ---------- Map ---------- */
  let theme = effectiveTheme();
  const { style, ok: styleOk } = await loadBaseStyle(theme);
  try {
    map = new MlMap({
      container: 'map',
      style,
      bounds: state.view ? undefined : DEFAULT_VIEW,
      fitBoundsOptions: { padding: 20 },
      center: state.view ? [state.view.lon, state.view.lat] : undefined,
      zoom: state.view?.zoom,
      minZoom: 1.5,
      maxZoom: 18,
      dragRotate: false,
      pitchWithRotate: false,
      touchPitch: false,
      attributionControl: false,
    });
  } catch (err) {
    console.error(err);
    map = null;
    mapMessage.hidden = false;
    mapMessage.innerHTML = html`<p><strong>The map could not start.</strong> Your browser may have WebGL switched off. You can still find a station with the search box and open its page.</p>`.value;
  }

  if (map) {
    const m = map;
    m.touchZoomRotate.disableRotation();
    m.keyboard.disableRotation();
    addControls(m);
    if (!styleOk) {
      mapMessage.hidden = false;
      mapMessage.textContent = 'The background map could not be loaded, so only the stations are shown. Try reloading later.';
    }
    m.on('style.load', () => installOverlays(m, { theme, base: BASE }));
    onThemeChange(async (eff) => {
      if (eff === theme) return;
      theme = eff;
      const next = await loadBaseStyle(eff);
      m.setStyle(next.style, { diff: false });
    });
    m.on('movestart', (e) => {
      if ((e as { originalEvent?: unknown }).originalEvent) viewTouched = true;
    });
    m.on('moveend', writeUrl);
    m.on('click', L_POINTS, (e: MapLayerMouseEvent) => {
      const f = e.features?.[0];
      if (f) select(String(f.properties.i), { fly: false, focus: false });
    });
    m.on('click', L_CLUSTERS, async (e: MapLayerMouseEvent) => {
      const f = e.features?.[0];
      if (!f) return;
      const src = m.getSource(SRC) as GeoJSONSource;
      const zoom = await src.getClusterExpansionZoom(Number(f.properties.cluster_id));
      m.easeTo({ center: (f.geometry as unknown as { coordinates: [number, number] }).coordinates, zoom: Math.min(zoom + 0.5, 14) });
    });
    for (const layer of [L_POINTS, L_CLUSTERS]) {
      m.on('mouseenter', layer, () => (m.getCanvas().style.cursor = 'pointer'));
      m.on('mouseleave', layer, () => (m.getCanvas().style.cursor = ''));
    }
    if (matchMedia('(hover: hover)').matches) {
      const tip = new Popup({ closeButton: false, closeOnClick: false, offset: 14, className: 'fr-tip', maxWidth: '280px' });
      m.on('mousemove', L_POINTS, (e: MapLayerMouseEvent) => {
        const f = e.features?.[0];
        if (!f) return;
        const p = f.properties as StationProps;
        tip.setLngLat((f.geometry as unknown as { coordinates: [number, number] }).coordinates)
          .setText(`${p.n} · ${kindWording(p.k).short} · ${statusWording(p.s, p.k).label}`)
          .addTo(m);
      });
      m.on('mouseleave', L_POINTS, () => tip.remove());
    }
  }

  /* ---------- Both ready: open a station named in the URL ---------- */
  if (!(await dataTask)) return;
  if (state.selected && !byId.has(state.selected)) {
    // A station the merge folded into another keeps its address: follow the redirect.
    state.selected = resolveRedirect(state.selected, await loadRedirects());
  }
  if (state.selected) {
    if (byId.has(state.selected)) select(state.selected, { fly: !state.view, focus: false });
    else {
      state.selected = null;
      writeUrl();
    }
  }
}

void main();
