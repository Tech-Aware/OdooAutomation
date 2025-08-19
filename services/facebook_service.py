from typing import List, Union
from io import BytesIO

import config
import requests


class FacebookService:
    """Service simulant la publication sur Facebook."""

    def __init__(self, logger) -> None:
        self.logger = logger

    def _prepare_files(self, image: Union[str, BytesIO] | None):
        """Prépare les données de fichier pour l'API Facebook."""
        if isinstance(image, BytesIO):
            image.seek(0)
            return {"source": image}, None
        if isinstance(image, str):
            fh = open(image, "rb")
            return {"source": fh}, fh
        return None, None

    def post_to_facebook_page(
        self, message: str, image: Union[str, BytesIO, None] = None
    ) -> None:
        """Planifie un post sur la page Facebook principale."""
        page_id = getattr(config, "FACEBOOK_PAGE_ID", "")
        page_token = getattr(config, "FACEBOOK_PAGE_TOKEN", "")
        if not page_id or not page_token:
            msg = "FACEBOOK_PAGE_ID or FACEBOOK_PAGE_TOKEN is missing in config"
            self.logger.error(msg)
            raise ValueError(msg)

        url = f"https://graph.facebook.com/{page_id}/photos"
        data = {"caption": message, "access_token": page_token}
        files, fh = self._prepare_files(image)
        try:
            response = requests.post(url, data=data, files=files, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Facebook page response: {response.text}")
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la publication sur la page Facebook : {e}"
            )
        finally:
            if fh:
                fh.close()

    def cross_post_to_groups(
        self, message: str, groups: List[str], image: Union[str, BytesIO, None] = None
    ) -> None:
        """Diffuse le message dans les groupes donnés."""
        page_token = getattr(config, "FACEBOOK_PAGE_TOKEN", "")
        if not page_token:
            msg = "FACEBOOK_PAGE_TOKEN is missing in config"
            self.logger.error(msg)
            raise ValueError(msg)

        for group in groups:
            url = f"https://graph.facebook.com/{group}/photos"
            data = {"caption": message, "access_token": page_token}
            files, fh = self._prepare_files(image)
            try:
                response = requests.post(url, data=data, files=files, timeout=10)
                response.raise_for_status()
                self.logger.info(
                    f"Réponse du groupe {group}: {response.text}"
                )
            except Exception as e:
                self.logger.error(
                    f"Erreur lors de la publication dans le groupe {group} : {e}"
                )
            finally:
                if fh:
                    fh.close()

