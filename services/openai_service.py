import base64
import os
from io import BytesIO
from pathlib import Path
from typing import List

from openai import OpenAI, OpenAIError
from config.log_config import log_execution


class OpenAIService:
    """Service simulant les appels à l'API OpenAI."""

    IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

    @log_execution
    def __init__(self, logger) -> None:
        self.logger = logger
        self.client = OpenAI()
        self.prompt_system = (
            Path(__file__).resolve().parents[1] / "prompt_system.txt"
        ).read_text(encoding="utf-8")

    @log_execution
    def generate_post_versions(self, text: str) -> List[str]:
        """Génère plusieurs versions d'un message."""
        prompt = (
            "Propose trois versions DISTINCTES du post suivant, chacune avec un ton et un style différents "
            "(ex: professionnel, humoristique, percutant). Retourne les versions séparées par '---'.\n"
            f"{text}"
        )
        try:
            messages = [
                {"role": "system", "content": self.prompt_system},
                {"role": "user", "content": prompt},
            ]
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=1.0,
            )
            content = response.choices[0].message.content
            return [v.strip() for v in content.split("---") if v.strip()]
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.exception(
                f"Erreur lors de la génération des versions : {err}"
            )
            return []

    @log_execution
    def correct_text(self, text: str) -> str:
        """Corrige le texte fourni (fonction factice pour les tests)."""
        return text

    @log_execution
    def generate_illustrations(self, prompt: str) -> List[BytesIO]:
        """Génère une liste d'illustrations en mémoire.

        Les images renvoyées par l'API sont décodées depuis du base64 et
        converties en ``BytesIO`` afin d'éviter toute écriture sur disque.
        """

        try:
            response = self.client.images.generate(
                model=self.IMAGE_MODEL,
                prompt=prompt,
                size="1024x1024",
                n=2,
            )

            images: List[BytesIO] = []
            for data in response.data:
                img_stream = BytesIO(base64.b64decode(data.b64_json))
                images.append(img_stream)
            return images
        except OpenAIError as err:

            self.logger.exception(f"Erreur de génération d’images : {err}")
            return []
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.exception(
                f"Erreur lors de la génération des illustrations : {err}"
            )
            return []

    @log_execution
    def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcrit un contenu audio en texte via le modèle Whisper."""

        try:
            audio_file = BytesIO(audio_data)
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=("voice.ogg", audio_file, "audio/ogg"),
            )
            return response.text.strip()
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.exception(
                f"Erreur lors de la transcription audio : {err}"
            )
            return ""
