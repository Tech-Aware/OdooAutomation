import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.openai_utils import chat_gpt

# Construction du chemin absolu vers le fichier de prompt
prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'facebook.txt')
with open(prompt_path, 'r', encoding='utf-8') as f:
    facebook_prompt = f.read()

reponse = chat_gpt(facebook_prompt)

if reponse:
    print(reponse)
else:
    print("Une erreur est survenue lors de l'appel à l'API OpenAI. Consulte le fichier de log.")
