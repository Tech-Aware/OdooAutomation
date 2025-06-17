# config/log_config.py

import logging
import os
import sys

def setup_logger():
    """
    Initialise et configure un logger qui écrit les messages dans un fichier log (UTF-8)
    et les affiche aussi dans la console (UTF-8 si supporté).
    Le logger permet de tracer tout ce qui se passe dans le script.
    En cas d'erreur lors de la configuration, une exception est levée.
    """
    try:
        log_file = "odoo_automation.log"  # Nom du fichier log

        # Si besoin, créer un dossier "logs" dédié (décommenter ces lignes)
        # logs_dir = "logs"
        # os.makedirs(logs_dir, exist_ok=True)
        # log_file = os.path.join(logs_dir, "odoo_automation.log")

        logger = logging.getLogger("odoo_automation")
        logger.setLevel(logging.DEBUG)  # Capture tout (DEBUG et au-dessus)

        # Pour éviter plusieurs handlers si la fonction est appelée plusieurs fois
        if not logger.handlers:
            try:
                # Handler fichier UTF-8
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)

                # Handler console (UTF-8 si supporté)
                stream_handler = logging.StreamHandler(stream=sys.stdout)
                stream_handler.setLevel(logging.INFO)

                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                stream_handler.setFormatter(formatter)

                logger.addHandler(file_handler)
                logger.addHandler(stream_handler)

            except Exception as handler_error:
                print(f"Erreur lors de la création des handlers de log : {handler_error}")
                raise

        return logger

    except Exception as e:
        print(f"Impossible d'initialiser le logger : {e}")
        raise
