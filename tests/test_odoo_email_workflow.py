import odoo_email_workflow
from odoo_email_workflow import main as workflow_main


class DummyLogger:
    def info(self, msg):
        pass

    def exception(self, msg):
        pass


class DummyOpenAIService:
    def __init__(self, logger):
        pass

    def generate_marketing_email(self, text):
        return "Sujet", "Corps"

    def apply_corrections(self, html, corrections):
        return html


class DummyTelegramService:
    instance = None

    def __init__(self, logger, openai_service):
        self.logger = logger
        self.openai_service = openai_service
        self.messages = ["contenu", "/publier", "/terminer"]
        self.index = 0
        self.buttons_calls = []
        self.sent_messages = []
        DummyTelegramService.instance = self

    def start(self):
        pass

    def send_message(self, msg):
        self.sent_messages.append(msg)

    def wait_for_message(self):
        msg = self.messages[self.index]
        self.index += 1
        return msg

    def send_message_with_buttons(self, text, options):
        self.buttons_calls.append(options)
        msg = self.wait_for_message()
        cmd = msg.lstrip("/").lower()
        for opt in options:
            if opt.lower().startswith(cmd):
                return opt
        return options[0]

    def ask_text(self, prompt):
        return ""


class DummyOdooEmailService:
    def __init__(self, logger):
        self.scheduled = False

    def _replace_link_placeholders(self, html, links):
        return html, []

    def schedule_email(self, subject, body, links, dt, list_ids, already_html=True):
        self.scheduled = True
        return 1


def test_final_options(monkeypatch):
    monkeypatch.setattr(
        "odoo_email_workflow.setup_logger", lambda name: DummyLogger()
    )
    monkeypatch.setattr(
        "odoo_email_workflow.OpenAIService", DummyOpenAIService
    )
    monkeypatch.setattr(
        "odoo_email_workflow.TelegramService", DummyTelegramService
    )
    monkeypatch.setattr(
        "odoo_email_workflow.OdooEmailService", DummyOdooEmailService
    )
    monkeypatch.setattr("odoo_email_workflow.ODOO_MAILING_LIST_IDS", [1])

    workflow_main()

    tg = DummyTelegramService.instance
    assert ["Recommencer", "Terminer"] in tg.buttons_calls
    assert "Fin du workflow email." in tg.sent_messages
