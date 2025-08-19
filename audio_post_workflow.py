"""Workflow de publication basé sur un message vocal reçu via Telegram.

Le script invite l'utilisateur à envoyer un message vocal et construit un post
à partir de la transcription obtenue. Les interactions utilisateurs sont
désormais réalisées via un véritable bot Telegram.

"""

from services.openai_service import OpenAIService
import asyncio
from io import BytesIO
from services.telegram_service import TelegramService
from services.facebook_service import FacebookService
from config.log_config import setup_logger


def main() -> None:
    logger = setup_logger()

    openai_service = OpenAIService(logger)
    telegram_service = TelegramService(logger, openai_service)
    telegram_service.start()
    facebook_service = FacebookService(logger)

    telegram_service.send_message("Il est temps de publier Kevin")

    while True:
        text = telegram_service.wait_for_voice_message()
        if not text:
            break

        try:
            versions = openai_service.generate_post_versions(text)
            choice = telegram_service.ask_options("Choisissez la version", versions)


            selected_image: BytesIO | None = None
            if telegram_service.ask_yes_no("Générer des illustrations ?"):
                illustrations = openai_service.generate_illustrations(choice)
                if illustrations:
                    selected_image = telegram_service.ask_image(illustrations)

            facebook_service.post_to_facebook_page(choice, selected_image)
            groups = telegram_service.ask_groups()
            if groups:
                facebook_service.cross_post_to_groups(
                    choice, groups, selected_image
                )

            logger.info("Publication terminée avec succès.")
        except Exception as err:  # pragma: no cover - log then continue
            logger.error(f"Erreur lors du traitement : {err}")


if __name__ == "__main__":
    main()
