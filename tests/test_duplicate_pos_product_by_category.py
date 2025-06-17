import unittest
from config.odoo_connect import get_odoo_connection
from pos_product_interaction.duplication.duplicate_pos_product_by_category import (
    get_pos_categories,
    duplicate_pos_products_in_categories,
    create_pos_category,
    extract_variant_key
)

class TestDuplicatePosProductByCategory(unittest.TestCase):

    def test_duplicate_by_category_with_new_category(self):
        """
        Teste la duplication de produits POS en changeant de catégorie, avec création de catégorie.
        """
        db, uid, password, models = get_odoo_connection()
        categories = get_pos_categories(db, uid, password, models)
        self.assertTrue(categories, "Aucune catégorie POS trouvée, test impossible.")

        # Prendre une catégorie POS existante qui a des produits
        category_id = None
        cat_found = None
        for cat in categories:
            product_ids = models.execute_kw(
                db, uid, password,
                'product.template', 'search',
                [[
                    ['available_in_pos', '=', True],
                    ['pos_categ_ids', 'in', [cat['id']]]
                ]]
            )
            if product_ids:
                category_id = cat['id']
                cat_found = cat
                break

        self.assertIsNotNone(category_id, "Aucune catégorie POS contenant au moins un produit POS trouvée.")

        # Créer une nouvelle catégorie POS
        new_cat_name = "Test Catégorie POS"
        new_cat_id = create_pos_category(db, uid, password, models, new_cat_name, parent_id=category_id)
        self.assertIsInstance(new_cat_id, int)
        print(f"Catégorie POS de test créée : {new_cat_id} ({new_cat_name})")

        suffix = "Copy Test"
        pos_category_change = {'new_cat_id': new_cat_id, 'created': True, 'parent_id': category_id}

        duplicated = duplicate_pos_products_in_categories([category_id], suffix, pos_category_change)
        if duplicated:
            for prod_id, name in duplicated:
                print(f"Produit dupliqué (test) : ID={prod_id}, Nom='{name}'")
                # Vérifie la catégorie dupliquée
                prod_data = models.execute_kw(
                    db, uid, password,
                    'product.template', 'read', [prod_id], {'fields': ['pos_categ_ids']}
                )[0]
                self.assertIn(new_cat_id, prod_data['pos_categ_ids'], "La catégorie POS dupliquée n'est pas correcte !")
        else:
            print("Aucun produit dupliqué lors du test (peut-être aucun produit dans cette catégorie).")

if __name__ == "__main__":
    unittest.main()
