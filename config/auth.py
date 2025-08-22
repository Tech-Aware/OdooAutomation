# config/auth.py

from config.log_config import setup_logger
import xmlrpc.client


logger = setup_logger(__name__)


def authenticate_odoo(url, db, username, password):
    """Authenticate against a real Odoo instance using XML-RPC."""
    logger.info("Tentative d'authentification Odoo...")
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    if not uid:
        logger.error("Échec de l'authentification Odoo : identifiants invalides.")
        raise Exception("Échec de l'authentification Odoo.")
    logger.info(f"Authentification Odoo réussie (uid={uid}).")
    return uid
