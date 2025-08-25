# config/log_config.py

import logging
import sys
import inspect
import asyncio
import os
from functools import wraps


class SensitiveDataFilter(logging.Filter):
    """Logging filter removing secrets from log records."""

    def __init__(self) -> None:
        super().__init__()
        secrets = [
            os.getenv("TELEGRAM_BOT_TOKEN", ""),
            os.getenv("OPENAI_API_KEY", ""),
            os.getenv("ODOO_PASSWORD", ""),
            os.getenv("PAGE_ACCESS_TOKEN", ""),
        ]
        self.secrets = [s for s in secrets if s]

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        message = record.getMessage()
        for secret in self.secrets:
            message = message.replace(secret, "[REDACTED]")
        record.msg = message
        record.args = ()
        return True


def setup_logger(name: str) -> logging.Logger:
    """Initialise un logger nommé et configure les handlers.

    Les messages sont écrits dans un fichier log (UTF-8) et affichés dans la
    console. Le format inclut le nom du module pour faciliter le suivi.

    """
    try:
        log_file = "odoo_automation.log"  # Nom du fichier log

        # Si besoin, créer un dossier "logs" dédié (décommenter ces lignes)
        # logs_dir = "logs"
        # os.makedirs(logs_dir, exist_ok=True)
        # log_file = os.path.join(logs_dir, "odoo_automation.log")

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        root_logger = logging.getLogger()
        if not root_logger.handlers:
            try:
                # Handler fichier UTF-8
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setLevel(logging.DEBUG)

                # Handler console (UTF-8 si supporté)
                stream_handler = logging.StreamHandler(stream=sys.stdout)
                stream_handler.setLevel(logging.INFO)

                formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d %(funcName)s - %(message)s'
                )
                file_handler.setFormatter(formatter)
                stream_handler.setFormatter(formatter)

                root_logger.setLevel(logging.DEBUG)
                root_logger.addHandler(file_handler)
                root_logger.addHandler(stream_handler)

            except Exception as handler_error:

                sys.stderr.write(f"Erreur lors de la création des handlers de log : {handler_error}\n")
                raise

        if not any(isinstance(f, SensitiveDataFilter) for f in root_logger.filters):
            root_logger.addFilter(SensitiveDataFilter())

        if not any(isinstance(f, SensitiveDataFilter) for f in logger.filters):
            logger.addFilter(SensitiveDataFilter())

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

