from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from config.log_config import log_execution
from config.odoo_connect import get_odoo_connection
from config import ODOO_MAILING_LIST_IDS, ODOO_EMAIL_FROM


class OdooEmailService:
    """Service pour créer et planifier des emails marketing via Odoo."""

    @log_execution
    def __init__(self, logger) -> None:
        self.logger = logger
        self.db, self.uid, self.password, self.models = get_odoo_connection()
        if not ODOO_EMAIL_FROM:
            raise RuntimeError("ODOO_EMAIL_FROM is not configured")
        self.email_from = ODOO_EMAIL_FROM
        # Retrieve model id for mailing.list once
        model_ids = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "ir.model",
            "search",
            [[("model", "=", "mailing.list")]],
            {"limit": 1},
        )
        self.mailing_model_id = model_ids[0] if model_ids else None

    @log_execution
    def schedule_email(
        self,
        subject: str,
        body: str,
        links: List[str],
        send_datetime: datetime,
        list_ids: Optional[List[int]] = None,
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

        if list_ids is None:
            list_ids = ODOO_MAILING_LIST_IDS

        links_html = (
            "<br>".join(f'<a href="{url}">{url}</a>' for url in links) if links else ""
        )
        body_html = f"<p>{body}</p>"
        if links_html:
            body_html += f"<br>{links_html}"

        link_ids: List[int] = []
        for url in links:
            link_id = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "link.tracker",
                "create",
                [{"url": url}],
            )
            link_ids.append(link_id)

        create_vals = {
            "subject": subject,
            "body_html": body_html,
            "mailing_type": "mail",
            "schedule_type": "scheduled",
            "email_from": self.email_from,
            "schedule_date": send_datetime.astimezone(ZoneInfo("UTC")).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
        if self.mailing_model_id:
            create_vals["mailing_model_id"] = self.mailing_model_id
        if list_ids:
            create_vals["contact_list_ids"] = [(6, 0, list_ids)]
        if link_ids:
            create_vals["links_ids"] = [(6, 0, link_ids)]

        mailing_id = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "mailing.mailing",
            "create",
            [create_vals],
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

