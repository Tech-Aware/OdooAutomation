from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo
import xmlrpc.client
import re

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

    def _append_before_closing(self, html: str, addition: str) -> str:
        """Insère ``addition`` avant la balise de fermeture principale."""
        if not addition:
            return html
        body_pattern = re.compile(r"</body>", re.IGNORECASE)
        if body_pattern.search(html):
            return body_pattern.sub(addition + "</body>", html, count=1)

        div_pattern = re.compile(r"</div>\s*$", re.IGNORECASE)
        if div_pattern.search(html):
            return div_pattern.sub(addition + "</div>", html)

        return html + addition

    def _format_body(self, body: str, links: List[str]) -> str:
        """Génère un contenu HTML simple et lisible pour l'email.

        Parameters
        ----------
        body: str
            Texte principal du message.
        links: List[str]
            Liste d'URL à intégrer comme liens cliquables.

        Returns
        -------
        str
            HTML complet prêt à être envoyé.
        """

        links_html = "".join(
            f'<p><a href="{url}" style="color:#1a0dab;">{url}</a></p>'
            for url in links
        )
        unsubscribe_html = (
            '<p><a href="/unsubscribe_from_list" '
            'style="color:#1a0dab;">Se désabonner</a></p>'
        )
        return (
            "<div style=\"font-family:Arial,sans-serif;line-height:1.6;"
            "color:#333;max-width:600px;margin:auto;\">"
            f"<p>{body}</p>"
            f"{links_html}"
            f"{unsubscribe_html}"
            "</div>"
        )

    def _append_unsubscribe_link(self, html: str) -> str:
        """Ajoute le lien de désinscription avant la balise de fermeture."""

        unsubscribe_html = (
            '<p><a href="/unsubscribe_from_list" '
            'style="color:#1a0dab;">Se désabonner</a></p>'
        )
        return self._append_before_closing(html, unsubscribe_html)

    @log_execution
    def schedule_email(
        self,
        subject: str,
        body: str,
        links: List[str],
        send_datetime: datetime,
        list_ids: Optional[List[int]] = None,
        already_html: bool = False,
    ) -> int:
        """Crée et programme un email marketing.

        Parameters
        ----------
        subject: str
            Objet de l'email.
        body: str
            Contenu principal de l'email. Peut être du texte brut ou un HTML
            complet.
        links: List[str]
            Liste d'URL à ajouter au contenu.
        send_datetime: datetime
            Date et heure d'envoi (avec fuseau horaire).
        already_html: bool, optional
            Indique si ``body`` est déjà un contenu HTML complet. Lorsque vrai,
            le corps est utilisé tel quel sans passer par ``_format_body``.

        Returns
        -------
        int
            L'identifiant de l'email créé.
        """

        if list_ids is None:
            list_ids = ODOO_MAILING_LIST_IDS

        is_html = already_html or bool(re.search(r"<[^>]+>", body))
        if is_html:
            links_html = "".join(
                f'<p><a href="{url}" style="color:#1a0dab;">{url}</a></p>'
                for url in links
            )
            body_html = self._append_before_closing(body, links_html)
            body_html = self._append_unsubscribe_link(body_html)
        else:
            body_html = self._format_body(body, links)

        create_vals = {
            "name": subject,
            "subject": subject,
            "body_arch": body_html,
            "body_html": body_html,
            "body_plaintext": body,
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

        mailing_id = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "mailing.mailing",
            "create",
            [create_vals],
        )

        try:
            self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "mailing.mailing",
                "action_schedule",
                [[mailing_id]],
            )
        except xmlrpc.client.Fault as err:
            if "cannot marshal None" in err.faultString:
                self.logger.warning(
                    "Odoo a retourné une valeur None lors de la programmation; "
                    "suppression de l'exception."
                )
            else:
                raise
        return mailing_id

