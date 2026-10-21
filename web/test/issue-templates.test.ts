import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { editIssueUrl, takedownIssueUrl } from '../src/render/common.ts';

const dir = resolve(import.meta.dirname, '../../.github/ISSUE_TEMPLATE');
const ids = (file: string) => [...readFileSync(resolve(dir, file), 'utf8').matchAll(/^\s+id: ([a-z_]+)$/gm)].map((m) => m[1]);
const ctx = { repo: 'holdTheDoorHoid/fresnel', siteUrl: 'https://example.org/fresnel/' };

describe('the issue forms the pages open', () => {
  it('the edit form has every field "Suggest an edit" fills in', () => {
    const url = new URL(editIssueUrl({ id: 'us-pr-punta-ejemplo', name: 'Faro de Punta Ejemplo', region: 'PR' }, ctx));
    expect(url.searchParams.get('title')).toBe('Edit: Faro de Punta Ejemplo (Puerto Rico)');
    expect(url.searchParams.get('where')).toBe('Puerto Rico, United States');
    const fields = ids('edit.yml');
    for (const key of url.searchParams.keys()) if (!['template', 'title', 'body'].includes(key)) expect(fields, key).toContain(key);
  });

  it('the takedown form has every field the photo credit link fills in', () => {
    const url = new URL(takedownIssueUrl({ id: 'ca-ns-fixture-island', name: 'Fixture Island Lighthouse' }, ctx));
    expect(url.searchParams.get('template')).toBe('takedown.yml');
    expect(url.searchParams.get('title')).toBe('Takedown: Fixture Island Lighthouse');
    const fields = ids('takedown.yml');
    for (const key of url.searchParams.keys()) if (!['template', 'title'].includes(key)) expect(fields, key).toContain(key);
  });

  it('a Canadian station names its country in the title and the "Where" box', () => {
    const url = new URL(editIssueUrl({ id: 'ca-ns-fixture-island', name: 'Fixture Island Lighthouse', region: 'NS' }, ctx));
    expect(url.searchParams.get('title')).toBe('Edit: Fixture Island Lighthouse (Nova Scotia, Canada)');
    expect(url.searchParams.get('where')).toBe('Nova Scotia, Canada');
  });
});
