from typing import List


class TelegramService:
    """Service simulant l'interaction via Telegram."""

    def __init__(self, logger) -> None:
        self.logger = logger

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
