/** Enhancements for a prerendered station page: theme, checklist buttons, copy coordinates, the light at night. */
import '../styles/station.css';
import { enhanceCoords, initCommon } from '../ui/common.ts';
import { initChecklistOnPage } from '../ui/checklist-ui.ts';
import siteConfig from '../../site.config.json';

async function devRender(): Promise<void> {
  // `npm run dev` serves the raw template; render a station client-side from ?id=… so the page
  // can be worked on without running the prerender. Production pages are already static HTML.
  const main = document.getElementById('main')!;
  if (!main.innerHTML.includes('fr:main')) return;
  const id = new URLSearchParams(location.search).get('id') ?? 'us-me-example-head';
  const { renderStationMain } = await import('../render/station.ts');
  const { fixtureBanner } = await import('../render/site.ts');
  const base = import.meta.env.BASE_URL;
  try {
    const [rec, meta] = await Promise.all([
      fetch(`${base}data/s/${id}.json`).then((r) => r.json()),
      fetch(`${base}data/meta.json`).then((r) => r.json()),
    ]);
    const ctx = { base, siteUrl: siteConfig.siteUrl, repo: siteConfig.repo, sources: new Map(meta.sources.map((s: { id: string }) => [s.id, s])) };
    main.innerHTML = renderStationMain(rec, ctx as never).value;
    main.insertAdjacentHTML('beforebegin', fixtureBanner(meta).value);
    document.title = `${rec.name} (dev render)`;
  } catch (err) {
    main.innerHTML = `<p class="plain-page">Dev render: could not load station ${id}. Run <code>npm run data:fixtures</code> first.</p>`;
    console.error(err);
  }
}

async function start(): Promise<void> {
  initCommon();
  if (import.meta.env.DEV) await devRender();
  initChecklistOnPage();
  enhanceCoords();
  // The light at night: its own chunk, so a station without a light never loads it.
  const night = document.querySelector<HTMLElement>('[data-night]');
  if (night) void import('../ui/night.ts').then((m) => m.initNight(night));
}

void start();
