from config.openai_utils import chat_gpt

question = "Donne-moi un exemple de prompt pour Odoo."
reponse = chat_gpt(question)

if reponse:
    print(reponse)
else:
    print("Une erreur est survenue lors de l'appel à l'API OpenAI. Consulte le fichier de log.")
