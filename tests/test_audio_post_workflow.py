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
        return "post"

    def generate_illustrations(self, prompt):
        return []


class DummyTelegramService:
    def __init__(self, logger, openai_service):
        self.logger = logger
        self.openai_service = openai_service
        self.messages = ["transcribed", "/publier", ""]
        self.index = 0

    def start(self):
        pass

    def send_message(self, msg):
        pass

    def wait_for_message(self):
        msg = self.messages[self.index]
        self.index += 1
        return msg

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

    assert fb_service.posted == ("post", None)


class SchedulingDummyTelegramService(DummyTelegramService):
    def __init__(self, logger, openai_service):
        super().__init__(logger, openai_service)
        self.messages = ["transcribed", "/programmer", ""]


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
    assert fb_service.scheduled[0] == "post"
    assert isinstance(fb_service.scheduled[1], datetime)

