from datetime import datetime
from audio_post_workflow import main as workflow_main


class DummyLogger:
    def info(self, msg):
        pass

    def exception(self, msg):
        pass


class DummyOpenAIService:
    def __init__(self, logger):
        self.logger = logger

    def generate_post_versions(self, text):
        assert text == "transcribed"
        return ["version1"]

    def apply_corrections(self, choice, corrections):
        assert choice == "version1"
        assert corrections == "fix"
        return "fixed"

    def generate_illustrations(self, prompt):
        return []


class DummyTelegramService:
    def __init__(self, logger, openai_service):
        self.logger = logger
        self.openai_service = openai_service
        self._step = 0

    def start(self):
        pass

    def send_message(self, msg):
        pass

    def wait_for_voice_message(self):
        if self._step == 0:
            self._step += 1
            return "transcribed"
        return ""

    def ask_options(self, prompt, options):
        return options[0]

    def ask_yes_no(self, prompt):
        mapping = {
            "Faut-il corriger cette version ?": True,
            "Ajouter un lien ?": True,
            "Générer des illustrations ?": False,
            "Souhaitez-vous programmer la publication ?": False,
        }
        return mapping.get(prompt, False)

    def ask_text(self, prompt):
        return "fix" if "corrections" in prompt.lower() else "http://example.com"

    def ask_image(self, prompt, illustrations):
        return None

    def ask_groups(self):
        return []


class DummyFacebookService:
    def __init__(self, logger):
        self.logger = logger
        self.posted = None
        self.scheduled = None

    def post_to_facebook_page(self, text, image_path):
        self.posted = (text, image_path)

    def schedule_post_to_facebook_page(self, text, publish_time, image_path):
        self.scheduled = (text, publish_time, image_path)

    def cross_post_to_groups(self, text, groups, image_path):
        pass


def test_main_flow(monkeypatch):
    monkeypatch.setattr(
        "audio_post_workflow.setup_logger", lambda name: DummyLogger()
    )
    monkeypatch.setattr(
        "audio_post_workflow.OpenAIService", DummyOpenAIService
    )
    monkeypatch.setattr(
        "audio_post_workflow.TelegramService", DummyTelegramService
    )
    fb_service = DummyFacebookService(DummyLogger())
    monkeypatch.setattr(
        "audio_post_workflow.FacebookService", lambda logger: fb_service
    )

    workflow_main()

    assert fb_service.posted == ("fixed\nhttp://example.com", None)


class SchedulingDummyTelegramService(DummyTelegramService):
    def ask_yes_no(self, prompt):
        mapping = {
            "Faut-il corriger cette version ?": True,
            "Ajouter un lien ?": True,
            "Générer des illustrations ?": False,
            "Souhaitez-vous programmer la publication ?": True,
        }
        return mapping.get(prompt, False)


def test_scheduling_flow(monkeypatch):
    monkeypatch.setattr(
        "audio_post_workflow.setup_logger", lambda name: DummyLogger()
    )
    monkeypatch.setattr(
        "audio_post_workflow.OpenAIService", DummyOpenAIService
    )
    monkeypatch.setattr(
        "audio_post_workflow.TelegramService",
        SchedulingDummyTelegramService,
    )

    schedule_args = {}

    monkeypatch.setattr(
        "audio_post_workflow.get_odoo_connection",
        lambda: ("db", 1, "pwd", object()),
    )
    monkeypatch.setattr(
        "audio_post_workflow.get_facebook_stream_id",
        lambda models, db, uid, pwd: 99,
    )

    def fake_schedule(models, db, uid, pwd, stream_id, message, minutes_later):
        schedule_args["params"] = (
            models,
            db,
            uid,
            pwd,
            stream_id,
            message,
            minutes_later,
        )

    monkeypatch.setattr(
        "audio_post_workflow.schedule_post",
        fake_schedule,
    )

    fb_service = DummyFacebookService(DummyLogger())
    monkeypatch.setattr(
        "audio_post_workflow.FacebookService", lambda logger: fb_service
    )

    workflow_main()

    assert "params" in schedule_args
    assert schedule_args["params"][5] == "fixed\nhttp://example.com"
    assert isinstance(schedule_args["params"][6], int)
    assert fb_service.scheduled is None
    assert fb_service.posted is None


class NoStreamTelegramService(SchedulingDummyTelegramService):
    def __init__(self, logger, openai_service):
        super().__init__(logger, openai_service)
        self.messages = []

    def send_message(self, msg):
        self.messages.append(msg)


def test_scheduling_without_stream(monkeypatch):
    monkeypatch.setattr(
        "audio_post_workflow.setup_logger", lambda name: DummyLogger()
    )
    monkeypatch.setattr(
        "audio_post_workflow.OpenAIService", DummyOpenAIService
    )

    last_service = {}

    def create_service(logger, openai_service):
        service = NoStreamTelegramService(logger, openai_service)
        last_service["instance"] = service
        return service

    monkeypatch.setattr(
        "audio_post_workflow.TelegramService", create_service
    )

    monkeypatch.setattr(
        "audio_post_workflow.get_odoo_connection",
        lambda: ("db", 1, "pwd", object()),
    )
    monkeypatch.setattr(
        "audio_post_workflow.get_facebook_stream_id", lambda *args: None
    )

    scheduled = {"called": False}

    def fake_schedule(*args, **kwargs):
        scheduled["called"] = True

    monkeypatch.setattr(
        "audio_post_workflow.schedule_post", fake_schedule
    )

    fb_service = DummyFacebookService(DummyLogger())
    monkeypatch.setattr(
        "audio_post_workflow.FacebookService", lambda logger: fb_service
    )

    workflow_main()

    assert scheduled["called"] is False
    assert any("flux Facebook" in msg for msg in last_service["instance"].messages)
