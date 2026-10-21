/**
 * The station page's mini-map for "The light at night": the light, the ring of how far out it
 * can be seen with the visitor's chosen eye height and visibility, and a dashed ring at the
 * chosen distance (the visitor is somewhere on it, at sea). MapLibre and the base map load only
 * when this scrolls into view, so a page that is only read never downloads them.
 */
import 'maplibre-gl/dist/maplibre-gl.css';
import { Map as MlMap, NavigationControl, ScaleControl, setWorkerUrl, type GeoJSONSource, type LngLatBoundsLike } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import { lengthFor, nauticalMiles } from '../lib/format.ts';
import { html } from '../lib/html.ts';
import { VISIBILITY, circleRing, type Sighting, type VisibilityId } from '../lib/sighting.ts';
import { loadBaseStyle, type Theme } from '../map/style.ts';
import { effectiveTheme, onThemeChange } from './theme.ts';

export interface NightMapView {
  sighting: Sighting;
  distanceNm: number;
  eyeM: number;
  visibility: VisibilityId;
  past: boolean;
}

const SRC = 'night-rings';

function ringColours(theme: Theme) {
  return theme === 'dark'
    ? { fill: '#ffc23d', line: '#ffc23d', past: '#c9d8e8', you: '#e8eef3', dot: '#ffc23d', halo: '#0b1622' }
    : { fill: '#f2a900', line: '#8a5300', past: '#4d6072', you: '#10263d', dot: '#f2a900', halo: '#ffffff' };
}

export async function createNightMap(host: HTMLElement, o: { lat: number; lon: number; name: string; country: string }): Promise<{ update(v: NightMapView): void } | null> {
  host.innerHTML = html`<div class="night-map" role="img" aria-label="Map of the light and how far out it can be seen"></div><p class="night-map-key fine" data-key></p>`.value;
  const box = host.querySelector<HTMLElement>('.night-map')!;
  const key = host.querySelector<HTMLElement>('[data-key]')!;
  setWorkerUrl(workerUrl);
  let theme = effectiveTheme();
  const { style } = await loadBaseStyle(theme);
  let map: MlMap;
  try {
    map = new MlMap({
      container: box,
      style,
      center: [o.lon, o.lat],
      zoom: 8,
      attributionControl: { compact: true },
      cooperativeGestures: true,
      dragRotate: false,
      pitchWithRotate: false,
      touchPitch: false,
    });
  } catch {
    host.innerHTML = '<p class="fine">The map could not start (your browser may have WebGL switched off). The distances are given in words above.</p>';
    return null;
  }
  map.touchZoomRotate.disableRotation();
  map.addControl(new NavigationControl({ showCompass: false }), 'top-right');
  map.addControl(new ScaleControl({ unit: 'nautical', maxWidth: 100 }), 'bottom-left');

  let last: NightMapView | null = null;
  let fitted = '';
  const data = (v: NightMapView) => {
    const features: object[] = [];
    const vis = v.sighting.visibleNm;
    if (vis !== null && vis > 0) {
      features.push({ type: 'Feature', properties: { k: 'reach' }, geometry: { type: 'Polygon', coordinates: [circleRing(o.lat, o.lon, vis)] } });
    }
    features.push({ type: 'Feature', properties: { k: 'you' }, geometry: { type: 'LineString', coordinates: circleRing(o.lat, o.lon, v.distanceNm) } });
    features.push({ type: 'Feature', properties: { k: 'light' }, geometry: { type: 'Point', coordinates: [o.lon, o.lat] } });
    return { type: 'FeatureCollection', features };
  };
  const install = () => {
    const c = ringColours(theme);
    if (!map.getSource(SRC)) map.addSource(SRC, { type: 'geojson', data: (last ? data(last) : { type: 'FeatureCollection', features: [] }) as never });
    const past = last?.past ?? false;
    if (!map.getLayer('night-reach-fill')) {
      map.addLayer({ id: 'night-reach-fill', type: 'fill', source: SRC, filter: ['==', ['get', 'k'], 'reach'], paint: { 'fill-color': past ? c.past : c.fill, 'fill-opacity': theme === 'dark' ? 0.16 : 0.2 } });
      map.addLayer({ id: 'night-reach-line', type: 'line', source: SRC, filter: ['==', ['get', 'k'], 'reach'], paint: { 'line-color': past ? c.past : c.line, 'line-width': 2, ...(past ? { 'line-dasharray': [3, 2] } : {}) } });
      map.addLayer({ id: 'night-you', type: 'line', source: SRC, filter: ['==', ['get', 'k'], 'you'], paint: { 'line-color': c.you, 'line-width': 1.5, 'line-dasharray': [1.5, 2.5], 'line-opacity': 0.85 } });
      map.addLayer({ id: 'night-light', type: 'circle', source: SRC, filter: ['==', ['get', 'k'], 'light'], paint: { 'circle-radius': 6, 'circle-color': c.dot, 'circle-stroke-color': c.halo, 'circle-stroke-width': 2.5 } });
    }
  };
  map.on('style.load', install);
  onThemeChange(async (eff) => {
    if (eff === theme) return;
    theme = eff;
    const next = await loadBaseStyle(eff);
    map.setStyle(next.style, { diff: false });
  });

  const fit = (v: NightMapView) => {
    const r = Math.max(v.sighting.visibleNm ?? 0, v.distanceNm, 1);
    const sig = `${r.toFixed(1)}`;
    if (sig === fitted) return;
    fitted = sig;
    const ring = circleRing(o.lat, o.lon, r * 1.08, 32);
    const lons = ring.map((p) => p[0]);
    const lats = ring.map((p) => p[1]);
    const bounds: LngLatBoundsLike = [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]];
    map.fitBounds(bounds, { padding: 16, duration: last ? 400 : 0 });
  };

  return {
    update(v: NightMapView) {
      const pastChanged = !!last && last.past !== v.past;
      last = v;
      const src = map.getSource(SRC) as GeoJSONSource | undefined;
      if (src) src.setData(data(v) as never);
      if (pastChanged && map.getLayer('night-reach-fill')) {
        for (const id of ['night-reach-fill', 'night-reach-line', 'night-you', 'night-light']) map.removeLayer(id);
        install();
      }
      fit(v);
      const s = v.sighting;
      const eye = lengthFor(o.country, v.eyeM);
      const visWord = VISIBILITY[v.visibility].label.toLowerCase();
      const reach = s.visibleNm !== null
        ? `${v.past ? 'Shaded (dashed edge): how far out it could be seen when it showed this pattern' : 'Shaded: how far out it can be seen'}, from ${eye} above the water in ${visWord} visibility: ${nauticalMiles(s.visibleNm)}, ${s.limit === 'horizon' ? 'where it drops below the horizon' : s.geographicNm !== null ? 'where it becomes too faint' : 'its range in this visibility (its height is not recorded, so the horizon may come sooner)'}.`
        : 'How far out it can be seen is not recorded.';
      key.textContent = `${reach} Dotted: your chosen distance, ${nauticalMiles(v.distanceNm)}; you are somewhere on it, at sea. The circles ignore land: headlands, hills and buildings can hide the light, and it was never meant to be seen inland.`;
    },
  };
}
