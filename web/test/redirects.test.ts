import { describe, expect, it } from 'vitest';
import { resolveRedirect, type RedirectsFile } from '../src/lib/redirects.ts';
import { renderRedirectPage } from '../src/render/redirect.ts';
import { fixtureData } from './helpers.ts';

const ctx = { base: '/fresnel/', siteUrl: 'https://example.org/fresnel/' };

describe('resolveRedirect', () => {
  const file: RedirectsFile = {
    redirects: {
      'us-me-example-head-light': 'us-me-example-head',
      'us-xx-a': 'us-xx-b',
      'us-xx-b': 'us-xx-c',
      'us-xx-loop-1': 'us-xx-loop-2',
      'us-xx-loop-2': 'us-xx-loop-1',
      'us-xx-bad': 'not an id',
    },
  };

  it('sends a retired id to the station that took it', () => {
    expect(resolveRedirect('us-me-example-head-light', file)).toBe('us-me-example-head');
  });

  it('leaves every other id alone, with or without a list', () => {
    expect(resolveRedirect('us-me-other', file)).toBe('us-me-other');
    expect(resolveRedirect('us-me-other', null)).toBe('us-me-other');
    expect(resolveRedirect('us-me-other', { redirects: {} })).toBe('us-me-other');
    expect(resolveRedirect('toString', file)).toBe('toString');
  });

  it('follows a chain, stops at a loop, and ignores a target that is not an id', () => {
    expect(resolveRedirect('us-xx-a', file)).toBe('us-xx-c');
    expect(['us-xx-loop-1', 'us-xx-loop-2']).toContain(resolveRedirect('us-xx-loop-1', file));
    expect(resolveRedirect('us-xx-bad', file)).toBe('us-xx-bad');
  });

  it('reads the redirects the pipeline writes for the fixtures', () => {
    const { redirects } = fixtureData();
    expect(redirects).toEqual({ 'us-me-example-head-light': 'us-me-example-head' });
  });
});

describe('renderRedirectPage', () => {
  it('redirects at once, names the new page and is not indexed', () => {
    const page = renderRedirectPage({ id: 'us-me-example-head', name: 'Example Head Light' }, ctx);
    expect(page.startsWith('<!doctype html>')).toBe(true);
    expect(page).toContain('<meta http-equiv="refresh" content="0; url=/fresnel/s/us-me-example-head/">');
    expect(page).toContain('<link rel="canonical" href="https://example.org/fresnel/s/us-me-example-head/">');
    expect(page).toContain('<meta name="robots" content="noindex">');
    expect(page).toContain('<a href="/fresnel/s/us-me-example-head/">Example Head Light</a>');
  });

  it('escapes the name', () => {
    const page = renderRedirectPage({ id: 'us-xx-b', name: '<img src=x onerror=alert(1)> "Joe\'s"' }, ctx);
    expect(page).not.toContain('<img');
    expect(page).toContain('&lt;img src=x onerror=alert(1)&gt; &quot;Joe&#39;s&quot;');
  });
});
