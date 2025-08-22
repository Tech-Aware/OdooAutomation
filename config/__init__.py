"""Centralise the loading of environment-based configuration.

This module exposes all the configuration values required across the
application. Each setting is retrieved from the ``.env`` file (if present)
and documented here for clarity.
"""

import os
from dotenv import load_dotenv
from .group_data_loader import load_group_data
from config.log_config import setup_logger

# Load variables from the .env file once
load_dotenv()
logger = setup_logger(__name__)

# --- OpenAI configuration -----------------------------------------------------
# Used by ``openai_utils`` and ``services.openai_service`` to authenticate calls
# to the OpenAI API.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- Odoo configuration -------------------------------------------------------
# Connection parameters for the Odoo XML-RPC API.
ODOO_URL = os.getenv("ODOO_URL", "")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USER = os.getenv("ODOO_USER", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")
# Comma-separated list IDs of mailing lists targeted by default.
# Falls back to mailing list ID ``2`` when unspecified.
_list_ids = os.getenv("ODOO_MAILING_LIST_IDS", "2")
ODOO_MAILING_LIST_IDS = [
    int(_id.strip()) for _id in _list_ids.split(",") if _id.strip()
]

# --- Telegram configuration ---------------------------------------------------
# Used by ``telegram_service`` to send notifications to a specific user.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))

# --- Facebook configuration ---------------------------------------------------
# Required by the Facebook posting utilities to publish on a page.
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "")
