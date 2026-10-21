/**
 * The station page and the map panel, rendered from the fixture stations exactly as the site
 * gets them (pipeline/build_site_data.py run on web/fixtures).
 */
import { describe, expect, it } from 'vitest';
import { SECTIONS, recordSummary, renderPanel, renderPanelStub, renderStationHead, renderStationMain } from '../src/render/station.ts';
import { countsLine, sourcesRows } from '../src/render/site.ts';
import { contextFor, fixtureData } from './helpers.ts';

const { records, meta, geo } = fixtureData();
const ctx = contextFor(meta);
const page = (id: string) => renderStationMain(records.get(id)!, ctx).value;
/** The words a reader sees: tags dropped, entities left as they are. */
const text = (h: string) => h.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');

describe('every fixture station renders cleanly', () => {
  it('has the fixtures it should (the hidden decoy and the merged duplicate are not published)', () => {
    expect([...records.keys()].sort()).toEqual(geo.features.map((f) => f.properties.i).sort());
    expect(records.has('us-fl-mini-golf-decoy')).toBe(false);
    expect(records.has('us-me-example-head-light')).toBe(false);
    expect(records.size).toBe(14);
  });

  it.each([...records.keys()])('%s never shows "null", "undefined" or "NaN"', (id) => {
    const rec = records.get(id)!;
    for (const out of [renderStationMain(rec, ctx).value, renderStationHead(rec, ctx).value, renderPanel(rec, ctx).value]) {
      expect(text(out)).not.toMatch(/\b(null|undefined|NaN)\b|\[object/);
      expect(out).not.toMatch(/="(null|undefined)"/);
    }
  });

  it.each([...records.keys()])('%s puts the practical sections first, in order', (id) => {
    const out = page(id);
    const at = SECTIONS.map((s) => out.indexOf(`<section class="s-section" id="${s.id}"`)).filter((i) => i >= 0);
    expect(at).toEqual([...at].sort((a, b) => a - b));
    expect(out.indexOf('id="visit"')).toBeLessThan(out.indexOf('id="facts"'));
    expect(out.indexOf('id="facts"')).toBeLessThan(out.indexOf('id="history"'));
    // every "On this page" link points at a section that is there
    const jump = out.slice(out.indexOf('<nav class="jump"'), out.indexOf('</nav>', out.indexOf('<nav class="jump"')));
    for (const m of jump.matchAll(/href="#([a-z-]+)"/g)) expect(out, m[1]).toContain(`id="${m[1]}"`);
  });

  it.each([...records.keys()])('%s has the status badge, the checklist and Suggest an edit', (id) => {
    const rec = records.get(id)!;
    const out = page(id);
    expect(out).toMatch(new RegExp(`<li class="badge badge-status status-${rec.status}"[^>]*><svg class="mk mk-`));
    expect(out.includes('badge-unverified')).toBe(rec.verification === 'unverified');
    for (const m of ['visited', 'climbed', 'stayed', 'want']) expect(out).toContain(`data-mark="${m}"`);
    expect(out).toContain('https://github.com/holdTheDoorHoid/fresnel/issues/new?template=edit.yml');
  });

  it.each([...records.keys()])('%s credits every source it uses, with its credit line', (id) => {
    const rec = records.get(id)!;
    const out = page(id);
    for (const s of rec.sources ?? []) {
      expect(out).toContain(`id="src-${s.source}"`);
      const info = meta.sources.find((x) => x.id === s.source);
      if (info?.credit) expect(out).toContain(info.credit.replace(/&/g, '&amp;'));
    }
  });
});

describe('Example Head Light (a researched lighthouse with a story and keepers)', () => {
  const out = page('us-me-example-head');

  it('reads the light in plain words and gives US units feet first', () => {
    expect(out).toContain('<code class="char">Fl W 4s</code>: one white flash every 4 seconds.');
    expect(out).toContain('98 ft (30 m)');
    expect(out).toContain('24 nmi (44 km)');
    expect(out).toContain('80 ft (24 m) tall');
    expect(out).toContain('Fourth order Fresnel lens');
  });

  it('lists the chapters and links them to the story\'s headings', () => {
    expect(out).toContain('In this history');
    for (const c of records.get('us-me-example-head')!.chapters!) {
      expect(out).toContain(`<a href="#${c.id}">${c.title}</a>`);
      expect(out).toContain(`<h3 id="${c.id}">`);
    }
    expect(out).toContain('class="footnotes"');
    expect(out).toContain('Researched 21 Oct 2026, fact-checked');
  });

  it('shows the keepers roster and the research sources', () => {
    expect(out).toContain('<table class="keepers">');
    expect(out).toContain('Hannah Example');
    expect(out).toContain('id="research-sources"');
    expect(out).toContain('id="rs-1"');
  });

  it('says plainly where sources disagree', () => {
    expect(out).toContain('Sources disagree on the year the light was first lit.');
    expect(out).toContain('<a class="disagree" href="#conflicts">sources disagree</a>');
  });

  it('shows the photo hotlinked from its source with credit, and the stay', () => {
    expect(out).toContain('src="https://commons.wikimedia.org/wiki/Special:FilePath/Example.jpg?width=640"');
    expect(out).toContain('Photo: Wikimedia Commons');
    expect(out).toContain('href="https://commons.wikimedia.org/wiki/File:Example.jpg"');
    expect(out).toContain('Volunteer keeper program');
    expect(out).toContain('See it on example.org');
  });

  it('links related stations and the timeline', () => {
    expect(out).toContain('<a href="/fresnel/s/us-nj-sample-beach-life-saving-station/">Sample Beach Life-Saving Station</a>');
    expect(out).toMatch(/<span class="tl-year">1855<\/span>\s*<span class="tl-body"><span class="tl-what">Rebuilt<\/span>/);
  });

  it('has a head with title, canonical address and (as a fixture) noindex', () => {
    const head = renderStationHead(records.get('us-me-example-head')!, ctx).value;
    expect(head).toContain('<title>Example Head Light: lighthouse in Maine · Fresnel</title>');
    expect(head).toContain('<link rel="canonical" href="https://example.org/fresnel/s/us-me-example-head/">');
    expect(head).toContain('<meta name="robots" content="noindex">');
  });
});

describe('stations without a history', () => {
  it('say so, with a summary built only from the record and labelled as such', () => {
    const out = page('us-nc-example-shoal');
    expect(out).toContain('No history has been written for this station yet.');
    expect(out).toContain('From the record, not a researched history');
    expect(recordSummary(records.get('us-nc-example-shoal')!)).toBe(
      'Example Shoal Light was a lighthouse in Carteret County, North Carolina. Its light was first lit in 1867 and went out in 1918. Swept away by ice in 1918.',
    );
    expect(recordSummary(records.get('us-me-example-head')!)).toBe('Example Head Light is a lighthouse in Cumberland County, Maine. Its light was first lit in 1791 and still shines.');
  });
});

describe('each kind and status says what it is', () => {
  it('a lost light: nothing to climb, the lost marker and its meaning', () => {
    const out = page('us-nc-example-shoal');
    expect(out).toContain('Lost: only the site is left.');
    expect(out).not.toContain('Can you climb it?');
    expect(out).toContain('mk mk-ghost');
    expect(out).toContain('F W</code>: a steady white light.');
    expect(out).toContain('As last recorded.');
  });

  it('a Canadian station reads metres first, and its place with the country', () => {
    const out = page('ca-ns-fixture-island');
    expect(out).toContain('43 m (141 ft)');
    expect(out).toContain('Halifax County, Nova Scotia, Canada');
    expect(out).toContain('25 m (82 ft) tall');
  });

  it('a territory is written in full', () => {
    expect(page('us-pr-punta-ejemplo')).toContain('Cabo Rojo, Puerto Rico');
    expect(page('us-gu-sample-point')).toContain('Piti, Guam');
    expect(page('us-as-example-reef')).toContain('Eastern District, American Samoa');
  });

  it('a life-saving station has no light and says "Standing", not "light out"', () => {
    const out = page('us-nj-sample-beach-life-saving-station');
    expect(out).toContain('<span>Standing</span>');
    expect(out).not.toContain('No details of the light');
  });

  it('a range shows both structures, the rear one with its own position', () => {
    const out = page('us-mi-sample-harbor-range');
    expect(out).toContain('Front light (front range light)');
    expect(out).toContain('Rear light (rear range light)');
    expect(out).toContain('Stands apart from the station’s pin');
  });

  it('a moved, a replica and an unknown station say so', () => {
    expect(page('ca-bc-fixture-rock')).toContain('<strong>Moved.</strong>');
    expect(page('us-wi-sample-bay-replica')).toContain('This is a replica of:');
    const unknown = page('us-gu-sample-point');
    expect(unknown).toContain('Status unknown');
    expect(unknown).toContain('<code class="char">Q(6)+LFl W 15s</code><span class="sub">As the source writes it.</span>');
  });
});

describe('the map panel', () => {
  it('sums up the facts and links the full page', () => {
    const out = renderPanel(records.get('us-me-example-head')!, ctx).value;
    expect(out).toContain('<h2 id="panel-title" tabindex="-1">Example Head Light</h2>');
    expect(out).toContain('Since 1791');
    expect(out).toContain('href="/fresnel/s/us-me-example-head/"');
    expect(out).toContain('You can climb it');
  });

  it('says when filters hide the station', () => {
    expect(renderPanel(records.get('us-me-example-head')!, ctx, { hiddenByFilters: true }).value).toContain('Your filters hide this station');
  });

  it('shows a stub from the map point while the record loads', () => {
    const p = geo.features.find((f) => f.properties.i === 'ca-ns-fixture-island')!.properties;
    const out = renderPanelStub(p, ctx, 'Loading details…').value;
    expect(out).toContain('Halifax County, Nova Scotia, Canada');
    expect(out).toContain('badge-unverified');
  });
});

describe('site pages from meta.json', () => {
  it('lists every source with its licence, credit line and counts', () => {
    const rows = sourcesRows(meta).value;
    for (const s of meta.sources) {
      expect(rows).toContain(`id="source-${s.id}"`);
      if (s.license) expect(rows).toContain(s.license);
    }
    expect(text(rows)).not.toMatch(/\b(null|undefined)\b/);
    expect(countsLine(meta)).toBe('14 stations on the map, 1 with a written history, 1 with a keepers roster.');
  });
});
