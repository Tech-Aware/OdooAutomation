import logging
from unittest.mock import Mock, mock_open, patch

import config
from services.facebook_service import FacebookService


@patch.object(config, "FACEBOOK_PAGE_ID", "123")
@patch.object(config, "PAGE_ACCESS_TOKEN", "token")
@patch("services.facebook_service.requests.post")
def test_post_without_image_uses_feed(mock_post):
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.text = "ok"
    mock_post.return_value = mock_response

    service = FacebookService(logger=logging.getLogger("test"))
    service.post_to_facebook_page("hello world")

    url = mock_post.call_args.args[0]
    kwargs = mock_post.call_args.kwargs
    assert url == "https://graph.facebook.com/123/feed"
    assert kwargs["data"] == {"message": "hello world", "access_token": "token"}
    assert "files" not in kwargs
    assert kwargs["timeout"] == 10


@patch.object(config, "FACEBOOK_PAGE_ID", "123")
@patch.object(config, "PAGE_ACCESS_TOKEN", "token")
@patch("builtins.open", new_callable=mock_open)
@patch("services.facebook_service.requests.post")
def test_post_with_image_uses_photos_and_closes_file(mock_post, mock_file):
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.text = "ok"
    mock_post.return_value = mock_response

    service = FacebookService(logger=logging.getLogger("test"))
    service.post_to_facebook_page("hello", "image.jpg")

    file_handle = mock_file.return_value
    expected_files = {"source": file_handle}

    url = mock_post.call_args.args[0]
    kwargs = mock_post.call_args.kwargs
    assert url == "https://graph.facebook.com/123/photos"
    assert kwargs["data"] == {"caption": "hello", "access_token": "token"}
    assert kwargs["files"] == expected_files
    assert kwargs["timeout"] == 10
    mock_file.assert_called_once_with("image.jpg", "rb")
    file_handle.close.assert_called_once()

