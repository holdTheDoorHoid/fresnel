"""Tests for pipeline/keepers.py: who is one person, who is left out, which archive place is which
station, how research rosters join, and the files the site loads (DESIGN.md 3.6)."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keepers as kp  # noqa: E402
import validate  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "web" / "fixtures"
VOCAB = REPO / "data" / "vocab.json"


def raw_line(name, span, person, role="head keeper", heading="Principal Lighthouse Keeper"):
    f, t, _, _ = kp.parse_span(span)
    return {"name": name, "role_raw": heading, "span": span, "from": f, "to": t, "person": person, "role": role}


def place(slug, name, state, nid, lat=None, lon=None, lines=0):
    p = {"slug": slug, "name": name, "state": state, "nid": nid, "roster_id": nid, "roster_lines": lines}
    if lat is not None:
        p["lat"], p["lon"] = lat, lon
    return p


def archive(rosters_spec):
    """{nid: (slug, name, [lines])} -> (places, rosters) in the shape of research/roster.py's files."""
    places, rosters = [], {}
    for nid, (slug, name, state, lines, *pos) in rosters_spec.items():
        lat, lon = pos if pos else (None, None)
        places.append(place(slug, name, state, nid, lat, lon, len(lines)))
        rosters[str(nid)] = {"slug": slug, "name": name, "lines": lines}
    return places, rosters


class SpanTest(unittest.TestCase):
    def test_years_are_read_from_the_span_as_printed(self):
        self.assertEqual(kp.parse_span("1861-1864"), (1861, 1864, False, False))
        self.assertEqual(kp.parse_span("at least 1950-1951"), (1950, 1951, True, False))
        self.assertEqual(kp.parse_span("1909-at least 1912"), (1909, 1912, False, True))
        self.assertEqual(kp.parse_span("1912.10.01-1913"), (1912, 1913, False, False))
        self.assertEqual(kp.parse_span("1909-"), (1909, None, False, False))
        self.assertEqual(kp.parse_span("-1911"), (None, 1911, False, False))
        self.assertEqual(kp.parse_span("-"), (None, None, False, False))

    def test_a_decade_counts_as_its_first_year(self):
        # The archive's "1950s-" has no year the cache's own parser can read; the cut-off must still see it.
        self.assertEqual(kp.parse_span("1950s-"), (1950, None, True, False))

    def test_a_typing_slip_is_not_a_year(self):
        self.assertEqual(kp.parse_span("1560-1943"), (None, 1943, False, False))


class CutoffTest(unittest.TestCase):
    def reason(self, *spans):
        return kp.withhold_reason([dict(zip(("from", "to"), kp.parse_span(s)[:2])) for s in spans])

    def test_service_that_begins_in_1950_or_later_is_withheld(self):
        self.assertEqual(self.reason("1950-1952"), "begins")
        self.assertEqual(self.reason("1949-1952"), None)
        self.assertEqual(self.reason("1975-1980"), "begins")
        self.assertEqual(self.reason("1950s-"), "begins")

    def test_service_that_ends_after_1960_is_withheld(self):
        self.assertEqual(self.reason("1930-1960"), None)
        self.assertEqual(self.reason("1930-1961"), "ends")

    def test_any_one_stint_is_enough(self):
        self.assertEqual(self.reason("1900-1910", "1962-1970"), "begins")
        self.assertEqual(self.reason("1900-1910", "1940-1962"), "ends")

    def test_a_stint_with_no_end_is_read_as_a_long_career(self):
        self.assertEqual(kp.OPEN_END_YEARS, 30)
        self.assertEqual(self.reason("1930-"), None)   # would end 1960 at the latest
        self.assertEqual(self.reason("1931-"), "open")  # might have ended 1961
        self.assertEqual(self.reason("1890-"), None)

    def test_no_year_at_all_is_withheld_but_one_dated_stint_is_enough(self):
        self.assertEqual(self.reason("-"), "undated")
        self.assertEqual(self.reason("-", "1890-1900"), None)

    def test_build_leaves_withheld_people_out_of_the_files_and_the_report_never_names_them(self):
        places, rosters = archive({1: ("a", "Alpha Point", "ME", [
            raw_line("Old Keeper", "1880-1890", "old-keeper"),
            raw_line("Recent Keeper", "1961-1970", "recent-keeper"),
            raw_line("Edge Keeper", "1949-1960", "edge-keeper"),
            raw_line("Late Keeper", "1900-1961", "late-keeper"),
            raw_line("Undated Keeper", "-", "undated-keeper"),
        ])})
        out = kp.build(places, rosters, [])
        self.assertEqual(sorted(out["people"]), ["edge-keeper", "old-keeper"])
        rep = out["report"]
        self.assertEqual((rep["archive_people"], rep["people_published"], rep["people_withheld"]), (5, 2, 3))
        self.assertEqual(rep["withheld_by_reason"], {"begins": 1, "ends": 1, "undated": 1})
        text = json.dumps(rep).lower()
        for who in ("recent", "late keeper", "undated keeper"):
            self.assertNotIn(who, text)


class GroupingTest(unittest.TestCase):
    def test_the_same_archive_record_at_two_stations_is_one_person_with_two_stints(self):
        places, rosters = archive({
            1: ("alpha", "Alpha Point", "ME", [raw_line("Jane Doe", "1870-1880", "jane-doe")]),
            2: ("beta", "Beta Rock", "NH", [raw_line("Jane Doe", "1881-1890", "jane-doe", "first assistant", "1st Assistant Lighthouse Keeper")]),
        })
        out = kp.build(places, rosters, [])
        self.assertEqual(list(out["people"]), ["jane-doe"])
        p = out["people"]["jane-doe"]
        self.assertEqual([(s["place"], s["from"], s["to"]) for s in p["stints"]], [("alpha", 1870, 1880), ("beta", 1881, 1890)])
        self.assertEqual(p["archive"], "https://archives.uslhs.org/people/jane-doe")
        self.assertEqual(out["report"]["people_with_stints_at_several_places"], 1)

    def test_the_same_name_in_different_records_is_two_people_and_never_one(self):
        places, rosters = archive({
            1: ("alpha", "Alpha Point", "ME", [raw_line("John Smith", "1850-1860", "john-smith")]),
            2: ("beta", "Beta Rock", "OR", [raw_line("John Smith", "1920-1930", "john-smith-0")]),
        })
        out = kp.build(places, rosters, [])
        self.assertEqual(sorted(out["people"]), ["john-smith", "john-smith-0"])
        for p in out["people"].values():
            self.assertEqual(len(p["stints"]), 1)
        self.assertEqual(out["report"]["people_with_stints_at_several_places"], 0)
        self.assertNotIn("possibly", out["people"]["john-smith"])  # a century and a continent apart

    def test_two_lines_at_one_place_are_one_person_and_two_stints(self):
        places, rosters = archive({1: ("alpha", "Alpha Point", "ME", [
            raw_line("Jane Doe", "1870-1875", "jane-doe", "first assistant", "1st Assistant Lighthouse Keeper"),
            raw_line("Jane Doe", "1875-1880", "jane-doe"),
        ])})
        p = kp.build(places, rosters, [])["people"]["jane-doe"]
        self.assertEqual([s["role"] for s in p["stints"]], ["first assistant", "head keeper"])
        self.assertEqual(p["name"], "Jane Doe")

    def test_roles_keep_the_archives_heading_only_when_it_is_not_a_standard_one(self):
        line = kp.make_line(raw_line("A B", "1900-1901", "a-b", "other", "Machinist"))
        self.assertEqual((line["role"], line["role_raw"]), ("other", "Machinist"))
        self.assertNotIn("role_raw", kp.make_line(raw_line("A B", "1900-1901", "a-b")))

    def test_an_acting_assistant_is_an_assistant_not_an_acting_keeper(self):
        line = kp.make_line(raw_line("A B", "1900-1901", "a-b", "acting keeper", "Acting Assistant"))
        self.assertEqual((line["role"], line["role_raw"]), ("assistant", "Acting Assistant"))
        line = kp.make_line(raw_line("A B", "1900-1901", "a-b", "acting keeper", "Acting Principal Lighthouse Keeper"))
        self.assertEqual(line["role"], "acting keeper")

    def test_the_archives_race_and_sex_fields_are_never_carried(self):
        raw = raw_line("A B", "1900-1901", "a-b")
        raw.update({"race": "x", "sex": "y", "gender": "z"})
        line = kp.make_line(raw)
        for k in ("race", "sex", "gender"):
            self.assertNotIn(k, line)


class PossiblyTest(unittest.TestCase):
    def people(self, *specs):
        out = {}
        for pid, name, state, span in specs:
            f, t, _, _ = kp.parse_span(span)
            out[pid] = {"id": pid, "name": name, "stints": [{"place": f"{pid}-p", "state": state, "from": f, "to": t}]}
        return out

    def test_same_name_with_years_and_region_that_fit_gets_a_hint_on_both_pages(self):
        people = self.people(("jc", "John Clark", "MA", "1834-1860"), ("jc-0", "John Clark", "RI", "1860-1861"))
        # different states, no positions: no fit
        kp.add_possible(people, {})
        self.assertNotIn("possibly", people["jc"])
        people = self.people(("jc", "John Clark", "MA", "1834-1860"), ("jc-0", "John Clark", "MA", "1861-1862"))
        self.assertEqual(kp.add_possible(people, {}), 2)
        self.assertEqual(people["jc"]["possibly"], ["jc-0"])
        self.assertEqual(people["jc-0"]["possibly"], ["jc"])

    def test_near_stations_in_two_states_fit_far_ones_do_not(self):
        people = self.people(("a", "Ann Lee", "MA", "1870-1880"), ("b", "Ann Lee", "RI", "1881-1885"))
        near = {"a-p": (41.7, -70.9), "b-p": (41.5, -71.3)}
        kp.add_possible(people, near)
        self.assertEqual(people["a"]["possibly"], ["b"])
        far = {"a-p": (41.7, -70.9), "b-p": (47.0, -122.0)}
        kp.add_possible(people, far)
        self.assertNotIn("possibly", people["a"])

    def test_overlapping_careers_are_two_people(self):
        people = self.people(("a", "Ann Lee", "ME", "1870-1885"), ("b", "Ann Lee", "ME", "1875-1890"))
        self.assertEqual(kp.add_possible(people, {}), 0)

    def test_a_long_gap_is_no_fit(self):
        people = self.people(("a", "Ann Lee", "ME", "1870-1875"), ("b", "Ann Lee", "ME", "1900-1905"))
        self.assertEqual(kp.add_possible(people, {}), 0)

    def test_a_name_too_common_to_say_anything_gets_no_hint(self):
        specs = [(f"p{i}", "John Johnson", "ME", "1870-1875") for i in range(1)]
        specs += [(f"q{i}", "John Johnson", "ME", f"{1876 + i}-{1876 + i}") for i in range(kp.MAX_HINTS + 2)]
        people = self.people(*specs)
        kp.add_possible(people, {})
        self.assertNotIn("possibly", people["p0"])

    def test_jr_and_sr_are_different_names(self):
        people = self.people(("a", "John Smith, Sr.", "ME", "1870-1880"), ("b", "John Smith, Jr.", "ME", "1881-1890"))
        self.assertEqual(kp.add_possible(people, {}), 0)

    def test_no_hint_without_years(self):
        people = {"a": {"id": "a", "name": "Ann Lee", "stints": [{"place": "x", "state": "ME"}]},
                  "b": {"id": "b", "name": "Ann Lee", "stints": [{"place": "y", "state": "ME", "from": 1880, "to": 1881}]}}
        self.assertEqual(kp.add_possible(people, {}), 0)


class NameTest(unittest.TestCase):
    def test_folding_and_surnames(self):
        self.assertEqual(kp.norm_name("Joshua F. Strout"), "joshua f strout")
        self.assertEqual(kp.norm_name("José  O'Malley"), "jose o malley")
        self.assertEqual(kp.surname_and_given("Joshua F. Strout"), ("strout", "joshua f"))
        self.assertEqual(kp.surname_and_given("William K. Herriage, Jr."), ("herriage", "william k"))
        self.assertEqual(kp.surname_and_given('Patrick "Luney" Looney'), ("looney", "patrick"))
        self.assertEqual(kp.surname_and_given("Jacob Brankhorst (Brankport)"), ("brankhorst", "jacob"))
        self.assertEqual(kp.surname_and_given("Sherman"), ("sherman", ""))

    def test_letters(self):
        self.assertEqual([kp.letter_of(n) for n in ("Joshua Strout", "Édouard Ünger", "Pat O'Brien", "x")], ["S", "U", "B", "X"])
        self.assertEqual(kp.letter_of("123"), "#")
        self.assertEqual(kp.chunk_name("#"), "other")
        self.assertEqual(kp.chunk_name("S"), "S")


class MatchTest(unittest.TestCase):
    def setUp(self):
        self.places, self.rosters = archive({
            10: ("one", "One Point", "ME", [raw_line("A A", "1900-1901", "a-a")]),
            11: ("two-front", "Two Range Front", "ME", [raw_line("B B", "1900-1901", "b-b")]),
            12: ("two-rear", "Two Range Rear", "ME", [raw_line("C C", "1900-1901", "c-c")]),
            13: ("three", "Three Rock", "ME", [raw_line("D D", "1900-1901", "d-d")]),
            14: ("empty", "Empty Bar", "ME", []),
        })

    def station(self, sid, *keys, **kw):
        return {"id": sid, "country": "US", "region": "ME", "sources": [{"source": "uslhs", "key": f"uslhs:{k}"} for k in keys], **kw}

    def test_the_merges_own_join_is_used_and_a_station_may_hold_two_places(self):
        out = kp.match_places([self.station("us-me-one", 10), self.station("us-me-two", 12, 11), self.station("us-me-none", 14)],
                              self.places, self.rosters)
        self.assertEqual([m["slug"] for m in out["us-me-one"]], ["one"])
        self.assertEqual([m["slug"] for m in out["us-me-two"]], ["two-front", "two-rear"])
        self.assertNotIn("us-me-none", out)  # its place has no roster

    def test_hidden_retired_and_canadian_stations_show_no_roster(self):
        out = kp.match_places([self.station("us-me-one", 10, hidden=True), self.station("us-me-two", 11, merged_into="us-me-x"),
                               self.station("ca-ns-x", 13, country="CA")], self.places, self.rosters)
        self.assertEqual(out, {})

    def resolver(self, mapping):
        def resolve(station_id, _places):
            slug, msg = mapping.get(station_id, (None, "no match"))
            p = next((p for p in self.places if p["slug"] == slug), None)
            return p, [], msg
        return resolve

    def test_a_station_with_no_archive_record_is_matched_as_roster_py_does_but_only_by_name_and_position(self):
        r = self.resolver({"us-me-new": ("three", "matched three by name and position (0.30 km)"),
                           "us-me-weak": ("one", "matched one by name only, WARNING: its USLHS position is 90 km from the station's")})
        out = kp.match_places([self.station("us-me-new"), self.station("us-me-weak")], self.places, self.rosters, resolve=r)
        self.assertEqual(list(out), ["us-me-new"])
        self.assertIn("name and position", out["us-me-new"][0]["how"])

    def test_a_place_another_station_already_claims_is_never_given_to_a_second(self):
        r = self.resolver({"us-me-new": ("one", "matched one by name and position (0.10 km)")})
        out = kp.match_places([self.station("us-me-owner", 10), self.station("us-me-new")], self.places, self.rosters, resolve=r)
        self.assertEqual(list(out), ["us-me-owner"])

    def test_two_stations_proposing_one_place_get_neither(self):
        r = self.resolver({"us-me-a": ("three", "matched three by name and position (0.10 km)"),
                           "us-me-b": ("three", "matched three by name and position (0.20 km)")})
        out = kp.match_places([self.station("us-me-a"), self.station("us-me-b")], self.places, self.rosters, resolve=r)
        self.assertEqual(out, {})

    def test_a_station_with_an_archive_record_is_never_rematched_by_name(self):
        r = self.resolver({"us-me-one": ("three", "matched three by name and position (0.10 km)")})
        out = kp.match_places([self.station("us-me-one", 14)], self.places, self.rosters, resolve=r)
        self.assertEqual(out, {})


class FilesTest(unittest.TestCase):
    def test_write_tree_is_stable_and_removes_people_the_rule_now_withholds(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertEqual(kp.write_tree(root, {"a.json": {"id": "a"}, "b.json": {"id": "b"}}), (2, 0))
            self.assertEqual(kp.write_tree(root, {"a.json": {"id": "a"}, "b.json": {"id": "b"}}), (0, 0))
            self.assertEqual(kp.write_tree(root, {"a.json": {"id": "a"}}), (0, 1))
            self.assertEqual([p.name for p in root.glob("*.json")], ["a.json"])

    def test_one_short_object_per_line(self):
        long = "x" * 120
        text = kp.dump({"id": "a", "name": "A B", "stints": [{"place": "x", "place_name": long, "from": 1900}, {"place": "y", "place_name": long, "from": 1910}]})
        self.assertEqual(json.loads(text)["stints"][1]["place"], "y")
        self.assertIn('  {"place": "x", "place_name": "' + long + '", "from": 1900},\n', text)


def keeper_data(people, rosters=None, research=None, report=None):
    return kp.KeeperData(people, rosters or {}, research or {}, report)


def person(pid, name, *stints, **kw):
    out = []
    for place, span, role in stints:
        f, t, fa, ta = kp.parse_span(span)
        s = {"place": place, "place_name": place.title(), "state": "ME", "role": role, "span": span}
        if f is not None:
            s["from"] = f
        if t is not None:
            s["to"] = t
        out.append(s)
    return {"id": pid, "name": name, "source": "uslhs", "archive": f"https://archives.uslhs.org/people/{pid}", "stints": out, **kw}


def roster_of(station, slug, name, *lines):
    return {"station": station, "source": "uslhs", "places": [{"slug": slug, "nid": 1, "name": name, "url": f"https://archives.uslhs.org/places/{slug}", "match": "merge (uslhs:1)",
                                                               "lines": [kp.make_line(l) for l in lines]}]}


class ResearchTest(unittest.TestCase):
    def setUp(self):
        self.people = {
            "jane-doe": person("jane-doe", "Jane Doe", ("alpha", "1870-1880", "head keeper")),
            "bob-roe": person("bob-roe", "Bob Roe", ("alpha", "1881-1890", "head keeper")),
        }
        self.rosters = {
            "us-me-alpha": roster_of("us-me-alpha", "alpha", "Alpha Point",
                                     raw_line("Jane Doe", "1870-1880", "jane-doe"), raw_line("Bob Roe", "1881-1890", "bob-roe"),
                                     raw_line("Recent Person", "1962-1970", "recent-person")),
            "us-nh-beta": roster_of("us-nh-beta", "beta", "Beta Rock", raw_line("Zed Zee", "1900-1905", "zed-zee")),
        }

    def research(self, *lines):
        return {"us-me-alpha": {"keepers": list(lines)}}

    def test_a_line_that_names_the_archive_record_replaces_the_overlapping_stint_and_adds_service_elsewhere(self):
        kd = keeper_data(self.people, self.rosters, self.research(
            {"name": "Jane Doe", "role": "keeper", "from": 1871, "to": 1879, "cite": [1], "person": "jane-doe",
             "other_stations": [{"name": "Beta Rock", "id": "us-nh-beta", "from": 1860, "to": 1869, "cite": [2]}]}))
        stints = kd.people["jane-doe"]["stints"]
        self.assertEqual([(s.get("station"), s["src"], s.get("from")) for s in stints], [("us-nh-beta", "research", 1860), ("us-me-alpha", "research", 1871)])
        self.assertTrue(all(s.get("checked") or s.get("via") for s in stints))
        self.assertEqual(len(stints), 2)  # the archive's own 1870-1880 stint is replaced, not doubled
        self.assertEqual(kd.line_person[("us-me-alpha", 0)], "jane-doe")
        self.assertIn("us-me-alpha", kd.checked)

    def test_a_line_with_no_person_and_no_other_stations_joins_nobody(self):
        kd = keeper_data(self.people, self.rosters, self.research({"name": "Jane Doe", "from": 1870, "to": 1880, "cite": [1]}))
        self.assertEqual(kd.line_person, {})
        self.assertEqual(kd.research_people, 0)
        self.assertEqual(len(kd.people["jane-doe"]["stints"]), 1)
        self.assertNotIn("src", kd.people["jane-doe"]["stints"][0])  # still the archive's own stint

    def test_the_same_name_without_a_connection_is_not_joined_to_the_archive_person(self):
        kd = keeper_data(self.people, self.rosters, self.research(
            {"name": "Jane Doe", "from": 1850, "to": 1860, "cite": [1],
             "other_stations": [{"name": "Beta Rock", "from": 1861, "to": 1869, "cite": [2]}]}))
        self.assertEqual(kd.research_people, 1)
        mine = kd.people["us-me-alpha--jane-doe"]
        self.assertEqual(mine["source"], "research")
        self.assertEqual(len(mine["stints"]), 2)
        self.assertEqual(len(kd.people["jane-doe"]["stints"]), 1)  # untouched
        self.assertEqual(kd.line_person[("us-me-alpha", 0)], "us-me-alpha--jane-doe")

    def test_other_stations_without_a_cite_are_not_added(self):
        kd = keeper_data(self.people, self.rosters, self.research(
            {"name": "Jane Doe", "from": 1870, "to": 1880, "cite": [1], "person": "jane-doe",
             "other_stations": [{"name": "Beta Rock", "from": 1860, "to": 1869}]}))
        self.assertEqual(len(kd.people["jane-doe"]["stints"]), 1 + 0 + 0)
        self.assertTrue(any("no cite" in w for w in kd.warnings))

    def test_a_line_naming_a_withheld_person_stays_a_row_with_no_person(self):
        kd = keeper_data(self.people, self.rosters, self.research({"name": "Recent Person", "from": 1962, "to": 1970, "cite": [1], "person": "recent-person"}))
        self.assertNotIn("recent-person", kd.people)
        self.assertEqual(kd.line_person, {})
        self.assertEqual(kd.warnings, [])

    def test_a_person_slug_the_archive_does_not_know_is_left_unlinked_with_a_warning(self):
        kd = keeper_data(self.people, self.rosters, self.research({"name": "Nobody", "from": 1870, "to": 1880, "cite": [1], "person": "nobody-here"}))
        self.assertEqual(kd.line_person, {})
        self.assertTrue(any("nobody-here" in w for w in kd.warnings))

    def test_research_that_puts_a_person_past_the_cutoff_removes_their_page(self):
        kd = keeper_data(self.people, self.rosters, self.research(
            {"name": "Jane Doe", "from": 1870, "to": 1965, "cite": [1], "person": "jane-doe"}))
        self.assertNotIn("jane-doe", kd.people)
        self.assertEqual(kd.withheld_by_research, 1)
        rec = {"keepers": [{"name": "Jane Doe", "person": "jane-doe"}]}
        kd.station_extras("us-me-alpha", rec)
        self.assertNotIn("person", rec["keepers"][0])

    def test_possibly_hints_to_people_who_vanish_are_dropped(self):
        people = {"a": person("a", "Ann Lee", ("alpha", "1870-1875", "keeper"), possibly=["b"]),
                  "b": person("b", "Ann Lee", ("alpha", "1876-1880", "keeper"), possibly=["a"])}
        kd = keeper_data(people, {}, {"us-me-alpha": {"keepers": [{"name": "Ann Lee", "person": "b", "from": 1876, "to": 1970, "cite": [1]}]}})
        self.assertNotIn("b", kd.people)
        self.assertNotIn("possibly", kd.people["a"])

    def test_station_extras_shows_the_archive_roster_when_unchecked_and_only_a_count_when_checked(self):
        kd = keeper_data(self.people, self.rosters)
        rec: dict = {}
        kd.station_extras("us-me-alpha", rec)
        lines = rec["archive_roster"]["places"][0]["lines"]
        self.assertEqual([l["name"] for l in lines], ["Jane Doe", "Bob Roe", "Recent Person"])
        self.assertEqual([l.get("person") for l in lines], ["jane-doe", "bob-roe", None])  # the withheld person has no link
        self.assertEqual(lines[2]["span"], "1962-1970")  # but is listed as printed
        self.assertEqual(rec["archive_roster"]["count"], 3)
        checked = keeper_data(self.people, self.rosters, self.research({"name": "Jane Doe", "from": 1870, "to": 1880, "cite": [1]}))
        rec2 = {"keepers": [{"name": "Jane Doe"}]}
        checked.station_extras("us-me-alpha", rec2)
        self.assertNotIn("lines", rec2["archive_roster"]["places"][0])
        self.assertEqual(rec2["archive_roster"]["count"], 3)


class SiteFilesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.people = {
            "jane-doe": person("jane-doe", "Jane Doe", ("alpha", "1870-1880", "head keeper"), ("beta", "1881-1890", "first assistant")),
            "bob-roe": person("bob-roe", "Bob Roe", ("alpha", "1881-1890", "head keeper")),
            "ann-xu": person("ann-xu", "Ann Xu", ("gone", "1900-1910", "keeper")),
        }
        self.rosters = {
            "us-me-alpha": roster_of("us-me-alpha", "alpha", "Alpha Point", raw_line("Jane Doe", "1870-1880", "jane-doe"), raw_line("Bob Roe", "1881-1890", "bob-roe")),
            "us-nh-beta": roster_of("us-nh-beta", "beta", "Beta Rock", raw_line("Jane Doe", "1881-1890", "jane-doe")),
            "us-me-gone": roster_of("us-me-gone", "gone", "Gone Light", raw_line("Ann Xu", "1900-1910", "ann-xu")),
        }
        self.stations = {"us-me-alpha": {"name": "Alpha Point Light", "region": "ME"}, "us-nh-beta": {"name": "Beta Rock Light", "region": "NH"},
                         "us-me-new": {"name": "Gone Light", "region": "ME"}}

    def write(self, **kw):
        kd = keeper_data(self.people, self.rosters, report={"people_withheld": 5})
        counts = kd.write_site(self.tmp, self.stations, kw.get("merged", {}), kw.get("stories", {}), "2026-10-21T00:00:00Z")
        return kd, counts

    def read(self, rel):
        return json.loads((self.tmp / "k" / rel).read_text())

    def test_chunks_by_surname_initial_and_a_manifest_that_counts(self):
        _, counts = self.write()
        m = self.read("index.json")
        self.assertEqual(m["letters"], {"D": 1, "R": 1, "X": 1})
        self.assertEqual((m["total"], m["multi"], m["withheld"]), (3, 1, 5))
        self.assertEqual(counts["people"], 3)
        self.assertEqual([r[0] for r in self.read("i/D.json")["rows"]], ["jane-doe"])
        self.assertEqual(sorted(p.name for p in (self.tmp / "k" / "i").iterdir()), ["D.json", "R.json", "X.json"])
        row = self.read("i/D.json")["rows"][0]
        self.assertEqual(row[:5], ["jane-doe", "Jane Doe", 1870, 1890, "ME NH"])
        stations = self.read("stations.json")["stations"]
        self.assertEqual([stations[i][0] for i in row[6]], ["us-me-alpha", "us-nh-beta"])

    def test_the_person_pages_data_has_the_station_name_and_the_source_of_each_stint(self):
        self.write()
        p = self.read("p/D.json")["jane-doe"]
        self.assertEqual([(s["station"], s["station_name"], s["src"]) for s in p["stints"]],
                         [("us-me-alpha", "Alpha Point Light", "uslhs"), ("us-nh-beta", "Beta Rock Light", "uslhs")])
        self.assertEqual(p["stints"][0]["place_url"], "https://archives.uslhs.org/places/alpha")

    def test_a_station_that_is_not_visible_leaves_the_stint_a_plain_archive_place(self):
        self.write()
        s = self.read("p/X.json")["ann-xu"]["stints"][0]
        self.assertNotIn("station", s)
        self.assertEqual((s["place_name"], s["region"]), ("Gone", "ME"))

    def test_a_retired_station_resolves_to_the_station_that_took_its_place(self):
        self.people["ann-xu"]["stints"][0]["place"] = "gone"
        self.write(merged={"us-me-gone": "us-me-new"})
        s = self.read("p/X.json")["ann-xu"]["stints"][0]
        self.assertEqual(s["station"], "us-me-new")

    def test_a_story_that_names_the_person_is_marked_and_one_that_does_not_still_links(self):
        self.write(stories={"us-me-alpha": "In 1871 Jane Doe lit the lamp.", "us-nh-beta": "A quiet place."})
        stints = self.read("p/D.json")["jane-doe"]["stints"]
        self.assertEqual([(s.get("story"), s.get("mentioned")) for s in stints], [(True, True), (True, None)])
        bob = self.read("p/R.json")["bob-roe"]["stints"][0]
        self.assertEqual((bob.get("story"), bob.get("mentioned")), (True, None))  # "Jane Doe" in the text is not Bob Roe

    def test_names_are_matched_whole_never_as_part_of_a_longer_name(self):
        self.write(stories={"us-me-alpha": "Bob Roeder and Jane Doerr kept the light."})
        self.assertNotIn("mentioned", self.read("p/D.json")["jane-doe"]["stints"][0])
        self.assertNotIn("mentioned", self.read("p/R.json")["bob-roe"]["stints"][0])


class ValidateKeepersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for name in ("stations", "research", "stories", "people", "rosters"):
            if (FIX / name).exists():
                shutil.copytree(FIX / name, self.tmp / name)
        (self.tmp / "sources").mkdir()

    def problems(self):
        return validate.validate(self.tmp / "stations", self.tmp / "research", self.tmp / "stories", self.tmp / "sources", VOCAB,
                                 people_dir=self.tmp / "people", rosters_dir=self.tmp / "rosters")

    def edit(self, rel, fn):
        path = self.tmp / rel
        rec = json.loads(path.read_text())
        fn(rec)
        path.write_text(json.dumps(rec))

    def assertError(self, needle):
        errors = self.problems().errors
        self.assertTrue(any(needle in e for e in errors), f"no error mentioning {needle!r} in {errors}")

    def test_fixtures_pass(self):
        self.assertEqual(self.problems().errors, [])

    def test_a_person_the_rule_withholds_must_not_have_a_file(self):
        self.edit("people/mary-sample.json", lambda r: r["stints"][0].update({"from": 1955, "to": 1962}))
        self.assertError("living-people rule")

    def test_a_person_with_no_year_must_not_have_a_file(self):
        def strip(r):
            for s in r["stints"]:
                s.pop("from", None), s.pop("to", None)
        self.edit("people/mary-sample.json", strip)
        self.assertError("living-people rule")

    def test_no_race_or_sex_field_anywhere(self):
        self.edit("people/mary-sample.json", lambda r: r.update(sex="f"))
        self.assertError("race or sex")
        self.edit("people/mary-sample.json", lambda r: (r.pop("sex"), r["stints"][0].update(race="x")))
        self.assertError("race or sex")

    def test_id_and_file_name_agree(self):
        self.edit("people/mary-sample.json", lambda r: r.update(id="mary-sample-9"))
        self.assertError("does not match the file name")

    def test_a_possibly_hint_must_point_at_a_person_who_has_a_file(self):
        self.edit("people/ezra-sample.json", lambda r: r.update(possibly=["nobody"]))
        self.assertError("possibly")

    def test_a_roster_names_a_station_that_exists(self):
        shutil.copy(self.tmp / "rosters/nc/us-nc-example-shoal.json", self.tmp / "rosters/nc/us-nc-ghost-light.json")
        self.edit("rosters/nc/us-nc-ghost-light.json", lambda r: r.update(station="us-nc-ghost-light"))
        self.assertError("not a station")

    def test_research_person_and_other_stations_are_checked(self):
        def bad(r):
            r["keepers"][0]["person"] = "Not A Slug"
            r["keepers"][1]["other_stations"] = [{"name": "X"}]
        self.edit("research/us-me-example-head.json", bad)
        self.assertError("person")
        self.assertError("other_stations")


class CommittedDataTest(unittest.TestCase):
    """The files in data/people and data/rosters, as committed: the living-people rule holds for every person
    with a file, and the two kinds of file agree."""

    @classmethod
    def setUpClass(cls):
        cls.people = kp.load_people(REPO / "data" / "people")
        cls.rosters = kp.load_station_rosters(REPO / "data" / "rosters")

    def test_nobody_with_a_file_is_withheld_by_the_rule(self):
        bad = [pid for pid, p in self.people.items() if kp.withhold_reason(p["stints"])]
        self.assertEqual(bad, [])

    def test_every_person_file_is_named_for_the_archive_record_and_links_back_to_it(self):
        for pid, p in self.people.items():
            self.assertEqual(p["archive"], f"https://archives.uslhs.org/people/{pid}")
            self.assertRegex(pid, kp.PERSON_ID_RE)

    def test_no_stint_is_in_a_roster_but_missing_from_the_person_or_the_other_way_round(self):
        lines = {(pl["slug"], l["person"], l["span"], l["name"]) for r in self.rosters.values() for pl in r["places"] for l in pl["lines"]}
        place_of_station = {pl["slug"] for r in self.rosters.values() for pl in r["places"]}
        for pid, p in self.people.items():
            for s in p["stints"]:
                if s["place"] in place_of_station:
                    self.assertIn((s["place"], pid, s["span"], p["name"]), lines, f"{pid} at {s['place']}")

    def test_the_rosters_keep_the_withheld_as_the_archive_prints_them_and_no_person_file_exists_for_them(self):
        withheld = {l["person"] for r in self.rosters.values() for pl in r["places"] for l in pl["lines"] if l["person"] not in self.people}
        self.assertGreater(len(withheld), 1000)
        self.assertTrue(all(not (REPO / "data" / "people" / f"{pid}.json").exists() for pid in list(withheld)[:200]))

    def test_the_report_matches_the_files(self):
        rep = json.loads((REPO / "data" / "people_report.json").read_text())
        self.assertEqual(rep["people_published"], len(self.people))
        self.assertEqual(rep["stations_with_archive_roster"], len(self.rosters))
        self.assertEqual(rep["people_published"] + rep["people_withheld"], rep["archive_people"])


if __name__ == "__main__":
    unittest.main()
