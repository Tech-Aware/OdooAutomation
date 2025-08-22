"""Tests for establishing a connection to Odoo via XML-RPC."""

import unittest
from unittest.mock import MagicMock, patch
import importlib

class TestOdooConnect(unittest.TestCase):
    def setUp(self):
        common = MagicMock()

        def _authenticate(db, username, password, _):
            return 1

        common.authenticate.side_effect = _authenticate
        models = MagicMock()

        def _execute_kw(db, uid, password, model, method, args=None, kwargs=None):
            if model == "product.template" and method == "search_count":
                return 42
            return []

        models.execute_kw.side_effect = _execute_kw

        def server_proxy(url, *args, **kwargs):
            if url.endswith("/common"):
                return common
            if url.endswith("/object"):
                return models
            return MagicMock()

        self.patcher = patch("xmlrpc.client.ServerProxy", side_effect=server_proxy)
        self.patcher.start()

        import config
        importlib.reload(config)
        import config.odoo_connect as odoo_connect
        importlib.reload(odoo_connect)
        self.get_odoo_connection = odoo_connect.get_odoo_connection
        self.addCleanup(self.patcher.stop)

    def test_connection(self):
        db, uid, password, models = self.get_odoo_connection()
        self.assertIsNotNone(uid, "L'UID utilisateur ne doit pas être None après connexion.")

    def test_product_count(self):
        db, uid, password, models = self.get_odoo_connection()
        count = models.execute_kw(db, uid, password, 'product.template', 'search_count', [[]])
        self.assertIsInstance(count, int, "Le nombre de produits doit être un entier.")

if __name__ == "__main__":
    unittest.main()
