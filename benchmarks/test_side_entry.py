import unittest
from examples.side_entry import trace


class SideEntryTests(unittest.TestCase):
    def test_one_fresh_material_label_per_section(self):
        r=trace()
        self.assertEqual(r["initial_counts"],[0]*5)
        self.assertEqual(r["terminal_counts"],[1]*5)
        self.assertTrue(r["all_five_fresh_and_positive"])
        self.assertTrue(r["only_one_label_per_section_during_entry"])
        self.assertAlmostEqual(r["terminal_material_mm"][2][0],1054.)
        self.assertAlmostEqual(r["all_sections_occupied_after_mm"],1.920002253)
