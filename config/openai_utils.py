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
