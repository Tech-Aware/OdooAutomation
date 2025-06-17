"""
Script pour planifier une publication Facebook dans Odoo via XML-RPC.
Dépendances :
    - Python >= 3.6
    - Ton fichier de config log_config.py (pour le logging)
    - Odoo avec module marketing_social et flux Facebook configuré

Auteur : Kevin, Tech Aware
"""

import xmlrpc.client
from datetime import datetime, timedelta
import logging
import sys
import os

# === Import de la config logging ===
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.log_config import setup_logger

# Initialisation logging
logger = setup_logger("schedule_facebook_post.log")

# === Configuration Odoo ===
ODOO_URL = "https://ton-instance-odoo.com"
ODOO_DB = "nom_de_ta_base"
ODOO_USERNAME = "ton_login"
ODOO_PASSWORD = "ton_mdp"

def connect_odoo():
    try:
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        if not uid:
            logger.error("Echec d'authentification à Odoo")
            raise Exception("Authentication failed")
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        logger.info("Connexion Odoo réussie")
        return uid, models
    except Exception as e:
        logger.error(f"Erreur lors de la connexion à Odoo : {e}")
        raise

def get_facebook_stream_id(models, uid):
    try:
        streams = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'marketing.social.stream', 'search_read',
            [[['media', '=', 'facebook']]],
            {'fields': ['id', 'name']}
        )
        if not streams:
            logger.error("Aucun flux Facebook trouvé dans Odoo.")
            raise Exception("Aucun flux Facebook trouvé")
        stream_id = streams[0]['id']
        logger.info(f"Flux Facebook sélectionné : {streams[0]['name']} (ID {stream_id})")
        return stream_id
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du flux Facebook : {e}")
        raise

def schedule_post(models, uid, stream_id, message, minutes_later=30):
    try:
        scheduled_date = (datetime.utcnow() + timedelta(minutes=minutes_later)).strftime('%Y-%m-%d %H:%M:%S')
        post_vals = {
            'stream_id': stream_id,
            'message': message,
            'scheduled_date': scheduled_date,
            'media': 'facebook',
        }
        post_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'marketing.social.post', 'create',
            [post_vals]
        )
        logger.info(f"Publication Facebook planifiée avec succès (ID {post_id}), à {scheduled_date}")
        return post_id
    except Exception as e:
        logger.error(f"Erreur lors de la planification de la publication Facebook : {e}")
        raise

def main():
    try:
        uid, models = connect_odoo()
        stream_id = get_facebook_stream_id(models, uid)
        post_message = "Votre message Facebook automatisé avec Odoo et Python 🚀"
        schedule_post(models, uid, stream_id, post_message)
        logger.info("Script terminé avec succès.")
    except Exception as err:
        logger.error(f"Échec du script : {err}")

if __name__ == "__main__":
    main()
