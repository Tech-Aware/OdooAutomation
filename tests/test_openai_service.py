import base64
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import openai
from services.openai_service import OpenAIService


class DummyLogger:
    def error(self, msg):
        pass


class DummyCompletions:
    def __init__(self):
        self.called_with = None

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
                            "message": type("Msg", (), {"content": "A---B---C"})()
                        },
                    )()
                ]
            },
        )
        return response


class DummyClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": DummyCompletions()})()


def test_generate_post_versions(monkeypatch):
    dummy_client = DummyClient()
    monkeypatch.setattr("services.openai_service.OpenAI", lambda: dummy_client)
    service = OpenAIService(DummyLogger())

    versions = service.generate_post_versions("Mon post")

    assert versions == ["A", "B", "C"]
    assert dummy_client.chat.completions.called_with["temperature"] >= 1.0
    prompt = dummy_client.chat.completions.called_with["messages"][0]["content"]
    assert "versions DISTINCTES" in prompt

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
    class DummyInvalidRequestError(Exception):
        pass

    openai.error = SimpleNamespace(InvalidRequestError=DummyInvalidRequestError)

    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.images.generate.side_effect = DummyInvalidRequestError("bad request")

    service = OpenAIService(MagicMock())
    result = service.generate_illustrations("prompt")

    assert result == []
