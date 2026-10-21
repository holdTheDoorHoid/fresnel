/**
 * Fresnel's own map layers, in one place. Each overlay is an object with an `install` step that
 * adds its sources, images and layers, and runs after every style load: a theme change swaps the
 * whole base style, which drops custom sources, layers and images, so `install` must be
 * idempotent and keep its own data. OVERLAYS lists them bottom to top; a new layer (the range
 * ring of the light at night, wrecks, old charts) is one more entry.
 */
import type { ExpressionSpecification, GeoJSONSource, Map as MlMap } from 'maplibre-gl';
import { GLYPHS, GLYPH_ORDER, SILHOUETTES, drawMarker, iconName } from '../lib/icons.ts';
import type { StationCollection } from '../lib/types.ts';
import { BOLD_FONT, LABEL_FONT, type Theme } from './style.ts';

export interface LayerContext {
  theme: Theme;
  base: string;
}

export interface Overlay {
  id: string;
  install(map: MlMap, ctx: LayerContext): void;
}

/* ---------- Stations ---------- */

export const SRC = 'fr-stations';
const SEL_SRC = 'fr-selected';
export const L_CLUSTERS = 'fr-clusters';
const L_CLUSTER_COUNT = 'fr-cluster-count';
export const L_POINTS = 'fr-points';
const L_SELECTED = 'fr-selected-ring';

const ICON_PX = 26;

/** The marker image of a point: its status's glyph on its kind's silhouette (lib/icons.ts). */
export const ICON_EXPR: ExpressionSpecification = [
  'concat',
  'fr-',
  ['match', ['get', 's'], 'active', 'lit', 'inactive', 'dark', 'ruins', 'broken', 'lost', 'ghost', 'relocated', 'moved', 'replica', 'copy', 'unknown'],
  '-',
  ['match', ['get', 'k'], ['lightship', 'lightship_station'], 'ship', 'life_saving_station', 'house', 'tower'],
];

/** Lost lights drawn under everything, active lights on top (GLYPH_ORDER). */
export const SORT_EXPR: ExpressionSpecification = [
  'match',
  ['get', 's'],
  'active', GLYPH_ORDER.lit,
  'inactive', GLYPH_ORDER.dark,
  'relocated', GLYPH_ORDER.moved,
  'replica', GLYPH_ORDER.copy,
  'ruins', GLYPH_ORDER.broken,
  'lost', GLYPH_ORDER.ghost,
  GLYPH_ORDER.unknown,
];

/** Draw the marker images for this theme (dark mode flips the unlit silhouette to pale). */
function addIcons(map: MlMap, theme: Theme): void {
  const ratio = 2;
  const px = ICON_PX * ratio;
  const canvas = document.createElement('canvas');
  canvas.width = px;
  canvas.height = px;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  for (const glyph of GLYPHS) {
    for (const sil of SILHOUETTES) {
      const name = iconName(glyph, sil);
      ctx.clearRect(0, 0, px, px);
      drawMarker(ctx, glyph, sil, px, theme);
      const image = ctx.getImageData(0, 0, px, px);
      if (map.hasImage(name)) map.updateImage(name, image);
      else map.addImage(name, image, { pixelRatio: ratio });
    }
  }
}

function selectionData(coords: [number, number] | null) {
  return {
    type: 'FeatureCollection',
    features: coords ? [{ type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: coords } }] : [],
  };
}

export class StationsOverlay implements Overlay {
  readonly id = 'stations';
  #data: StationCollection = { type: 'FeatureCollection', features: [] };
  #selected: [number, number] | null = null;
  #map: MlMap | null = null;

  install(map: MlMap, ctx: LayerContext): void {
    this.#map = map;
    addIcons(map, ctx.theme);
    const dark = ctx.theme === 'dark';
    const ink = dark ? '#e8eef3' : '#10263d';
    const paper = dark ? '#0b1622' : '#ffffff';
    if (!map.getSource(SRC)) {
      map.addSource(SRC, {
        type: 'geojson',
        data: this.#data as never,
        cluster: true,
        clusterRadius: 38,
        clusterMaxZoom: 7,
        attribution: `<a href="${ctx.base}credits/">Station data: Fresnel and its sources (ODbL)</a>`,
      });
    }
    if (!map.getSource(SEL_SRC)) map.addSource(SEL_SRC, { type: 'geojson', data: selectionData(this.#selected) as never });
    if (!map.getLayer(L_CLUSTERS)) {
      map.addLayer({
        id: L_CLUSTERS,
        type: 'circle',
        source: SRC,
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': ink,
          'circle-opacity': 0.9,
          'circle-radius': ['step', ['get', 'point_count'], 13, 10, 16, 50, 20, 200, 25, 1000, 30],
          'circle-stroke-color': paper,
          'circle-stroke-width': 2.5,
        },
      });
    }
    if (!map.getLayer(L_CLUSTER_COUNT)) {
      map.addLayer({
        id: L_CLUSTER_COUNT,
        type: 'symbol',
        source: SRC,
        filter: ['has', 'point_count'],
        layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': BOLD_FONT, 'text-size': 13, 'text-allow-overlap': true },
        paint: { 'text-color': paper },
      });
    }
    if (!map.getLayer(L_SELECTED)) {
      map.addLayer({
        id: L_SELECTED,
        type: 'circle',
        source: SEL_SRC,
        paint: { 'circle-radius': 19, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': dark ? '#ffc23d' : '#b25e00', 'circle-stroke-width': 3 },
      });
    }
    if (!map.getLayer(L_POINTS)) {
      map.addLayer({
        id: L_POINTS,
        type: 'symbol',
        source: SRC,
        filter: ['!', ['has', 'point_count']],
        layout: {
          'icon-image': ICON_EXPR,
          'icon-size': ['interpolate', ['linear'], ['zoom'], 3, 0.72, 8, 0.92, 13, 1.1],
          'icon-allow-overlap': true,
          'icon-ignore-placement': true,
          'symbol-sort-key': SORT_EXPR,
          'text-field': ['step', ['zoom'], '', 9, ['get', 'n']],
          'text-font': LABEL_FONT,
          'text-size': 12,
          'text-offset': [0, 1.35],
          'text-anchor': 'top',
          'text-optional': true,
          'text-max-width': 9,
        },
        paint: {
          'text-color': dark ? '#e8eef3' : '#10263d',
          'text-halo-color': dark ? 'rgba(11,22,34,0.92)' : 'rgba(255,255,255,0.95)',
          'text-halo-width': 1.6,
        },
      });
    }
  }

  setData(data: StationCollection): void {
    this.#data = data;
    (this.#map?.getSource(SRC) as GeoJSONSource | undefined)?.setData(data as never);
  }

  setSelection(coords: [number, number] | null): void {
    this.#selected = coords;
    (this.#map?.getSource(SEL_SRC) as GeoJSONSource | undefined)?.setData(selectionData(coords) as never);
  }
}

export const stations = new StationsOverlay();

/** Bottom to top. */
export const OVERLAYS: readonly Overlay[] = [stations];

export function installOverlays(map: MlMap, ctx: LayerContext): void {
  for (const o of OVERLAYS) o.install(map, ctx);
}
