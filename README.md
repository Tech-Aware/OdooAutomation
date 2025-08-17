# OdooAutomation

Ce dépôt contient des scripts d'automatisation autour d'Odoo. On y génère des publications à l'aide d'OpenAI puis on peut les planifier directement dans Odoo.

## Structure du projet

- **config/** : connexion à Odoo, authentification, utilitaires OpenAI et configuration du logger.
- **generate_post/** : scripts de génération de posts (Facebook, LinkedIn, X) basés sur ChatGPT. Les prompts sont stockés dans `prompts/`.
- **schedule_post_in_odoo/** : script pour planifier une publication dans Odoo (exemple pour Facebook).
- **pos_product_interaction/** : exemples de manipulation de produits du point de vente (duplication).
- **pos_category_management/** : activation ou désactivation automatique des catégories du point de vente selon le jour.
- **tests/** : quelques tests unitaires couvrant la configuration et l'intégration.

## Dépendances

Le projet s'appuie sur les bibliothèques suivantes (voir `requirements.txt`) :

```
python-dotenv
openai
```

Installez-les avec :

```bash
pip install -r requirements.txt
```

## Configuration `.env`

Créez un fichier `.env` à la racine contenant :

```dotenv
OPENAI_API_KEY=<votre clef API OpenAI>
ODOO_URL=<url de votre instance Odoo>
ODOO_DB=<base de données>
ODOO_USER=<utilisateur>
ODOO_PASSWORD=<mot de passe>
```

Ces variables permettent de se connecter à Odoo et à l'API OpenAI.

## Utilisation principale

- Générer un post : exécuter un des scripts de `generate_post/`.
  ```bash
  python generate_post/generate_facebook_post.py
  ```
- Planifier un post dans Odoo :
  ```bash
  python schedule_post_in_odoo/schedule_facebook_post.py
  ```
- Mettre à jour automatiquement les catégories POS selon le jour :
  ```bash
  python pos_category_management/manage_pos_categories.py
  ```

## Exécution des tests

Les tests utilisent `unittest` et se lancent avec :

```bash
python -m unittest discover -s tests -v
```

Plusieurs tests nécessitent une connexion réseau (serveur Odoo ou API OpenAI). En environnement hors-ligne, exécutez uniquement les tests locaux par exemple :

```bash
python -m unittest tests/test_log_config.py
```
