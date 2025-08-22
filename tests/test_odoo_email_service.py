import logging
from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo
import xmlrpc.client

from services.odoo_email_service import OdooEmailService


def test_format_body_returns_fragment(monkeypatch):
    mock_models = MagicMock()

    def fake_connect():
        return ("db", 1, "pwd", mock_models)

    monkeypatch.setattr(
        "services.odoo_email_service.get_odoo_connection", fake_connect
    )
    monkeypatch.setattr(
        "services.odoo_email_service.ODOO_EMAIL_FROM", "sender@example.com"
    )

    service = OdooEmailService(logging.getLogger("test"))
    html = service._format_body("Corps", ["http://ex"])

    assert "<!DOCTYPE" not in html
    assert "<html" not in html.lower()
    assert html.startswith("<div")


def test_schedule_email_calls_odoo(monkeypatch):
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
    mailing_id = service.schedule_email("Sujet", "Corps", ["http://ex"], dt, [7])

    assert mailing_id == 1
    expected_body = service._format_body("Corps", ["http://ex"])
    mock_models.execute_kw.assert_any_call(
        "db",
        1,
        "pwd",
        "mailing.mailing",
        "create",
        [
            {
                "name": "Sujet",
                "subject": "Sujet",
                "body_arch": expected_body,
                "body_html": expected_body,
                "body_plaintext": "Corps",
                "mailing_type": "mail",
                "schedule_type": "scheduled",
                "email_from": "sender@example.com",
                "schedule_date": "2024-05-29 06:00:00",
                "mailing_model_id": 99,
                "contact_list_ids": [(6, 0, [7])],
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


def test_schedule_email_accepts_html(monkeypatch):
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
    html = "<html><body><p>Corps</p></body></html>"
    service._format_body = MagicMock(side_effect=AssertionError("should not be called"))

    mailing_id = service.schedule_email("Sujet", html, [], dt, already_html=True)

    assert mailing_id == 1
    mock_models.execute_kw.assert_any_call(
        "db",
        1,
        "pwd",
        "mailing.mailing",
        "create",
        [
            {
                "name": "Sujet",
                "subject": "Sujet",
                "body_arch": html,
                "body_html": html,
                "body_plaintext": html,
                "mailing_type": "mail",
                "schedule_type": "scheduled",
                "email_from": "sender@example.com",
                "schedule_date": "2024-05-29 06:00:00",
                "mailing_model_id": 99,
                "contact_list_ids": [(6, 0, [2])],
            }
        ],
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
    expected_body = service._format_body("Corps", [])
    mock_models.execute_kw.assert_any_call(
        "db",
        1,
        "pwd",
        "mailing.mailing",
        "create",
        [
            {
                "name": "Sujet",
                "subject": "Sujet",
                "body_arch": expected_body,
                "body_html": expected_body,
                "body_plaintext": "Corps",
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


def test_schedule_email_handles_none_fault(monkeypatch):
    mock_models = MagicMock()
    fault = xmlrpc.client.Fault(
        1, "TypeError: cannot marshal None unless allow_none is enabled"
    )
    mock_models.execute_kw.side_effect = [[99], 1, fault]

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
