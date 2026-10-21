/** The map's count chip. */
import { formatCount } from './format.ts';

/**
 * What the count chip says: what it counts and whether filters narrow it. "All 2,431 stations
 * shown" / "312 of 2,431 stations shown" with a short line of what a station is.
 */
export function countText(shown: number, total: number, filtered: boolean): { main: string; sub: string } {
  const sub = 'lighthouses, lightships and life-saving stations, standing or lost';
  if (total === 0) return { main: 'No stations loaded', sub: '' };
  if (shown === 0) return { main: 'No stations match your filters', sub: '' };
  if (!filtered || shown === total) return { main: `All ${formatCount(total)} stations shown`, sub };
  return { main: `${formatCount(shown)} of ${formatCount(total)} stations shown`, sub: 'narrowed by your filters' };
}
