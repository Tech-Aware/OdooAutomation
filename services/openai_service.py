from io import BytesIO
from typing import List

from openai import OpenAI


class OpenAIService:
    """Service simulant les appels à l'API OpenAI."""

    def __init__(self, logger) -> None:
        self.logger = logger
        self.client = OpenAI()

    def generate_post_versions(self, text: str) -> List[str]:
        """Génère plusieurs versions d'un message."""
        prompt = (
            "Propose trois versions DISTINCTES du post suivant, chacune avec un ton et un style différents "
            "(ex: professionnel, humoristique, percutant). Retourne les versions séparées par '---'.\n"
            f"{text}"
        )
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0,
            )
            content = response.choices[0].message.content
            return [v.strip() for v in content.split("---") if v.strip()]
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.error(f"Erreur lors de la génération des versions : {err}")
            return []

    def generate_illustrations(self, text: str) -> List[BytesIO]:
        """Génère une liste d'illustrations en mémoire.

        Pour l'instant, cette implémentation renvoie simplement deux flux
        ``BytesIO`` fictifs. Dans une version réelle, on appellerait l'API
        OpenAI et on transformerait les images reçues en objets ``BytesIO`` sans
        jamais les écrire sur disque.
        """
        try:
            return [BytesIO(b"image1"), BytesIO(b"image2")]
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.error(
                f"Erreur lors de la génération des illustrations : {err}"
            )
            return []

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
            self.logger.error(
                f"Erreur lors de la transcription audio : {err}"
            )
            return ""
