/** A keeper's page: theme only. In `npm run dev` the page is rendered here from ?id=… (production pages are prerendered). */
import '../styles/station.css';
import { initCommon } from '../ui/common.ts';
import siteConfig from '../../site.config.json';

async function devRender(): Promise<void> {
  const main = document.getElementById('main')!;
  if (!main.innerHTML.includes('fr:main')) return;
  const id = new URLSearchParams(location.search).get('id') ?? 'jonas-example';
  const { renderPersonMain } = await import('../render/people.ts');
  const base = import.meta.env.BASE_URL;
  try {
    const meta = await fetch(`${base}data/meta.json`).then((r) => r.json());
    const manifest = await fetch(`${base}data/k/index.json`).then((r) => r.json());
    let person = null;
    for (const letter of Object.keys(manifest.letters)) {
      const chunk = await fetch(`${base}data/k/p/${letter === '#' ? 'other' : letter}.json`).then((r) => r.json());
      if (chunk[id]) {
        person = chunk[id];
        break;
      }
    }
    if (!person) throw new Error(`no person ${id}`);
    const sources = new Map(meta.sources.map((s: { id: string }) => [s.id, s]));
    main.innerHTML = renderPersonMain(person, { base, siteUrl: siteConfig.siteUrl, repo: siteConfig.repo, sources } as never).value;
    document.title = `${person.name} (dev render)`;
  } catch (err) {
    main.innerHTML = `<p class="plain-page">Dev render: could not load person ${id}. Run <code>npm run data:fixtures</code> first.</p>`;
    console.error(err);
  }
}

initCommon();
if (import.meta.env.DEV) void devRender();
