/**
 * Formatting shared by the map and the prerendered pages. Pure, no DOM.
 *
 * Units (DESIGN.md 3.3): data is always metres. Heights read feet first with metres alongside in
 * the US and its territories ("80 ft (24 m)"), metres first with feet alongside in Canada
 * ("24 m (80 ft)"). Ranges and distances at sea are nautical miles everywhere, with km alongside
 * ("24 nmi (44 km)"), because that is how lights are charted.
 */

const nf = new Intl.NumberFormat('en-US');
const nf1 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });

export const FOOT = 0.3048;
export const NAUTICAL_MILE = 1852;

export function formatCount(n: number): string {
  return nf.format(n);
}

function finite(v: unknown): v is number {
  return typeof v === 'number' && Number.isFinite(v);
}

/** "80 ft (24 m)". US readers read feet first; metres stay alongside. */
export function feetAndMetres(metres: number | null | undefined, decimals = 0): string | null {
  if (!finite(metres)) return null;
  const feet = Math.round(metres / FOOT);
  const m = decimals ? nf1.format(Number(metres.toFixed(decimals))) : nf.format(Math.round(metres));
  return `${nf.format(feet)} ft (${m} m)`;
}

/** "24 m (80 ft)": metres first, for stations outside the US. */
export function metresAndFeet(metres: number | null | undefined, decimals = 0): string | null {
  if (!finite(metres)) return null;
  const feet = Math.round(metres / FOOT);
  const m = decimals ? nf1.format(Number(metres.toFixed(decimals))) : nf.format(Math.round(metres));
  return `${m} m (${nf.format(feet)} ft)`;
}

/** A height in the units its country reads first: feet first in the US, metres first elsewhere. */
export function lengthFor(country: string | null | undefined, metres: number | null | undefined, decimals = 0): string | null {
  return (country ?? 'US') === 'US' ? feetAndMetres(metres, decimals) : metresAndFeet(metres, decimals);
}

/** "24 nmi (44 km)": a range or a distance at sea, everywhere. */
export function nauticalMiles(nm: number | null | undefined): string | null {
  if (!finite(nm) || nm < 0) return null;
  const km = nm * (NAUTICAL_MILE / 1000);
  return `${nf1.format(Number(nm.toFixed(1)))} nmi (${km < 10 ? nf1.format(Number(km.toFixed(1))) : nf.format(Math.round(km))} km)`;
}

/** A distance on land, in the country's units first: "820 m (2,690 ft)", "2.4 km (1.5 mi)"; feet and miles first in the US. */
export function distanceFor(country: string | null | undefined, metres: number): string {
  const us = (country ?? 'US') === 'US';
  if (metres < 1000) {
    const m = `${nf.format(Math.round(metres))} m`;
    const ft = `${nf.format(Math.round(metres / FOOT))} ft`;
    return us ? `${ft} (${m})` : `${m} (${ft})`;
  }
  const km = metres / 1000;
  const mi = metres / 1609.344;
  const kmS = `${km < 10 ? nf1.format(Number(km.toFixed(1))) : nf.format(Math.round(km))} km`;
  const miS = `${mi < 10 ? nf1.format(Number(mi.toFixed(1))) : nf.format(Math.round(mi))} mi`;
  return us ? `${miS} (${kmS})` : `${kmS} (${miS})`;
}

/** "43.61000, −70.21000" with a real minus sign. */
export function formatCoords(lat: number, lon: number): string {
  const f = (v: number) => v.toFixed(5).replace('-', '−');
  return `${f(lat)}, ${f(lon)}`;
}

/** Plain "43.61000,-70.21000" for copying into other apps. */
export function plainCoords(lat: number, lon: number): string {
  return `${lat.toFixed(5)},${lon.toFixed(5)}`;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** "2026-10-21" -> "21 Oct 2026"; "1880-05" -> "May 1880"; anything else unchanged; null for nothing. */
export function formatDate(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const s = String(iso);
  const m = /^(\d{4})-(\d{2})(?:-(\d{2}))?/.exec(s);
  if (!m) return s;
  const month = MONTHS[Number(m[2]) - 1];
  if (!month) return s;
  return m[3] ? `${Number(m[3])} ${month} ${m[1]}` : `${month} ${m[1]}`;
}

/** Distance in metres between two WGS84 points (haversine). */
export function distanceMetres(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371008.8;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

export function yesNo(v: boolean | null | undefined, yes: string, no: string, unknown = 'Not recorded'): string {
  return v === true ? yes : v === false ? no : unknown;
}

/** "1791", "May 1880", "12 May 1880" from a year number or a "YYYY" / "YYYY-MM(-DD)" string; null otherwise. */
export function formatYearish(v: unknown): string | null {
  if (typeof v === 'number' && Number.isInteger(v) && v > 0) return String(v);
  if (typeof v === 'string') {
    const s = v.trim();
    if (/^\d{4}$/.test(s)) return s;
    if (/^\d{4}-\d{2}(-\d{2})?$/.test(s)) return formatDate(s);
  }
  return null;
}

/** The year of a year number or a "YYYY..." string, for sorting; null otherwise. */
export function yearOf(v: unknown): number | null {
  if (typeof v === 'number' && Number.isInteger(v)) return v;
  if (typeof v === 'string') {
    const m = /^(\d{4})/.exec(v.trim());
    if (m) return Number(m[1]);
  }
  return null;
}

/**
 * The years a keeper served, in words: "1791–1795", "1880" (one year), "from 1855", "until 1884",
 * "12 May 1880 – 1884"; "Not recorded" when neither end is known.
 */
export function yearSpan(from: unknown, to: unknown, fromApprox = false, toApprox = false): string {
  const fa = formatYearish(from);
  const fb = formatYearish(to);
  // "about" when the source gives only an approximate year (research/STORY_GUIDE.md: from_approx / to_approx)
  const a = fa && fromApprox ? `c. ${fa}` : fa;
  const b = fb && toApprox ? `c. ${fb}` : fb;
  if (a && b) {
    if (a === b) return a;
    const spaced = a.includes(' ') || b.includes(' ');
    return spaced ? `${a} – ${b}` : `${a}–${b}`;
  }
  if (a) return `from ${a}`;
  if (b) return `until ${b}`;
  return 'Not recorded';
}
