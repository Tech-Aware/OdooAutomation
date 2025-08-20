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
    def __init__(self, content="A---B---C"):
        self.called_with = None
        self.content = content

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
    def __init__(self, content="A---B---C"):
        self.chat = type("Chat", (), {"completions": DummyCompletions(content)})()


def test_generate_post_versions(monkeypatch):
    dummy_client = DummyClient()
    monkeypatch.setattr("services.openai_service.OpenAI", lambda: dummy_client)
    service = OpenAIService(DummyLogger())

    versions = service.generate_post_versions("Mon post")

    assert versions == ["A", "B", "C"]
    assert dummy_client.chat.completions.called_with["temperature"] >= 1.0
    messages = dummy_client.chat.completions.called_with["messages"]
    expected_prompt = Path("prompt_system.txt").read_text(encoding="utf-8")
    assert messages[0] == {"role": "system", "content": expected_prompt}
    assert "versions DISTINCTES" in messages[1]["content"]


def test_apply_corrections(monkeypatch):
    dummy_client = DummyClient(content="Texte corrigé")
    monkeypatch.setattr("services.openai_service.OpenAI", lambda: dummy_client)
    service = OpenAIService(DummyLogger())

    result = service.apply_corrections("Original", "Correction")

    assert result == "Texte corrigé"
    messages = dummy_client.chat.completions.called_with["messages"]
    assert "Correction" in messages[1]["content"]

@patch("services.openai_service.OpenAI")
def test_generate_illustrations_returns_bytesio(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.images.generate.return_value = type(
        "Resp",
        (),
        {
            "data": [
                type(
                    "Data",
                    (),
                    {
                        "b64_json": base64.b64encode(b"img1").decode("utf-8")
                    },
                )(),
                type(
                    "Data",
                    (),
                    {
                        "b64_json": base64.b64encode(b"img2").decode("utf-8")
                    },
                )(),
            ]
        },
    )()

    service = OpenAIService(MagicMock())
    images = service.generate_illustrations("prompt")
    assert len(images) == 2
    assert all(isinstance(img, BytesIO) for img in images)


@patch("services.openai_service.OpenAI")
def test_generate_illustrations_invalid_request(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.images.generate.side_effect = openai.OpenAIError("bad request")

    service = OpenAIService(MagicMock())
    result = service.generate_illustrations("prompt")

    assert result == []
