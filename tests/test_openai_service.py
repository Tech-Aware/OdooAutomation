from io import BytesIO
from unittest.mock import MagicMock, patch

from services.openai_service import OpenAIService


@patch("services.openai_service.OpenAI")
def test_generate_illustrations_returns_bytesio(mock_client):
    service = OpenAIService(MagicMock())
    images = service.generate_illustrations("prompt")
    assert len(images) == 2
    assert all(isinstance(img, BytesIO) for img in images)
