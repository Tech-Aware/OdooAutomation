import base64
import os
import re
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
        self.prompt_correction = (
            "Tu es correcteur·rice pour des posts de réseaux sociaux. "
            "Corrige le texte fourni selon les instructions et réponds "
            "uniquement avec le texte final."
        )

    @log_execution
    def generate_event_post(self, text: str) -> str:
        """Génère un post unique à partir d'un texte libre décrivant l'événement."""
        user_prompt = (
            "Rédige un post pour les réseaux sociaux à partir des informations "
            f"suivantes : {text}"
        )
        messages = [
            {"role": "system", "content": self.prompt_system},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.exception(
                f"Erreur lors de la génération du post : {err}"
            )
            return ""

    @log_execution
    def generate_marketing_email(self, text: str) -> tuple[str, str]:
        """Génère un email marketing et renvoie l'objet ainsi que le corps HTML.

        L'objet est retourné sur la première ligne, suivi d'une ligne vide puis
        du corps complet de l'email au format HTML.

        Returns
        -------
        tuple[str, str]
            L'objet de l'email et son corps HTML complet.
        """

        user_prompt = (
            "Rédige un email marketing à partir des informations suivantes : "
            f"{text}. Fournis l'objet sur la première ligne, une ligne vide, "
            "puis le corps complet de l'email en HTML avec les balises <html> et "
            "<body>."
        )
        messages = [
            {"role": "system", "content": self.prompt_system},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
            )
            content = response.choices[0].message.content or ""
            if "\n\n" in content:
                subject, html_body = content.split("\n\n", 1)
            else:
                subject, html_body = content, ""
            subject = re.sub(r"^[Oo]bjet\s*:\s*", "", subject).strip()
            return subject, html_body.strip()
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.exception(
                f"Erreur lors de la génération de l'email : {err}"
            )
            return "", ""

    @log_execution
    def apply_corrections(self, text: str, corrections: str) -> str:
        """Applique une liste de corrections sur un texte.

        Parameters
        ----------
        text: str
            Le texte d'origine.
        corrections: str
            Les instructions de correction à appliquer.

        Returns
        -------
        str
            Le texte corrigé. En cas d'erreur, retourne le texte original.
        """

        prompt = (
            "Corrige le texte suivant en appliquant les corrections fournies.\n"
            f"Texte: {text}\n"
            f"Corrections: {corrections}"
        )

        try:
            messages = [
                {"role": "system", "content": self.prompt_correction},
                {"role": "user", "content": prompt},
            ]
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            return response.choices[0].message.content.strip()
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.exception(
                f"Erreur lors de l'application des corrections : {err}"
            )
            return text

    @log_execution
    def generate_illustrations(
        self,
        post: str,
        style: str,
        text: str | None = None,
        event_date: str | None = None,
    ) -> List[BytesIO]:
        """Génère une liste d'illustrations en mémoire dans un style donné.

        L'illustration doit mettre en scène la publication tout en affichant le
        texte ``Esplas-de-Sérou`` complété éventuellement par ``<date>`` et
        ``<texte>`` lorsque fournis.

        Les images renvoyées par l'API sont décodées depuis du base64 et
        converties en ``BytesIO`` afin d'éviter toute écriture sur disque.
        """

        parts = ["Esplas-de-Sérou"]
        if event_date:
            parts.append(event_date)
        if text:
            parts.append(text)
        text_prompt = " ".join(parts)
        prompt = (
            f"Crée une illustration dans un style {style} représentant la "
            f"publication suivante : {post}. L'image doit contenir uniquement le "
            f"texte {text_prompt} et ne contenir aucun autre texte."
        )

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
            # The OpenAI client expects a file-like object with a ``name`` attribute
            # to correctly infer the audio format. Using a tuple can lead to the
            # file being sent without proper headers, which results in the API
            # failing to decode the audio content. By setting the ``name``
            # attribute on the ``BytesIO`` object and passing it directly, the
            # library uploads the data as a real file and Whisper can decode it.
            audio_file.name = "voice.ogg"
            audio_file.seek(0)
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
            return response.text.strip()
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.exception(
                f"Erreur lors de la transcription audio : {err}"
            )
            return ""
