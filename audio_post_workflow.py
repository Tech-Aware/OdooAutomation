"""Workflow de publication basé sur un message vocal reçu via Telegram.

Le script invite l'utilisateur à envoyer un message vocal et construit un post
à partir de la transcription obtenue. Les interactions utilisateurs sont
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
        text = telegram_service.wait_for_voice_message()
        if not text:
            break

        try:
            choice = openai_service.generate_event_post(text)

            if telegram_service.ask_yes_no("Ajouter un lien ?"):
                link = telegram_service.ask_text("Quel lien ajouter ?")
                choice = f"{choice}\n{link}"

            selected_image_path: str | None = None
            if telegram_service.ask_yes_no("Générer des illustrations ?"):
                illustrations = openai_service.generate_illustrations(choice)
                if illustrations:
                    chosen_image = telegram_service.ask_image(
                        "Choisissez une illustration", illustrations
                    )
                    if chosen_image:
                        chosen_image.seek(0)
                        selected_image_path = "selected_image.png"
                        with open(selected_image_path, "wb") as fh:
                            fh.write(chosen_image.getvalue())

            telegram_service.send_message(choice)

            if telegram_service.ask_yes_no("Faut-il corriger ce post ?"):
                corrections = telegram_service.ask_text("Envoyez les corrections :")
                choice = openai_service.apply_corrections(choice, corrections)
                telegram_service.send_message(choice)

            if telegram_service.ask_yes_no("Souhaitez-vous programmer la publication ?"):
                now = datetime.utcnow()
                target = now.replace(hour=20, minute=0, second=0, microsecond=0)
                if now >= target:
                    target = (now + timedelta(days=1)).replace(
                        hour=8, minute=0, second=0, microsecond=0
                    )
                facebook_service.schedule_post_to_facebook_page(
                    choice, target, selected_image_path
                )
                telegram_service.send_message("Publication planifiée.")
                logger.info("Publication programmée avec succès.")
                continue

            facebook_service.post_to_facebook_page(choice, selected_image_path)
            groups = telegram_service.ask_groups()
            if groups:
                facebook_service.cross_post_to_groups(
                    choice, groups, selected_image_path
                )

            logger.info("Publication terminée avec succès.")
        except Exception as err:  # pragma: no cover - log then continue
            logger.exception(f"Erreur lors du traitement : {err}")


if __name__ == "__main__":
    main()
