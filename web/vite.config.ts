import { defineConfig } from 'vitest/config';
import type { Plugin } from 'vite';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import siteConfig from './site.config.json' with { type: 'json' };

const root = import.meta.dirname;

/** Which header link is the current page, from the entry's path. */
function navFor(path: string): string {
  if (path.includes('credits')) return 'credits';
  if (path.includes('about')) return 'about';
  if (path.includes('404') || path.includes('station')) return 'none';
  return 'map';
}

/**
 * Shared page chrome. Every HTML entry writes `<!--fr:header-->` and `<!--fr:footer-->`;
 * this plugin swaps in `src/partials/*.html`, fills `{{base}}`, `{{repo}}` and `{{sister}}`,
 * and marks the current nav link.
 */
function partials(): Plugin {
  const read = (name: string) => readFileSync(resolve(root, 'src/partials', name), 'utf8');
  return {
    name: 'fresnel-partials',
    transformIndexHtml: {
      order: 'pre',
      handler(html, ctx) {
        const page = navFor(ctx.path);
        const header = read('header.html').replace(`data-nav="${page}"`, `data-nav="${page}" aria-current="page"`);
        return html
          .replace('<!--fr:header-->', header)
          .replace('<!--fr:footer-->', read('footer.html'))
          .replaceAll('{{base}}', siteConfig.base)
          .replaceAll('{{repo}}', siteConfig.repo)
          .replaceAll('{{sister}}', siteConfig.sisterUrl);
      },
    },
  };
}

export default defineConfig({
  base: siteConfig.base,
  plugins: [partials()],
  server: { port: 5194, strictPort: true },
  preview: { port: 5195, strictPort: true },
  build: {
    target: 'es2022',
    // MapLibre GL is ~1 MB minified (300 KB gzipped) and only loads on the map page.
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      input: {
        map: resolve(root, 'index.html'),
        about: resolve(root, 'about/index.html'),
        credits: resolve(root, 'credits/index.html'),
        station: resolve(root, 'station.html'),
        notfound: resolve(root, '404.html'),
      },
    },
  },
  test: {
    include: ['test/**/*.test.ts'],
    environment: 'node',
  },
});
