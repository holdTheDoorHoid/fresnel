/**
 * Access labels (DESIGN.md 1, "Access": exact location for every site; private residences,
 * Coast Guard property closed to the public, island stations reachable only by boat, tribal
 * land and staffed lightstations get a prominent label. Warn, don't hide).
 *
 * `accessLabels` turns a record into the labels a page shows, most serious first. Each label
 * has a tone: "stop" (do not go without permission, or at all), "caution" (you can go, but read
 * this first), "ok" (open), "unknown" (not recorded). The map panel shows the same labels from
 * the record, and `accessLabelsFromProps` gives the short form the map point carries.
 */
import { ACCESS, type Tone } from './vocab.ts';
import type { StationProps, StationRecord } from './types.ts';

export interface AccessLabel {
  id: 'private' | 'closed' | 'permission' | 'tribal' | 'restricted' | 'boat_only' | 'staffed' | 'volunteer' | 'public' | 'unknown';
  label: string;
  meaning: string;
  tone: Tone;
}

const TONE_ORDER: Record<Tone, number> = { stop: 0, caution: 1, unknown: 2, ok: 3 };

export const STAFFED_LABEL: Omit<AccessLabel, 'id'> = {
  label: 'A working lightstation',
  meaning: 'Keepers live and work here: it is their home and workplace. Visit only where and when visitors are welcome, and respect their privacy.',
  tone: 'caution',
};
export const VOLUNTEER_LABEL: Omit<AccessLabel, 'id'> = {
  label: 'Keepers live here',
  meaning: 'Volunteer or caretaker keepers live at the station, at least in season. Respect their privacy and the posted hours.',
  tone: 'caution',
};
export const BOAT_LABEL: Omit<AccessLabel, 'id'> = {
  label: 'Reached only by boat',
  meaning: 'There is no road or path to it. You need a boat or a tour, and landing may not be allowed.',
  tone: 'caution',
};
export const TRIBAL_LABEL: Omit<AccessLabel, 'id'> = {
  label: 'Tribal land: permission required',
  meaning: 'This station is on tribal land. Ask the tribe for permission before you visit, and follow its rules.',
  tone: 'stop',
};

type AccessInput = {
  level?: string | null;
  tribal?: boolean;
  boatOnly?: boolean;
  staffing?: string | null;
};

function labels(i: AccessInput): AccessLabel[] {
  const out: AccessLabel[] = [];
  const level = i.level ?? 'unknown';
  if (i.tribal && level !== 'private' && level !== 'closed') {
    out.push({ id: 'tribal', ...TRIBAL_LABEL });
  } else if (level !== 'unknown' || (!i.boatOnly && !i.staffing)) {
    const w = ACCESS[level] ?? { label: level.replace(/_/g, ' '), meaning: '', tone: 'unknown' as const };
    out.push({ id: (ACCESS[level] ? level : 'unknown') as AccessLabel['id'], label: w.label, meaning: w.meaning, tone: w.tone });
  }
  if (i.staffing === 'staffed') out.push({ id: 'staffed', ...STAFFED_LABEL });
  else if (i.staffing === 'volunteer') out.push({ id: 'volunteer', ...VOLUNTEER_LABEL });
  if (i.boatOnly) out.push({ id: 'boat_only', ...BOAT_LABEL });
  return out.sort((a, b) => TONE_ORDER[a.tone] - TONE_ORDER[b.tone]);
}

/** The labels for a full record, most serious first. Always at least one. */
export function accessLabels(r: Pick<StationRecord, 'access' | 'ownership' | 'visit' | 'staffing'>): AccessLabel[] {
  return labels({
    level: r.access?.level,
    tribal: r.ownership === 'tribal',
    boatOnly: r.visit?.boat_only === true,
    staffing: r.staffing?.status,
  });
}

/** The same from a map point's short properties (no ownership there, so no tribal label). */
export function accessLabelsFromProps(p: Pick<StationProps, 'a' | 'bo' | 'sf'>): AccessLabel[] {
  return labels({ level: p.a, boatOnly: !!p.bo, staffing: p.sf ?? null });
}

/** True when the page should lead with the warning, above everything else. */
export function isProminent(l: AccessLabel): boolean {
  return l.tone === 'stop' || l.tone === 'caution';
}
