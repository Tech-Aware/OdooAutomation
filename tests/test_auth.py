"""Tests for authentication against the Odoo XML-RPC API."""

import unittest
from unittest.mock import MagicMock, patch
import importlib
from config.auth import authenticate_odoo

class TestAuthOdoo(unittest.TestCase):
    def setUp(self):
        common = MagicMock()

        def _authenticate(db, username, password, _):
            return False if password == "mauvais_mot_de_passe" else 1

        common.authenticate.side_effect = _authenticate
        models = MagicMock()
        models.execute_kw.return_value = []

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
        self.config = config
        self.url = config.ODOO_URL
        self.db = config.ODOO_DB
        self.username = config.ODOO_USER
        self.password = config.ODOO_PASSWORD
        self.addCleanup(self.patcher.stop)

    def test_authenticate_success(self):
        uid = authenticate_odoo(self.url, self.db, self.username, self.password)
        self.assertIsNotNone(uid, "L'UID Odoo doit être non nul après authentification réussie.")

    def test_authenticate_fail(self):
        with self.assertRaises(Exception):
            authenticate_odoo(self.url, self.db, self.username, "mauvais_mot_de_passe")

if __name__ == "__main__":
    unittest.main()
