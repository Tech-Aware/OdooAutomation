from io import BytesIO
import base64
from typing import List

from openai import OpenAI


class OpenAIService:
    """Service d'accès à l'API OpenAI pour la génération et la transcription."""

    def __init__(self, logger) -> None:
        self.logger = logger
        self.client = OpenAI()

    def generate_post_versions(self, text: str) -> List[str]:
        """Génère plusieurs versions distinctes d'un message."""
        try:
            prompt = (
                "Propose trois versions différentes et concises d'un post basé sur le texte suivant:\n"
                f"{text}"
            )
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content.strip()
            versions = [v.strip("- ") for v in content.split("\n") if v.strip()]
            return versions[:3]
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.error(f"Erreur lors de la génération des versions : {err}")
            return []

    def generate_illustrations(self, text: str) -> List[str]:
        """Génère des illustrations via l'API d'images d'OpenAI et renvoie les chemins."""
        try:
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=text,
                n=2,
                size="512x512",
                response_format="b64_json",
            )
            paths: List[str] = []
            for i, data in enumerate(response.data):
                image_bytes = base64.b64decode(data.b64_json)
                file_path = f"illustration_{i}.png"
                with open(file_path, "wb") as f:
                    f.write(image_bytes)
                paths.append(file_path)
            return paths
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.error(f"Erreur lors de la génération des illustrations : {err}")
            return []

    def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcrit un contenu audio en texte via Whisper."""
        try:
            audio_file = BytesIO(audio_data)
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=("voice.ogg", audio_file, "audio/ogg"),
            )
            return response.text.strip()
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.error(f"Erreur lors de la transcription audio : {err}")
            return ""
