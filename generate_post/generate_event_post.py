import sys
import os
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.openai_utils import chat_gpt
from config.log_config import setup_logger
from generate_post.prompt_builder import build_user_prompt

logger = setup_logger(__name__)


def main(json_path: str) -> None:
    with open(json_path, 'r', encoding='utf-8') as fh:
        info = json.load(fh)
    user_prompt = build_user_prompt(info)
    response = chat_gpt(user_prompt)
    if response:
        logger.info(response)
    else:
        logger.error("Une erreur est survenue lors de l'appel à l'API OpenAI. Consulte le fichier de log.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_event_post.py info.json")
        sys.exit(1)
    main(sys.argv[1])
