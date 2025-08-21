from datetime import datetime
from io import BytesIO
import audio_post_workflow
from audio_post_workflow import main as workflow_main


class DummyLogger:
    def info(self, msg):
        pass

    def exception(self, msg):
        pass


class DummyOpenAIService:
    def __init__(self, logger):
        self.logger = logger
        self.corrected = None

    def generate_event_post(self, text):
        assert text == "transcribed"
        return "post"

    def generate_illustrations(self, prompt, style):
        return []

    def apply_corrections(self, text, corrections):
        self.corrected = (text, corrections)
        return "post modifié"


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


class EditingDummyTelegramService(DummyTelegramService):
    def __init__(self, logger, openai_service):
        super().__init__(logger, openai_service)
        self.messages = ["transcribed", "/modifier", "/publier", ""]

    def ask_text(self, prompt):
        return "modif"


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


class IllustrationDummyOpenAIService(DummyOpenAIService):
    def __init__(self, logger):
        super().__init__(logger)
        self.called_with = None

    def generate_illustrations(self, prompt, style):
        self.called_with = (prompt, style)
        return [BytesIO(b"img")]


class IllustrationDummyTelegramService(DummyTelegramService):
    def __init__(self, logger, openai_service):
        super().__init__(logger, openai_service)
        self.messages = ["transcribed", "/illustrer", "/publier", ""]

    def ask_options(self, prompt, options):
        assert "style" in prompt.lower()
        assert "Manga" in options
        assert len(options) > 3
        return "Réaliste"

    def ask_image(self, prompt, images):
        return images[0]


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


def test_modification_flow(monkeypatch):
    monkeypatch.setattr(
        "audio_post_workflow.setup_logger", lambda name: DummyLogger()
    )
    openai_service = DummyOpenAIService(DummyLogger())
    monkeypatch.setattr(
        "audio_post_workflow.OpenAIService", lambda logger: openai_service
    )
    monkeypatch.setattr(
        "audio_post_workflow.TelegramService", EditingDummyTelegramService
    )
    fb_service = DummyFacebookService(DummyLogger())
    monkeypatch.setattr(
        "audio_post_workflow.FacebookService", lambda logger: fb_service
    )

    workflow_main()

    assert openai_service.corrected == ("post", "modif")
    assert fb_service.posted == ("post modifié", None)


def test_illustration_flow(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "audio_post_workflow.setup_logger", lambda name: DummyLogger()
    )
    openai_service = IllustrationDummyOpenAIService(DummyLogger())
    monkeypatch.setattr(
        "audio_post_workflow.OpenAIService", lambda logger: openai_service
    )
    monkeypatch.setattr(
        "audio_post_workflow.TelegramService", IllustrationDummyTelegramService
    )
    fb_service = DummyFacebookService(DummyLogger())
    monkeypatch.setattr(
        "audio_post_workflow.FacebookService", lambda logger: fb_service
    )
    import builtins

    real_open = builtins.open

    def fake_open(path, mode="r", *args, **kwargs):
        if path == "selected_image.png":
            return real_open(tmp_path / path, mode, *args, **kwargs)
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    workflow_main()

    assert openai_service.called_with == ("post", "Réaliste")
    assert fb_service.posted == ("post", "selected_image.png")

