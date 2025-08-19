import os
from typing import Optional, Tuple


class AudioService:
    """Service de gestion des fichiers audio.

    Les fichiers audio sont simulés par des fichiers texte placés dans un
    dossier. Le contenu du fichier représente la transcription attendue.
    """

    def __init__(self, logger, input_dir: str = "audio_inputs") -> None:
        self.logger = logger
        self.input_dir = input_dir
        os.makedirs(self.input_dir, exist_ok=True)

    def get_transcribed_text(self) -> Optional[Tuple[str, str]]:
        """Retourne le texte transcrit et le chemin du fichier source.

        Le service cherche le premier fichier ``.txt`` présent dans le dossier
        configuré. Si aucun fichier n'est trouvé, ``None`` est retourné.
        """
        try:
            files = [f for f in os.listdir(self.input_dir) if f.endswith(".txt")]
            if not files:
                self.logger.info("Aucun fichier audio à traiter.")
                return None
            file_path = os.path.join(self.input_dir, files[0])
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            self.logger.info(f"Fichier audio transcrit : {file_path}")
            return text, file_path
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.error(f"Erreur lors de la transcription audio : {err}")
            return None

    def delete_file(self, file_path: str) -> None:
        """Supprime le fichier audio traité."""
        if not file_path:
            return
        try:
            os.remove(file_path)
            self.logger.info(f"Fichier supprimé : {file_path}")
        except OSError as err:  # pragma: no cover - log then ignore
            self.logger.error(
                f"Erreur lors de la suppression du fichier {file_path}: {err}"
            )
