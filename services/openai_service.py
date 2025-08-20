import base64
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Dict, List

from openai import OpenAI, OpenAIError
from config.log_config import log_execution
from generate_post.prompt_builder import build_user_prompt


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
            "uniquement avec le texte final, sans astérisques, sans préambule "
            "ni mention de version, et sans commentaire supplémentaire. "
            "Fournis simplement le texte terminé suivi des hashtags sur une seule ligne."
        )

    @staticmethod
    def _sanitize_text(text: str) -> str:
        """Nettoie les éléments de mise en forme indésirables."""
        cleaned = text.replace("*", "")
        cleaned = re.sub(
            r"(?i)voici le texte corrigé selon vos indications\s*:?", "", cleaned
        )
        cleaned = re.sub(r"(?i)version\s+(standard|courte)\s*:?", "", cleaned)
        cleaned = re.sub(r"(?mi)^\s*[-–]{3,}\s*$", "", cleaned)
        cleaned = re.sub(r"\b\d+\.\s*(#)", r"\1", cleaned)
        cleaned = re.sub(r"(?mi)^\s*\d+\s*hashtags?\s+propos[ée]s?.*$", "", cleaned)
        cleaned = re.sub(r"(?mi)^si vous avez besoin.*$", "", cleaned)
        cleaned = re.sub(r"\n{2,}", "\n", cleaned)
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        hashtags: List[str] = []
        new_lines: List[str] = []
        for line in lines:
            if line.startswith("#"):
                hashtags.extend(part for part in line.split() if part.startswith("#"))
            else:
                new_lines.append(line)
        if hashtags:
            new_lines.append(" ".join(dict.fromkeys(hashtags)))
        return "\n".join(new_lines).strip()

    @log_execution
    def generate_event_post(self, text: str) -> Dict[str, object]:
        """Génère les livrables A–E pour un texte d'événement donné."""
        info = {"programme": text}
        user_prompt = build_user_prompt(info)
        messages = [
            {"role": "system", "content": self.prompt_system},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
            )
            content = response.choices[0].message.content
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.exception(
                f"Erreur lors de la génération du post : {err}"
            )
            return {
                "standard": "",
                "short": "",
                "hooks": [],
                "hashtags": [],
                "thanks": "",
            }

        sections: Dict[str, object] = {
            "standard": "",
            "short": "",
            "hooks": [],
            "hashtags": [],
            "thanks": "",
        }
        current = None
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("A)"):
                current = "standard"
                sections[current] = line[2:].strip()
            elif line.startswith("B)"):
                current = "short"
                sections[current] = line[2:].strip()
            elif line.startswith("C)"):
                current = "hooks"
                sections[current] = []
                remainder = line[2:].strip()
                if remainder:
                    sections[current].append(remainder.lstrip("- "))
            elif line.startswith("D)"):
                current = "hashtags"
                sections[current] = []
                remainder = line[2:].strip()
                if remainder:
                    sections[current].append(remainder.lstrip("- "))
            elif line.startswith("E)"):
                current = "thanks"
                sections[current] = line[2:].strip()
            else:
                if current in {"hooks", "hashtags"}:
                    if line:
                        sections[current].append(line.lstrip("- "))
                elif current in {"standard", "short", "thanks"} and line:
                    sections[current] += (" " + line)
        sections["standard"] = self._sanitize_text(sections["standard"])
        sections["short"] = self._sanitize_text(sections["short"])
        sections["hooks"] = [self._sanitize_text(h) for h in sections["hooks"]]
        sections["hashtags"] = [self._sanitize_text(h) for h in sections["hashtags"]]
        sections["thanks"] = self._sanitize_text(sections["thanks"])
        return sections

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
                model="gpt-4o-mini",
                messages=messages,
            )
            content = response.choices[0].message.content.strip()
            return self._sanitize_text(content)
        except Exception as err:  # pragma: no cover - log then ignore
            self.logger.exception(
                f"Erreur lors de l'application des corrections : {err}"
            )
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
