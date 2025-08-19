# config/auth.py

from config.log_config import setup_logger


def authenticate_odoo(url, db, username, password):
    """Simule l'authentification Odoo pour les tests hors ligne."""
    logger = setup_logger()
    logger.info("Tentative d'authentification Odoo...")
    if password == "mauvais_mot_de_passe":
        logger.error("Échec de l'authentification Odoo : identifiants invalides.")
        raise Exception("Échec de l'authentification Odoo.")
    # Retourne un UID fictif sans contacter un serveur distant
    uid = 1
    logger.info(f"Authentification Odoo réussie (uid={uid}).")
    return uid
