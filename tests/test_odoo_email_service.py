import logging
from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from services.odoo_email_service import OdooEmailService


def test_schedule_email_calls_odoo(monkeypatch):
    mock_models = MagicMock()
    mock_models.execute_kw.side_effect = [1, True]

    def fake_connect():
        return ("db", 1, "pwd", mock_models)

    monkeypatch.setattr(
        "services.odoo_email_service.get_odoo_connection", fake_connect
    )

    service = OdooEmailService(logging.getLogger("test"))
    dt = datetime(2024, 5, 29, 8, 0, tzinfo=ZoneInfo("Europe/Paris"))
    mailing_id = service.schedule_email("Sujet", "Corps", ["http://ex"], dt)

    assert mailing_id == 1
    expected_body = (
        "<p>Corps</p><br><a href=\"http://ex\">http://ex</a>"
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
                "schedule_date": "2024-05-29 06:00:00",
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
