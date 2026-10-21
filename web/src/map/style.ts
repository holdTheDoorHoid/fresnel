/**
 * Base map: OpenFreeMap vector styles (keyless). Positron reads best under thousands of
 * markers because it is quiet; we tint it toward a chart palette (foam-white land, pale sea
 * blue water) and, in dark mode, a night chart (deep navy sea, slate land), and add Natural
 * Earth shaded relief at country scale.
 */
import type { StyleSpecification, LayerSpecification } from 'maplibre-gl';

export type Theme = 'light' | 'dark';

const STYLE_URL: Record<Theme, string> = {
  light: 'https://tiles.openfreemap.org/styles/positron',
  dark: 'https://tiles.openfreemap.org/styles/dark',
};

const GLYPHS = 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf';
export const LABEL_FONT = ['Noto Sans Regular'];
export const BOLD_FONT = ['Noto Sans Bold'];

/** Keep the backgrounds in step with --map-land / --map-sea in src/styles/base.css. */
export const MAP_LAND: Record<Theme, string> = { light: '#f3f5f2', dark: '#1c2834' };
export const MAP_SEA: Record<Theme, string> = { light: '#c6dbe8', dark: '#071522' };

const LIGHT_PAINT: Record<string, Record<string, string>> = {
  background: { 'background-color': MAP_LAND.light },
  park: { 'fill-color': '#e2e9dc' },
  landcover_wood: { 'fill-color': '#dfe7d8' },
  landuse_residential: { 'fill-color': '#eceeea' },
  water: { 'fill-color': MAP_SEA.light },
  waterway: { 'line-color': '#b5cfdf' },
  building: { 'fill-color': '#e4e7e2' },
};

const DARK_PAINT: Record<string, Record<string, string>> = {
  background: { 'background-color': MAP_LAND.dark },
  landcover_wood: { 'fill-color': '#1a2733' },
  landuse_park: { 'fill-color': '#1b2934' },
  water: { 'fill-color': MAP_SEA.dark },
};

function patch(style: StyleSpecification, theme: Theme): StyleSpecification {
  const paints = theme === 'light' ? LIGHT_PAINT : DARK_PAINT;
  for (const layer of style.layers) {
    const p = paints[layer.id];
    if (p && 'paint' in layer) {
      (layer as { paint?: Record<string, unknown> }).paint = { ...(layer.paint ?? {}), ...p };
    }
  }
  // Country-scale shaded relief (Natural Earth, public domain), fading out as you zoom in.
  if (style.sources.ne2_shaded && !style.layers.some((l) => 'source' in l && l.source === 'ne2_shaded')) {
    const relief: LayerSpecification = {
      id: 'fr-base-relief',
      type: 'raster',
      source: 'ne2_shaded',
      maxzoom: 8,
      paint:
        theme === 'light'
          ? { 'raster-opacity': ['interpolate', ['linear'], ['zoom'], 2, 0.42, 6, 0.3, 8, 0], 'raster-saturation': -0.35 }
          : { 'raster-opacity': ['interpolate', ['linear'], ['zoom'], 2, 0.22, 8, 0], 'raster-saturation': -0.7, 'raster-brightness-max': 0.45 },
    };
    const at = style.layers.findIndex((l) => l.id === 'background') + 1;
    style.layers.splice(at, 0, relief);
  }
  return style;
}

/** A plain fallback when OpenFreeMap cannot be reached: the stations still show. */
export function fallbackStyle(theme: Theme): StyleSpecification {
  return {
    version: 8,
    glyphs: GLYPHS,
    sources: {},
    layers: [{ id: 'background', type: 'background', paint: { 'background-color': MAP_LAND[theme] } }],
  };
}

const cache = new Map<Theme, StyleSpecification>();

export async function loadBaseStyle(theme: Theme): Promise<{ style: StyleSpecification; ok: boolean }> {
  const hit = cache.get(theme);
  if (hit) return { style: structuredClone(hit), ok: true };
  try {
    const res = await fetch(STYLE_URL[theme]);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const style = patch((await res.json()) as StyleSpecification, theme);
    cache.set(theme, style);
    return { style: structuredClone(style), ok: true };
  } catch (err) {
    console.warn('Base map style failed to load', err);
    return { style: fallbackStyle(theme), ok: false };
  }
}
