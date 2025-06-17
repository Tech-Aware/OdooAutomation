# tests/test_auth.py

import unittest
import os
from dotenv import load_dotenv
from config.auth import authenticate_odoo

class TestAuthOdoo(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USER')
        self.password = os.getenv('ODOO_PASSWORD')

    def test_authenticate_success(self):
        uid = authenticate_odoo(self.url, self.db, self.username, self.password)
        self.assertIsNotNone(uid, "L'UID Odoo doit être non nul après authentification réussie.")

    def test_authenticate_fail(self):
        with self.assertRaises(Exception):
            authenticate_odoo(self.url, self.db, self.username, "mauvais_mot_de_passe")

if __name__ == "__main__":
    unittest.main()
