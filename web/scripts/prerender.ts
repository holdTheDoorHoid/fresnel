/**
 * Prerender one static page per station and per keeper, plus the About, Credits and Keepers pages'
 * generated parts.
 * Runs after `vite build` (see package.json "build"): node scripts/prerender.ts
 *
 * Input:  dist/station.html (template with hashed asset links, from Vite)
 *         dist/data/s/<id>.json, dist/data/meta.json, dist/data/redirects.json
 *         (from pipeline/build_site_data.py, copied from public/data by Vite)
 *         dist/person.html (template), dist/data/k/index.json and dist/data/k/p/<L>.json (the keepers
 *         index, DESIGN.md 3.6; the p/ files are read here and then deleted, not published)
 * Output: dist/s/<id>/index.html; dist/k/<person id>/index.html; a redirecting page at the address
 *         of each station the merge folded into another; the key and counts in dist/about/index.html;
 *         the sources table in dist/credits/index.html; the explanation in dist/keepers/index.html;
 *         dist/sitemap.xml
 *
 * Plain string templates and synchronous file writes: ~3,000 pages take a few seconds.
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { performance } from 'node:perf_hooks';
import config from '../site.config.json' with { type: 'json' };
import { isStationId } from '../src/lib/station-id.ts';
import type { RedirectsFile } from '../src/lib/redirects.ts';
import { isSafeStoryHtml } from '../src/lib/html.ts';
import type { Meta, SourceInfo, StationRecord } from '../src/lib/types.ts';
import type { RenderContext } from '../src/render/common.ts';
import { isPersonId, chunkName, type KeeperManifest, type PersonRecord } from '../src/lib/people.ts';
import { renderKeepersMain, renderPersonHead, renderPersonMain } from '../src/render/people.ts';
import { renderRedirectPage } from '../src/render/redirect.ts';
import { countsLine, fixtureBanner, mapKey, sourcesRows, takedownEmail } from '../src/render/site.ts';
import { renderStationHead, renderStationMain } from '../src/render/station.ts';
import { escapeHtml } from '../src/lib/html.ts';

const t0 = performance.now();
const root = resolve(import.meta.dirname, '..');
const dist = join(root, 'dist');
const dataDir = join(dist, 'data');

function fail(msg: string): never {
  console.error(`prerender: ${msg}`);
  process.exit(1);
}

if (!existsSync(join(dist, 'station.html'))) fail('dist/station.html is missing. Run `vite build` first.');
if (!existsSync(join(dataDir, 'meta.json'))) {
  fail('dist/data/meta.json is missing. Run `npm run data:fixtures` (sample data) or `python3 pipeline/build_site_data.py` before building the site.');
}

const meta = JSON.parse(readFileSync(join(dataDir, 'meta.json'), 'utf8')) as Meta;
const ctx: RenderContext = {
  base: config.base,
  siteUrl: config.siteUrl,
  repo: config.repo,
  sources: new Map<string, SourceInfo>(meta.sources.map((s) => [s.id, s])),
  takedownEmail: config.takedownEmail,
  photosBase: config.photosBase ?? null,
};
const banner = fixtureBanner(meta).value;
/** Drop template indentation (about a third of each page); there is no <pre> on these pages. */
const squeeze = (s: string) => s.replace(/\n\s+/g, '\n');

/* ---------- Station pages ---------- */
const template = readFileSync(join(dist, 'station.html'), 'utf8');
for (const mark of ['<!--fr:head-->', '<!--fr:main-->', '<!--fr:banner-->']) {
  if (!template.includes(mark)) fail(`station.html template has no ${mark} placeholder`);
}
// Split once so each page is a cheap concatenation.
const [beforeHead, afterHead] = template.split('<!--fr:head-->') as [string, string];
const [headToBanner, afterBanner] = afterHead.split('<!--fr:banner-->') as [string, string];
const [bannerToMain, afterMain] = afterBanner.split('<!--fr:main-->') as [string, string];

const files = existsSync(join(dataDir, 's')) ? readdirSync(join(dataDir, 's')).filter((f) => f.endsWith('.json')) : [];
const outDir = join(dist, 's');
rmSync(outDir, { recursive: true, force: true });
mkdirSync(outDir);

let pages = 0;
let unsafeStories = 0;
const sitemap: string[] = [];
const names = new Map<string, string>();
for (const file of files) {
  const rec = JSON.parse(readFileSync(join(dataDir, 's', file), 'utf8')) as StationRecord;
  if (!isStationId(rec.id) || `${rec.id}.json` !== file) {
    console.warn(`prerender: skipped ${file}: id ${JSON.stringify(rec.id)} does not match the file name`);
    continue;
  }
  if (rec.story_html && !isSafeStoryHtml(rec.story_html)) {
    unsafeStories++;
    console.warn(`prerender: ${rec.id}: story HTML contains markup outside the allowed set; the page shows a notice instead`);
  }
  const page = squeeze(beforeHead + renderStationHead(rec, ctx).value + headToBanner + banner + bannerToMain + renderStationMain(rec, ctx).value + afterMain);
  mkdirSync(join(outDir, rec.id));
  writeFileSync(join(outDir, rec.id, 'index.html'), page);
  names.set(rec.id, rec.name);
  pages++;
  if (!rec.fixture) sitemap.push(`<url><loc>${escapeHtml(`${ctx.siteUrl}s/${rec.id}/`)}</loc>${rec.updated ? `<lastmod>${escapeHtml(rec.updated)}</lastmod>` : ''}</url>`);
}

/* ---------- Old addresses of stations the merge folded into others ---------- */
let redirectPages = 0;
const redirectsPath = join(dataDir, 'redirects.json');
if (existsSync(redirectsPath)) {
  const { redirects } = JSON.parse(readFileSync(redirectsPath, 'utf8')) as RedirectsFile;
  for (const [oldId, newId] of Object.entries(redirects ?? {})) {
    const name = names.get(newId);
    if (!isStationId(oldId) || !name || names.has(oldId)) {
      console.warn(`prerender: no redirect page for ${oldId} -> ${newId}`);
      continue;
    }
    mkdirSync(join(outDir, oldId));
    writeFileSync(join(outDir, oldId, 'index.html'), renderRedirectPage({ id: newId, name }, ctx));
    redirectPages++;
  }
}
rmSync(join(dist, 'station.html'));
rmSync(join(dataDir, '.fresnel-site-data'), { force: true }); // the pipeline's own bookkeeping file

/* ---------- About and Credits ---------- */
const fill = (path: string, parts: Record<string, string>) => {
  if (!existsSync(path)) return;
  let page = readFileSync(path, 'utf8');
  // Function replacements: a "$" in the content must not be read as a replacement pattern.
  for (const [mark, value] of Object.entries(parts)) page = page.replace(mark, () => value);
  writeFileSync(path, page);
};
fill(join(dist, 'about', 'index.html'), {
  '<!--fr:key-->': squeeze(mapKey({ headingLevel: 3, idPrefix: 'about-key' }).value),
  '<!--fr:banner-->': banner,
  '<!--fr:counts-->': escapeHtml(countsLine(meta)),
  '<!--fr:takedown-email-->': takedownEmail(config.takedownEmail).value,
});
fill(join(dist, 'credits', 'index.html'), {
  '<!--fr:sources-->': squeeze(sourcesRows(meta).value),
  '<!--fr:banner-->': banner,
  '<!--fr:built-->': escapeHtml(`Data built ${meta.built.slice(0, 10)}.`),
});

/* ---------- Keepers: the index page and one page per person (DESIGN.md 3.6) ---------- */
let personPages = 0;
const personSitemap: string[] = [];
const keeperManifestPath = join(dataDir, 'k', 'index.json');
const keeperManifest: KeeperManifest = existsSync(keeperManifestPath)
  ? (JSON.parse(readFileSync(keeperManifestPath, 'utf8')) as KeeperManifest)
  : { built: meta.built, total: 0, multi: 0, withheld: 0, letters: {}, regions: [], roles: [], stations: 0 };
fill(join(dist, 'keepers', 'index.html'), {
  '<!--fr:keepers-->': squeeze(renderKeepersMain(keeperManifest, ctx).value),
  '<!--fr:banner-->': banner,
});
if (existsSync(join(dist, 'person.html'))) {
  const ptemplate = readFileSync(join(dist, 'person.html'), 'utf8');
  for (const mark of ['<!--fr:head-->', '<!--fr:main-->', '<!--fr:banner-->']) {
    if (!ptemplate.includes(mark)) fail(`person.html template has no ${mark} placeholder`);
  }
  const [pBeforeHead, pAfterHead] = ptemplate.split('<!--fr:head-->') as [string, string];
  const [pHeadToBanner, pAfterBanner] = pAfterHead.split('<!--fr:banner-->') as [string, string];
  const [pBannerToMain, pAfterMain] = pAfterBanner.split('<!--fr:main-->') as [string, string];
  const kDir = join(dist, 'k');
  rmSync(kDir, { recursive: true, force: true });
  mkdirSync(kDir);
  for (const letter of Object.keys(keeperManifest.letters)) {
    const chunkPath = join(dataDir, 'k', 'p', `${chunkName(letter)}.json`);
    if (!existsSync(chunkPath)) fail(`${chunkPath} is missing (listed in k/index.json)`);
    const people = JSON.parse(readFileSync(chunkPath, 'utf8')) as Record<string, PersonRecord>;
    for (const [id, p] of Object.entries(people)) {
      if (!isPersonId(id) || p.id !== id) {
        console.warn(`prerender: skipped person ${JSON.stringify(id)}: not a valid person id`);
        continue;
      }
      const page = squeeze(pBeforeHead + renderPersonHead(p, ctx).value + pHeadToBanner + banner + pBannerToMain + renderPersonMain(p, ctx).value + pAfterMain);
      mkdirSync(join(kDir, id));
      writeFileSync(join(kDir, id, 'index.html'), page);
      personPages++;
      if (!p.fixture) personSitemap.push(`<url><loc>${escapeHtml(`${ctx.siteUrl}k/${id}/`)}</loc></url>`);
    }
  }
  rmSync(join(dataDir, 'k', 'p'), { recursive: true, force: true }); // read here; the browser never needs it
  rmSync(join(dist, 'person.html'));
}

/* ---------- Sitemap ---------- */
const fixed = ['', 'about/', 'credits/', 'keepers/'].map((p) => `<url><loc>${escapeHtml(ctx.siteUrl + p)}</loc></url>`);
writeFileSync(
  join(dist, 'sitemap.xml'),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${[...fixed, ...sitemap, ...personSitemap].join('\n')}\n</urlset>\n`,
);

const ms = performance.now() - t0;
console.log(
  `prerender: ${pages} station pages, ${personPages} keeper pages and ${redirectPages} redirects in ${(ms / 1000).toFixed(2)} s` +
    (meta.fixtures ? ' (FIXTURE DATA: station pages are marked noindex and left out of the sitemap)' : '') +
    (unsafeStories ? `; ${unsafeStories} unsafe stories replaced by a notice` : ''),
);
