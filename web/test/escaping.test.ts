import { describe, expect, it } from 'vitest';
import { escapeHtml, html, isSafeStoryHtml, raw, safeUrl } from '../src/lib/html.ts';
import type { StationRecord } from '../src/lib/types.ts';
import { renderPanel, renderStationHead, renderStationMain } from '../src/render/station.ts';
import { python } from './helpers.ts';

const ctx = { base: '/fresnel/', siteUrl: 'https://example.org/fresnel/', repo: 'holdTheDoorHoid/fresnel', sources: new Map() };

/** Run the pipeline's story converter (pipeline/story_md.py) on `md`. */
function pythonStory(md: string): string {
  return python('from story_md import markdown_to_html; sys.stdout.write(markdown_to_html(sys.stdin.read()))', md);
}

describe('escapeHtml and the html template', () => {
  it('escapes the five HTML-special characters', () => {
    expect(escapeHtml(`<a href="x">'&'</a>`)).toBe('&lt;a href=&quot;x&quot;&gt;&#39;&amp;&#39;&lt;/a&gt;');
  });

  it('escapes interpolations but not nested safe HTML', () => {
    const name = '<img src=x onerror=alert(1)>';
    expect(html`<p title="${name}">${name} ${html`<b>ok</b>`}</p>`.value).toBe('<p title="&lt;img src=x onerror=alert(1)&gt;">&lt;img src=x onerror=alert(1)&gt; <b>ok</b></p>');
  });

  it('renders null, undefined and false as nothing, and joins arrays', () => {
    expect(html`${null}${undefined}${false}${['a', '<', raw('<i>')]}`.value).toBe('a&lt;<i>');
  });
});

describe('safeUrl', () => {
  it.each(['https://www.lighthousefriends.com/light.asp?ID=1', 'http://example.org/x', 'mailto:a@b.org', '/fresnel/s/x/', '#fn-1', 'relative/path'])('allows %s', (u) => expect(safeUrl(u)).toBe(u));
  it.each(['javascript:alert(1)', 'JavaScript:alert(1)', ' javascript:alert(1)', 'java\tscript:alert(1)', 'java\nscript:x', 'data:text/html,<b>', 'vbscript:x', 'file:///etc/passwd'])('rejects %j', (u) =>
    expect(safeUrl(u)).toBeNull(),
  );
  it('rejects non-strings and empty strings', () => {
    expect(safeUrl(null)).toBeNull();
    expect(safeUrl(42)).toBeNull();
    expect(safeUrl('  ')).toBeNull();
  });
});

describe('isSafeStoryHtml', () => {
  it('accepts what the converter produces', () => {
    expect(isSafeStoryHtml(pythonStory('## The place\n\nA *granite* point & a **light**.[^1][^2]\n\n> A quote.\n\n- one\n- two\n\n[^1]: Source, https://example.org/a?b=1&c=2.\n[^2]: Another.\n'))).toBe(true);
  });
  it.each([
    '<script>alert(1)</script>',
    '<p onclick="x">hi</p>',
    '<img src="x">',
    '<a href="javascript:alert(1)">x</a>',
    '<a href="&#106;avascript:alert(1)">x</a>',
    '<p style="color:red">x</p>',
    '<!-- comment -->',
    '<p>a < b</p>',
    "<a href='x'>single quotes</a>",
    '</p class="x">',
    '<svg><script>x</script></svg>',
  ])('rejects %s', (markup) => expect(isSafeStoryHtml(markup)).toBe(false));
});

describe('story Markdown converter (pipeline/story_md.py)', () => {
  it('escapes raw HTML and script tags', () => {
    const out = pythonStory('Hello <script>alert(1)</script> and <img src=x onerror=alert(2)>\n');
    expect(out).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(out).not.toMatch(/<script|<img/);
    expect(isSafeStoryHtml(out)).toBe(true);
  });

  it('drops dangerous link targets but keeps the link text', () => {
    const out = pythonStory('[click](javascript:alert(1)) [ok](https://example.org/x?a=1&b=2) [data](data:text/html;base64,xx)\n');
    expect(out).not.toMatch(/javascript:|data:/i);
    expect(out).toContain('<a href="https://example.org/x?a=1&amp;b=2" rel="noopener noreferrer">ok</a>');
    expect(isSafeStoryHtml(out)).toBe(true);
  });

  it('gives chapters ids the page can link to', () => {
    const out = pythonStory('## The keepers\n\nText.\n');
    expect(out).toContain('<h3 id="s-the-keepers">The keepers</h3>');
  });
});

describe('station page rendering escapes hostile data', () => {
  const evil: StationRecord = {
    id: 'us-me-evil',
    name: '<img src=x onerror=alert(1)>Evil Light',
    other_names: ['"><script>alert(2)</script>'],
    region: 'ME',
    county: '<b>County</b>',
    kind: 'lighthouse',
    location: { lat: 43, lon: -70, precision: 'exact', from: 'osm' },
    status: 'active',
    status_note: '<script>alert(3)</script>',
    verification: 'unverified',
    access: { level: 'private', note: '<script>alert(4)</script>' },
    light: { characteristic: '<script>x</script>', lens: { type: '<i>x</i>', where: '<b>y</b>' }, fog_signal: '<b>horn</b>' },
    structures: [{ role: 'tower', name: '<i>t</i>', note: '<script>n</script>', location: { lat: 43, lon: -70 } }],
    registers: [{ register: 'NRHP', number: '<b>1</b>', url: 'javascript:alert(5)' }],
    stay: { type: 'rental', provider: '<b>p</b>', url: 'javascript:alert(6)', note: '<i>n</i>' },
    events: [{ year: 1900, event: 'built', note: '<script>alert(7)</script>' }],
    related: [{ id: 'us-me-other', relation: 'related', name: '<script>r</script>' }],
    photos: [{ thumb_url: 'javascript:alert(8)', credit: '<b>me</b>' }, { thumb_url: 'https://example.org/p.jpg', credit: 'x', source_url: 'javascript:alert(9)', caption: '"><b>c</b>' }],
    links: [{ label: 'bad', url: 'javascript:alert(10)' }],
    sources: [{ source: '<script>', fields: ['<x>'] }],
    conflicts: [{ field: '<f>', values: [{ source: 'osm', value: '<script>alert(11)</script>' }], note: '<script>' }],
    keepers: [{ name: '<script>k</script>', role: '<b>r</b>', from: '<i>', note: '<script>', cite: [1] }],
    research_sources: [{ n: 1, title: '<script>t</script>', url: 'javascript:alert(12)' }],
    chapters: [{ id: 's-x"><script>', title: '<script>' }],
    story_html: '<p>ok</p><script>alert(13)</script>',
  };

  const outputs = {
    main: renderStationMain(evil, ctx).value,
    head: renderStationHead(evil, ctx).value,
    panel: renderPanel(evil, ctx).value,
  };

  it.each(Object.keys(outputs))('%s has no live script, handler or javascript: URL', (key) => {
    const out = outputs[key as keyof typeof outputs];
    expect(out).not.toMatch(/<script/i);
    expect(out).not.toMatch(/<img src=x/i);
    expect(out).not.toMatch(/<b>|<i>/);
    expect(out).not.toMatch(/(href|src)="\s*javascript:/i);
  });

  it('shows a notice instead of an unsafe story', () => {
    expect(outputs.main).toContain('history could not be shown');
    expect(outputs.main).not.toContain('<p>ok</p>');
  });

  it('pre-fills the Suggest an edit issue with the template, title, id, name and page URL', () => {
    const m = /href="(https:\/\/github\.com\/holdTheDoorHoid\/fresnel\/issues\/new\?[^"]+)"/.exec(outputs.main);
    expect(m).not.toBeNull();
    const url = new URL(m![1]!.replace(/&amp;/g, '&'));
    expect(url.searchParams.get('template')).toBe('edit.yml');
    expect(url.searchParams.get('title')).toBe(`Edit: ${evil.name} (Maine)`);
    expect(url.searchParams.get('station_id')).toBe('us-me-evil');
    expect(url.searchParams.get('station_name')).toBe(evil.name);
    expect(url.searchParams.get('page_url')).toBe('https://example.org/fresnel/s/us-me-evil/');
    expect(url.searchParams.get('body')).toContain('https://example.org/fresnel/s/us-me-evil/');
    expect(url.searchParams.get('body')).toContain('us-me-evil');
  });
});
