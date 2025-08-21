"""Workflow de création d'email marketing via Telegram."""

from datetime import datetime, timedelta
from services.openai_service import OpenAIService
from services.telegram_service import TelegramService
from services.odoo_email_service import OdooEmailService
from config.log_config import setup_logger, log_execution


@log_execution
def main() -> None:
    logger = setup_logger(__name__)

    openai_service = OpenAIService(logger)
    telegram_service = TelegramService(logger, openai_service)
    telegram_service.start()
    try:
        email_service = OdooEmailService(logger)
    except RuntimeError as err:
        logger.exception(f"Initialisation du service Odoo échouée : {err}")
        telegram_service.send_message(str(err))
        return

    telegram_service.send_message("Prêt pour l'email marketing !")

    while True:
        text = telegram_service.wait_for_message()
        if not text:
            break

        try:
            subject, body = openai_service.generate_marketing_email(text)
            links: list[str] = []
            while True:
                preview = f"Objet: {subject}\n\n{body}"
                action = telegram_service.send_message_with_buttons(
                    preview,
                    ["Modifier", "Liens", "Publier", "Programmer", "Terminer"],
                )

                if action == "Modifier":
                    corrections = telegram_service.ask_text(
                        "Partagez vos modifications s'il vous plaît !"
                    )
                    body = openai_service.apply_corrections(body, corrections)
                    continue

                if action == "Liens":
                    link_text = telegram_service.ask_text(
                        "Fournissez les liens séparés par des espaces ou retours à la ligne"
                    )
                    new_links = [l.strip() for l in link_text.split() if l.strip()]
                    links.extend(new_links)
                    continue

                if action == "Publier":
                    email_service.schedule_email(
                        subject, body, links, datetime.utcnow()
                    )
                    telegram_service.send_message("Email envoyé.")
                    break

                if action == "Programmer":
                    now = datetime.utcnow()
                    days_ahead = (2 - now.weekday()) % 7  # 2 = mercredi
                    target = (now + timedelta(days=days_ahead)).replace(
                        hour=6, minute=0, second=0, microsecond=0
                    )
                    if target <= now:
                        target += timedelta(days=7)
                    email_service.schedule_email(subject, body, links, target)
                    telegram_service.send_message("Email programmé.")
                    break

                if action == "Terminer":
                    break
        except Exception as err:  # pragma: no cover - log then continue
            logger.exception(f"Erreur lors du traitement : {err}")


if __name__ == "__main__":
    main()

