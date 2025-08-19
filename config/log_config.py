# config/log_config.py

import logging
import os
import sys
import inspect
import asyncio
from functools import wraps


def setup_logger(name: str = "odoo_automation"):
    """
    Initialise et configure un logger qui écrit les messages dans un fichier log (UTF-8)
    et les affiche aussi dans la console (UTF-8 si supporté).
    Le logger permet de tracer tout ce qui se passe dans le script.
    En cas d'erreur lors de la configuration, une exception est levée.

    Parameters
    ----------
    name: str
        Nom du logger à initialiser, généralement ``__name__``.
    """
    try:
        log_file = "odoo_automation.log"  # Nom du fichier log

        # Si besoin, créer un dossier "logs" dédié (décommenter ces lignes)
        # logs_dir = "logs"
        # os.makedirs(logs_dir, exist_ok=True)
        # log_file = os.path.join(logs_dir, "odoo_automation.log")

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # Capture tout (DEBUG et au-dessus)

        # Pour éviter plusieurs handlers si la fonction est appelée plusieurs fois
        if not logger.handlers:
            try:
                # Handler fichier UTF-8
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)

                # Handler console (UTF-8 si supporté)
                stream_handler = logging.StreamHandler(stream=sys.stdout)
                stream_handler.setLevel(logging.INFO)

                formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d %(funcName)s - %(message)s'
                )
                file_handler.setFormatter(formatter)
                stream_handler.setFormatter(formatter)

                logger.addHandler(file_handler)
                logger.addHandler(stream_handler)

            except Exception as handler_error:
                sys.stderr.write(f"Erreur lors de la création des handlers de log : {handler_error}\n")
                raise

        return logger

    except Exception as e:
        sys.stderr.write(f"Impossible d'initialiser le logger : {e}\n")
        raise


def log_execution(func):
    """Decorator logging function entry and exit with location information."""

    async def _log_async(*args, **kwargs):
        logger = logging.getLogger("odoo_automation")
        cls_name = None
        if args:
            obj = args[0]
            if hasattr(obj, func.__name__):
                cls_name = obj.__class__.__name__
        source_file = inspect.getsourcefile(func) or "<unknown>"
        line_no = inspect.getsourcelines(func)[1]
        name = f"{cls_name + '.' if cls_name else ''}{func.__name__}"
        logger.info(f"Starting {name} ({source_file}:{line_no})")
        try:
            return await func(*args, **kwargs)
        finally:
            logger.info(f"Completed {name} ({source_file}:{line_no})")

    def _log_sync(*args, **kwargs):
        logger = logging.getLogger("odoo_automation")
        cls_name = None
        if args:
            obj = args[0]
            if hasattr(obj, func.__name__):
                cls_name = obj.__class__.__name__
        source_file = inspect.getsourcefile(func) or "<unknown>"
        line_no = inspect.getsourcelines(func)[1]
        name = f"{cls_name + '.' if cls_name else ''}{func.__name__}"
        logger.info(f"Starting {name} ({source_file}:{line_no})")
        try:
            return func(*args, **kwargs)
        finally:
            logger.info(f"Completed {name} ({source_file}:{line_no})")

    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await _log_async(*args, **kwargs)

        return wrapper

    @wraps(func)
    def wrapper(*args, **kwargs):
        return _log_sync(*args, **kwargs)

    return wrapper

