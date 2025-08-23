# OdooAutomation

Ce dépôt contient des scripts d'automatisation autour d'Odoo. On y génère des publications à l'aide d'OpenAI puis on peut les publier ou les planifier sur Facebook via l'API Graph.

## Structure du projet

- **config/** : connexion à Odoo, authentification, utilitaires OpenAI et configuration du logger.
- **generate_post/** : scripts de génération de posts (Facebook, LinkedIn) basés sur ChatGPT. Les prompts sont stockés dans `prompts/`.
- **pos_category_management/** : activation ou désactivation automatique des catégories du point de vente selon le jour (BUVETTE, EPICERIE, BUREAU le vendredi dès 6h ; BUVETTE, EPICERIE, BUREAU et FOURNIL le dimanche dès 6h).
- **tests/** : quelques tests unitaires couvrant la configuration et l'intégration.
- **services/** : couches d'abstraction pour OpenAI, Facebook, Odoo et Telegram.
- **facebook_post/** : accès plus bas niveau à l'API Graph pour publier et partager des posts existants.
- **audio_post_workflow.py** : workflow interactif via Telegram pour générer et publier un post Facebook à partir d'un message vocal ou texte.
- **odoo_email_workflow.py** : workflow interactif créant un email marketing et le programmant dans Odoo.

## Dépendances

Le projet s'appuie sur les bibliothèques suivantes (voir `requirements.txt`) :

```
python-dotenv
openai
python-telegram-bot
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
TELEGRAM_BOT_TOKEN=<token du bot Telegram>
TELEGRAM_USER_ID=<identifiant Telegram du destinataire>
FACEBOOK_PAGE_ID=<id de votre page Facebook>
PAGE_ACCESS_TOKEN=<token de la page Facebook>
```

Ces variables permettent de se connecter à Odoo, à l'API OpenAI, à Facebook et à Telegram pour l'envoi de notifications. `TELEGRAM_BOT_TOKEN` et `TELEGRAM_USER_ID` sont utilisés par `services/telegram_service.py` pour envoyer des messages, tandis que `FACEBOOK_PAGE_ID` et `PAGE_ACCESS_TOKEN` servent aux modules de publication Facebook.

## Services principaux

- **OpenAIService** (`services/openai_service.py`) : génération de posts ou d'emails, correction de texte, création d'illustrations et transcription audio via l'API OpenAI.
- **FacebookService** (`services/facebook_service.py`) : publication et planification de posts sur la page Facebook principale.
- **OdooEmailService** (`services/odoo_email_service.py`) : construction d'emails marketing enrichis de liens utiles et planification dans Odoo.
- **AudioService** (`services/audio_service.py`) : lecture de fichiers audio (simulés par des `.txt`) pour extraire du texte.
- **TelegramService** (`services/telegram_service.py`) : bot interactif capable de recevoir texte, voix, images et de proposer des boutons de choix.

## Utilisation principale

- Générer un post statique : exécuter un des scripts de `generate_post/`.
  ```bash
  python generate_post/generate_facebook_post.py
  python generate_post/generate_linkedin_post.py
  ```
- Lancer le workflow audio pour publier sur Facebook :
  ```bash
  python audio_post_workflow.py
  ```
  Le script récupère un message vocal ou texte via Telegram, génère un post avec OpenAI, propose d'ajouter des images puis publie ou planifie sur Facebook.
- Lancer le workflow de création d'email marketing :
  ```bash
  python odoo_email_workflow.py
  ```
  Il compose un email marketing, permet d'insérer des liens utiles et programme l'envoi dans Odoo.
- Mettre à jour manuellement les catégories POS selon le jour :
  ```bash
  python pos_category_management/update_categories.py
  ```
  Ce script active BUVETTE, EPICERIE et BUREAU le vendredi à partir de 6h, puis BUVETTE, EPICERIE, BUREAU et FOURNIL le dimanche à partir de 6h. Les autres jours, ces catégories sont désactivées.

  Chaque catégorie POS possède aussi un **ID Odoo** utile pour les tests ou les vérifications manuelles. Voici les correspondances actuelles :

  - BUVETTE : `79`
  - EPICERIE : `72`
  - BUREAU : `53`
  - FOURNIL : `58`

  Pour convertir les noms renvoyés par `compute_category_actions` en IDs :

  ```python
  from datetime import datetime
  from pos_category_management.manage_pos_categories import compute_category_actions

  CATEGORY_IDS = {"BUVETTE": 79, "EPICERIE": 72, "BUREAU": 53, "FOURNIL": 58}

  add, remove = compute_category_actions(datetime(2024, 9, 6, 7))  # Vendredi 07h
  add_ids = [CATEGORY_IDS[name] for name in add]
  # add_ids == [79, 72, 53]

  add, remove = compute_category_actions(datetime(2024, 9, 8, 10))  # Dimanche 10h
  add_ids = [CATEGORY_IDS[name] for name in add]
  # add_ids == [79, 72, 53, 58]
  ```

## Workflows interactifs via Telegram

Les workflows `audio_post_workflow.py` et `odoo_email_workflow.py` guident l'utilisateur pas à pas grâce au bot Telegram :

- **audio_post_workflow.py** : attend un message vocal ou texte, génère un post d'événement, propose des corrections, permet de joindre ou générer des images puis publie ou programme le contenu sur Facebook.
- **odoo_email_workflow.py** : compose un email marketing complet, suggère des liens utiles, autorise les corrections et planifie l'envoi dans Odoo à une date choisie.

## Service Telegram

Le fichier `services/telegram_service.py` fournit la classe `TelegramService` permettant de dialoguer avec un bot Telegram en mode polling.  
Pour l'utiliser :

```python
from services.telegram_service import TelegramService
from services.openai_service import OpenAIService
from config import logger

openai_service = OpenAIService(logger)
service = TelegramService(logger, openai_service)
service.start()
service.send_message("Bot prêt !")
```

`TelegramService` propose aussi des méthodes interactives comme `ask_text` (qui accepte une réponse texte ou vocale), `ask_options`, `ask_yes_no`, `wait_for_voice_message` ou `ask_image`, exploitées par des scripts tels que `audio_post_workflow.py`.

## Exécution des tests

Les tests utilisent `unittest` et se lancent avec :

```bash
python -m unittest discover -s tests -v
```

Plusieurs tests nécessitent une connexion réseau (serveur Odoo ou API OpenAI). En environnement hors-ligne, exécutez uniquement les tests locaux par exemple :

```bash
python -m unittest tests/test_log_config.py
```
