from datetime import datetime
import unittest

from pos_category_management.manage_pos_categories import compute_category_actions


class TestComputeCategoryActions(unittest.TestCase):
    def test_friday_morning(self):
        dt = datetime(2024, 9, 6, 7, 0)  # Friday 07:00
        add, remove = compute_category_actions(dt)
        self.assertEqual(set(add), {"BUVETTE", "EPICERIE", "BUREAU"})
        self.assertEqual(set(remove), {"FOURNIL"})

    def test_sunday_morning(self):
        dt = datetime(2024, 9, 8, 10, 0)  # Sunday 10:00
        add, remove = compute_category_actions(dt)
        self.assertEqual(set(add), {"BUVETTE", "FOURNIL", "EPICERIE", "BUREAU"})
        self.assertEqual(set(remove), set())

    def test_other_day(self):
        dt = datetime(2024, 9, 4, 12, 0)  # Wednesday
        add, remove = compute_category_actions(dt)
        self.assertEqual(set(add), set())
        self.assertEqual(set(remove), {"BUVETTE", "EPICERIE", "BUREAU", "FOURNIL"})


if __name__ == "__main__":
    unittest.main()
