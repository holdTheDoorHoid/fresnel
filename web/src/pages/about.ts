/** About page: theme and the checklist dialog. The key and counts are filled at build time (in dev, here). */
import '../styles/pages.css';
import { initCommon } from '../ui/common.ts';
import { initChecklistOnPage } from '../ui/checklist-ui.ts';

async function devFill(): Promise<void> {
  const counts = document.querySelector('[data-fr-counts]');
  if (!counts || document.querySelector('.map-key')) return;
  const { mapKey, countsLine } = await import('../render/site.ts');
  document.getElementById('key-h')?.nextElementSibling?.insertAdjacentHTML('afterend', mapKey({ headingLevel: 3, idPrefix: 'about-key' }).value);
  try {
    const meta = await fetch(`${import.meta.env.BASE_URL}data/meta.json`).then((r) => r.json());
    counts.textContent = countsLine(meta);
  } catch {
    /* no data in dev: leave it empty */
  }
}

initCommon();
initChecklistOnPage();
if (import.meta.env.DEV) void devFill();
