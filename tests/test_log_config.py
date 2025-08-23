# tests/test_log_config.py

import logging
import os
import unittest
import io
from config.log_config import setup_logger


class TestLogger(unittest.TestCase):
    def setUp(self):
        # Préparation des variables sensibles et du logger
        os.environ["TELEGRAM_BOT_TOKEN"] = "super-secret-token"
        root_logger = logging.getLogger()
        root_logger.filters = []
        self.logger = setup_logger(__name__)

    def test_info_log(self):
        try:
            self.logger.info("Test INFO : message d'information pour le logger.")
            # Ici, on suppose que si aucun bug n'est levé, c'est OK
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Erreur inattendue lors de l'écriture d'un log INFO : {e}")

    def test_error_log(self):
        try:
            self.logger.error("Test ERROR : message d'erreur pour le logger.")
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Erreur inattendue lors de l'écriture d'un log ERROR : {e}")

    def test_sensitive_data_redacted(self):
        secret = os.environ["TELEGRAM_BOT_TOKEN"]
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        try:
            self.logger.info("Token: %s", secret)
        finally:
            root_logger.removeHandler(handler)
        log_output = stream.getvalue()
        self.assertNotIn(secret, log_output)
        self.assertIn("[REDACTED]", log_output)

if __name__ == "__main__":
    unittest.main()

