from config.odoo_connect import get_odoo_connection
from config.log_config import setup_logger

def duplicate_first_pos_product(suffix):
    """
    Duplique le premier produit disponible dans le POS avec ses caractéristiques standard.
    Le suffixe est obligatoire. Le nom devient 'NomOriginal-SUFFIXE'.
    Retourne l'ID (int) et le nom du produit dupliqué, ou None si erreur.
    """
    logger = setup_logger()
    logger.info(f"Début du processus de duplication d'un produit POS avec le suffixe '{suffix}'.")

    try:
        db, uid, password, models = get_odoo_connection()
    except Exception as e:
        logger.error(f"Échec de connexion à Odoo : {e}")
        return None

    try:
        # 1. Recherche du premier produit dispo POS
        product_ids = models.execute_kw(
            db, uid, password,
            'product.template', 'search',
            [[['available_in_pos', '=', True]]],
            {'limit': 1}
        )
        if not product_ids:
            logger.error("Aucun produit POS trouvé à dupliquer.")
            return None

        prod_id = product_ids[0]
        prod_data = models.execute_kw(
            db, uid, password,
            'product.template', 'read', [prod_id], {'fields': ['name']}
        )[0]
        new_name = prod_data['name'] + ' - ' + suffix

        # 2. Dupliquer le produit avec son nom modifié et disponible POS
        new_prod_id = models.execute_kw(
            db, uid, password,
            'product.template', 'copy',
            [prod_id, {'name': new_name, 'available_in_pos': True}]
        )
        if isinstance(new_prod_id, list):
            if new_prod_id:
                new_prod_id = new_prod_id[0]
            else:
                new_prod_id = None

        logger.info(f"Produit POS '{prod_data['name']}' dupliqué sous '{new_name}' (ID {new_prod_id}).")
        return new_prod_id, new_name

    except Exception as e:
        logger.error(f"Erreur lors de la duplication standard du produit POS : {e}")
        return None

if __name__ == "__main__":
    suffix = input("Quel suffixe veux-tu ajouter au nom du produit dupliqué ? (Exemple : Copie2024)\n> ").strip()
    if suffix == '':
        print("Aucun suffixe saisi. Annulation.")
    else:
        result = duplicate_first_pos_product(suffix)
        if result:
            print(f"Produit dupliqué avec succès : ID={result[0]}, Nom='{result[1]}'")
        else:
            print("La duplication standard a échoué.")
