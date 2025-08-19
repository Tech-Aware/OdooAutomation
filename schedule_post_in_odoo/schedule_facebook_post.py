"""
Script pour planifier une publication Facebook dans Odoo via XML-RPC.
Dépendances :
    - Python >= 3.6
    - Ton fichier de config log_config.py (pour le logging)
    - Odoo avec module marketing_social et flux Facebook configuré

Auteur : Kevin, Tech Aware
"""

from datetime import datetime, timedelta
from config.log_config import setup_logger, log_execution
from config.odoo_connect import get_odoo_connection

# Initialisation logging
logger = setup_logger()

# === Configuration Odoo ===

@log_execution
def get_facebook_stream_id(models, db, uid, password):
    try:
        streams = models.execute_kw(
            db, uid, password,
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

@log_execution
def schedule_post(models, db, uid, password, stream_id, message, minutes_later=30):
    try:
        scheduled_date = (datetime.utcnow() + timedelta(minutes=minutes_later)).strftime('%Y-%m-%d %H:%M:%S')
        post_vals = {
            'stream_id': stream_id,
            'message': message,
            'scheduled_date': scheduled_date,
            'media': 'facebook',
        }
        post_id = models.execute_kw(
            db, uid, password,
            'marketing.social.post', 'create',
            [post_vals]
        )
        logger.info(f"Publication Facebook planifiée avec succès (ID {post_id}), à {scheduled_date}")
        return post_id
    except Exception as e:
        logger.error(f"Erreur lors de la planification de la publication Facebook : {e}")
        raise

@log_execution
def main():
    try:
        db, uid, password, models = get_odoo_connection()
        stream_id = get_facebook_stream_id(models, db, uid, password)
        post_message = "Votre message Facebook automatisé avec Odoo et Python 🚀"
        schedule_post(models, db, uid, password, stream_id, post_message)
        logger.info("Script terminé avec succès.")
    except Exception as err:
        logger.error(f"Échec du script : {err}")

if __name__ == "__main__":
    main()
