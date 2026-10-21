/**
 * How far out a light can be seen, and how it looks from a given distance: the physics behind
 * "The light at night" and the range rings. Pure functions, no DOM. DESIGN.md section 4 lists
 * the assumptions; in short:
 *
 *  - Geographic range (the horizon): D = 2.08 × (√H + √h) nautical miles, H the light's focal
 *    height and h the eye's height above the water, in metres. The 2.08 folds in standard
 *    refraction; it corresponds to a sphere of effective radius R' = (2.08 × 1852)² / 2
 *    ≈ 7,420 km, which the vertical angles in the scene use too.
 *  - Luminous range (brightness): Allard's law, E = I × T^d / d², with the transmissivity T
 *    from the meteorological visibility V by Koschmieder's 5 % contrast (T = 0.05^(1/V) per
 *    nautical mile), and the threshold the charted nominal range implies: a light of nominal
 *    range Rn is just visible at Rn when V = 10 nautical miles (IALA's definition of nominal
 *    range). So the light's brightness relative to the faintest the eye can see at night is
 *    (Rn / d)² × 0.05^(d / V − Rn / 10). The light's intensity and the threshold (0.2 µlux in
 *    IALA's recommendation) cancel out; only the charted range is needed.
 *  - The visible range is the smaller of the two.
 *  - Loom: a light whose charted range is 18 nautical miles or more, below your horizon but
 *    within its luminous range, lights the air above the horizon. Its strength in the scene is a
 *    sketch (it fades from the horizon distance to the luminous range), not a measured glow.
 */

export const NM = 1852;
/** Nautical miles per √metre of height, standard refraction (US Light List, Bowditch). */
export const RANGE_COEFF = 2.08;
/** The effective earth radius (refraction included) that makes D = 2.08√h exact. */
export const R_EFF = (RANGE_COEFF * NM) ** 2 / 2;
/** Koschmieder's contrast threshold: the meteorological visibility is where contrast falls to 5 %. */
const CONTRAST = 0.05;
/** The visibility the charted nominal range assumes (IALA). */
export const NOMINAL_VISIBILITY_NM = 10;
/** A light whose charted range is at least this is treated as a major light that shows a loom. */
export const LOOM_MIN_RANGE_NM = 18;

export type VisibilityId = 'clear' | 'normal' | 'haze' | 'fog';

export const VISIBILITY: Record<VisibilityId, { nm: number; label: string; meaning: string }> = {
  clear: { nm: 20, label: 'Very clear', meaning: 'very clear air: you can see about 20 nautical miles' },
  normal: { nm: 10, label: 'Normal', meaning: 'about 10 nautical miles: the visibility the charted range assumes' },
  haze: { nm: 3, label: 'Haze', meaning: 'haze: you can see about 3 nautical miles' },
  fog: { nm: 0.5, label: 'Fog', meaning: 'fog: you can see about half a nautical mile' },
};
export const VISIBILITY_ORDER: VisibilityId[] = ['clear', 'normal', 'haze', 'fog'];

export interface EyeHeight {
  m: number;
  label: string;
}

/** Eye heights the visitor can choose. A small boat's deck is the default. */
export const EYE_HEIGHTS: EyeHeight[] = [
  { m: 1, label: 'in a kayak or dinghy' },
  { m: 3, label: 'on a small boat’s deck' },
  { m: 6, label: 'in a fishing boat’s wheelhouse' },
  { m: 15, label: 'on a ship’s bridge' },
  { m: 30, label: 'on a large ship’s bridge' },
];
export const DEFAULT_EYE_M = 3;

function finite(v: unknown): v is number {
  return typeof v === 'number' && Number.isFinite(v);
}

/** Distance to the sea horizon from a height, in nautical miles. */
export function horizonNm(heightM: number): number {
  return RANGE_COEFF * Math.sqrt(Math.max(0, heightM));
}

/** How far a light at focal height H can be seen over the horizon from an eye at height h. */
export function geographicRangeNm(focalM: number, eyeM: number): number {
  return horizonNm(focalM) + horizonNm(eyeM);
}

/**
 * How many times brighter than the faintest light the eye can see at night a light of charted
 * (nominal) range `nominalNm` looks from `distanceNm`, in meteorological visibility `visNm`.
 * 1 = just perceptible; below 1, not seen. Allard's law with the IALA nominal-range threshold.
 */
export function brightnessRatio(nominalNm: number, distanceNm: number, visNm: number): number {
  const d = Math.max(distanceNm, 0.01);
  return (nominalNm / d) ** 2 * CONTRAST ** (d / visNm - nominalNm / NOMINAL_VISIBILITY_NM);
}

/** The luminous range: the distance at which `brightnessRatio` falls to 1. */
export function luminousRangeNm(nominalNm: number, visNm: number): number {
  if (!(nominalNm > 0) || !(visNm > 0)) return 0;
  let lo = 0.001;
  let hi = 400;
  for (let i = 0; i < 80; i++) {
    const mid = (lo + hi) / 2;
    if (brightnessRatio(nominalNm, mid, visNm) >= 1) lo = mid;
    else hi = mid;
  }
  return lo;
}

/** The angle by which the sea horizon lies below the eye's horizontal, in radians. */
export function dipRad(eyeM: number): number {
  return Math.sqrt((2 * Math.max(0, eyeM)) / R_EFF);
}

/**
 * The light's angle above the eye's horizontal (negative below), in radians, for a light at
 * height H seen across `distanceNm` of sea, on a sphere of radius R' (refraction included).
 */
export function elevationRad(focalM: number, eyeM: number, distanceNm: number): number {
  const d = Math.max(distanceNm, 0.001) * NM;
  return (focalM - eyeM) / d - d / (2 * R_EFF);
}

export interface SightingInput {
  focalM: number | null;
  nominalNm: number | null;
  eyeM: number;
  distanceNm: number;
  visibility: VisibilityId;
}

export type SightingState = 'seen' | 'too_faint' | 'below_horizon' | 'unknown';

export interface Sighting {
  /** Over the horizon from this eye height; null when the focal height is not recorded. */
  geographicNm: number | null;
  /** Bright enough in this visibility; null when the charted range is not recorded. */
  luminousNm: number | null;
  /** The smaller of the two known ranges; null when neither is known. */
  visibleNm: number | null;
  /** Which limit sets the visible range. */
  limit: 'horizon' | 'brightness' | null;
  /** Null when the focal height is not recorded. */
  aboveHorizon: boolean | null;
  /** Brightness over the threshold; null when the charted range is not recorded. */
  ratio: number | null;
  state: SightingState;
  /** Right on the horizon: within 0.3 nautical miles of the geographic range. */
  dipping: boolean;
  /** 0..1, the loom's strength when the light is below the horizon (0: no loom). */
  loom: number;
  elevation: number | null;
  dip: number;
}

export function sight(i: SightingInput): Sighting {
  const vis = VISIBILITY[i.visibility].nm;
  const focal = finite(i.focalM) && i.focalM > 0 ? i.focalM : null;
  const nominal = finite(i.nominalNm) && i.nominalNm > 0 ? i.nominalNm : null;
  const geographicNm = focal !== null ? geographicRangeNm(focal, i.eyeM) : null;
  const luminousNm = nominal !== null ? luminousRangeNm(nominal, vis) : null;
  const known = [geographicNm, luminousNm].filter((v): v is number => v !== null);
  const visibleNm = known.length ? Math.min(...known) : null;
  const limit = geographicNm !== null && luminousNm !== null ? (geographicNm <= luminousNm ? 'horizon' : 'brightness') : geographicNm !== null ? 'horizon' : luminousNm !== null ? 'brightness' : null;
  const aboveHorizon = geographicNm !== null ? i.distanceNm < geographicNm : null;
  const ratio = nominal !== null ? brightnessRatio(nominal, i.distanceNm, vis) : null;
  let state: SightingState;
  if (aboveHorizon === false) state = 'below_horizon';
  else if (ratio !== null) state = ratio >= 1 ? 'seen' : 'too_faint';
  else state = 'unknown';
  const dipping = geographicNm !== null && Math.abs(i.distanceNm - geographicNm) <= 0.3;
  let loom = 0;
  if (state === 'below_horizon' && nominal !== null && nominal >= LOOM_MIN_RANGE_NM && luminousNm !== null && geographicNm !== null && i.distanceNm < luminousNm) {
    loom = Math.max(0, Math.min(1, 1 - (i.distanceNm - geographicNm) / Math.max(0.5, luminousNm - geographicNm)));
  }
  return {
    geographicNm,
    luminousNm,
    visibleNm,
    limit,
    aboveHorizon,
    ratio,
    state,
    dipping,
    loom,
    elevation: focal !== null ? elevationRad(focal, i.eyeM, i.distanceNm) : null,
    dip: dipRad(i.eyeM),
  };
}

/** The range for the map ring: the smaller of the charted range and the horizon at this eye height. */
export function ringRangeNm(focalM: number | null | undefined, nominalNm: number | null | undefined, eyeM: number): { nm: number; limit: 'horizon' | 'range' } | null {
  const geo = finite(focalM) && focalM > 0 ? geographicRangeNm(focalM, eyeM) : null;
  const nom = finite(nominalNm) && nominalNm > 0 ? nominalNm : null;
  if (geo === null && nom === null) return null;
  if (geo !== null && (nom === null || geo <= nom)) return { nm: geo, limit: 'horizon' };
  return { nm: nom!, limit: 'range' };
}

/** A starting distance: a typical approach, inside the light's visible range (1 to 10 nmi). */
export function defaultDistanceNm(visibleNm: number | null): number {
  if (visibleNm === null) return 5;
  return Math.min(10, Math.max(1, Math.round(visibleNm * 0.6 * 2) / 2));
}

/** The slider's far end: well past the farthest the light could be seen. */
export function maxDistanceNm(focalM: number | null, nominalNm: number | null): number {
  const geo = focalM ? geographicRangeNm(focalM, 30) : 0;
  const lum = nominalNm ? luminousRangeNm(nominalNm, VISIBILITY.clear.nm) : 0;
  const far = Math.max(geo, lum, 10);
  return Math.min(80, Math.ceil((far * 1.25) / 5) * 5);
}

/** A circle on the earth's surface as a closed ring of [lon, lat] points (longitudes not wrapped). */
export function circleRing(lat: number, lon: number, radiusNm: number, steps = 96): [number, number][] {
  const toRad = Math.PI / 180;
  const R = 6371008.8;
  const ang = (radiusNm * NM) / R;
  const φ1 = lat * toRad;
  const λ1 = lon * toRad;
  const out: [number, number][] = [];
  for (let i = 0; i <= steps; i++) {
    const θ = (i / steps) * 2 * Math.PI;
    const φ2 = Math.asin(Math.sin(φ1) * Math.cos(ang) + Math.cos(φ1) * Math.sin(ang) * Math.cos(θ));
    const λ2 = λ1 + Math.atan2(Math.sin(θ) * Math.sin(ang) * Math.cos(φ1), Math.cos(ang) - Math.sin(φ1) * Math.sin(φ2));
    out.push([Number((λ2 / toRad).toFixed(5)), Number((φ2 / toRad).toFixed(5))]);
  }
  out[out.length - 1] = out[0]!;
  return out;
}
