import base64
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import openai
from services.openai_service import OpenAIService


class DummyLogger:
    def error(self, msg):
        pass


class DummyCompletions:
    def __init__(self, content=None):
        self.called_with = None
        self.content = content or "Texte final"

    def create(self, **kwargs):
        self.called_with = kwargs
        response = type(
            "Response",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "message": type("Msg", (), {"content": self.content})()
                        },
                    )()
                ]
            },
        )
        return response


class DummyClient:
    def __init__(self, content=None):
        self.chat = type("Chat", (), {"completions": DummyCompletions(content)})()


def test_generate_event_post(monkeypatch):
    dummy_client = DummyClient()
    monkeypatch.setattr("services.openai_service.OpenAI", lambda: dummy_client)
    service = OpenAIService(DummyLogger())

    result = service.generate_event_post("Mon programme")

    assert result == "Texte final"
    messages = dummy_client.chat.completions.called_with["messages"]
    expected_prompt = Path("prompt_system.txt").read_text(encoding="utf-8")
    assert messages[0] == {"role": "system", "content": expected_prompt}
    assert "Mon programme" in messages[1]["content"]


def test_apply_corrections(monkeypatch):
    raw = "Texte corrigé"
    dummy_client = DummyClient(content=raw)
    monkeypatch.setattr("services.openai_service.OpenAI", lambda: dummy_client)
    service = OpenAIService(DummyLogger())

    result = service.apply_corrections("Original", "Correction")
    assert result == raw
    messages = dummy_client.chat.completions.called_with["messages"]
    assert "Correction" in messages[1]["content"]


def test_generate_marketing_email(monkeypatch):
    html = "<html><body><p>Corps</p></body></html>"
    dummy_client = DummyClient(content=f"Objet\n\n{html}")
    monkeypatch.setattr("services.openai_service.OpenAI", lambda: dummy_client)
    service = OpenAIService(DummyLogger())

    subject, body = service.generate_marketing_email("Infos")
    assert subject == "Objet"
    assert body == html


def test_generate_marketing_email_strips_prefix(monkeypatch):
    html = "<html><body><p>Corps</p></body></html>"
    dummy_client = DummyClient(content=f"Objet : Promotion\n\n{html}")
    monkeypatch.setattr("services.openai_service.OpenAI", lambda: dummy_client)
    service = OpenAIService(DummyLogger())

    subject, body = service.generate_marketing_email("Infos")
    assert subject == "Promotion"
    assert body == html


@patch("services.openai_service.OpenAI")
def test_generate_illustrations_returns_bytesio(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.images.generate.return_value = type(
        "Resp",
        (),
        {
            "data": [
                type("Data", (), {"b64_json": base64.b64encode(b"img1").decode("utf-8")})(),
                type("Data", (), {"b64_json": base64.b64encode(b"img2").decode("utf-8")})(),
            ]
        },
    )()

    service = OpenAIService(MagicMock())
    images = service.generate_illustrations(
        "prompt", "Cubisme", text="Texte", event_date="01/02/2025"
    )
    assert len(images) == 2
    assert all(isinstance(img, BytesIO) for img in images)
    _, kwargs = mock_client.images.generate.call_args
    assert "Esplas-de-Sérou 01/02/2025 Texte" in kwargs["prompt"]
    assert "Cubisme" in kwargs["prompt"]


@patch("services.openai_service.OpenAI")
def test_generate_illustrations_invalid_request(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.images.generate.side_effect = openai.OpenAIError("bad request")

    service = OpenAIService(MagicMock())
    result = service.generate_illustrations("prompt", "Cubisme")

    assert result == []

