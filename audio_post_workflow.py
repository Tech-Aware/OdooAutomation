"""Workflow de publication basé sur un message vocal reçu via Telegram.

Le script invite l'utilisateur à envoyer un message vocal et construit un post
à partir de la transcription obtenue. Les interactions utilisateurs sont
désormais réalisées via un véritable bot Telegram.

"""

from services.openai_service import OpenAIService
import asyncio
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
            versions = openai_service.generate_post_versions(text)
            choice = telegram_service.ask_options("Choisissez la version", versions)

            corrected = openai_service.correct_text(choice)
            telegram_service.send_message(corrected)
            if not telegram_service.ask_yes_no("Valider ce texte ?"):
                continue
            telegram_service.send_message("Texte confirmé")
            link = telegram_service.ask_text("Ajoutez un lien (optionnel)")
            if link:
                telegram_service.send_message(link)
                final_text = f"{corrected} {link}"
            else:
                final_text = corrected

            selected_image_path: str | None = None
            if telegram_service.ask_yes_no("Générer des illustrations ?"):
                illustrations = openai_service.generate_illustrations(final_text)
                if illustrations:
                    chosen_image = telegram_service.ask_image(
                        "Choisissez une illustration", illustrations
                    )
                    if chosen_image:
                        chosen_image.seek(0)
                        selected_image_path = "selected_image.png"
                        with open(selected_image_path, "wb") as fh:
                            fh.write(chosen_image.getvalue())
            facebook_service.post_to_facebook_page(final_text, selected_image_path)
            groups = telegram_service.ask_groups()
            if groups:
                facebook_service.cross_post_to_groups(
                    final_text, groups, selected_image_path
                )

            logger.info("Publication terminée avec succès.")
        except Exception as err:  # pragma: no cover - log then continue
            logger.exception(f"Erreur lors du traitement : {err}")


if __name__ == "__main__":
    main()
