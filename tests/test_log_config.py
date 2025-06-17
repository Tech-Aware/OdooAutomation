# tests/test_log_config.py

import unittest
from config.log_config import setup_logger

class TestLogger(unittest.TestCase):
    def setUp(self):
        # Initialisation du logger avant chaque test
        self.logger = setup_logger()

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

if __name__ == "__main__":
    unittest.main()

