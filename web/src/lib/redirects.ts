/**
 * Stations the merge folded into others (data/stations files with `merged_into`). A station id
 * is a URL and a checklist key and never changes, so the old id keeps working:
 * pipeline/build_site_data.py lists old id -> new id in redirects.json, the prerender step writes
 * a redirecting page at each old address, the map follows the same list for `?s=<old id>`, and
 * the checklist moves marks saved under an old id to the new one.
 */
import { isStationId } from './station-id.ts';

export interface RedirectsFile {
  note?: string;
  /** Old station id -> the id of the station that has its records now. */
  redirects: Record<string, string>;
}

/** The id to show for `id`: the station it was folded into, or `id` itself. Follows a chain, never loops. */
export function resolveRedirect(id: string, file: RedirectsFile | null | undefined): string {
  const map = file?.redirects ?? {};
  const seen = new Set<string>();
  let at = id;
  while (Object.hasOwn(map, at) && !seen.has(at)) {
    seen.add(at);
    const next = map[at];
    if (!isStationId(next)) break;
    at = next;
  }
  return at;
}
