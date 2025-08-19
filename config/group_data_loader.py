# config/group_data_loader.py

import json
import os
from .log_config import setup_logger

logger = setup_logger(__name__)

def load_group_data(file_name="group_data.json"):
    """
    Charge les données de groupe depuis un fichier JSON.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Données de groupe chargées depuis {file_path}.")
        return data
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données de groupe : {e}")
        return {}
