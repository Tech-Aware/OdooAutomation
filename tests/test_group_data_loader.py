# tests/test_group_data_loader.py

import unittest
from config.group_data_loader import load_group_data

class TestGroupDataLoader(unittest.TestCase):
    def test_load_group_data(self):
        data = load_group_data()
        self.assertIn("mega_groupe_ariege", data)
        self.assertEqual(data["mega_groupe_ariege"], ["ID1", "ID2"])
        self.assertEqual(data["mega_groupe_vallees"], ["ID3"])

if __name__ == "__main__":
    unittest.main()
