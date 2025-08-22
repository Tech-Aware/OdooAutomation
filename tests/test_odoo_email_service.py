import logging
from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from services.odoo_email_service import OdooEmailService


def test_schedule_email_calls_odoo(monkeypatch):
    mock_models = MagicMock()
    mock_models.execute_kw.side_effect = [[99], 42, 1, True]

    def fake_connect():
        return ("db", 1, "pwd", mock_models)

    monkeypatch.setattr(
        "services.odoo_email_service.get_odoo_connection", fake_connect
    )
    monkeypatch.setattr(
        "services.odoo_email_service.ODOO_EMAIL_FROM", "sender@example.com"
    )

    service = OdooEmailService(logging.getLogger("test"))
    dt = datetime(2024, 5, 29, 8, 0, tzinfo=ZoneInfo("Europe/Paris"))
    mailing_id = service.schedule_email("Sujet", "Corps", ["http://ex"], dt, [7])

    assert mailing_id == 1
    expected_body = (
        "<p>Corps</p><br><a href=\"http://ex\">http://ex</a>"
    )
    mock_models.execute_kw.assert_any_call(
        "db",
        1,
        "pwd",
        "link.tracker",
        "create",
        [{"url": "http://ex"}],
    )
    mock_models.execute_kw.assert_any_call(
        "db",
        1,
        "pwd",
        "mailing.mailing",
        "create",
        [
            {
                "subject": "Sujet",
                "body_html": expected_body,
                "mailing_type": "mail",
                "schedule_type": "scheduled",
                "email_from": "sender@example.com",
                "schedule_date": "2024-05-29 06:00:00",
                "mailing_model_id": 99,
                "contact_list_ids": [(6, 0, [7])],
                "links_ids": [(6, 0, [42])],
            }
        ],
    )
    mock_models.execute_kw.assert_any_call(
        "db",
        1,
        "pwd",
        "mailing.mailing",
        "action_schedule",
        [[1]],
    )


def test_schedule_email_uses_default_list(monkeypatch):
    mock_models = MagicMock()
    mock_models.execute_kw.side_effect = [[99], 1, True]

    def fake_connect():
        return ("db", 1, "pwd", mock_models)

    monkeypatch.setattr(
        "services.odoo_email_service.get_odoo_connection", fake_connect
    )
    monkeypatch.setattr(
        "services.odoo_email_service.ODOO_EMAIL_FROM", "sender@example.com"
    )

    service = OdooEmailService(logging.getLogger("test"))
    dt = datetime(2024, 5, 29, 8, 0, tzinfo=ZoneInfo("Europe/Paris"))
    mailing_id = service.schedule_email("Sujet", "Corps", [], dt)

    assert mailing_id == 1
    mock_models.execute_kw.assert_any_call(
        "db",
        1,
        "pwd",
        "mailing.mailing",
        "create",
        [
            {
                "subject": "Sujet",
                "body_html": "<p>Corps</p>",
                "mailing_type": "mail",
                "schedule_type": "scheduled",
                "email_from": "sender@example.com",
                "schedule_date": "2024-05-29 06:00:00",
                "mailing_model_id": 99,
                "contact_list_ids": [(6, 0, [2])],
            }
        ],
    )
    mock_models.execute_kw.assert_any_call(
        "db",
        1,
        "pwd",
        "mailing.mailing",
        "action_schedule",
        [[1]],
    )
