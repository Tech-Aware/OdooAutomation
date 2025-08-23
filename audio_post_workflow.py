"""Workflow de publication basé sur un message reçu via Telegram.

Le script invite l'utilisateur à envoyer un message vocal ou texte et construit
un post à partir du contenu obtenu. Les interactions utilisateurs sont
désormais réalisées via un véritable bot Telegram.
"""

from datetime import datetime, timedelta

from services.facebook_service import FacebookService
from services.openai_service import OpenAIService
from services.telegram_service import TelegramService
from config.log_config import setup_logger, log_execution


@log_execution
def run_workflow(
    logger,
    telegram_service: "TelegramService",
    openai_service: "OpenAIService",
    facebook_service: "FacebookService",
) -> None:
    """Exécute le workflow de publication avec des services déjà initialisés."""
    timeout = 300

    try:
        action = telegram_service.send_message_with_buttons(
            (
                "Bienvenue dans l'assistant de publication Facebook ! Il vous permet de :\n"
                "- Générer une publication optimisée pour Facebook grâce à l'IA à partir de votre propre contenu.\n"
                "- Apporter des modifications à la publication générée.\n"
                "- Illustrer la publication dans un style qui vous convient grâce à l'IA ou joindre vos propres photos.\n"
                "- Publier directement votre publication sur la page du comité ou la programmer (20h le soir si programmation avant 20h, sinon remis au lendemain matin 08h).\n"
                "- Revenir au menu principal à tout moment.\n\n"
                "Pour commencer, sélectionnez 'Continuer' puis fournissez votre contenu sous forme de texte ou d'audio."
            ),
            ["Continuer", "Retour"],
            timeout=timeout,
        )
    except TimeoutError:
        telegram_service.send_message("Inactivité prolongée, retour au menu principal.")
        return
    if action == "Retour":
        return

    try:
        text = telegram_service.ask_text(
            "Envoyez le sujet de la publication via un message audio ou un message texte !",
            timeout=timeout,
        )
        if not text:
            return

        last_post = openai_service.generate_event_post(text)
        selected_image_paths: list[str] = []

        while True:
            action = telegram_service.send_message_with_buttons(
                last_post,
                [
                    "Modifier",
                    "Illustrer",
                    "Publier",
                    "Programmer",
                    "Retour au menu principal",
                ],
                timeout=timeout,
            )

            if action == "Modifier":
                corrections = telegram_service.ask_text(
                    "Partagez vos modifications s'il vous plaît !",
                    timeout=timeout,
                )
                last_post = openai_service.apply_corrections(last_post, corrections)
                continue

            if action == "Illustrer":
                choice = telegram_service.send_message_with_buttons(
                    "Comment souhaitez-vous illustrer ?",
                    ["Générer", "Joindre", "Retour"],
                    timeout=timeout,
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
                        "Choisissez un style d'illustration", styles, timeout=timeout
                    )
                    illustrations = openai_service.generate_illustrations(
                        last_post, style
                    )
                    if illustrations:
                        chosen_image = telegram_service.ask_image(
                            "Choisissez une illustration",
                            illustrations,
                            timeout=timeout,
                        )
                        if chosen_image:
                            chosen_image.seek(0)
                            path = f"generated_image_{len(selected_image_paths)}.png"
                            with open(path, "wb") as fh:
                                fh.write(chosen_image.getvalue())
                            selected_image_paths = [path]
                    continue
                if choice == "Joindre":
                    images = telegram_service.ask_user_images(timeout=timeout)
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
                logger.info("Post généré avec succès.")
                final_action = telegram_service.send_message_with_buttons(
                    "Publication effectuée.",
                    ["Recommencer", "Retour au menu principal"],
                    timeout=timeout,
                )
                if final_action == "Recommencer":
                    return
                telegram_service.send_message("Retour au menu principal.")
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
                    "Publication planifiée.",
                    ["Recommencer", "Retour au menu principal"],
                    timeout=timeout,
                )
                if final_action == "Recommencer":
                    return
                telegram_service.send_message("Retour au menu principal.")
                return

            if action == "Retour au menu principal":
                telegram_service.send_message("Retour au menu principal.")
                return
    except TimeoutError:
        telegram_service.send_message("Inactivité prolongée, retour au menu principal.")
        return
    except Exception as err:  # pragma: no cover - log then continue
        logger.exception(f"Erreur lors du traitement : {err}")


@log_execution
def main() -> None:
    logger = setup_logger(__name__)

    openai_service = OpenAIService(logger)
    telegram_service = TelegramService(logger, openai_service)
    telegram_service.start()
    try:
        try:
            facebook_service = FacebookService(logger)
        except RuntimeError as err:
            logger.exception(f"Initialisation du service Facebook échouée : {err}")
            telegram_service.send_message(str(err))
            return

        run_workflow(logger, telegram_service, openai_service, facebook_service)
    except KeyboardInterrupt:
        logger.info("Arrêt manuel du programme")
    finally:
        telegram_service.stop()


if __name__ == "__main__":
    main()
