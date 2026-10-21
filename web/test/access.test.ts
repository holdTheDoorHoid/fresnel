import { describe, expect, it } from 'vitest';
import { accessLabels, accessLabelsFromProps, isProminent } from '../src/lib/access.ts';
import type { StationRecord } from '../src/lib/types.ts';
import { renderPanel, renderStationMain } from '../src/render/station.ts';
import { contextFor, fixtureData } from './helpers.ts';

type In = Pick<StationRecord, 'access' | 'ownership' | 'visit' | 'staffing'>;
const ids = (r: In) => accessLabels(r).map((l) => l.id);

describe('access labels', () => {
  it('labels each access level', () => {
    expect(ids({ access: { level: 'public' } })).toEqual(['public']);
    expect(ids({ access: { level: 'private' } })).toEqual(['private']);
    expect(ids({ access: { level: 'closed' } })).toEqual(['closed']);
    expect(ids({ access: { level: 'permission' } })).toEqual(['permission']);
    expect(ids({ access: { level: 'restricted' } })).toEqual(['restricted']);
    expect(ids({})).toEqual(['unknown']);
  });

  it('gives tribal land its own label', () => {
    expect(ids({ access: { level: 'permission' }, ownership: 'tribal' })).toEqual(['tribal']);
    expect(accessLabels({ access: { level: 'permission' }, ownership: 'tribal' })[0]!.label).toBe('Tribal land: permission required');
    // private or closed tribal land says that instead
    expect(ids({ access: { level: 'closed' }, ownership: 'tribal' })).toEqual(['closed']);
  });

  it('labels boat-only stations and staffed lightstations, most serious first', () => {
    expect(ids({ access: { level: 'permission' }, visit: { boat_only: true }, staffing: { status: 'staffed' } })).toEqual(['permission', 'staffed', 'boat_only']);
    expect(ids({ access: { level: 'public' }, visit: { boat_only: true } })).toEqual(['boat_only', 'public']);
    expect(ids({ visit: { boat_only: true } })).toEqual(['boat_only']);
    expect(ids({ access: { level: 'public' }, staffing: { status: 'volunteer' } })).toEqual(['volunteer', 'public']);
  });

  it('calls a staffed lightstation the keepers\' home and workplace, and warns rather than hides', () => {
    const [l] = accessLabels({ staffing: { status: 'staffed' } });
    expect(l!.label).toBe('A working lightstation');
    expect(l!.meaning).toContain('home and workplace');
    expect(l!.tone).toBe('caution');
  });

  it('makes private, closed, permission, restricted, boat-only and staffed prominent; public is not', () => {
    for (const level of ['private', 'closed', 'permission', 'restricted']) expect(isProminent(accessLabels({ access: { level } })[0]!), level).toBe(true);
    expect(isProminent(accessLabels({ visit: { boat_only: true } })[0]!)).toBe(true);
    expect(isProminent(accessLabels({ access: { level: 'public' } })[0]!)).toBe(false);
  });

  it('reads the same from a map point', () => {
    expect(accessLabelsFromProps({ a: 'permission', bo: 1, sf: 'staffed' }).map((l) => l.id)).toEqual(['permission', 'staffed', 'boat_only']);
    expect(accessLabelsFromProps({}).map((l) => l.id)).toEqual(['unknown']);
    expect(accessLabelsFromProps({ a: 'permission', tr: 1 }).map((l) => l.id)).toContain('tribal');
  });
});

describe('access labels on the pages', () => {
  const { records, meta } = fixtureData();
  const ctx = contextFor(meta);

  it('puts the warnings at the top of a staffed island lightstation\'s page and in its panel', () => {
    const rec = records.get('ca-ns-fixture-island')!;
    const page = renderStationMain(rec, ctx).value;
    const head = page.slice(0, page.indexOf('<div class="s-grid">'));
    for (const t of ['Permission required', 'A working lightstation', 'Reached only by boat']) expect(head, t).toContain(`<p class="notice-title">${t}</p>`);
    expect(head).toContain('A working lightstation and the keepers'); // the record's own note
    const panel = renderPanel(rec, ctx).value;
    expect(panel).toContain('A working lightstation');
    expect(panel).toContain('Reached only by boat');
  });

  it('labels a private home, Coast Guard property, and tribal land', () => {
    expect(renderStationMain(records.get('us-nj-sample-beach-life-saving-station')!, ctx).value).toContain('<p class="notice-title">Private property</p>');
    expect(renderStationMain(records.get('us-ak-fixture-cape')!, ctx).value).toContain('<p class="notice-title">Closed to visitors</p>');
    expect(renderStationMain(records.get('us-wa-example-spit')!, ctx).value).toContain('<p class="notice-title">Tribal land: permission required</p>');
  });

  it('shows open access in Visit, climb and stay, not as a warning', () => {
    const page = renderStationMain(records.get('us-me-example-head')!, ctx).value;
    expect(page).not.toContain('class="notice tone-ok"');
    expect(page).toContain('<strong>Open to the public.</strong>');
  });
});
