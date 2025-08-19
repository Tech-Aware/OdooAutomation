from typing import List, Optional

import config
import requests


class FacebookService:
    """Service simulant la publication sur Facebook."""

    def __init__(self, logger) -> None:
        self.logger = logger

    def post_to_facebook_page(self, message: str, image: Optional[str] = None) -> None:
        """Planifie un post sur la page Facebook principale."""
        url = f"https://graph.facebook.com/{config.FACEBOOK_PAGE_ID}/photos"
        data = {"caption": message, "access_token": config.FACEBOOK_PAGE_TOKEN}
        files = None
        try:
            if image:
                files = {"source": open(image, "rb")}
            requests.post(url, data=data, files=files, timeout=10).raise_for_status()
            self.logger.info(
                f"Publication planifiée sur la page : {message} (image={image})"
            )
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la publication sur la page Facebook : {e}"
            )
        finally:
            if files:
                files["source"].close()

    def cross_post_to_groups(
        self, message: str, groups: List[str], image: Optional[str] = None
    ) -> None:
        """Diffuse le message dans les groupes donnés."""
        for group in groups:
            url = f"https://graph.facebook.com/{group}/photos"
            data = {"caption": message, "access_token": config.FACEBOOK_PAGE_TOKEN}
            files = None
            try:
                if image:
                    files = {"source": open(image, "rb")}
                requests.post(url, data=data, files=files, timeout=10).raise_for_status()
                self.logger.info(
                    f"Publication envoyée au groupe {group} : {message} (image={image})"
                )
            except Exception as e:
                self.logger.error(
                    f"Erreur lors de la publication dans le groupe {group} : {e}"
                )
            finally:
                if files:
                    files["source"].close()
