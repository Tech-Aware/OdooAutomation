# config/openai_utils.py

import openai
from dotenv import load_dotenv
import os
from typing import Optional

from .log_config import setup_logger  # Import du setup_logger depuis le même dossier

# Initialise le logger via la config centrale
logger = setup_logger()

# Charge les variables d’environnement du .env
load_dotenv(override=True)

# Récupère la clé API
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("Clé API OpenAI manquante dans le fichier .env")
else:
    openai.api_key = api_key

# Obtenir le chemin du dossier parent
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Construire le chemin complet vers le fichier
file_path = os.path.join(parent_dir, 'prompt_system.txt')

# Lire le contenu avec with open()
with open(file_path, 'r', encoding='utf-8') as f:
    prompt_system = f.read()


def chat_gpt(prompt, model="gpt-4.1", system_prompt=prompt_system):
    """
    Appelle l'API OpenAI ChatGPT avec gestion d’erreur et log.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    try:
        logger.info(f"Appel API OpenAI : modèle={model}, prompt={prompt}")
        response = openai.chat.completions.create(
            model=model,
            messages=messages
        )
        content = response.choices[0].message.content
        logger.info("Réponse OpenAI reçue avec succès.")
        return content
    except Exception as e:
        logger.error(f"Erreur lors de l'appel OpenAI : {e}")
        return None


def generate_post_versions(text, model="gpt-4o-mini"):
    """Génère trois versions alternatives d'un texte donné.

    Args:
        text: Le texte source à transformer.
        model: Le modèle OpenAI à utiliser.

    Returns:
        Une liste contenant jusqu'à trois versions du texte.
    """
    prompt = (
        "Propose trois versions différentes du texte suivant. "
        "Sépare chaque version par une nouvelle ligne :\n"
        f"{text}"
    )
    response = chat_gpt(prompt, model=model)
    if not response:
        return []
    versions = [line.strip(" -\t") for line in response.splitlines() if line.strip()]
    return versions[:3]


def generate_illustrations(prompt_text):
    """Génère trois illustrations à partir d'un prompt texte."""
    try:
        logger.info(f"Génération d'illustrations : {prompt_text}")
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt_text,
            n=3,
            size="1024x1024"
        )
        urls = []
        for data in response.data:
            url = data.get("url") if isinstance(data, dict) else getattr(data, "url", None)
            if url:
                urls.append(url)
        return urls
    except Exception as e:
        logger.error(f"Erreur lors de la génération d'images : {e}")
        return []

# --- Audio transcription utilities -------------------------------------------------

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"}
PROCESSED_TRACK_FILE = "processed_files.txt"


def _resolve_directory(directory: str) -> str:
    """Return absolute path for the audio inbox directory."""
    if os.path.isabs(directory):
        return directory
    return os.path.join(parent_dir, directory)


def detect_new_audio(directory: str = "audio_inbox") -> Optional[str]:
    """Return path of the first unprocessed audio file in *directory*.

    The directory is created if missing. Processed files are tracked in a
    ``processed_files.txt`` file located inside the directory.
    """

    dir_path = _resolve_directory(directory)
    os.makedirs(dir_path, exist_ok=True)

    processed_file_path = os.path.join(dir_path, PROCESSED_TRACK_FILE)
    processed = set()
    if os.path.exists(processed_file_path):
        with open(processed_file_path, "r", encoding="utf-8") as f:
            processed = {line.strip() for line in f if line.strip()}

    for filename in sorted(os.listdir(dir_path)):
        ext = os.path.splitext(filename)[1].lower()
        if ext in AUDIO_EXTENSIONS and filename not in processed:
            return os.path.join(dir_path, filename)
    return None


def transcribe_audio(path: str) -> Optional[str]:
    """Transcribe *path* with OpenAI Whisper and mark it as processed."""

    try:
        with open(path, "rb") as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        text = response.get("text") if isinstance(response, dict) else getattr(response, "text", None)

        # Track as processed
        directory = os.path.dirname(path)
        processed_file_path = os.path.join(directory, PROCESSED_TRACK_FILE)
        with open(processed_file_path, "a", encoding="utf-8") as f:
            f.write(os.path.basename(path) + "\n")

        return text
    except Exception as e:
        logger.error(f"Erreur lors de la transcription audio : {e}")
        return None


def get_transcribed_text() -> Optional[str]:
    """Detect a new audio file and return its transcription."""

    audio_path = detect_new_audio()
    if not audio_path:
        logger.info("Aucun nouveau fichier audio à transcrire.")
        return None
    return transcribe_audio(audio_path)

