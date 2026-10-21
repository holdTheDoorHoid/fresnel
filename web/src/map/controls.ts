/**
 * The map's controls, in one place: zoom, "show my location", the attribution, the scales and
 * the "Go to" jumps between the far-apart places Fresnel covers. A new control (the year slider,
 * the old charts switch) is one more line in `addControls`.
 */
import { AttributionControl, GeolocateControl, NavigationControl, ScaleControl, type IControl, type Map as MlMap } from 'maplibre-gl';
import { html } from '../lib/html.ts';
import { MAP_VIEWS } from '../lib/views.ts';

/** "Go to": a button that opens a list of places (Lower 48, Great Lakes, Alaska, the Pacific…). */
export class JumpControl implements IControl {
  #el: HTMLDivElement | null = null;
  #map: MlMap | null = null;

  onAdd(map: MlMap): HTMLElement {
    this.#map = map;
    const el = document.createElement('div');
    el.className = 'maplibregl-ctrl fr-jump';
    el.innerHTML = html`<button type="button" class="fr-jump-btn" aria-expanded="false" aria-controls="fr-jump-list">
        <svg width="16" height="16" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><circle cx="10" cy="10" r="7.3" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 2.7v3M10 14.3v3M2.7 10h3M14.3 10h3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="m10 6.6 1.4 3.4L10 13.4 8.6 10Z" fill="currentColor"/></svg>
        <span>Go to</span>
      </button>
      <ul class="fr-jump-list" id="fr-jump-list" hidden>${MAP_VIEWS.map((v) => html`<li><button type="button" data-view="${v.id}" title="${v.about}">${v.label}</button></li>`)}</ul>`.value;
    const btn = el.querySelector<HTMLButtonElement>('.fr-jump-btn')!;
    const list = el.querySelector<HTMLUListElement>('.fr-jump-list')!;
    const setOpen = (open: boolean, focusBack = false) => {
      list.hidden = !open;
      btn.setAttribute('aria-expanded', String(open));
      if (open) list.querySelector<HTMLButtonElement>('button')?.focus();
      else if (focusBack) btn.focus();
    };
    btn.addEventListener('click', () => setOpen(list.hidden === true));
    list.addEventListener('click', (e) => {
      const b = (e.target as Element).closest<HTMLElement>('[data-view]');
      const v = b ? MAP_VIEWS.find((x) => x.id === b.dataset.view) : undefined;
      if (!v) return;
      setOpen(false, true);
      this.#map?.fitBounds(v.bounds, { padding: 24, duration: 800, essential: true });
    });
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !list.hidden) {
        e.stopPropagation();
        setOpen(false, true);
      }
    });
    document.addEventListener('click', (e) => {
      if (!list.hidden && !el.contains(e.target as Node)) setOpen(false);
    });
    this.#el = el;
    return el;
  }

  onRemove(): void {
    this.#el?.remove();
  }
}

export function addControls(map: MlMap): void {
  map.addControl(new AttributionControl({ compact: true }), 'bottom-right');
  map.addControl(new NavigationControl({ showCompass: false }), 'top-right');
  map.addControl(new GeolocateControl({ positionOptions: { enableHighAccuracy: false }, trackUserLocation: false }), 'top-right');
  // Distances at sea are nautical miles, with kilometres alongside (DESIGN.md 3.3).
  map.addControl(new ScaleControl({ unit: 'nautical', maxWidth: 110 }), 'bottom-left');
  map.addControl(new ScaleControl({ unit: 'metric', maxWidth: 110 }), 'bottom-left');
  map.addControl(new JumpControl(), 'bottom-left');
}
