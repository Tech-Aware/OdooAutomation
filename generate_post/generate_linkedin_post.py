from config.openai_utils import chat_gpt

# Lire le contenu avec with open()
with open('prompts/linkedin.txt', 'r', encoding='utf-8') as f:
    linkedin_prompt = f.read()

reponse = chat_gpt(linkedin_prompt)

if reponse:
    print(reponse)
else:
    print("Une erreur est survenue lors de l'appel à l'API OpenAI. Consulte le fichier de log.")
