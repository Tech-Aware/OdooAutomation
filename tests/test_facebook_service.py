import unittest
from unittest.mock import patch, Mock, mock_open
import logging
import pytest
from io import BytesIO
from unittest.mock import MagicMock, patch

import config
from services.facebook_service import FacebookService


class FacebookServiceTests(unittest.TestCase):
    @patch.object(config, "FACEBOOK_PAGE_ID", "123")
    @patch.object(config, "PAGE_ACCESS_TOKEN", "token")
    @patch("services.facebook_service.requests.post")
    def test_post_without_image_uses_feed(self, mock_post, *_):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.text = "ok"
        mock_post.return_value = mock_response

        service = FacebookService(logger=logging.getLogger("test"))
        service.post_to_facebook_page("hello world")

        mock_post.assert_called_once_with(
            "https://graph.facebook.com/123/feed",
            data={"message": "hello world", "access_token": "token"},
            files=None,
            timeout=10,
        )

    @patch.object(config, "FACEBOOK_PAGE_ID", "123")
    @patch.object(config, "PAGE_ACCESS_TOKEN", "token")
    @patch("builtins.open", new_callable=mock_open)
    @patch("services.facebook_service.requests.post")
    def test_post_with_image_uses_photos_and_closes_file(self, mock_post, mock_file, *_):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.text = "ok"
        mock_post.return_value = mock_response

        service = FacebookService(logger=logging.getLogger("test"))
        service.post_to_facebook_page("hello", "image.jpg")

        file_handle = mock_file.return_value
        expected_files = {"source": file_handle}
        mock_post.assert_called_once_with(
            "https://graph.facebook.com/123/photos",
            data={"caption": "hello", "access_token": "token"},
            files=expected_files,
            timeout=10,
        )
        mock_file.assert_called_once_with("image.jpg", "rb")
        file_handle.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
=======
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
