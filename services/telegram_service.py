from typing import List, Optional


class TelegramService:
    """Service simulant l'interaction via Telegram."""

    def __init__(self, logger, openai_service: Optional["OpenAIService"] = None) -> None:
        self.logger = logger
        self.openai_service = openai_service

    def send_message(self, text: str) -> None:
        """Envoie un message textuel à l'utilisateur (simulation)."""
        self.logger.info(f"Message envoyé : {text}")
        print(text)

    def wait_for_voice_message(self) -> str:
        """Attend un message vocal et retourne sa transcription.

        L'utilisateur est invité à saisir la transcription attendue. Une
        chaîne vide met fin à l'attente.
        """
        self.logger.info("En attente d'un message vocal…")
        audio_sim = input("Message vocal (laisser vide pour arrêter) : ").strip()
        if not audio_sim:
            return ""
        if self.openai_service:
            return self.openai_service.transcribe_audio(audio_sim.encode("utf-8"))
        return audio_sim

    def ask_options(self, prompt: str, options: List[str]) -> str:
        """Demande à l'utilisateur de choisir parmi plusieurs options."""
        self.logger.info(prompt)
        for idx, opt in enumerate(options, 1):
            print(f"{idx}. {opt}")
        try:
            choice = int(input("Choix : ")) - 1
            return options[choice]
        except Exception:  # pragma: no cover - comportement interactif
            self.logger.error("Choix invalide, première option retenue par défaut.")
            return options[0]

    def ask_yes_no(self, prompt: str) -> bool:
        """Retourne True si l'utilisateur répond oui."""
        answer = input(f"{prompt} (o/n) : ").strip().lower()
        return answer in {"o", "oui", "y", "yes"}

    def ask_groups(self) -> List[str]:
        """Demande la liste des groupes Facebook."""
        groups = input("Groupes Facebook (séparés par des virgules) : ")
        if groups.strip():
            return [g.strip() for g in groups.split(",")]
        return []
