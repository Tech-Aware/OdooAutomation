# config/auth.py

import xmlrpc.client
from config.log_config import setup_logger

def authenticate_odoo(url, db, username, password):
    """
    Authentifie un utilisateur Odoo via l'API XML-RPC.
    Retourne l'uid si succès, sinon lève une exception.
    """
    logger = setup_logger()
    try:
        logger.info("Tentative d'authentification Odoo...")
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        if not uid:
            logger.error("Échec de l'authentification Odoo : identifiants invalides.")
            raise Exception("Échec de l'authentification Odoo.")
        logger.info(f"Authentification Odoo réussie (uid={uid}).")
        return uid
    except Exception as e:
        logger.error(f"Erreur lors de l'authentification Odoo : {e}")
        raise
