from typing import List, Union
from io import BytesIO

import config
import requests
from config.log_config import log_execution


class FacebookService:
    """Service simulant la publication sur Facebook."""

    @log_execution
    def __init__(self, logger) -> None:
        self.logger = logger
        if not config.FACEBOOK_PAGE_ID or not config.PAGE_ACCESS_TOKEN:
            raise RuntimeError(
                "FACEBOOK_PAGE_ID or PAGE_ACCESS_TOKEN is missing in config"
            )
        self.page_id = config.FACEBOOK_PAGE_ID
        self.page_token = config.PAGE_ACCESS_TOKEN

    def _prepare_files(self, image: Union[str, BytesIO] | None):
        """Prépare les données de fichier pour l'API Facebook."""
        if isinstance(image, BytesIO):
            image.seek(0)
            return {"source": image}, None
        if isinstance(image, str):
            fh = open(image, "rb")
            return {"source": fh}, fh
        return None, None

    @log_execution
    def post_to_facebook_page(
        self, message: str, image: Union[str, BytesIO, None] = None
    ) -> None:
        """Planifie un post sur la page Facebook principale."""
        url = f"https://graph.facebook.com/{self.page_id}/photos"
        data = {"caption": message, "access_token": self.page_token}
        files, fh = self._prepare_files(image)
        try:
            response = requests.post(url, data=data, files=files, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Facebook page response: {response.text}")
        except Exception as e:
            self.logger.exception(
                f"Erreur lors de la publication sur la page Facebook : {e}"
            )
        finally:
            if fh:
                fh.close()

    @log_execution
    def cross_post_to_groups(
        self, message: str, groups: List[str], image: Union[str, BytesIO, None] = None
    ) -> List[str]:
        """Diffuse le message dans les groupes donnés et retourne les IDs de réponse."""
        response_ids: List[str] = []
        for group in groups:
            files = fh = None
            if image is not None:
                url = f"https://graph.facebook.com/{group}/photos"
                data = {"caption": message, "access_token": self.page_token}
                files, fh = self._prepare_files(image)
            else:
                url = f"https://graph.facebook.com/{group}/feed"
                data = {"message": message, "access_token": self.page_token}
            try:
                response = requests.post(url, data=data, files=files, timeout=10)
                response.raise_for_status()
                response_ids.append(response.json().get("id"))
                self.logger.info(
                    f"Réponse du groupe {group}: {response.text}"
                )
            except Exception as e:
                self.logger.exception(
                    f"Erreur lors de la publication dans le groupe {group} : {e}"
                )
                raise
            finally:
                if fh:
                    fh.close()
        return response_ids

