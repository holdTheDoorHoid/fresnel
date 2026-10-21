/**
 * "How far the lights reach": an optional map layer with a ring round every light the filters
 * show, of the distance it can be seen at night from a chosen eye height (DESIGN.md section 4):
 * the smaller of its charted range and the distance to its horizon (lib/sighting.ts). Several
 * rings together show how the lights covered a coast. Lights that are lit today are amber; the
 * rest (out, lost, or status unknown) are grey with a dashed edge, as last recorded.
 *
 * The layer (ReachOverlay, in OVERLAYS under the stations) and its control (initReach: a chip
 * in the map's status bar that opens a small panel) live here. The URL keeps it: &reach=<eye m>.
 */
import type { ExpressionSpecification, GeoJSONSource, Map as MlMap } from 'maplibre-gl';
import { formatCount, lengthFor } from '../lib/format.ts';
import { html } from '../lib/html.ts';
import { DEFAULT_EYE_M, EYE_HEIGHTS, circleRing, ringRangeNm } from '../lib/sighting.ts';
import type { StationFeature } from '../lib/types.ts';
import { hasLight } from '../lib/vocab.ts';
import type { LayerContext, Overlay } from './layers.ts';
import { LABEL_FONT } from './style.ts';

const SRC = 'fr-reach';
const L_FILL = 'fr-reach-fill';
const L_LINE_LIT = 'fr-reach-line';
const L_LINE_PAST = 'fr-reach-line-past';
const L_LABEL = 'fr-reach-label';

export interface ReachFeatureProps {
  i: string;
  lit: 0 | 1;
  nm: number;
  limit: 'horizon' | 'range';
}

/** The rings for these stations from this eye height: lit lights last, so they draw on top. */
export function reachCollection(features: readonly StationFeature[], eyeM: number) {
  const out = [];
  for (const f of features) {
    const p = f.properties;
    if (!hasLight(p.k)) continue;
    const ring = ringRangeNm(p.fh, p.rn, eyeM);
    if (!ring) continue;
    const [lon, lat] = f.geometry.coordinates;
    const props: ReachFeatureProps = { i: p.i, lit: p.s === 'active' ? 1 : 0, nm: Number(ring.nm.toFixed(1)), limit: ring.limit };
    out.push({ type: 'Feature' as const, properties: props, geometry: { type: 'Polygon' as const, coordinates: [circleRing(lat, lon, ring.nm, 72)] } });
  }
  out.sort((a, b) => a.properties.lit - b.properties.lit || b.properties.nm - a.properties.nm);
  return { type: 'FeatureCollection' as const, features: out };
}

export class ReachOverlay implements Overlay {
  readonly id = 'reach';
  #map: MlMap | null = null;
  #features: readonly StationFeature[] = [];
  #eye: number | null = null;
  #count = 0;

  /** How many of the given stations got a ring. */
  get count(): number {
    return this.#count;
  }

  install(map: MlMap, ctx: LayerContext): void {
    this.#map = map;
    const dark = ctx.theme === 'dark';
    const lit = dark ? '#ffc23d' : '#c98a00';
    const past = dark ? '#a2b0be' : '#5d6975';
    if (!map.getSource(SRC)) map.addSource(SRC, { type: 'geojson', data: this.#data() as never });
    const isLit: ExpressionSpecification = ['==', ['get', 'lit'], 1];
    if (!map.getLayer(L_FILL)) {
      map.addLayer({
        id: L_FILL,
        type: 'fill',
        source: SRC,
        paint: { 'fill-color': ['case', isLit, lit, past], 'fill-opacity': ['case', isLit, dark ? 0.09 : 0.11, 0.05] },
      });
    }
    if (!map.getLayer(L_LINE_PAST)) {
      map.addLayer({ id: L_LINE_PAST, type: 'line', source: SRC, filter: ['!', isLit], paint: { 'line-color': past, 'line-width': 1.2, 'line-dasharray': [3, 2], 'line-opacity': 0.8 } });
    }
    if (!map.getLayer(L_LINE_LIT)) {
      map.addLayer({ id: L_LINE_LIT, type: 'line', source: SRC, filter: isLit, paint: { 'line-color': lit, 'line-width': 1.6, 'line-opacity': 0.9 } });
    }
    if (!map.getLayer(L_LABEL)) {
      map.addLayer({
        id: L_LABEL,
        type: 'symbol',
        source: SRC,
        minzoom: 8,
        layout: { 'symbol-placement': 'line', 'text-field': ['concat', ['to-string', ['get', 'nm']], ' nmi'], 'text-font': LABEL_FONT, 'text-size': 11, 'symbol-spacing': 400 },
        paint: { 'text-color': dark ? '#e8eef3' : '#10263d', 'text-halo-color': dark ? 'rgba(11,22,34,0.9)' : 'rgba(255,255,255,0.9)', 'text-halo-width': 1.4 },
      });
    }
  }

  #data() {
    if (this.#eye === null) {
      this.#count = 0;
      return { type: 'FeatureCollection', features: [] };
    }
    const c = reachCollection(this.#features, this.#eye);
    this.#count = c.features.length;
    return c;
  }

  /** The stations the filters show, and the eye height (null: the layer is off). */
  set(features: readonly StationFeature[], eyeM: number | null): void {
    this.#features = features;
    this.#eye = eyeM;
    (this.#map?.getSource(SRC) as GeoJSONSource | undefined)?.setData(this.#data() as never);
  }
}

export const reach = new ReachOverlay();

export const REACH_EYES = EYE_HEIGHTS.map((h) => h.m);

export interface ReachDeps {
  host: HTMLElement;
  country: () => string;
  eye: () => number | null;
  /** How many shown stations got a ring, and how many lights were shown. */
  counts: () => { rings: number; lights: number };
  onChange: (eye: number | null) => void;
  /** Another panel wants the room. */
  onOpen: () => void;
}

export interface ReachControl {
  readonly isOpen: boolean;
  close(): void;
  sync(): void;
}

/** The "Light ranges" chip and its panel. */
export function initReach(d: ReachDeps): ReachControl {
  d.host.innerHTML = html`<button type="button" class="btn btn-chip fr-reach-btn" aria-expanded="false" aria-controls="fr-reach-panel">
      <svg width="16" height="16" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><circle cx="10" cy="10" r="7.4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="2.4 1.8"/><circle cx="10" cy="10" r="2.4" fill="currentColor"/></svg>
      <span>Light ranges</span><span class="fr-reach-on" aria-hidden="true" hidden>on</span>
    </button>
    <section class="fr-reach-panel" id="fr-reach-panel" aria-labelledby="fr-reach-h" hidden>
      <div class="key-panel-head">
        <h2 id="fr-reach-h">How far the lights reach</h2>
        <button type="button" class="icon-btn" data-reach-close aria-label="Close">
          <svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="m5 5 10 10M15 5 5 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
      </div>
      <label class="fr-reach-toggle"><input type="checkbox" data-reach-on> Show a ring round each light</label>
      <label class="fr-reach-eye">Seen with your eye
        <select data-reach-eye></select>
      </label>
      <p class="fine" data-reach-count></p>
      <ul class="fr-reach-key fine">
        <li><span class="sw sw-lit" aria-hidden="true"></span> Lit today: how far out it can be seen at night.</li>
        <li><span class="sw sw-past" aria-hidden="true"></span> Out, lost, or status unknown: how far it could be seen, as last recorded.</li>
      </ul>
      <p class="fine">Each ring is the smaller of the light’s charted range (how bright it is, in clear weather) and the distance to its horizon from that height. Lights with neither recorded have no ring. The rings ignore land: headlands and hills can hide a light. A guide, not a navigation aid.</p>
    </section>`.value;
  const btn = d.host.querySelector<HTMLButtonElement>('.fr-reach-btn')!;
  const on = d.host.querySelector<HTMLElement>('.fr-reach-on')!;
  const panel = d.host.querySelector<HTMLElement>('.fr-reach-panel')!;
  const box = d.host.querySelector<HTMLInputElement>('[data-reach-on]')!;
  const sel = d.host.querySelector<HTMLSelectElement>('[data-reach-eye]')!;
  const count = d.host.querySelector<HTMLElement>('[data-reach-count]')!;
  let lastEye = d.eye() ?? DEFAULT_EYE_M;

  const fillEyes = () => {
    const c = d.country();
    sel.innerHTML = EYE_HEIGHTS.map((h) => html`<option value="${h.m}"${h.m === lastEye ? html` selected` : ''}>${lengthFor(c, h.m)}, ${h.label}</option>`.value).join('');
  };
  const sync = () => {
    const eye = d.eye();
    if (eye !== null) lastEye = eye;
    box.checked = eye !== null;
    sel.value = String(lastEye);
    sel.disabled = eye === null;
    on.hidden = eye === null;
    btn.classList.toggle('is-on', eye !== null);
    const n = d.counts();
    count.textContent = eye === null ? '' : n.lights ? `Rings for ${formatCount(n.rings)} of the ${formatCount(n.lights)} lights shown; the others have no height or range recorded.` : 'No lights are shown with the current filters.';
  };
  const setOpen = (open: boolean, focusBack = false) => {
    panel.hidden = !open;
    btn.setAttribute('aria-expanded', String(open));
    if (open) {
      d.onOpen();
      fillEyes();
      sync();
      box.focus();
    } else if (focusBack) btn.focus();
  };
  btn.addEventListener('click', () => setOpen(panel.hidden === true));
  d.host.querySelector('[data-reach-close]')!.addEventListener('click', () => setOpen(false, true));
  panel.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      setOpen(false, true);
    }
  });
  box.addEventListener('change', () => {
    d.onChange(box.checked ? lastEye : null);
    sync();
  });
  sel.addEventListener('change', () => {
    lastEye = Number(sel.value);
    d.onChange(lastEye);
    sync();
  });
  fillEyes();
  sync();
  return {
    get isOpen() {
      return !panel.hidden;
    },
    close: () => setOpen(false),
    sync,
  };
}
