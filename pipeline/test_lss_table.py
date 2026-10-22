"""Tests for pipeline/lss_table.py on snippets of the Life-Saving Service reports' OCR text.

Each layout below is copied (shortened) from the 1909 report or an older one: the OCR cuts the printed
table into fragments and the fragments arrive in different orders in different districts."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lss_table as T  # noqa: E402


def lines(text: str) -> list[str]:
    """The corpus text has two spaces between words and a blank line between cells."""
    return [ln.replace(" ", "  ") + " " for ln in text.strip().split("\n")]


ROW_ORDER = """
Quoddy Head .
Maine .
Carrying Point Cove ....
44 48 40
66 58 50
Cross Island .
. do .
Off Machiasport .
44 36 45
67 16 30
Great Wass Island.
. do .
Off Jonesport .
44 28 00
67 35 30
"""

COLUMN_ORDER = """
Quoddy Head
Cross Island
Crumple Island
Me .
Me .
Me .
Carrying Point Cove
Off Machias Port
Off Jonesport
44 48 40
44 36 00
44 26 40
66 58 50
67 17 00
67 35 50
"""

SPLIT_NUMBERS = """
Cape Henry .
Virginia .
Virginia Beach .
. do .
At the cape .
South of the cape .
36
55
10
75
59
50
36
51
10
75
58
40
"""

PAIRED = """
SandyJHook .
Spermaceti Cove _
New Jersey .
. do .
On Bay side J mile south of point of Hook.
2| miles south of Sandy Hook light .
O / //
40 27 51
40 25 40
o / rt
74 00 27
73 59 00
"""


class DistrictAndStateTest(unittest.TestCase):
    def test_district_headings_read_through_ocr_slips(self):
        self.assertEqual(T.district_number("SEVENTH  DISTRICT. "), 7)
        self.assertEqual(T.district_number("FIEST  DISTEICT. "), 1)
        self.assertEqual(T.district_number("THIRTEENTH  DISTRICT. "), 13)
        self.assertEqual(T.district_number("TWELFTH DISTRICT — COAST OF LAKE MICHIGAN."), 12)

    def test_prose_is_not_a_heading(self):
        self.assertIsNone(T.district_number("The third district of the coast has been enlarged this year by the building of new stations"))
        self.assertIsNone(T.district_number("Name of station."))

    def test_state_cells(self):
        self.assertEqual(T.state_cell("Maine ."), "ME")
        self.assertEqual(T.state_cell("N.H...."), "NH")
        self.assertEqual(T.state_cell(". do ."), T.DITTO)
        self.assertEqual(T.state_cell("_ do ."), T.DITTO)
        self.assertEqual(T.state_cell("New Jersey ."), "NJ")

    def test_a_station_name_that_is_nearly_a_state_is_not_a_state(self):
        # Georgica is a station on Long Island; read as "Georgia" it put 25 stations in the wrong state once
        self.assertIsNone(T.state_cell("Georgica"))
        self.assertIsNone(T.state_cell("Maddequet"))


class CoordinateTest(unittest.TestCase):
    def test_dms_value(self):
        self.assertAlmostEqual(T.dms_value((44, 48, 40)), 44 + 48 / 60 + 40 / 3600, places=6)
        self.assertIsNone(T.dms_value((44, 61, 0)))          # minutes over 59: damaged
        self.assertIsNone(T.dms_value((44, None, 0)))

    def test_latitude_and_longitude_are_told_apart_by_degrees(self):
        self.assertEqual(T.classify_triple((44, 48, 40)), "lat")
        self.assertEqual(T.classify_triple((66, 58, 50)), "lon")
        self.assertEqual(T.classify_triple((124, 34, 40)), "lon")
        self.assertIsNone(T.classify_triple((55, 0, 0)))
        # Nome: latitude 64, longitude 165
        self.assertEqual(T.classify_triple((64, 30, 0), alaska=True), "lat")
        self.assertEqual(T.classify_triple((165, 23, 0), alaska=True), "lon")

    def test_numeric_lines(self):
        self.assertTrue(T.is_numeric_line("44  48  40"))
        self.assertTrue(T.is_numeric_line("00  iSS  50"))
        self.assertTrue(T.is_numeric_line(".50"))
        self.assertFalse(T.is_numeric_line("4 miles north of Absecon light"))
        self.assertFalse(T.is_numeric_line("Fort Point"))


class RowOrderTest(unittest.TestCase):
    def test_one_row_after_another(self):
        rows, notes, problems = T.parse_district(1, lines(ROW_ORDER))
        self.assertEqual([r.name for r in rows], ["Quoddy Head .", "Cross Island .", "Great Wass Island."])
        self.assertEqual([r.state for r in rows], ["ME", "ME", "ME"])
        self.assertTrue(all(r.clean for r in rows))
        self.assertAlmostEqual(rows[0].lat, 44.811111, places=5)
        self.assertAlmostEqual(rows[0].lon, -66.980556, places=5)         # west is negative
        self.assertEqual(rows[1].locality, "Off Machiasport")
        self.assertEqual(T.split_mark(rows[0].name)[0], "Quoddy Head")

    def test_a_damaged_number_unreads_only_its_own_station(self):
        text = ROW_ORDER.replace("66 58 50", "00 iSS 50")
        rows, _, _ = T.parse_district(1, lines(text))
        self.assertFalse(rows[0].clean)
        self.assertEqual(rows[0].problem, "a coordinate is damaged")
        self.assertTrue(rows[1].clean and rows[2].clean)

    def test_a_missing_coordinate_leaves_the_block_unclean_and_never_guesses(self):
        text = ROW_ORDER.replace("44 36 45\n67 16 30\n", "")
        rows, _, _ = T.parse_district(1, lines(text))
        # three stations in two blocks of one: the second block has two names and one coordinate pair
        self.assertTrue(rows[0].clean)
        self.assertFalse(any(r.clean for r in rows[1:]))
        self.assertTrue(all(r.lat is None for r in rows[1:]))


class OtherLayoutsTest(unittest.TestCase):
    def test_all_names_then_all_states_then_localities_then_numbers(self):
        rows, _, _ = T.parse_district(1, lines(COLUMN_ORDER))
        self.assertEqual([T.split_mark(r.name)[0] for r in rows], ["Quoddy Head", "Cross Island", "Crumple Island"])
        self.assertTrue(all(r.clean for r in rows))
        self.assertAlmostEqual(rows[2].lat, 44.444444, places=5)
        self.assertAlmostEqual(rows[2].lon, -67.597222, places=5)

    def test_degrees_minutes_and_seconds_on_lines_of_their_own(self):
        rows, _, _ = T.parse_district(7, lines(SPLIT_NUMBERS))
        self.assertEqual([r.state for r in rows], ["VA", "VA"])
        self.assertTrue(all(r.clean for r in rows))
        self.assertAlmostEqual(rows[0].lat, 36 + 55 / 60 + 10 / 3600, places=5)
        self.assertAlmostEqual(rows[1].lon, -(75 + 58 / 60 + 40 / 3600), places=5)

    def test_two_names_two_states_then_two_latitudes_and_two_longitudes(self):
        rows, _, _ = T.parse_district(5, lines(PAIRED))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r.clean for r in rows))
        self.assertAlmostEqual(rows[0].lat, 40 + 27 / 60 + 51 / 3600, places=5)
        self.assertAlmostEqual(rows[1].lon, -(73 + 59 / 60), places=5)
        self.assertEqual({r.state for r in rows}, {"NJ"})

    def test_a_name_wrapped_over_two_cells(self):
        text = "Portsmouth Har-\n. do .\nWood Island, Portsmouth Harbor .\n43 03 50\n70 41 55\nbor.\n"
        rows, _, _ = T.parse_district(1, lines(text))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].name, "Portsmouth Harbor.")
        self.assertTrue(rows[0].clean)

    def test_a_dropped_state_cell_takes_the_state_of_both_neighbours(self):
        # names and states alternate; Salmon Creek's "do" is missing
        text = "Big Sandy .\nNew York .\nSalmon Creek a . . . .\nOswego .\nNew York .\nCharlotte .\n. do .\n"
        rows, _, _ = T.parse_district(10, lines(text))
        self.assertEqual([r.state for r in rows], ["NY", "NY", "NY", "NY"])
        self.assertEqual([r.state_inferred for r in rows], [False, True, False, False])

    def test_a_dropped_state_cell_is_not_guessed_between_two_states(self):
        text = "Erie .\nPennsylvania .\nAshtabula .\nFairport .\nOhio .\n"
        rows, _, _ = T.parse_district(10, lines(text))
        self.assertEqual([r.state for r in rows], ["PA", None, "OH"])

    def test_page_numbers_beside_the_running_head_are_not_degrees(self):
        text = ("Cape Henlopen .\nDelaware .\nNear light .\n38 46 50\n75 07 10\n"
                "314\nREPORT UNITED STATES LIFE-SAVING SERVICE.\n315\nLewes .\n. do .\nAt the village .\n38 47 20\n75 08 00\n")
        rows, _, _ = T.parse_district(6, lines(text))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r.clean for r in rows))
        # a degree beside the head is kept: "40" is the last token of a latitude, not a page number
        text2 = "Cape Henlopen .\nDelaware .\nNear light .\n38\n46\n50\n75\n07\n40\nREPORT UNITED STATES LIFE-SAVING SERVICE.\n"
        rows2, _, _ = T.parse_district(6, lines(text2))
        self.assertAlmostEqual(rows2[0].lon, -(75 + 7 / 60 + 40 / 3600), places=5)

    def test_pooled_columns_when_blocks_do_not_add_up(self):
        # the first row is cut away from the rest: name, state, locality, then ALL the numbers, then the other rows
        text = ("Quoddy Head .\nMaine .\nAt Carrying Point Cove .\n44 48 40\n44 36 45\n44 28 00\n66 58 50\n67 16 30\n67 35 30\n"
                "Cross Island .\nGreat Wass Island .\n. do .\n. do .\nOff Machiasport .\nOff Jonesport .\n")
        rows, _, problems = T.parse_district(1, lines(text))
        self.assertEqual([T.split_mark(r.name)[0] for r in rows], ["Quoddy Head", "Cross Island", "Great Wass Island"])
        self.assertTrue(all(r.clean for r in rows))
        self.assertIn("read as parallel columns", problems)
        self.assertAlmostEqual(rows[1].lat, 44.6125, places=4)
        self.assertAlmostEqual(rows[2].lon, -(67 + 35 / 60 + 30 / 3600), places=4)


class NameTest(unittest.TestCase):
    def test_marks_come_off_names(self):
        self.assertEqual(T.split_mark("Bolinas  Bay  b . "), ("Bolinas Bay", "b"))
        self.assertEqual(T.split_mark("Fort Lauderdale t"), ("Fort Lauderdale", "*"))      # a dagger the OCR read as t
        self.assertEqual(T.split_mark("Indian  River  Inlet® "), ("Indian River Inlet", "*"))
        self.assertEqual(T.split_mark("Quoddy  Head . "), ("Quoddy Head", None))

    def test_good_names(self):
        self.assertTrue(T.good_name("Cahoons Hollow"))
        self.assertTrue(T.good_name("Hunniwell's Beach"))
        self.assertFalse(T.good_name("4 miles north of Absecon light"))
        self.assertFalse(T.good_name("Wallops^ Beach"))

    def test_names_against_localities(self):
        self.assertTrue(T.looks_like_name("North Scituate"))
        self.assertTrue(T.looks_like_name("Point Judith"))
        self.assertFalse(T.looks_like_name("Near the Lights"))
        self.assertFalse(T.looks_like_name("Biddeford Pool, Fletchers Neck"))
        self.assertFalse(T.looks_like_name("5 miles north of Fort Gratiot light"))


class TableFindingTest(unittest.TestCase):
    def test_the_table_is_found_by_its_heading_even_when_the_ocr_spoils_a_word(self):
        text = ["Some prose.", "MFE-SAVING  DISTRICTS  AND   STATIONS    IN  THE   UNITED", "STATES.", "FIRST  DISTRICT.",
                "COASTS  OF  MAINE  AND  NEW  HAMPSHIRE.", "Name  of  station.", "State.", "Locality."]
        found = T.find_tables(text)
        self.assertEqual(found, [(1, 0)])

    def test_an_index_entry_is_not_the_table(self):
        self.assertEqual(T.find_tables(["Districts  and  stations  on,  number  of  11", "Some more index."]), [])


if __name__ == "__main__":
    unittest.main()
