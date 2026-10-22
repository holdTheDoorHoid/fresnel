# Data license

The Fresnel lighthouse database (everything under `data/`, and the generated
`stations.geojson` / per-station JSON published with the site) is made available under the
**Open Database License (ODbL) v1.0**: https://opendatacommons.org/licenses/odbl/1-0/

Individual contents of the database (facts, coordinates, dates) are licensed under the
Database Contents License v1.0: https://opendatacommons.org/licenses/dbcl/1-0/

You may share, adapt and build on the data, including commercially, provided you
**attribute** Fresnel and its sources, and **keep any adapted database open** under the
ODbL.

## What this license does NOT cover

- **Photos and images.** Each photo keeps its own copyright and licence, recorded next to it
  (`credit`, `license`, `source_url`). Many are mirrored from community sites with credit;
  they are *not* relicensed by being here. See the takedown note in the README.
- **Written history (`data/stories/`).** Our own prose is CC BY-SA 4.0. Quotations inside it
  belong to their authors.
- **Code** is GPL-3.0 (see `LICENSE`).

## Sources folded into this database

Facts come from many places, each credited on every station page that uses them and listed in
`data/sources/`. So far: Wikidata (CC0) and OpenStreetMap contributors (ODbL), both read through
QLever (University of Freiburg). Later rounds add NOAA, the US Coast Guard, the National Park
Service (public domain) and Canadian government sources, each with its own credit line.

`data/people/` and `data/rosters/` (the keepers index) hold **facts only** (names, roles, years, places)
taken from the U.S. Lighthouse Society's Digital Archive, which transcribes the National Archives'
keeper registers. The archive's own text is all rights reserved and is not copied; every roster and
person page links to the archive's pages and credits it. People whose service begins in 1950 or later
or ends after 1960 are left out of `data/people/` (DESIGN.md 3.6).
