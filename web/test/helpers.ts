/** Shared test helpers: run the pipeline's Python, build the fixture data into a temporary folder. */
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import type { Meta, SourceInfo, StationCollection, StationRecord } from '../src/lib/types.ts';
import type { RenderContext } from '../src/render/common.ts';

export const WEB = resolve(import.meta.dirname, '..');
export const PIPELINE = resolve(WEB, '../pipeline');

/** Run Python code with pipeline/ on the path; returns stdout. */
export function python(code: string, input = ''): string {
  return execFileSync('python3', ['-c', `import sys; sys.path.insert(0, ${JSON.stringify(PIPELINE)})\n${code}`], { input, encoding: 'utf8' });
}

export interface FixtureData {
  dir: string;
  meta: Meta;
  geo: StationCollection;
  records: Map<string, StationRecord>;
  redirects: Record<string, string>;
}

let cached: FixtureData | null = null;

/** pipeline/build_site_data.py run on web/fixtures, into a fresh temporary folder (once per test file). */
export function fixtureData(): FixtureData {
  if (cached) return cached;
  const dir = mkdtempSync(join(tmpdir(), 'fresnel-fixtures-'));
  execFileSync(
    'python3',
    [join(PIPELINE, 'build_site_data.py'), '--stations', join(WEB, 'fixtures/stations'), '--stories', join(WEB, 'fixtures/stories'), '--research', join(WEB, 'fixtures/research'), '--out', dir, '--quiet'],
    { encoding: 'utf8' },
  );
  const read = (p: string) => JSON.parse(readFileSync(join(dir, p), 'utf8'));
  const records = new Map<string, StationRecord>();
  for (const f of readdirSync(join(dir, 's'))) {
    const rec = read(`s/${f}`) as StationRecord;
    records.set(rec.id, rec);
  }
  cached = { dir, meta: read('meta.json'), geo: read('stations.geojson'), records, redirects: read('redirects.json').redirects };
  return cached;
}

export function contextFor(meta: Pick<Meta, 'sources'>): RenderContext {
  return {
    base: '/fresnel/',
    siteUrl: 'https://example.org/fresnel/',
    repo: 'holdTheDoorHoid/fresnel',
    sources: new Map<string, SourceInfo>(meta.sources.map((s) => [s.id, s])),
  };
}
