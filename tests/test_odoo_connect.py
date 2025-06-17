# tests/test_odoo_connect.py

import unittest
from config.odoo_connect import get_odoo_connection

class TestOdooConnect(unittest.TestCase):
    def test_connection(self):
        try:
            db, uid, password, models = get_odoo_connection()
            self.assertIsNotNone(uid, "L'UID utilisateur ne doit pas être None après connexion.")
        except Exception as e:
            self.fail(f"Erreur lors de la connexion à Odoo : {e}")

    def test_product_count(self):
        try:
            db, uid, password, models = get_odoo_connection()
            count = models.execute_kw(db, uid, password, 'product.template', 'search_count', [[]])
            self.assertIsInstance(count, int, "Le nombre de produits doit être un entier.")
        except Exception as e:
            self.fail(f"Erreur lors du comptage des produits Odoo : {e}")

if __name__ == "__main__":
    unittest.main()
