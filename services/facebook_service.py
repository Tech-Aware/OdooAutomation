from typing import List, Union
from io import BytesIO
from datetime import datetime

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

    def _prepare_files(
        self, image: Union[str, BytesIO, List[Union[str, BytesIO]], None]
    ):
        """Prépare les données de fichier pour l'API Facebook.

        Si ``image`` est une liste, seule la première est utilisée."""
        if isinstance(image, list):
            image = image[0] if image else None
        if isinstance(image, BytesIO):
            image.seek(0)
            return {"source": image}, None
        if isinstance(image, str):
            fh = open(image, "rb")
            return {"source": fh}, fh
        return None, None

    @log_execution
    def post_to_facebook_page(
        self,
        message: str,
        image: Union[str, BytesIO, List[Union[str, BytesIO]], None] = None,
    ) -> dict | None:
        """Planifie un post sur la page Facebook principale."""
        files, fh = self._prepare_files(image)

        if files:
            url = f"https://graph.facebook.com/{self.page_id}/photos"
            data = {"caption": message, "access_token": self.page_token}
        else:
            url = f"https://graph.facebook.com/{self.page_id}/feed"
            data = {"message": message, "access_token": self.page_token}

        request_kwargs = {"data": data, "timeout": 10}
        if files:
            request_kwargs["files"] = files

        try:
            response = requests.post(url, **request_kwargs)
            response.raise_for_status()
            self.logger.info(f"Facebook page response: {response.text}")
            return response.json()
        except Exception as e:
            response = getattr(e, "response", None)
            if response is not None:
                try:
                    error_detail = response.json()
                except ValueError:
                    error_detail = response.text
            else:
                error_detail = str(e)
            self.logger.exception(
                f"Erreur lors de la publication sur la page Facebook : {error_detail}"
            )
            raise requests.HTTPError(response=response) from e
        finally:
            if fh:
                fh.close()

    @log_execution
    def schedule_post_to_facebook_page(
        self,
        message: str,
        publish_time: datetime,
        image: Union[str, BytesIO, List[Union[str, BytesIO]], None] = None,
    ) -> dict | None:
        """Planifie la publication d'un post sur la page principale."""
        files, fh = self._prepare_files(image)
        timestamp = int(publish_time.timestamp())

        if files:
            url = f"https://graph.facebook.com/{self.page_id}/photos"
            data = {
                "caption": message,
                "published": "false",
                "scheduled_publish_time": timestamp,
                "access_token": self.page_token,
            }
        else:
            url = f"https://graph.facebook.com/{self.page_id}/feed"
            data = {
                "message": message,
                "published": "false",
                "scheduled_publish_time": timestamp,
                "access_token": self.page_token,
            }

        request_kwargs = {"data": data, "timeout": 10}
        if files:
            request_kwargs["files"] = files

        try:
            response = requests.post(url, **request_kwargs)
            response.raise_for_status()
            self.logger.info(f"Facebook page response: {response.text}")
            return response.json()
        except Exception as e:
            response = getattr(e, "response", None)
            if response is not None:
                try:
                    error_detail = response.json()
                except ValueError:
                    error_detail = response.text
            else:
                error_detail = str(e)
            self.logger.exception(
                f"Erreur lors de la programmation sur la page Facebook : {error_detail}"
            )
            raise requests.HTTPError(response=response) from e
        finally:
            if fh:
                fh.close()

