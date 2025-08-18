from datetime import datetime

from config.odoo_connect import get_odoo_connection
from config.log_config import setup_logger

logger = setup_logger()

# Category identifiers used for automatic activation/deactivation.
# These values come from the Odoo database and therefore are integers
# rather than category names.
FRIDAY_CATEGORY_IDS: tuple[int, ...] = (79, 72, 53)
SUNDAY_CATEGORY_IDS: tuple[int, ...] = FRIDAY_CATEGORY_IDS + (58,)


def _ensure_category_active(models, db, uid, password, category_id):
    """Ensure the given category is available in the POS."""
    try:
        models.execute_kw(
            db,
            uid,
            password,
            "pos.category",
            "write",
            [[category_id], {"available_in_pos": True}],
        )
    except Exception:
        # Fallback for older versions where categories are controlled
        # through the POS configuration record.
        config_ids = models.execute_kw(
            db, uid, password, "pos.config", "search", [[]], {"limit": 1}
        )
        if config_ids:
            models.execute_kw(
                db,
                uid,
                password,
                "pos.config",
                "write",
                [[config_ids[0]], {"iface_available_categ_ids": [(4, category_id)]}],
            )


def _deactivate_category(models, db, uid, password, category_id):
    """Make the given category unavailable in the POS."""
    try:
        models.execute_kw(
            db,
            uid,
            password,
            "pos.category",
            "write",
            [[category_id], {"available_in_pos": False}],
        )
    except Exception:
        config_ids = models.execute_kw(
            db, uid, password, "pos.config", "search", [[]], {"limit": 1}
        )
        if config_ids:
            models.execute_kw(
                db,
                uid,
                password,
                "pos.config",
                "write",
                [[config_ids[0]], {"iface_available_categ_ids": [(3, category_id)]}],
            )


def compute_category_actions(
    current_dt: datetime,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Return category IDs to activate and deactivate for given datetime."""
    weekday = current_dt.weekday()
    hour = current_dt.hour

    if weekday == 4 and hour >= 6:  # Friday from 6 AM
        # Activate Friday categories and deactivate the Sunday-only one.
        return FRIDAY_CATEGORY_IDS, (58,)
    if weekday == 6 and hour >= 6:  # Sunday from 6 AM
        return SUNDAY_CATEGORY_IDS, ()
    return (), SUNDAY_CATEGORY_IDS


def update_pos_categories(current_dt: datetime | None = None):
    """Update POS categories according to the current day and time."""
    if current_dt is None:
        current_dt = datetime.now()

    to_activate, to_deactivate = compute_category_actions(current_dt)

    db, uid, password, models = get_odoo_connection()

    for category_id in to_activate:
        try:
            _ensure_category_active(models, db, uid, password, category_id)
            logger.info("Catégorie POS activée : %s", category_id)
        except Exception as err:
            logger.error(
                "Erreur lors de l'activation de la catégorie %s : %s",
                category_id,
                err,
            )

    for category_id in to_deactivate:
        try:
            _deactivate_category(models, db, uid, password, category_id)
            logger.info("Catégorie POS désactivée : %s", category_id)
        except Exception as err:
            logger.error(
                "Erreur lors de la désactivation de la catégorie %s : %s",
                category_id,
                err,
            )


if __name__ == "__main__":
    update_pos_categories()
