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

    def generate_event_post(self, text):
        assert text == "transcribed"
        return {
            "standard": "version1",
            "short": "version2",
            "hooks": [],
            "hashtags": [],
            "thanks": "",
        }

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

    fb_service = DummyFacebookService(DummyLogger())
    monkeypatch.setattr(
        "audio_post_workflow.FacebookService", lambda logger: fb_service
    )

    workflow_main()

    assert fb_service.scheduled is not None
    assert fb_service.posted is None
    assert fb_service.scheduled[0] == "fixed\nhttp://example.com"
    assert isinstance(fb_service.scheduled[1], datetime)
