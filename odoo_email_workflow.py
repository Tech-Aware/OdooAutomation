"""Workflow de création d'email marketing via Telegram."""

from datetime import datetime, timedelta
import os
import re
import xmlrpc.client
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from services.openai_service import OpenAIService
from services.telegram_service import TelegramService
from services.odoo_email_service import OdooEmailService, DEFAULT_LINKS
from config.log_config import setup_logger, log_execution
from config import ODOO_MAILING_LIST_IDS


@log_execution
def run_workflow(
    logger,
    telegram_service: "TelegramService",
    openai_service: "OpenAIService",
    email_service: "OdooEmailService",
) -> None:
    """Exécute le workflow d'email marketing avec des services déjà initialisés."""

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

    action = telegram_service.send_message_with_buttons(
        "Bienvenue dans le workflow d'email marketing.",
        ["Continuer", "Retour"],
    )
    if action == "Retour":
        return

    text = telegram_service.ask_text(
        "Envoyez le sujet du mail via un message audio ou un message texte !",
    )
    if not text:
        return

    try:
        subject, html_body = openai_service.generate_marketing_email(text)
        links: list[tuple[str, str]] = DEFAULT_LINKS.copy()
        while True:
            links_preview = email_service.format_links_preview(links)
            preview_body = html_body
            if links_preview:
                preview_body += "\n\n" + links_preview
            preview_body += "\n\nSe désabonner"
            preview = f"{subject}\n\n{preview_body}" if subject else preview_body
            action = telegram_service.send_message_with_buttons(
                preview,
                ["Modifier", "Liens", "Programmer", "Retour au menu principal"],
            )

            if action == "Modifier":
                corrections = telegram_service.ask_text(
                    "Partagez vos modifications s'il vous plaît !",
                )
                html_body = openai_service.apply_corrections(html_body, corrections)
                continue

            if action == "Liens":
                link_text = telegram_service.ask_text(
                    "Fournissez les liens au format 'Nom : URL' séparés par des virgules ou retours à la ligne",
                )
                parts = re.split(r",|\n", link_text)
                new_links = []
                for part in parts:
                    if ":" in part:
                        name, url = part.split(":", 1)
                        name, url = name.strip(), url.strip()
                        if name and url:
                            new_links.append((name, url))
                existing_urls = {u for _, u in new_links}
                links = new_links + [l for l in links if l[1] not in existing_urls]
                continue

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
                    logger.exception(f"Erreur lors de la programmation : {err}")
                    telegram_service.send_message(
                        f"Erreur lors de la programmation : {err}"
                    )
                final_action = telegram_service.send_message_with_buttons(
                    "Que souhaitez-vous faire ?",
                    ["Recommencer", "Retour au menu principal"],
                )
                if final_action == "Retour au menu principal":
                    telegram_service.send_message("Retour au menu principal.")
                    return
                return

            if action == "Retour au menu principal":
                telegram_service.send_message("Retour au menu principal.")
                return
    except Exception as err:  # pragma: no cover - log then continue
        logger.exception(f"Erreur lors du traitement : {err}")


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

    run_workflow(logger, telegram_service, openai_service, email_service)


if __name__ == "__main__":
    main()

