# config/odoo_connect.py

import os
import xmlrpc.client
from dotenv import load_dotenv
from config.log_config import setup_logger
from config.auth import authenticate_odoo

def get_odoo_connection():
    """
    Initialise la connexion à Odoo via l'API XML-RPC.
    Utilise la fonction authenticate_odoo pour gérer l'authentification.
    Retourne : db, uid, password, models (proxy pour manipuler les objets Odoo)
    """
    logger = setup_logger()
    logger.info("Démarrage de l'initialisation de la connexion à Odoo.")

    try:
        # Charger les variables d'environnement depuis .env
        load_dotenv()
        url = os.getenv('ODOO_URL')
        db = os.getenv('ODOO_DB')
        username = os.getenv('ODOO_USER')
        password = os.getenv('ODOO_PASSWORD')

        # Vérification des informations essentielles
        if not all([url, db, username, password]):
            logger.error("Une ou plusieurs variables d'environnement Odoo sont manquantes dans le .env.")
            raise Exception("Variables d'environnement Odoo incomplètes.")

        logger.debug(f"Variables d'environnement récupérées : URL={url}, DB={db}, USER={username}")

        # Authentification via la fonction dédiée
        try:
            uid = authenticate_odoo(url, db, username, password)
        except Exception as auth_error:
            logger.error(f"Erreur lors de l'authentification : {auth_error}")
            raise

        # Connexion aux objets Odoo
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        logger.info("Connexion à Odoo réussie.")

        return db, uid, password, models

    except Exception as conn_error:
        logger.error(f"Erreur lors de la connexion à Odoo : {conn_error}")
        raise
