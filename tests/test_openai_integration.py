from config.openai_utils import chat_gpt
from config.log_config import setup_logger

logger = setup_logger(__name__)


def main():
    question = "Donne-moi un exemple de prompt pour Odoo."
    reponse = chat_gpt(question)

    if reponse:
        logger.info(reponse)
    else:
        logger.error(
            "Une erreur est survenue lors de l'appel à l'API OpenAI. Consulte le fichier de log."
        )


if __name__ == "__main__":
    main()
