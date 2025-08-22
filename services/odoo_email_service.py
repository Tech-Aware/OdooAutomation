from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo
import xmlrpc.client
import re

from config.log_config import log_execution
from config.odoo_connect import get_odoo_connection
from config import ODOO_MAILING_LIST_IDS, ODOO_EMAIL_FROM


DEFAULT_LINKS = [
    "https://www.cdfesplas.com",
    "https://www.facebook.com/cdfesplas",
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

    def _normalize_links(self, links: List[str]) -> List[str]:
        """Nettoie les URLs et supprime les doublons."""
        seen = set()
        result: List[str] = []
        for link in links:
            norm = self._ensure_scheme(link.strip())
            if norm and norm not in seen:
                result.append(norm)
                seen.add(norm)
        return result

    def _replace_link_placeholders(
        self, html: str, links: List[str]
    ) -> tuple[str, List[str]]:
        """Remplace les balises ``[LIEN]`` par les URLs fournies.

        Si la balise est immédiatement suivie d'un mot (ex. ``[LIEN] Facebook``),
        ce mot devient l'ancre cliquable pointant vers l'URL correspondante,
        sans afficher l'URL en clair.

        Parameters
        ----------
        html: str
            Contenu HTML dans lequel insérer les liens.
        links: List[str]
            URLs à insérer à la place des balises.

        Returns
        -------
        tuple[str, List[str]]
            Le HTML mis à jour et la liste des liens restants non utilisés.
        """

        remaining = self._normalize_links(links)
        placeholder = "[LIEN]"
        while placeholder in html and remaining:
            url = self._ensure_scheme(remaining.pop(0))
            idx = html.index(placeholder)
            after = html[idx + len(placeholder) :]
            match = re.match(r"\s*([^<\n\r]+)", after)
            if match:
                full = match.group(0)
                text = match.group(1)
                leading_ws = full[: len(full) - len(text)]
                text = text.rstrip()
                punct = ""
                if text and text[-1] in ".,!?;:":
                    punct = text[-1]
                    text = text[:-1]
                replacement = (
                    f"{leading_ws}<a href=\"{url}\" style=\"color:#1a0dab;\">{text}</a>{punct}"
                )
                html = html[:idx] + replacement + after[len(full) :]
            else:
                anchor = f'<a href="{url}" style="color:#1a0dab;">{url}</a>'
                html = html.replace(placeholder, anchor, 1)

        html = html.replace(placeholder, "")
        return html, remaining

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

        links = self._normalize_links(links)
        body, remaining = self._replace_link_placeholders(body, links)
        links_html = "".join(
            f'<p><a href="{url}" style="color:#1a0dab;">{url}</a></p>'
            for url in remaining
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
        links = self._normalize_links(list(links) + DEFAULT_LINKS)

        is_html = already_html or bool(re.search(r"<[^>]+>", body))
        if is_html:
            body_html, remaining_links = self._replace_link_placeholders(body, links)
            if remaining_links:
                links_html = "".join(
                    f'<p><a href="{url}" style="color:#1a0dab;">{url}</a></p>'
                    for url in remaining_links
                )
                body_html = self._append_before_closing(body_html, links_html)
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
