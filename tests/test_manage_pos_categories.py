from datetime import datetime
import unittest

from pos_category_management.manage_pos_categories import compute_category_actions


class TestComputeCategoryActions(unittest.TestCase):
    def test_friday_evening(self):
        dt = datetime(2024, 9, 6, 19, 0)  # Friday 19:00
        add, remove = compute_category_actions(dt)
        self.assertEqual(set(add), {"BUVETTE", "EPICERIE"})
        self.assertEqual(set(remove), {"FOURNIL"})

    def test_sunday(self):
        dt = datetime(2024, 9, 8, 10, 0)  # Sunday morning
        add, remove = compute_category_actions(dt)
        self.assertEqual(set(add), {"FOURNIL"})
        self.assertEqual(set(remove), {"BUVETTE", "EPICERIE"})

    def test_other_day(self):
        dt = datetime(2024, 9, 4, 12, 0)  # Wednesday
        add, remove = compute_category_actions(dt)
        self.assertEqual(set(add), set())
        self.assertEqual(set(remove), {"BUVETTE", "EPICERIE", "FOURNIL"})


if __name__ == "__main__":
    unittest.main()
