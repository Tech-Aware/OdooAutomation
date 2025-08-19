import pytest
from io import BytesIO
from unittest.mock import MagicMock, patch

import config
from services.facebook_service import FacebookService


@patch("services.facebook_service.requests.post")
def test_post_to_page_without_image(mock_post, monkeypatch):
    monkeypatch.setattr(config, "FACEBOOK_PAGE_ID", "123")
    monkeypatch.setattr(config, "PAGE_ACCESS_TOKEN", "token")

    logger = MagicMock()
    service = FacebookService(logger)

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.text = "ok"
    response.json.return_value = {"id": "post123"}
    mock_post.return_value = response

    result = service.post_to_facebook_page("hello world")

    assert result == {"id": "post123"}
    mock_post.assert_called_once()
    url = mock_post.call_args[0][0]
    kwargs = mock_post.call_args.kwargs
    assert url == "https://graph.facebook.com/123/feed"
    assert kwargs["data"] == {"message": "hello world", "access_token": "token"}
    assert "files" not in kwargs


@patch("services.facebook_service.requests.post")
def test_post_to_page_with_image(mock_post, monkeypatch):
    monkeypatch.setattr(config, "FACEBOOK_PAGE_ID", "123")
    monkeypatch.setattr(config, "PAGE_ACCESS_TOKEN", "token")

    logger = MagicMock()
    service = FacebookService(logger)

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.text = "ok"
    response.json.return_value = {"id": "post456"}
    mock_post.return_value = response

    image = BytesIO(b"image")
    result = service.post_to_facebook_page("hello", image)

    assert result == {"id": "post456"}
    mock_post.assert_called_once()
    url = mock_post.call_args[0][0]
    kwargs = mock_post.call_args.kwargs
    assert url == "https://graph.facebook.com/123/photos"
    assert kwargs["data"] == {"caption": "hello", "access_token": "token"}
    assert "files" in kwargs
    assert "source" in kwargs["files"]
