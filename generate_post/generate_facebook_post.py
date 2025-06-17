import sys
import os

from .. .. config.openai_utils import chat_gpt

# Lire le contenu avec with open()
with open('prompts/facebook.txt', 'r', encoding='utf-8') as f:
    facebook_prompt = f.read()

reponse = chat_gpt(facebook_prompt)

if reponse:
    print(reponse)
else:
    print("Une erreur est survenue lors de l'appel à l'API OpenAI. Consulte le fichier de log.")
