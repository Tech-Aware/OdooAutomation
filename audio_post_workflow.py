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

    while True:
        text = telegram_service.wait_for_message()
        if not text:
            break

        try:
            last_post = openai_service.generate_event_post(text)
            selected_image_path: str | None = None

            while True:
                action = telegram_service.send_message_with_buttons(
                    last_post,
                    ["Modifier", "Illustrer", "Publier", "Programmer", "Terminer"],
                )

                if action == "Modifier":
                    corrections = telegram_service.ask_text(
                        "Partagez vos modifications s'il vous plaît !"
                    )
                    last_post = openai_service.apply_corrections(
                        last_post, corrections
                    )
                    continue

                if action == "Illustrer":
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

                if action == "Publier":
                    facebook_service.post_to_facebook_page(
                        last_post, selected_image_path
                    )
                    groups = telegram_service.ask_groups()
                    if groups:
                        facebook_service.cross_post_to_groups(
                            last_post, groups, selected_image_path
                        )
                    telegram_service.send_message("Publication effectuée.")
                    logger.info("Post généré avec succès.")
                    break

                if action == "Programmer":
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
                    logger.info("Publication programmée avec succès.")
                    break

                if action == "Terminer":
                    break
        except Exception as err:  # pragma: no cover - log then continue
            logger.exception(f"Erreur lors du traitement : {err}")


if __name__ == "__main__":
    main()
