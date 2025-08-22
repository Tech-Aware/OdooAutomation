from datetime import datetime
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo
import xmlrpc.client
import re

from config.log_config import log_execution
from config.odoo_connect import get_odoo_connection
from config import ODOO_MAILING_LIST_IDS, ODOO_EMAIL_FROM


# Links par défaut pour les emails marketing.
# L'ordre reflète les canaux privilégiés : Facebook puis site web.
DEFAULT_LINKS: List[Tuple[str, str]] = [
    ("Facebook", "https://www.facebook.com/cdfesplas"),
    ("Site web", "https://www.cdfesplas.com"),
]


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

    def _ensure_scheme(self, url: str) -> str:
        """Ajoute ``https://`` si le schéma est manquant."""
        return url if re.match(r"^https?://", url) else f"https://{url}"

    def _normalize_links(self, links: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Nettoie les URLs, noms et supprime les doublons."""
        seen = set()
        result: List[Tuple[str, str]] = []
        for name, url in links:
            clean_name = name.strip()
            norm_url = self._ensure_scheme(url.strip())
            if norm_url and norm_url not in seen:
                result.append((clean_name, norm_url))
                seen.add(norm_url)
        return result

    def _build_links_section(self, links: List[Tuple[str, str]]) -> str:
        """Construit la section HTML des liens utiles."""
        links = self._normalize_links(links)
        if not links:
            return ""
        items = "".join(
            f'<p>{name} : <a href="{url}" style="color:#1a0dab;">{url}</a></p>'
            for name, url in links
        )
        return f'<div><p>Liens utiles :</p>{items}</div>'

    def format_links_preview(self, links: List[Tuple[str, str]]) -> str:
        """Retourne une représentation texte des liens."""
        links = self._normalize_links(links)
        if not links:
            return ""
        lines = "\n".join(f"{name} : {url}" for name, url in links)
        return f"Liens utiles :\n{lines}"

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

    def _format_body(self, body: str, links: List[Tuple[str, str]]) -> str:
        """Génère un contenu HTML simple et lisible pour l'email.

        Parameters
        ----------
        body: str
            Texte principal du message.
        links: List[Tuple[str, str]]
            Paires ``(nom, URL)`` à intégrer comme liens cliquables.

        Returns
        -------
        str
            HTML complet prêt à être envoyé.
        """

        links_html = self._build_links_section(links)
        unsubscribe_html = (
            '<p><a href="/unsubscribe_from_list" '
            'style="color:#1a0dab;">Se désabonner</a></p>'
        )
        return (
            "<div style=\"font-family:Arial,sans-serif;line-height:1.6;\""
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
        links: List[Tuple[str, str]],
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
        links: List[Tuple[str, str]]
            Paires ``(nom, URL)`` à ajouter au contenu.
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
        links = self._normalize_links(list(links))

        is_html = already_html or bool(re.search(r"<[^>]+>", body))
        if is_html:
            body_html = self._append_before_closing(body, self._build_links_section(links))
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
