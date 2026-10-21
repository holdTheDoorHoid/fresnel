/** Credits page: theme and the checklist dialog. The sources table is filled at build time (in dev, here). */
import '../styles/pages.css';
import { initCommon } from '../ui/common.ts';
import { initChecklistOnPage } from '../ui/checklist-ui.ts';

async function devFill(): Promise<void> {
  const body = document.querySelector('[data-fr-sources]');
  if (!body || body.children.length) return;
  const { sourcesRows } = await import('../render/site.ts');
  try {
    const meta = await fetch(`${import.meta.env.BASE_URL}data/meta.json`).then((r) => r.json());
    body.innerHTML = sourcesRows(meta).value;
  } catch {
    body.innerHTML = '<tr><td colspan="5">Run <code>npm run data:fixtures</code> to see the sources.</td></tr>';
  }
}

initCommon();
initChecklistOnPage();
if (import.meta.env.DEV) void devFill();
