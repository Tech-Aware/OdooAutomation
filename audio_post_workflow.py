"""Workflow de publication basé sur un fichier audio.

Le script parcourt les fichiers présents dans ``audio_inputs`` et simule la
création d'un post à partir de leur contenu. Les interactions utilisateurs sont
réalisées via la console pour simplifier l'exemple.
"""

from services.audio_service import AudioService
from services.openai_service import OpenAIService
from services.telegram_service import TelegramService
from services.facebook_service import FacebookService
from config.log_config import setup_logger


def main() -> None:
    logger = setup_logger()

    audio_service = AudioService(logger)
    openai_service = OpenAIService(logger)
    telegram_service = TelegramService(logger)
    facebook_service = FacebookService(logger)

    while True:
        result = audio_service.get_transcribed_text()
        if not result:
            break
        text, file_path = result

        try:
            versions = openai_service.generate_post_versions(text)
            choice = telegram_service.ask_options("Choisissez la version", versions)

            selected_image = None
            if telegram_service.ask_yes_no("Générer des illustrations ?"):
                illustrations = openai_service.generate_illustrations(choice)
                if illustrations:
                    selected_image = telegram_service.ask_options(
                        "Choisissez l'illustration", illustrations
                    )

            facebook_service.post_to_facebook_page(choice, selected_image)
            groups = telegram_service.ask_groups()
            if groups:
                facebook_service.cross_post_to_groups(
                    choice, groups, selected_image
                )

            logger.info("Publication terminée avec succès.")
        except Exception as err:  # pragma: no cover - log then continue
            logger.error(f"Erreur lors du traitement : {err}")
        finally:
            audio_service.delete_file(file_path)


if __name__ == "__main__":
    main()
