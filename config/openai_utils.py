# config/openai_utils.py

import openai
from dotenv import load_dotenv
import os

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
