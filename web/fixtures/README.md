# Fixtures

Sample data for building and testing the Fresnel site before (or without) real pipeline data:
`npm run data:fixtures` builds `web/public/data/` from these files.

**Invented. Not authoritative.** The names ("Example Head Light", "Fixture Island Lighthouse")
are made up on purpose so nobody mistakes them for real stations; the numbers only exercise the
map, the station pages, the filters and the checklist. Every record says `"fixture": true`, and a
site built from them shows a "Sample data" banner.

- `stations/<dir>/<id>.json`: canonical station records (DESIGN.md 3.2), one per kind and status,
  a staffed Canadian lightstation reached by boat, a territory (Puerto Rico), a range with two
  structures, and one hidden decorative record to test the out-of-scope rule.
- `stories/us-me-example-head.md`: a story in chapters with footnotes.
- `research/us-me-example-head.json`: its research, with a keepers roster (DESIGN.md 3.6).
