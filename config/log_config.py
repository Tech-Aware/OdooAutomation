# config/log_config.py

import logging
import sys


def setup_logger(name: str) -> logging.Logger:
    """Initialise un logger nommé et configure les handlers.

    Les messages sont écrits dans un fichier log (UTF-8) et affichés dans la
    console. Le format inclut le nom du module pour faciliter le suivi.
    """
    try:
        log_file = "odoo_automation.log"  # Nom du fichier log

        # Si besoin, créer un dossier "logs" dédié (décommenter ces lignes)
        # logs_dir = "logs"
        # os.makedirs(logs_dir, exist_ok=True)
        # log_file = os.path.join(logs_dir, "odoo_automation.log")

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        root_logger = logging.getLogger()
        if not root_logger.handlers:
            try:
                # Handler fichier UTF-8
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setLevel(logging.DEBUG)

                # Handler console (UTF-8 si supporté)
                stream_handler = logging.StreamHandler(stream=sys.stdout)
                stream_handler.setLevel(logging.INFO)

                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                file_handler.setFormatter(formatter)
                stream_handler.setFormatter(formatter)

                root_logger.setLevel(logging.DEBUG)
                root_logger.addHandler(file_handler)
                root_logger.addHandler(stream_handler)

            except Exception as handler_error:
                print(
                    f"Erreur lors de la création des handlers de log : {handler_error}"
                )
                raise

        return logger

    except Exception as e:
        print(f"Impossible d'initialiser le logger : {e}")
        raise
