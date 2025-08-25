"""Point d'entrée principal orchestrant les différents workflows via Telegram."""

from services.openai_service import OpenAIService
from services.telegram_service import TelegramService
from services.facebook_service import FacebookService
from services.odoo_email_service import OdooEmailService
from config.log_config import setup_logger, log_execution

from audio_post_workflow import run_workflow as run_audio_workflow
from odoo_email_workflow import run_workflow as run_email_workflow


@log_execution
def main() -> None:
    logger = setup_logger(__name__)

    openai_service = OpenAIService(logger)
    telegram_service = TelegramService(logger, openai_service)
    telegram_service.start()
    timeout = 600

    try:
        while True:
            try:
                action = telegram_service.send_message_with_buttons(
                    "Que souhaitez-vous faire ?",
                    ["Publier sur Facebook", "Mass Mailing", "Quitter"],
                    timeout=timeout,
                )
            except TimeoutError:
                telegram_service.send_message(
                    "Inactivité prolongée, fermeture du programme."
                )
                break

            if action == "Publier sur Facebook":
                try:
                    facebook_service = FacebookService(logger)
                except RuntimeError as err:
                    logger.exception(
                        f"Initialisation du service Facebook échouée : {err}"
                    )
                    telegram_service.send_message(str(err))
                    continue
                run_audio_workflow(
                    logger, telegram_service, openai_service, facebook_service
                )
                continue

            if action == "Mass Mailing":
                try:
                    email_service = OdooEmailService(logger)
                except RuntimeError as err:
                    logger.exception(
                        f"Initialisation du service Odoo échouée : {err}"
                    )
                    telegram_service.send_message(str(err))
                    continue
                run_email_workflow(
                    logger, telegram_service, openai_service, email_service
                )
                continue

            if action == "Quitter":
                telegram_service.send_message("Fin du programme.")
                break
    except KeyboardInterrupt:
        logger.info("Arrêt manuel du programme")
    finally:
        telegram_service.stop()


if __name__ == "__main__":
    main()

