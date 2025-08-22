# config/odoo_connect.py

from config.log_config import setup_logger
from config.auth import authenticate_odoo
from config import ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD
import xmlrpc.client


logger = setup_logger(__name__)

def get_odoo_connection():
    """
    Initialise la connexion à Odoo via l'API XML-RPC.
    Utilise la fonction authenticate_odoo pour gérer l'authentification.
    Retourne : db, uid, password, models (proxy pour manipuler les objets Odoo)
    """
    logger.info("Démarrage de l'initialisation de la connexion à Odoo.")

    try:
        # Retrieve connection settings from the central config
        url = ODOO_URL or "https://example.com"
        db = ODOO_DB or "db"
        username = ODOO_USER or "user"
        password = ODOO_PASSWORD or "password"

        logger.debug(
            f"Variables d'environnement récupérées : URL={url}, DB={db}, USER={username}"
        )

        # Authentification réelle
        uid = authenticate_odoo(url, db, username, password)

        # Proxy XML-RPC pour les objets Odoo
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        logger.info("Connexion à Odoo établie.")

        return db, uid, password, models

    except Exception as conn_error:
        logger.exception(f"Erreur lors de la connexion à Odoo : {conn_error}")
        raise
