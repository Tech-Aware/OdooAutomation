from config.odoo_connect import get_odoo_connection
from config.log_config import setup_logger

def extract_variant_key(display_name):
    """
    Extrait la clé variante (ex: 'Blonde') depuis le display_name du produit.
    Prend toujours la DERNIÈRE parenthèse !
    Ex : 'Sirop (villageois) (Fraise)' -> 'Fraise'
    """
    import re
    match = re.search(r'\(([^()]*)\)\s*$', display_name)
    if match:
        return match.group(1).strip()
    return display_name.strip()

def get_pos_categories(db, uid, password, models):
    """
    Récupère toutes les catégories utilisées dans le POS.
    """
    category_ids = models.execute_kw(
        db, uid, password,
        'pos.category', 'search', [[]]
    )
    categories = models.execute_kw(
        db, uid, password,
        'pos.category', 'read', [category_ids], {'fields': ['id', 'name', 'parent_id']}
    )
    return categories

def create_pos_category(db, uid, password, models, name, parent_id=None):
    """
    Crée une nouvelle catégorie POS, éventuellement avec un parent.
    """
    cat_vals = {'name': name}
    if parent_id:
        cat_vals['parent_id'] = parent_id
    new_id = models.execute_kw(
        db, uid, password,
        'pos.category', 'create',
        [cat_vals]
    )
    return new_id

def duplicate_pos_products_in_categories(category_ids, suffix, pos_category_change=None):
    """
    Duplique tous les produits POS des catégories sélectionnées, ajoute le suffixe.
    Si pos_category_change est spécifié, modifie la catégorie PDV du dupliqué.
    Après duplication, seules les variantes actives du produit d'origine (même clé de variante) sont gardées.
    """
    logger = setup_logger()
    logger.info(f"Début de la duplication des produits POS pour les catégories {category_ids} avec suffixe '{suffix}'.")

    try:
        db, uid, password, models = get_odoo_connection()
    except Exception as e:
        logger.error(f"Échec de connexion à Odoo : {e}")
        return []

    try:
        # Récupérer les produits POS des catégories sélectionnées
        product_ids = models.execute_kw(
            db, uid, password,
            'product.template', 'search',
            [[
                ['available_in_pos', '=', True],
                ['pos_categ_ids', 'in', category_ids]
            ]]
        )
        if not product_ids:
            logger.warning("Aucun produit POS trouvé dans les catégories sélectionnées.")
            return []

        results = []
        for prod_id in product_ids:
            # Lire nom produit et catégories originelles
            prod_data = models.execute_kw(
                db, uid, password,
                'product.template', 'read', [prod_id], {'fields': ['name', 'pos_categ_ids']}
            )[0]
            new_name = prod_data['name'] + ' - ' + suffix

            copy_args = {'name': new_name, 'available_in_pos': True}

            # Gestion éventuelle de la nouvelle catégorie POS
            if pos_category_change:
                copy_args['pos_categ_ids'] = [(6, 0, [pos_category_change['new_cat_id']])]

            # Dupliquer le produit
            new_prod_id = models.execute_kw(
                db, uid, password,
                'product.template', 'copy',
                [prod_id, copy_args]
            )
            if isinstance(new_prod_id, list):
                if new_prod_id:
                    new_prod_id = new_prod_id[0]
                else:
                    new_prod_id = None

            logger.info(f"Produit POS '{prod_data['name']}' dupliqué sous '{new_name}' (ID {new_prod_id}).")

            # ---- Nettoyage des variantes dupliquées ----
            active_variants_src = models.execute_kw(
                db, uid, password,
                'product.product', 'search_read',
                [[['product_tmpl_id', '=', prod_id], ['active', '=', True]]],
                {'fields': ['display_name']}
            )
            active_keys = set(extract_variant_key(var['display_name']) for var in active_variants_src)

            variants_new = models.execute_kw(
                db, uid, password,
                'product.product', 'search_read',
                [[['product_tmpl_id', '=', new_prod_id]]],
                {'fields': ['id', 'display_name', 'active']}
            )
            to_archive = []
            for var in variants_new:
                if extract_variant_key(var['display_name']) not in active_keys:
                    to_archive.append(var['id'])

            if to_archive:
                models.execute_kw(
                    db, uid, password,
                    'product.product', 'write',
                    [to_archive, {'active': False}]
                )
                logger.info(f"Variantes non souhaitées archivées pour le produit {new_prod_id}: {to_archive}")

            results.append((new_prod_id, new_name))
        return results

    except Exception as e:
        logger.error(f"Erreur lors de la duplication des produits POS par catégorie : {e}")
        return []

if __name__ == "__main__":
    logger = setup_logger()
    try:
        db, uid, password, models = get_odoo_connection()
        categories = get_pos_categories(db, uid, password, models)
        print("Catégories POS disponibles :")
        for cat in categories:
            parent = f"(parent ID {cat['parent_id'][0]})" if cat.get('parent_id') else ""
            print(f"{cat['id']}: {cat['name']} {parent}")

        selected_ids = input(
            "\nIndique les IDs des catégories à dupliquer (séparés par des virgules) : "
        ).strip()
        if not selected_ids:
            print("Aucune catégorie sélectionnée. Arrêt.")
            exit()
        category_ids = [int(id_.strip()) for id_ in selected_ids.split(',') if id_.strip().isdigit()]
        if not category_ids:
            print("Sélection invalide. Arrêt.")
            exit()

        suffix = input("Quel suffixe veux-tu ajouter au nom des produits dupliqués ?\n> ").strip()
        if not suffix:
            print("Aucun suffixe fourni. Arrêt.")
            exit()

        # 1. Créer la nouvelle catégorie racine
        root_cat_name = input("Entrez le nom de la nouvelle catégorie POS racine (ex : 'NouveauBar') :\n> ").strip()
        if not root_cat_name:
            print("Nom de catégorie invalide. Arrêt.")
            exit()
        root_cat_id = create_pos_category(db, uid, password, models, root_cat_name)
        print(f"Catégorie POS racine créée : {root_cat_name} (ID {root_cat_id})")

        results = []
        for orig_cat_id in category_ids:
            # Récupérer la catégorie d'origine pour afficher le nom
            orig_cat = next((c for c in categories if c['id'] == orig_cat_id), None)
            if not orig_cat:
                print(f"Catégorie d'origine {orig_cat_id} introuvable, ignorée.")
                continue

            # 2. Créer la catégorie POS enfant
            child_cat_name = orig_cat['name']
            child_cat_id = create_pos_category(db, uid, password, models, child_cat_name, parent_id=root_cat_id)
            print(f"Catégorie enfant créée : {child_cat_name} (ID {child_cat_id}), parent : {root_cat_name} (ID {root_cat_id})")

            # 3. Dupliquer les produits de la catégorie d'origine, les placer dans la catégorie enfant
            pos_category_change = {'new_cat_id': child_cat_id, 'created': True, 'parent_id': root_cat_id}
            dupli = duplicate_pos_products_in_categories([orig_cat_id], suffix, pos_category_change)
            if dupli:
                results.extend(dupli)

        if results:
            print("\nProduits dupliqués :")
            for prod_id, name in results:
                print(f"ID : {prod_id}, Nom : '{name}'")
        else:
            print("Aucun produit dupliqué.")

    except Exception as e:
        logger.error(f"Erreur inattendue dans le script principal : {e}")
        print(f"Erreur inattendue : {e}")
