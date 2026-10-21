/**
 * "My checklist": visited / climbed / stayed / want to go, kept only in this browser
 * (DESIGN.md 1, "Checklist"). No accounts, nothing collected.
 *
 * Every storage access is wrapped in try/catch. If the browser blocks storage (private mode,
 * strict settings, full quota) the checklist keeps working in memory for this page, and
 * `persistent` turns false so the UI can warn: "this will be lost, use Export".
 *
 * Retired stations: when the merge folds one station into another (data/redirects.json, see
 * src/lib/redirects.ts) a mark saved under the old id moves to the surviving id: on load (as soon
 * as the list is known: `setRedirects`), on reload from another tab, on export and on import. If
 * both ids carry marks the survivor keeps each mark that either had, so the strongest state wins
 * ("climbed" and "stayed" always include "visited", and are never lost to a plain "visited") and
 * a "want to go" is not dropped either (a station can be both visited and wanted).
 */
import { resolveRedirect, type RedirectsFile } from './redirects.ts';
import { isStationId } from './station-id.ts';

export { isStationId };

export type Mark = 'visited' | 'climbed' | 'stayed' | 'want';
export const MARKS: readonly Mark[] = ['visited', 'climbed', 'stayed', 'want'];
export const MARK_LABELS: Record<Mark, string> = {
  visited: 'Visited',
  climbed: 'Climbed',
  stayed: 'Stayed',
  want: 'Want to go',
};
/** Marks that mean you were there, so they also mark "Visited". */
const IMPLIES_VISIT: readonly Mark[] = ['climbed', 'stayed'];

function emptySets(): Record<Mark, Set<string>> {
  return { visited: new Set(), climbed: new Set(), stayed: new Set(), want: new Set() };
}

export const STORAGE_KEY = 'fresnel.checklist.v1';
const BACKUP_KEY = 'fresnel.checklist.v1.unreadable-backup';
const MAX_IDS = 100_000;

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export interface ChecklistFile {
  app: 'fresnel';
  kind: 'checklist';
  version: 1;
  exported?: string;
  visited: string[];
  climbed: string[];
  stayed: string[];
  want: string[];
}

export type ImportResult =
  | { ok: true; added: Record<Mark, number>; ignored: number }
  | { ok: false; error: string };

export type Marks = Record<Mark, boolean>;

/** Safely get window.localStorage; even reading the property can throw. */
export function browserStorage(): StorageLike | null {
  try {
    const s = globalThis.localStorage;
    return s ?? null;
  } catch {
    return null;
  }
}

export class Checklist {
  #storage: StorageLike | null;
  #sets: Record<Mark, Set<string>> = emptySets();
  #listeners = new Set<() => void>();
  #redirects: RedirectsFile | null = null;
  /** False when changes cannot be saved in this browser. */
  persistent = true;
  /** Plain-language reason when something went wrong, for the UI. */
  problem: string | null = null;

  constructor(storage: StorageLike | null) {
    this.#storage = storage;
    if (!storage) {
      this.persistent = false;
      this.problem = 'This browser is not letting Fresnel save anything, so your checklist will be lost when you close the page. Use “Download my checklist” to keep it.';
    }
    this.reload();
  }

  /** Re-read from storage (also used when another tab changed it). */
  reload(): void {
    if (!this.#storage) return;
    let text: string | null;
    try {
      text = this.#storage.getItem(STORAGE_KEY);
    } catch {
      this.persistent = false;
      this.problem = 'This browser blocked access to saved data, so your checklist cannot be loaded or saved here. Use “Download my checklist” to keep changes.';
      return;
    }
    const fresh: Record<Mark, Set<string>> = emptySets();
    if (text) {
      try {
        const data = JSON.parse(text) as Partial<Record<Mark, unknown>>;
        for (const mark of MARKS) {
          const list = data[mark];
          if (Array.isArray(list)) for (const id of list) if (isStationId(id)) fresh[mark].add(id);
        }
      } catch {
        // Keep a copy of what we could not read rather than silently overwriting it.
        try {
          this.#storage.setItem(BACKUP_KEY, text);
        } catch {
          /* nothing more we can do */
        }
        this.problem = 'Your saved checklist could not be read, so it starts empty. A copy of the unreadable data was kept in this browser.';
      }
    }
    this.#sets = fresh;
    // Another tab (or an older page) may have saved ids that have been retired since.
    if (this.#migrate(fresh) > 0) this.#save();
    this.#emit();
  }

  /**
   * Tell the checklist which stations were folded into others (data/redirects.json). Marks saved
   * under a retired id move to the surviving id and are saved; returns how many retired ids were
   * moved. Later loads, sets, exports and imports use the list too. A missing list changes nothing.
   */
  setRedirects(file: RedirectsFile | null | undefined): number {
    if (!file || typeof file.redirects !== 'object' || file.redirects === null) return 0;
    this.#redirects = file;
    const moved = this.#migrate(this.#sets);
    if (moved > 0) {
      this.#save();
      this.#emit();
    }
    return moved;
  }

  /** The id a station has now: itself, or the station it was folded into. */
  #resolve(id: string): string {
    return this.#redirects ? resolveRedirect(id, this.#redirects) : id;
  }

  /** Move marks from retired ids to their survivors, in place; returns the number of ids moved. */
  #migrate(sets: Record<Mark, Set<string>>): number {
    if (!this.#redirects) return 0;
    const moved = new Set<string>();
    for (const mark of MARKS) {
      for (const id of [...sets[mark]]) {
        const now = this.#resolve(id);
        if (now === id) continue;
        sets[mark].delete(id);
        sets[mark].add(now);
        moved.add(id);
      }
    }
    return moved.size;
  }

  has(id: string, mark: Mark): boolean {
    return this.#sets[mark].has(id);
  }

  marks(id: string): Marks {
    return { visited: this.#sets.visited.has(id), climbed: this.#sets.climbed.has(id), stayed: this.#sets.stayed.has(id), want: this.#sets.want.has(id) };
  }

  /** True if the station has any of the given marks. */
  hasAny(id: string, marks: Iterable<Mark>): boolean {
    for (const m of marks) if (this.#sets[m].has(id)) return true;
    return false;
  }

  /**
   * Set or clear one mark. You cannot climb or stay without visiting, so marking "climbed" or
   * "stayed" also marks "visited", and clearing "visited" also clears both.
   */
  set(id: string, mark: Mark, on: boolean): void {
    if (!isStationId(id)) return;
    id = this.#resolve(id);
    const apply = (m: Mark, value: boolean) => (value ? this.#sets[m].add(id) : this.#sets[m].delete(id));
    apply(mark, on);
    if (IMPLIES_VISIT.includes(mark) && on) apply('visited', true);
    if (mark === 'visited' && !on) for (const m of IMPLIES_VISIT) apply(m, false);
    this.#save();
    this.#emit();
  }

  toggle(id: string, mark: Mark): boolean {
    const next = !this.has(id, mark);
    this.set(id, mark, next);
    return next;
  }

  ids(mark: Mark): string[] {
    return [...this.#sets[mark]].sort();
  }

  counts(): Record<Mark, number> & { stations: number } {
    const all = new Set(MARKS.flatMap((m) => [...this.#sets[m]]));
    return { visited: this.#sets.visited.size, climbed: this.#sets.climbed.size, stayed: this.#sets.stayed.size, want: this.#sets.want.size, stations: all.size };
  }

  toFile(now = new Date()): ChecklistFile {
    // Retired ids go out under the station that took them, even if they are still in memory.
    const sets = emptySets();
    for (const m of MARKS) for (const id of this.#sets[m]) sets[m].add(id);
    this.#migrate(sets);
    return {
      app: 'fresnel',
      kind: 'checklist',
      version: 1,
      exported: now.toISOString(),
      visited: [...sets.visited].sort(),
      climbed: [...sets.climbed].sort(),
      stayed: [...sets.stayed].sort(),
      want: [...sets.want].sort(),
    };
  }

  /** Merge a checklist file into this one. Never removes anything; ids of retired stations land on the station that took them. */
  importText(text: string): ImportResult {
    let data: unknown;
    try {
      data = JSON.parse(text);
    } catch {
      return { ok: false, error: 'That file is not a Fresnel checklist (it is not valid JSON).' };
    }
    return this.importData(data);
  }

  importData(data: unknown): ImportResult {
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      return { ok: false, error: 'That file is not a Fresnel checklist.' };
    }
    const obj = data as Record<string, unknown>;
    if (obj.app !== undefined && obj.app !== 'fresnel') {
      return { ok: false, error: 'That file was made by a different app, not Fresnel.' };
    }
    if (!MARKS.some((m) => Array.isArray(obj[m]))) {
      return { ok: false, error: 'That file has no visited, climbed, stayed or want-to-go lists in it.' };
    }
    const added: Record<Mark, number> = { visited: 0, climbed: 0, stayed: 0, want: 0 };
    let ignored = 0;
    let seen = 0;
    for (const mark of MARKS) {
      const list = obj[mark];
      if (!Array.isArray(list)) continue;
      for (const raw of list) {
        if (++seen > MAX_IDS) break;
        if (!isStationId(raw)) {
          ignored++;
          continue;
        }
        const id = this.#resolve(raw);
        if (!this.#sets[mark].has(id)) {
          this.#sets[mark].add(id);
          added[mark]++;
        }
        if (IMPLIES_VISIT.includes(mark) && !this.#sets.visited.has(id)) {
          this.#sets.visited.add(id);
          added.visited++;
        }
      }
    }
    this.#save();
    this.#emit();
    return { ok: true, added, ignored };
  }

  subscribe(fn: () => void): () => void {
    this.#listeners.add(fn);
    return () => this.#listeners.delete(fn);
  }

  #save(): void {
    if (!this.#storage) return;
    const payload = JSON.stringify({ version: 1, visited: this.ids('visited'), climbed: this.ids('climbed'), stayed: this.ids('stayed'), want: this.ids('want') });
    try {
      this.#storage.setItem(STORAGE_KEY, payload);
      if (!this.persistent) {
        // Storage works again (e.g. space was freed).
        this.persistent = true;
        this.problem = null;
      }
    } catch {
      this.persistent = false;
      this.problem = 'Your browser did not let Fresnel save your checklist, so changes will be lost when you close the page. Use “Download my checklist” to keep them.';
    }
  }

  #emit(): void {
    for (const fn of this.#listeners) {
      try {
        fn();
      } catch (err) {
        console.error(err);
      }
    }
  }
}
