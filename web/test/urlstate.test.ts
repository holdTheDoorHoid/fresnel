import { describe, expect, it } from 'vitest';
import { defaultState, formatView, parseState, serializeState, type AppState } from '../src/lib/urlstate.ts';

function roundTrip(s: AppState): AppState {
  return parseState(serializeState(s));
}

describe('URL state', () => {
  it('the default state is an empty query', () => {
    expect(serializeState(defaultState())).toBe('');
    expect(parseState('')).toEqual(defaultState());
  });

  it('round-trips every filter, the view and the selection', () => {
    const s = defaultState();
    s.filters.status = new Set(['active', 'relocated']);
    s.filters.kind = new Set(['lightship', 'lighthouse']);
    s.filters.verification = new Set(['researched', 'verified']);
    s.filters.access = new Set(['public', 'unknown']);
    s.filters.climbable = true;
    s.filters.stay = true;
    s.filters.registered = true;
    s.filters.story = true;
    s.filters.staffed = true;
    s.filters.noBoat = true;
    s.filters.region = 'PR';
    s.filters.mine = new Set(['visited', 'climbed']);
    s.view = { zoom: 7.25, lat: 43.6123, lon: -70.2079 };
    s.selected = 'us-me-portland-head';
    expect(roundTrip(s)).toEqual(s);
  });

  it('selects a station with ?s=<id>', () => {
    expect(parseState('?s=ca-ns-sambro-island').selected).toBe('ca-ns-sambro-island');
    expect(parseState('?s=../../etc').selected).toBeNull();
  });

  it('writes a readable, stable query', () => {
    const s = defaultState();
    s.filters.status = new Set(['lost', 'active']);
    s.filters.climbable = true;
    s.view = { zoom: 6, lat: 44.5, lon: -68.25 };
    expect(serializeState(s)).toBe('?at=6/44.5/-68.25&status=active,lost&climb=1');
  });

  it('keeps a view past the 180th meridian (Alaska, the Pacific)', () => {
    expect(parseState('?at=4/55/190').view).toEqual({ zoom: 4, lat: 55, lon: 190 });
  });

  it('rounds the view to sensible precision', () => {
    expect(formatView({ zoom: 7.123456, lat: 44.123456789, lon: -121.987654321 })).toBe('7.12/44.1235/-121.9877');
  });

  it('keeps a deliberately empty selection as "none"', () => {
    const s = defaultState();
    s.filters.status = new Set();
    expect(serializeState(s)).toBe('?status=none');
    expect(roundTrip(s).filters.status).toEqual(new Set());
  });

  it('treats "every value" as no filter', () => {
    expect(parseState('?status=active,inactive,ruins,lost,relocated,replica,unknown').filters.status).toBeNull();
  });

  it('reads a region (or the older state=), or a whole country', () => {
    expect(parseState('?region=ns').filters.region).toBe('NS');
    expect(parseState('?state=gu').filters.region).toBe('GU');
    expect(parseState('?country=CA').filters.country).toBe('CA');
    // a region wins over a country; nonsense is dropped
    expect(parseState('?country=CA&region=NS').filters.country).toBeNull();
    expect(parseState('?country=XX').filters.country).toBeNull();
    expect(parseState('?region=ZZ').filters.region).toBeNull();
  });

  it('drops unknown or malformed values instead of failing', () => {
    const s = parseState('?status=active,bogus&kind=castle&at=99/1/2&mine=nope&climb=yes&access=everything');
    expect(s.filters.status).toEqual(new Set(['active']));
    expect(s.filters.kind).toBeNull();
    expect(s.view).toBeNull();
    expect(s.filters.mine).toBeNull();
    expect(s.filters.climbable).toBe(false);
    expect(s.filters.access).toBeNull();
  });
});
