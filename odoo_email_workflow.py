"""Workflow de création d'email marketing via Telegram."""

from datetime import datetime, timedelta
import os
import xmlrpc.client
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from services.openai_service import OpenAIService
from services.telegram_service import TelegramService
from services.odoo_email_service import OdooEmailService
from config.log_config import setup_logger, log_execution
from config import ODOO_MAILING_LIST_IDS


@log_execution
def main() -> None:
    logger = setup_logger(__name__)

    openai_service = OpenAIService(logger)
    telegram_service = TelegramService(logger, openai_service)
    telegram_service.start()

    tz_name = os.getenv("EMAIL_TIMEZONE", "Europe/Paris")
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        logger.warning(
            "Fuseau horaire '%s' introuvable, utilisation de UTC. "
            "Installez le paquet 'tzdata' pour davantage de fuseaux horaires.",
            tz_name,
        )
        tz = ZoneInfo("UTC")

    utc = ZoneInfo("UTC")
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
            subject, html_body = openai_service.generate_marketing_email(text)
            links: list[str] = []
            while True:
                preview = f"{subject}\n\n{html_body}" if subject else html_body
                if links:
                    preview += "\n\n" + "\n".join(links)
                action = telegram_service.send_message_with_buttons(
                    preview,
                    ["Modifier", "Liens", "Publier", "Programmer", "Terminer"],
                )

                if action == "Modifier":
                    corrections = telegram_service.ask_text(
                        "Partagez vos modifications s'il vous plaît !"
                    )
                    html_body = openai_service.apply_corrections(html_body, corrections)
                    continue

                if action == "Liens":
                    link_text = telegram_service.ask_text(
                        "Fournissez les liens séparés par des espaces ou retours à la ligne"
                    )
                    new_links = [l.strip() for l in link_text.split() if l.strip()]
                    links.extend(new_links)
                    continue

                if action == "Publier":
                    target = datetime.now(tz)
                    target_utc = target.astimezone(utc)
                    try:
                        email_service.schedule_email(
                            subject,
                            html_body,
                            links,
                            target_utc,
                            ODOO_MAILING_LIST_IDS,
                            already_html=True,
                        )
                        telegram_service.send_message("Email envoyé.")
                    except xmlrpc.client.Fault as err:
                        logger.exception(
                            f"Erreur lors de l'envoi de l'email : {err}"
                        )
                        telegram_service.send_message(
                            f"Erreur lors de l'envoi de l'email : {err}"
                        )
                    break

                if action == "Programmer":
                    now = datetime.now(tz)
                    days_ahead = (2 - now.weekday()) % 7  # 2 = mercredi
                    target = (now + timedelta(days=days_ahead)).replace(
                        hour=6, minute=0, second=0, microsecond=0
                    )
                    if target <= now:
                        target += timedelta(days=7)
                    target_utc = target.astimezone(utc)
                    try:
                        email_service.schedule_email(
                            subject,
                            html_body,
                            links,
                            target_utc,
                            ODOO_MAILING_LIST_IDS,
                            already_html=True,
                        )
                        telegram_service.send_message("Email programmé.")
                    except xmlrpc.client.Fault as err:
                        logger.exception(
                            f"Erreur lors de la programmation : {err}"
                        )
                        telegram_service.send_message(
                            f"Erreur lors de la programmation : {err}"
                        )
                    break

                if action == "Terminer":
                    telegram_service.send_message("Fin du workflow email.")
                    return
        except Exception as err:  # pragma: no cover - log then continue
            logger.exception(f"Erreur lors du traitement : {err}")


if __name__ == "__main__":
    main()

