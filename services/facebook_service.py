from typing import List, Optional


class FacebookService:
    """Service simulant la publication sur Facebook."""

    def __init__(self, logger) -> None:
        self.logger = logger

    def post_to_facebook_page(self, message: str, image: Optional[str] = None) -> None:
        """Planifie un post sur la page Facebook principale."""
        self.logger.info(
            f"Publication planifiée sur la page : {message} (image={image})"
        )

    def cross_post_to_groups(
        self, message: str, groups: List[str], image: Optional[str] = None
    ) -> None:
        """Diffuse le message dans les groupes donnés."""
        for group in groups:
            self.logger.info(
                f"Publication envoyée au groupe {group} : {message} (image={image})"
            )
