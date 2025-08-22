import logging
from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo
import xmlrpc.client

from services.odoo_email_service import OdooEmailService, DEFAULT_LINKS


def _setup_service(monkeypatch):
    mock_models = MagicMock()
    mock_models.execute_kw.return_value = [99]

    def fake_connect():
        return ("db", 1, "pwd", mock_models)

    monkeypatch.setattr("services.odoo_email_service.get_odoo_connection", fake_connect)
    monkeypatch.setattr("services.odoo_email_service.ODOO_EMAIL_FROM", "sender@example.com")
    service = OdooEmailService(logging.getLogger("test"))
    return service, mock_models


def test_format_body_includes_links_section(monkeypatch):
    service, _ = _setup_service(monkeypatch)
    html = service._format_body("Corps", [("Site", "http://ex")])
    assert "Liens utiles" in html
    assert '<a href="http://ex"' in html
    assert "/unsubscribe_from_list" in html


def test_schedule_email_calls_odoo(monkeypatch):
    service, mock_models = _setup_service(monkeypatch)
    mock_models.execute_kw.side_effect = [1, True]
    dt = datetime(2024, 5, 29, 8, 0, tzinfo=ZoneInfo("Europe/Paris"))
    mailing_id = service.schedule_email("Sujet", "Corps", [("Nom", "http://ex")], dt, [7])
    assert mailing_id == 1
    expected_body = service._format_body("Corps", [("Nom", "http://ex")] + DEFAULT_LINKS)
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


def test_schedule_email_accepts_html(monkeypatch):
    service, mock_models = _setup_service(monkeypatch)
    mock_models.execute_kw.side_effect = [1, True]
    dt = datetime(2024, 5, 29, 8, 0, tzinfo=ZoneInfo("Europe/Paris"))
    html = "<html><body><p>Corps</p></body></html>"
    links_html = service._build_links_section(DEFAULT_LINKS)
    expected_html = (
        "<html><body><p>Corps</p>"
        + links_html
        + '<p><a href="/unsubscribe_from_list" style="color:#1a0dab;">Se désabonner</a></p>'
        "</body></html>"
    )
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
                "body_arch": expected_html,
                "body_html": expected_html,
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


def test_schedule_email_inserts_links_into_html(monkeypatch):
    service, mock_models = _setup_service(monkeypatch)
    mock_models.execute_kw.side_effect = [1, True]
    dt = datetime(2024, 5, 29, 8, 0, tzinfo=ZoneInfo("Europe/Paris"))
    html = "<html><body><p>Corps</p></body></html>"
    mailing_id = service.schedule_email(
        "Sujet", html, [("Nom", "http://ex")], dt, already_html=True
    )
    assert mailing_id == 1
    links_html = service._build_links_section([("Nom", "http://ex")] + DEFAULT_LINKS)
    expected_html = (
        "<html><body><p>Corps</p>"
        + links_html
        + '<p><a href="/unsubscribe_from_list" style="color:#1a0dab;">Se désabonner</a></p>'
        "</body></html>"
    )
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
                "body_arch": expected_html,
                "body_html": expected_html,
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
    service, mock_models = _setup_service(monkeypatch)
    mock_models.execute_kw.side_effect = [1, True]
    dt = datetime(2024, 5, 29, 8, 0, tzinfo=ZoneInfo("Europe/Paris"))
    mailing_id = service.schedule_email("Sujet", "Corps", [], dt)
    assert mailing_id == 1
    expected_body = service._format_body("Corps", DEFAULT_LINKS)
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


def test_schedule_email_handles_none_fault(monkeypatch):
    service, mock_models = _setup_service(monkeypatch)
    fault = xmlrpc.client.Fault(
        1, "TypeError: cannot marshal None unless allow_none is enabled"
    )
    mock_models.execute_kw.side_effect = [1, fault]
    dt = datetime(2024, 5, 29, 8, 0, tzinfo=ZoneInfo("Europe/Paris"))
    mailing_id = service.schedule_email("Sujet", "Corps", [], dt)
    assert mailing_id == 1
