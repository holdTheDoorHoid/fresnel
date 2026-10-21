import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { buildIndex, normalize, search } from '../src/lib/search.ts';
import type { StationFeature } from '../src/lib/types.ts';
import {
  ACCESS, EVENT, KIND, LENS_ORDER, LENS_STATUS, LENS_TYPE, LINK_KIND, MATERIAL, OWNERSHIP, RELATION, SETTING, STAFFING, STATUS,
  STAY_TYPE, STRUCTURE_ROLE, STRUCTURE_STATUS, STRUCTURE_TYPE, VERIFICATION, ACCESS_ORDER, KIND_ORDER, STATUS_ORDER, VERIFICATION_ORDER,
} from '../src/lib/vocab.ts';

const vocab = JSON.parse(readFileSync(resolve(import.meta.dirname, '../../data/vocab.json'), 'utf8')) as Record<string, string[]>;

describe('site wording covers data/vocab.json', () => {
  it.each([
    ['kind', KIND],
    ['status', STATUS],
    ['structure_status', STRUCTURE_STATUS],
    ['structure_type', STRUCTURE_TYPE],
    ['structure_role', STRUCTURE_ROLE],
    ['structure_material', MATERIAL],
    ['lens_type', LENS_TYPE],
    ['lens_order', LENS_ORDER],
    ['lens_status', LENS_STATUS],
    ['access', ACCESS],
    ['verification', VERIFICATION],
    ['staffing', STAFFING],
    ['ownership', OWNERSHIP],
    ['stay_type', STAY_TYPE],
    ['setting', SETTING],
    ['event', EVENT],
    ['relation', RELATION],
    ['link_kind', LINK_KIND],
  ] as const)('every %s code has plain-language wording', (key, table) => {
    expect(vocab[key], key).toBeDefined();
    for (const code of vocab[key]!) expect(table, `${key}.${code}`).toHaveProperty(code);
  });

  it('offers every status, kind, access and verification code as a filter', () => {
    expect([...STATUS_ORDER].sort()).toEqual([...vocab.status!].sort());
    expect([...KIND_ORDER].sort()).toEqual([...vocab.kind!].sort());
    expect([...ACCESS_ORDER].sort()).toEqual([...vocab.access!].sort());
    expect([...VERIFICATION_ORDER].sort()).toEqual([...vocab.verification!].sort());
  });
});

function st(i: string, n: string, r = 'ME', o?: string, cc?: string): StationFeature {
  return { type: 'Feature', geometry: { type: 'Point', coordinates: [0, 0] }, properties: { i, n, r, k: 'lighthouse', s: 'active', v: 'facts', ...(o ? { o } : {}), ...(cc ? { cc } : {}) } };
}

describe('name search', () => {
  const index = buildIndex([
    st('us-me-portland-head', 'Portland Head Light', 'ME'),
    st('us-me-pemaquid-point', 'Pemaquid Point Light', 'ME'),
    st('ca-ns-sambro-island', 'Sambro Island Lighthouse', 'NS', 'Sambro Light', 'CA'),
    st('us-pr-punta-higuero', 'Faro de Punta Higüero', 'PR', 'Punta Higuero Light'),
    st('us-mi-big-sable-point', 'Big Sable Point Light', 'MI'),
  ]);
  const names = (q: string) => search(index, q).map((e) => e.props.i);

  it('normalises case, accents and punctuation', () => {
    expect(normalize("  Faro de Punta Higüero's  LIGHT—x ")).toBe('faro de punta higuero s light x');
  });

  it('ranks names that start with the query first (shorter first), then word matches', () => {
    expect(names('p')).toEqual(['us-me-portland-head', 'us-me-pemaquid-point', 'us-pr-punta-higuero', 'us-mi-big-sable-point']);
  });

  it('matches word prefixes in any order, including the region and its name', () => {
    expect(names('head maine')).toEqual(['us-me-portland-head']);
    expect(names('point me')).toEqual(['us-me-pemaquid-point']);
    expect(names('nova scotia')).toEqual(['ca-ns-sambro-island']);
    expect(names('canada')).toEqual(['ca-ns-sambro-island']);
    expect(names('puerto rico')).toEqual(['us-pr-punta-higuero']);
  });

  it('finds other names, accents folded, and plain substrings', () => {
    expect(names('sambro light')).toEqual(['ca-ns-sambro-island']);
    expect(names('higuero')).toEqual(['us-pr-punta-higuero']);
    expect(names('sable')).toEqual(['us-mi-big-sable-point']);
  });

  it('returns nothing for an empty query', () => {
    expect(search(index, '   ')).toEqual([]);
  });
});
