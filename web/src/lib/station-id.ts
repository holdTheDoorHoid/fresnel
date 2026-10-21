/**
 * The shape of a station id ("us-me-portland-head", "ca-ns-sambro-island"): `<country>-<region>-<slug>`,
 * the same rule as pipeline/build_site_data.py ID_RE. Ids are URLs and checklist keys; they never change.
 */
const ID_RE = /^[a-z]{2}-[a-z0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function isStationId(value: unknown): value is string {
  return typeof value === 'string' && value.length <= 120 && ID_RE.test(value);
}
