"""Workflow de publication basé sur un message reçu via Telegram.

Le script invite l'utilisateur à envoyer un message vocal ou texte et construit
un post à partir du contenu obtenu. Les interactions utilisateurs sont
désormais réalisées via un véritable bot Telegram.

"""

from services.openai_service import OpenAIService
from datetime import datetime, timedelta
from services.telegram_service import TelegramService
from services.facebook_service import FacebookService
from config.log_config import setup_logger, log_execution


@log_execution
def main() -> None:
    logger = setup_logger(__name__)

    openai_service = OpenAIService(logger)
    telegram_service = TelegramService(logger, openai_service)
    telegram_service.start()
    try:
        facebook_service = FacebookService(logger)
    except RuntimeError as err:
        logger.exception(f"Initialisation du service Facebook échouée : {err}")
        telegram_service.send_message(str(err))
        return

    telegram_service.send_message("Il est temps de publier Kevin")

    last_post: str | None = None
    selected_image_path: str | None = None

    while True:
        text = telegram_service.wait_for_message()
        if not text:
            break

        try:
            if text.startswith("/illustrer"):
                if not last_post:
                    telegram_service.send_message("Aucun post à illustrer.")
                    continue
                styles = [
                    "Réaliste",
                    "Dessin animé",
                    "Pixel art",
                    "Manga",
                    "Aquarelle",
                    "Croquis",
                    "Peinture à l'huile",
                    "Low poly",
                    "Cyberpunk",
                    "Art déco",
                    "Noir et blanc",
                    "Fantaisie",
                ]
                style = telegram_service.ask_options(
                    "Choisissez un style d'illustration", styles
                )
                illustrations = openai_service.generate_illustrations(
                    last_post, style
                )
                if illustrations:
                    chosen_image = telegram_service.ask_image(
                        "Choisissez une illustration", illustrations
                    )
                    if chosen_image:
                        chosen_image.seek(0)
                        selected_image_path = "selected_image.png"
                        with open(selected_image_path, "wb") as fh:
                            fh.write(chosen_image.getvalue())
                continue

            if text.startswith("/modifier"):
                if not last_post:
                    telegram_service.send_message("Aucun post à modifier.")
                    continue
                corrections = telegram_service.ask_text(
                    "Partagez vos modifications s'il vous plaît !"
                )
                last_post = openai_service.apply_corrections(
                    last_post, corrections
                )
                telegram_service.send_message(last_post)
                continue

            if text.startswith("/publier"):
                if not last_post:
                    telegram_service.send_message("Aucun post à publier.")
                    continue
                facebook_service.post_to_facebook_page(
                    last_post, selected_image_path
                )
                groups = telegram_service.ask_groups()
                if groups:
                    facebook_service.cross_post_to_groups(
                        last_post, groups, selected_image_path
                    )
                telegram_service.send_message("Publication effectuée.")
                last_post = None
                selected_image_path = None
                continue

            if text.startswith("/programmer"):
                if not last_post:
                    telegram_service.send_message("Aucun post à programmer.")
                    continue
                now = datetime.utcnow()
                target = now.replace(hour=20, minute=0, second=0, microsecond=0)
                if now >= target:
                    target = (now + timedelta(days=1)).replace(
                        hour=8, minute=0, second=0, microsecond=0
                    )
                facebook_service.schedule_post_to_facebook_page(
                    last_post, target, selected_image_path
                )
                telegram_service.send_message("Publication planifiée.")
                last_post = None
                selected_image_path = None
                logger.info("Publication programmée avec succès.")
                continue

            # Par défaut, le message est transmis à OpenAI pour générer un post
            last_post = openai_service.generate_event_post(text)
            telegram_service.send_message(last_post)
            logger.info("Post généré avec succès.")
        except Exception as err:  # pragma: no cover - log then continue
            logger.exception(f"Erreur lors du traitement : {err}")


if __name__ == "__main__":
    main()
