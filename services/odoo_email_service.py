from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

from config.log_config import log_execution
from config.odoo_connect import get_odoo_connection


class OdooEmailService:
    """Service pour créer et planifier des emails marketing via Odoo."""

    @log_execution
    def __init__(self, logger) -> None:
        self.logger = logger
        self.db, self.uid, self.password, self.models = get_odoo_connection()

    @log_execution
    def schedule_email(
        self, subject: str, body: str, links: List[str], send_datetime: datetime
    ) -> int:
        """Crée et programme un email marketing.

        Parameters
        ----------
        subject: str
            Objet de l'email.
        body: str
            Contenu principal de l'email (HTML ou texte).
        links: List[str]
            Liste d'URL à ajouter au contenu.
        send_datetime: datetime
            Date et heure d'envoi (avec fuseau horaire).

        Returns
        -------
        int
            L'identifiant de l'email créé.
        """

        links_html = (
            "<br>".join(f'<a href="{url}">{url}</a>' for url in links)
            if links
            else ""
        )
        body_html = f"<p>{body}</p>"
        if links_html:
            body_html += f"<br>{links_html}"

        mailing_id = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "mailing.mailing",
            "create",
            [
                {
                    "subject": subject,
                    "body_html": body_html,
                    "mailing_type": "mail",
                    "schedule_date": send_datetime.astimezone(
                        ZoneInfo("UTC")
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                }
            ],
        )

        self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "mailing.mailing",
            "action_schedule",
            [[mailing_id]],
        )
        return mailing_id
