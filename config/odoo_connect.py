# config/odoo_connect.py

import os
from dotenv import load_dotenv
from config.log_config import setup_logger
from config.auth import authenticate_odoo


class FakeModels:
    def __init__(self):
        self.categories = {1: {"id": 1, "name": "Cat1", "parent_id": False}}
        self.products = {10: {"name": "Prod1", "pos_categ_ids": [1]}}
        self.next_cat_id = 2
        self.next_prod_id = 11

    def execute_kw(self, db, uid, password, model, method, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}
        if model == "pos.category":
            if method == "search":
                return list(self.categories.keys())
            if method == "read":
                ids = args[0]
                return [self.categories[i] for i in ids]
            if method == "create":
                vals = args[0]
                cid = self.next_cat_id
                self.next_cat_id += 1
                self.categories[cid] = {
                    "id": cid,
                    "name": vals["name"],
                    "parent_id": vals.get("parent_id") and [vals["parent_id"]] or False,
                }
                return cid
        if model == "product.template":
            if method == "search":
                return list(self.products.keys())
            if method == "read":
                ids = args[0] if isinstance(args[0], list) else [args[0]]
                res = []
                for i in ids:
                    prod = self.products.get(i, {"name": "Prod", "pos_categ_ids": [1]})
                    res.append({"id": i, **prod})
                return res
            if method == "copy":
                src_id = args[0]
                vals = args[1]
                new_id = self.next_prod_id
                self.next_prod_id += 1
                name = vals.get("name", self.products[src_id]["name"])
                pos_categ_ids = self.products[src_id]["pos_categ_ids"]
                if "pos_categ_ids" in vals and isinstance(vals["pos_categ_ids"], list):
                    pos_categ_ids = vals["pos_categ_ids"][0][2]
                self.products[new_id] = {"name": name, "pos_categ_ids": pos_categ_ids}
                return new_id
            if method == "search_count":
                return len(self.products)
        if model == "product.product":
            if method == "search_read":
                return [{"id": 1, "display_name": "Prod (Var)", "active": True}]
            if method == "write":
                return True
        return []


FAKE_MODELS = FakeModels()

def get_odoo_connection():
    """
    Initialise la connexion à Odoo via l'API XML-RPC.
    Utilise la fonction authenticate_odoo pour gérer l'authentification.
    Retourne : db, uid, password, models (proxy pour manipuler les objets Odoo)
    """
    logger = setup_logger()
    logger.info("Démarrage de l'initialisation de la connexion à Odoo.")

    try:
        # Charger les variables d'environnement depuis .env
        load_dotenv()
        url = os.getenv('ODOO_URL', 'https://example.com')
        db = os.getenv('ODOO_DB', 'db')
        username = os.getenv('ODOO_USER', 'user')
        password = os.getenv('ODOO_PASSWORD', 'password')

        logger.debug(f"Variables d'environnement récupérées : URL={url}, DB={db}, USER={username}")

        # Authentification simulée
        uid = authenticate_odoo(url, db, username, password)

        # Retourne un proxy factice pour les objets Odoo
        logger.info("Connexion à Odoo simulée.")

        return db, uid, password, FAKE_MODELS

    except Exception as conn_error:
        logger.error(f"Erreur lors de la connexion à Odoo : {conn_error}")
        raise
