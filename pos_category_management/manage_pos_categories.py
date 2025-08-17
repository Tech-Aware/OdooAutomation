from datetime import datetime
from typing import Iterable, Tuple

from config.odoo_connect import get_odoo_connection
from config.log_config import setup_logger

logger = setup_logger()

FRIDAY_CATEGORIES = ["BUVETTE", "EPICERIE"]
SUNDAY_CATEGORY = "FOURNIL"


def _search_category(models, db, uid, password, name):
    return models.execute_kw(db, uid, password, 'pos.category', 'search', [[('name', '=', name)]])


def _ensure_category_active(models, db, uid, password, name):
    ids = _search_category(models, db, uid, password, name)
    if ids:
        models.execute_kw(db, uid, password, 'pos.category', 'write', [ids, {'active': True}])
        return ids[0]
    return models.execute_kw(db, uid, password, 'pos.category', 'create', [{'name': name}])


def _deactivate_category(models, db, uid, password, name):
    ids = _search_category(models, db, uid, password, name)
    if ids:
        models.execute_kw(db, uid, password, 'pos.category', 'write', [ids, {'active': False}])


def compute_category_actions(current_dt: datetime) -> Tuple[Iterable[str], Iterable[str]]:
    """Return categories to activate and deactivate for given datetime."""
    weekday = current_dt.weekday()
    hour = current_dt.hour

    if weekday == 4 and hour >= 18:  # Friday evening
        return FRIDAY_CATEGORIES, [SUNDAY_CATEGORY]
    if weekday == 6:  # Sunday
        return [SUNDAY_CATEGORY], FRIDAY_CATEGORIES
    return [], FRIDAY_CATEGORIES + [SUNDAY_CATEGORY]


def update_pos_categories(current_dt: datetime | None = None):
    """Update POS categories according to the current day and time."""
    if current_dt is None:
        current_dt = datetime.now()

    to_activate, to_deactivate = compute_category_actions(current_dt)

    db, uid, password, models = get_odoo_connection()

    for name in to_activate:
        try:
            _ensure_category_active(models, db, uid, password, name)
            logger.info("Catégorie POS activée : %s", name)
        except Exception as err:
            logger.error("Erreur lors de l'activation de la catégorie %s : %s", name, err)

    for name in to_deactivate:
        try:
            _deactivate_category(models, db, uid, password, name)
            logger.info("Catégorie POS désactivée : %s", name)
        except Exception as err:
            logger.error("Erreur lors de la désactivation de la catégorie %s : %s", name, err)


if __name__ == "__main__":
    update_pos_categories()
