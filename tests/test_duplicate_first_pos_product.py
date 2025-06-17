import unittest
from pos_product_interaction.duplication.duplicate_first_pos_product import duplicate_first_pos_product

class TestDuplicatePosProduct(unittest.TestCase):

    def test_duplicate_standard_pos_product(self):
        """
        Teste la duplication standard du premier produit POS disponible avec le suffixe 'Copy Test'.
        """
        suffix = "Copy Test"
        result = duplicate_first_pos_product(suffix)
        if result is not None:
            prod_id, prod_name = result
            print(f"Produit dupliqué (test) : ID={prod_id}, Nom='{prod_name}'")
            self.assertIsInstance(prod_id, int, "L'ID du produit dupliqué doit être un entier.")
            self.assertIsInstance(prod_name, str, "Le nom du produit dupliqué doit être une chaîne.")
            self.assertTrue(prod_name.endswith(" - " + suffix), f"Le nom du produit dupliqué doit finir par ' - {suffix}'.")
        else:
            print("Aucun produit POS n'a pu être dupliqué (voir log pour détail).")
            self.fail("La duplication du produit POS a échoué (aucun produit dupliqué).")

if __name__ == "__main__":
    unittest.main()
