from datetime import datetime
import unittest

from pos_category_management.manage_pos_categories import compute_category_actions


class TestComputeCategoryActions(unittest.TestCase):
    def test_friday_morning(self):
        dt = datetime(2024, 9, 6, 7, 0)  # Friday 07:00
        add, remove = compute_category_actions(dt)
        self.assertIsInstance(add, tuple)
        self.assertIsInstance(remove, tuple)
        self.assertEqual(set(add), {79, 72, 53})
        self.assertEqual(set(remove), {58})

    def test_sunday_morning(self):
        dt = datetime(2024, 9, 8, 10, 0)  # Sunday 10:00
        add, remove = compute_category_actions(dt)
        self.assertIsInstance(add, tuple)
        self.assertIsInstance(remove, tuple)
        self.assertEqual(set(add), {79, 72, 53, 58})
        self.assertEqual(set(remove), set())

    def test_other_day(self):
        dt = datetime(2024, 9, 4, 12, 0)  # Wednesday
        add, remove = compute_category_actions(dt)
        self.assertIsInstance(add, tuple)
        self.assertIsInstance(remove, tuple)
        self.assertEqual(set(add), set())
        self.assertEqual(set(remove), {79, 72, 53, 58})


if __name__ == "__main__":
    unittest.main()
