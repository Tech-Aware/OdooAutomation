"""Utilities to build user prompts for social media posts."""

from __future__ import annotations

import os
from typing import Dict

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "prompts", "event_template.txt")

_FIELDS = {
    "objet": "",
    "date": "",
    "horaires": "",
    "lieu": "",
    "programme": "",
    "restauration": "",
    "tarifs": "",
    "reservation": "",
    "deadline": "",
    "benevoles": "",
    "liens": "",
    "contexte": "",
}

def build_user_prompt(info: Dict[str, str]) -> str:
    """Return the user prompt filled with *info* fields.

    Missing fields are replaced by empty strings to avoid hallucinations.
    """
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    fields = _FIELDS.copy()
    for key, value in info.items():
        if key in fields and value is not None:
            fields[key] = value
    return template.format(**fields)
