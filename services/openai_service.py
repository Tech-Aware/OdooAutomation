from typing import List


class OpenAIService:
    """Service simulant les appels à l'API OpenAI."""

    def __init__(self, logger) -> None:
        self.logger = logger

    def generate_post_versions(self, text: str) -> List[str]:
        """Génère plusieurs versions d'un message."""
        try:
            return [f"{text}", f"{text} (variante)"]
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.error(f"Erreur lors de la génération des versions : {err}")
            return []

    def generate_illustrations(self, text: str) -> List[str]:
        """Génère une liste de noms d'illustrations fictives."""
        try:
            return ["image1.png", "image2.png"]
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.error(
                f"Erreur lors de la génération des illustrations : {err}"
            )
            return []

    def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcrit un contenu audio en texte.

        Dans cette implémentation simplifiée, ``audio_data`` représente les
        données brutes du message vocal. La transcription est simulée en
        décodant ces octets en UTF-8. En cas d'erreur, une chaîne vide est
        retournée.
        """
        try:
            return audio_data.decode("utf-8").strip()
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.error(f"Erreur lors de la transcription audio : {err}")
            return ""
