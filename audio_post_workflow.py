"""Workflow de publication basé sur un message reçu via Telegram.

Le script invite l'utilisateur à envoyer un message vocal ou texte et construit
un post à partir du contenu obtenu. Les interactions utilisateurs sont
désormais réalisées via un véritable bot Telegram.

"""

from services.openai_service import OpenAIService
from datetime import datetime, timedelta
from services.telegram_service import TelegramService
from services.facebook_service import FacebookService
from config.log_config import setup_logger, log_execution


@log_execution
def main() -> None:
    logger = setup_logger(__name__)

    openai_service = OpenAIService(logger)
    telegram_service = TelegramService(logger, openai_service)
    telegram_service.start()
    try:
        facebook_service = FacebookService(logger)
    except RuntimeError as err:
        logger.exception(f"Initialisation du service Facebook échouée : {err}")
        telegram_service.send_message(str(err))
        return

    telegram_service.send_message("Il est temps de publier Kevin")

    while True:
        text = telegram_service.wait_for_message()
        if not text:
            break

        try:
            last_post = openai_service.generate_event_post(text)
            selected_image_paths: list[str] = []

            while True:
                action = telegram_service.send_message_with_buttons(
                    last_post,
                    ["Modifier", "Illustrer", "Publier", "Programmer", "Terminer"],
                )

                if action == "Modifier":
                    corrections = telegram_service.ask_text(
                        "Partagez vos modifications s'il vous plaît !"
                    )
                    last_post = openai_service.apply_corrections(
                        last_post, corrections
                    )
                    continue

                if action == "Illustrer":
                    choice = telegram_service.send_message_with_buttons(
                        "Comment souhaitez-vous illustrer ?",
                        ["Générer", "Joindre", "Retour"],
                    )
                    if choice == "Générer":
                        styles = [
                            "Réaliste",
                            "Dessin animé",
                            "Pixel art",
                            "Manga",
                            "Aquarelle",
                            "Croquis",
                            "Peinture à l'huile",
                            "Low poly",
                            "Cyberpunk",
                            "Art déco",
                            "Noir et blanc",
                            "Fantaisie",
                        ]
                        style = telegram_service.ask_options(
                            "Choisissez un style d'illustration", styles
                        )
                        illustrations = openai_service.generate_illustrations(
                            last_post, style
                        )
                        if illustrations:
                            chosen_image = telegram_service.ask_image(
                                "Choisissez une illustration", illustrations
                            )
                            if chosen_image:
                                chosen_image.seek(0)
                                path = f"generated_image_{len(selected_image_paths)}.png"
                                with open(path, "wb") as fh:
                                    fh.write(chosen_image.getvalue())
                                selected_image_paths = [path]
                        continue
                    if choice == "Joindre":
                        images = telegram_service.ask_user_images()
                        start = len(selected_image_paths)
                        for idx, img in enumerate(images):
                            img.seek(0)
                            path = f"user_image_{start + idx}.png"
                            with open(path, "wb") as fh:
                                fh.write(img.getvalue())
                            selected_image_paths.append(path)
                        continue
                    if choice == "Retour":
                        continue

                if action == "Publier":
                    facebook_service.post_to_facebook_page(
                        last_post, selected_image_paths or None
                    )
                    groups = telegram_service.ask_groups()
                    if groups:
                        facebook_service.cross_post_to_groups(
                            last_post, groups, selected_image_paths or None
                        )
                    logger.info("Post généré avec succès.")
                    final_action = telegram_service.send_message_with_buttons(
                        "Publication effectuée.", ["Recommencer", "Terminer"]
                    )
                    if final_action == "Recommencer":
                        break
                    if final_action == "Terminer":
                        telegram_service.send_message("Fin du processus.")
                        return

                if action == "Programmer":
                    now = datetime.utcnow()
                    target = now.replace(hour=20, minute=0, second=0, microsecond=0)
                    if now >= target:
                        target = (now + timedelta(days=1)).replace(
                            hour=8, minute=0, second=0, microsecond=0
                        )
                    facebook_service.schedule_post_to_facebook_page(
                        last_post, target, selected_image_paths or None
                    )
                    logger.info("Publication programmée avec succès.")
                    final_action = telegram_service.send_message_with_buttons(
                        "Publication planifiée.", ["Recommencer", "Terminer"]
                    )
                    if final_action == "Recommencer":
                        break
                    if final_action == "Terminer":
                        telegram_service.send_message("Fin du processus.")
                        return

                if action == "Terminer":
                    telegram_service.send_message("Fin du processus.")
                    return
        except Exception as err:  # pragma: no cover - log then continue
            logger.exception(f"Erreur lors du traitement : {err}")


if __name__ == "__main__":
    main()
