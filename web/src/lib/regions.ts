/**
 * Countries and their regions (states, territories, provinces), mirroring pipeline/regions.py
 * (DESIGN.md 3.3). test/regions.test.ts runs the Python module and checks that the two agree:
 * the names, which codes are territories, and how a local unit is written.
 *
 * - A station's `country` is "US" or "CA"; its `region` the postal code inside it ("ME", "PR",
 *   "GU", "NS"). The US territories (Puerto Rico, the US Virgin Islands, Guam, the Northern
 *   Mariana Islands, American Samoa, the Minor Outlying Islands) are regions of the US.
 * - Region codes are unique across the countries listed, so a code alone says its country.
 *
 * Page copy (DESIGN.md 3.3): a territory is written in full ("Puerto Rico", "Guam"), a Canadian
 * place with its country ("Nova Scotia, Canada"), a US county with its word ("Cumberland County",
 * "Plaquemines Parish", "Nome Census Area"), a territory's or Canada's local unit as given.
 */

export const COUNTRY_NAMES: Record<string, string> = { US: 'United States', CA: 'Canada' };
/** As running text says it: "in the United States", "in Canada". */
export const COUNTRY_IN_TEXT: Record<string, string> = { US: 'the United States', CA: 'Canada' };
/** [one, many]: "state or territory" / "provinces and territories". */
export const REGION_WORDS: Record<string, [string, string]> = {
  US: ['state or territory', 'states and territories'],
  CA: ['province or territory', 'provinces and territories'],
};
/** Listed in this order: the US's states first, then its territories, then Canada. */
export const COUNTRY_ORDER = ['US', 'CA'] as const;

export const US_STATES: Record<string, string> = {
  AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California',
  CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', FL: 'Florida', GA: 'Georgia',
  HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa',
  KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
  MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi',
  MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire',
  NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina',
  ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania',
  RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee',
  TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington',
  WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming',
};
export const US_OTHER: Record<string, string> = {
  DC: 'District of Columbia',
  PR: 'Puerto Rico', VI: 'U.S. Virgin Islands', GU: 'Guam',
  MP: 'Northern Mariana Islands', AS: 'American Samoa',
  UM: 'U.S. Minor Outlying Islands',
};
/** The territories, in listing order ("Puerto Rico, a US territory"). */
export const US_TERRITORIES = ['PR', 'VI', 'GU', 'MP', 'AS', 'UM'] as const;
export const CA_PROVINCES: Record<string, string> = {
  AB: 'Alberta', BC: 'British Columbia', MB: 'Manitoba', NB: 'New Brunswick',
  NL: 'Newfoundland and Labrador', NS: 'Nova Scotia', NT: 'Northwest Territories',
  NU: 'Nunavut', ON: 'Ontario', PE: 'Prince Edward Island', QC: 'Quebec',
  SK: 'Saskatchewan', YT: 'Yukon',
};
export const REGIONS_BY_COUNTRY: Record<string, Record<string, string>> = { US: { ...US_STATES, ...US_OTHER }, CA: CA_PROVINCES };

/** Every region code and its English name. */
export const REGIONS: Record<string, string> = { ...US_STATES, ...US_OTHER, ...CA_PROVINCES };

const REGION_COUNTRY: Record<string, string> = Object.fromEntries(
  Object.entries(REGIONS_BY_COUNTRY).flatMap(([c, tbl]) => Object.keys(tbl).map((code) => [code, c])),
);

/** "NS" -> "CA", "ME" -> "US", "PR" -> "US"; null for an unknown code. */
export function countryOf(region: string | null | undefined): string | null {
  return region ? (REGION_COUNTRY[region.toUpperCase()] ?? null) : null;
}

/** The country of a station: its own field (`country`, or `cc` on a map point), else its region's, else the US. */
export function stationCountry(r: { country?: string | null; region?: string | null; cc?: string; r?: string }): string {
  return r.country || r.cc || countryOf(r.region ?? r.r) || 'US';
}

/** "Maine", "Puerto Rico"; the code itself when unknown; "" for none (pipeline regions.region_name). */
export function regionName(code: string | null | undefined): string {
  if (!code) return '';
  return REGIONS[code.toUpperCase()] ?? code;
}

/** "Maine"; "Puerto Rico"; "Nova Scotia, Canada" (pipeline regions.region_with_country). */
export function regionWithCountry(code: string | null | undefined): string {
  const name = regionName(code);
  const c = countryOf(code);
  return c && c !== 'US' && name ? `${name}, ${COUNTRY_NAMES[c]}` : name;
}

export function isTerritory(code: string | null | undefined): boolean {
  return (US_TERRITORIES as readonly string[]).includes((code ?? '').toUpperCase());
}

/** The word for one region: "state", "territory", "district" or "province". */
export function regionKind(code: string | null | undefined): string {
  const c = (code ?? '').toUpperCase();
  if (countryOf(c) === 'CA') return ['NT', 'NU', 'YT'].includes(c) ? 'territory' : 'province';
  if (isTerritory(c)) return 'territory';
  if (c === 'DC') return 'district';
  return 'state';
}

export interface RegionGroup {
  country: string;
  name: string;
  regions: { code: string; name: string; territory: boolean }[];
}

/** Python's sorted(): plain code-point order, so both sides list regions the same way. */
function byCodePoint(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

/**
 * The regions to list, grouped by country in the pipeline's order (regions_meta): the US's
 * states and DC alphabetically, then its territories, then Canada's provinces and territories.
 * `only` keeps the codes given (those with stations); omit it for every region.
 */
export function regionGroups(only?: Iterable<string>): RegionGroup[] {
  const keep = only ? new Set([...only].map((c) => c.toUpperCase())) : null;
  return COUNTRY_ORDER.map((country) => {
    const codes = Object.keys(REGIONS_BY_COUNTRY[country]!);
    const main = codes.filter((c) => !isTerritory(c)).sort((a, b) => byCodePoint(regionName(a), regionName(b)));
    const terr = US_TERRITORIES.filter((c) => codes.includes(c));
    return {
      country,
      name: COUNTRY_NAMES[country]!,
      regions: [...main, ...terr]
        .filter((code) => !keep || keep.has(code))
        .map((code) => ({ code, name: regionName(code), territory: isTerritory(code) })),
    };
  }).filter((g) => g.regions.length > 0);
}

/** Metres first outside the US (DESIGN.md 3.3); feet first in the US and its territories. */
export function metricFirst(country: string | null | undefined): boolean {
  return (country ?? 'US') !== 'US';
}

/* ---------- Local units ("county" in the data model): pipeline regions.local_unit_label ---------- */

const AK_CENSUS_AREAS = new Set([
  'aleutians west', 'bethel', 'chugach', 'copper river', 'dillingham', 'hoonah-angoon',
  'kusilvak', 'nome', 'prince of wales-hyder', 'southeast fairbanks', 'yukon-koyukuk',
  'valdez-cordova', 'wade hampton', 'skagway-hoonah-angoon', 'wrangell-petersburg',
  'prince of wales-outer ketchikan',
]);
const UNIT_SUFFIX_RE = /\b(County|Parish|Borough|Census Area|Municipality|City and Borough|Municipio|District|Island|Islands|Village)$/i;

/** Lower case, accents dropped, spaces collapsed: "Québec" -> "quebec" (pipeline regions.fold). */
export function fold(text: string): string {
  return text.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/\s+/g, ' ').trim();
}

/**
 * The local unit as a page writes it: "Cumberland County", "Plaquemines Parish", "Nome Census
 * Area", "Juneau Borough"; Puerto Rico's municipios and every other territory's units bare
 * ("Cabo Rojo"); a Canadian unit exactly as its source names it. Null when there is none.
 */
export function localUnitLabel(country: string | null | undefined, region: string | null | undefined, county: string | null | undefined): string | null {
  if (!county || !county.trim()) return null;
  const c = county.trim();
  const cc = (country || countryOf(region) || 'US').toUpperCase();
  if (cc !== 'US') return c;
  const reg = (region ?? '').toUpperCase();
  if (UNIT_SUFFIX_RE.test(c) || c.includes('/') || isTerritory(reg) || reg === 'DC') return c;
  if (reg === 'LA') return `${c} Parish`;
  if (reg === 'AK') return AK_CENSUS_AREAS.has(fold(c)) ? `${c} Census Area` : `${c} Borough`;
  return `${c} County`;
}

/**
 * "Cumberland County, Maine"; "Cabo Rojo, Puerto Rico"; "Halifax County, Nova Scotia, Canada";
 * just the region when the local unit is not recorded.
 */
export function placeLine(r: { county?: string | null; region: string; country?: string | null }): string {
  const region = regionWithCountry(r.region);
  const unit = localUnitLabel(stationCountry(r), r.region, r.county);
  return unit ? `${unit}, ${region}` : region;
}
