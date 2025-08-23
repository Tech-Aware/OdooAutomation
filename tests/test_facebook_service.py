from unittest.mock import Mock, MagicMock, mock_open, patch
import pytest
import requests
import logging
import unittest
from io import BytesIO
import importlib
from datetime import datetime, timezone, timedelta


def _server_proxy(url):
    common = MagicMock()
    common.authenticate.return_value = 1
    models = MagicMock()
    models.execute_kw.return_value = []
    if url.endswith("/common"):
        return common
    return models


_patcher = patch("xmlrpc.client.ServerProxy", side_effect=_server_proxy)
_patcher.start()
import config
importlib.reload(config)
_patcher.stop()
from services.facebook_service import FacebookService


@patch.object(config, "FACEBOOK_PAGE_ID", "123")
@patch.object(config, "PAGE_ACCESS_TOKEN", "token")
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

    assert "files" in kwargs
    assert "source" in kwargs["files"]


@patch("services.facebook_service.requests.post")
def test_post_to_page_logs_api_error(mock_post, monkeypatch, caplog):
    monkeypatch.setattr(config, "FACEBOOK_PAGE_ID", "123")
    monkeypatch.setattr(config, "PAGE_ACCESS_TOKEN", "token")

    logger = logging.getLogger("test")
    service = FacebookService(logger)

    response = MagicMock()
    response.json.return_value = {"error": "bad request"}
    response.text = "{\"error\": \"bad request\"}"
    http_error = requests.HTTPError(response=response)
    response.raise_for_status.side_effect = http_error
    mock_post.return_value = response

    with caplog.at_level(logging.ERROR), pytest.raises(requests.HTTPError):
        service.post_to_facebook_page("hello")

    assert "bad request" in caplog.text


@patch.object(config, "FACEBOOK_PAGE_ID", "123")
@patch.object(config, "PAGE_ACCESS_TOKEN", "token")
@patch("services.facebook_service.requests.post")
def test_schedule_post_uses_utc_timestamp(mock_post):
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.text = "ok"
    mock_post.return_value = mock_response

    service = FacebookService(logger=logging.getLogger("test"))
    publish_time = datetime(2024, 1, 1, 12, 0)
    service.schedule_post_to_facebook_page("hello", publish_time)

    kwargs = mock_post.call_args.kwargs
    expected_ts = int(datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc).timestamp())
    assert kwargs["data"]["scheduled_publish_time"] == expected_ts


@patch.object(config, "FACEBOOK_PAGE_ID", "123")
@patch.object(config, "PAGE_ACCESS_TOKEN", "token")
@patch("services.facebook_service.requests.post")
@patch("services.facebook_service.datetime")
def test_schedule_post_naive_time_uses_local_timezone(
    mock_datetime, mock_post
):
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.text = "ok"
    mock_post.return_value = mock_response

    local_tz = timezone(timedelta(hours=2))
    mock_now = Mock()
    mock_now.astimezone.return_value = datetime(2023, 1, 1, tzinfo=local_tz)
    mock_datetime.now.return_value = mock_now

    service = FacebookService(logger=logging.getLogger("test"))
    publish_time = datetime(2024, 1, 1, 12, 0)
    service.schedule_post_to_facebook_page("hello", publish_time)

    kwargs = mock_post.call_args.kwargs
    expected_ts = int(
        datetime(2024, 1, 1, 12, 0, tzinfo=local_tz)
        .astimezone(timezone.utc)
        .timestamp()
    )
    assert kwargs["data"]["scheduled_publish_time"] == expected_ts
