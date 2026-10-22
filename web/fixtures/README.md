# Fixtures

Sample data for building and testing the Fresnel site before (or without) real pipeline data:
`npm run data:fixtures` builds `web/public/data/` from these files.

**Invented. Not authoritative.** The names ("Example Head Light", "Fixture Island Lighthouse")
are made up on purpose so nobody mistakes them for real stations; the numbers only exercise the
map, the station pages, the filters and the checklist. Every record says `"fixture": true`, and a
site built from them shows a "Sample data" banner.

- `stations/<dir>/<id>.json`: canonical station records (DESIGN.md 3.2), one per kind and status,
  a staffed Canadian lightstation reached by boat, territories (Puerto Rico, Guam, American
  Samoa), an Aleutian light west of the 180th meridian on closed Coast Guard land, tribal land,
  a range with two structures, a moved pier light (British Columbia), a replica with a place to
  stay, a lightship station at sea, a characteristic in a form the site does not read
  (`Al W 10s`: alternating, but only one colour given), one record merged into another (`merged_into`, so the site writes a
  redirect) and one hidden decorative record to test the out-of-scope rule.
- `stories/us-me-example-head.md`: a story in chapters with footnotes.
- `research/us-me-example-head.json`: its research, with a keepers roster (DESIGN.md 3.6).
- `people/<id>.json`, `rosters/<dir>/<station id>.json`, `people_report.json`: the keepers index (DESIGN.md 3.6) in
  the shape `pipeline/build_people.py` writes, for invented people at the invented stations: one person at two
  stations under one archive record (`jonas-example`), three records named Ezra Sample (a pair whose years and
  region fit, so each says "possibly the same person as", and one a century away, so nothing is said), a stint at
  a depot that is not on the map (`lars-fixture`), a research line that names an archive record
  (`samuel-sample` in the research file) and one whose `other_stations` makes a person only the research names
  (Joseph Example, who also served at the Canadian fixture), and two lines that the living-people rule leaves in
  the station's table with no person (`alex-present`, `pat-coastguard`). `us-nc-example-shoal` shows the
  archive's roster; `us-me-example-head` has a research roster, which takes precedence.
