import unittest
from unittest.mock import patch

from facebook_post import facebook_api as fb


class FacebookApiTests(unittest.TestCase):
    @patch.object(fb, "PAGE_ID", "123")
    @patch.object(fb, "ACCESS_TOKEN", "token")
    @patch.object(fb, "_post")
    def test_post_to_facebook_page_without_image(self, mock_post, *_):
        mock_post.return_value = {"id": "post123"}
        post_id = fb.post_to_facebook_page("hello world")
        self.assertEqual(post_id, "post123")
        mock_post.assert_called_once_with(
            "https://graph.facebook.com/123/feed",
            {"message": "hello world", "access_token": "token"},
        )

    @patch.object(fb, "PAGE_ID", "123")
    @patch.object(fb, "ACCESS_TOKEN", "token")
    @patch.object(fb, "_post")
    def test_upload_image_to_page(self, mock_post, *_):
        mock_post.return_value = {"id": "media123"}
        media_id = fb._upload_image_to_page("http://image")
        self.assertEqual(media_id, "media123")
        mock_post.assert_called_once_with(
            "https://graph.facebook.com/123/photos",
            {"url": "http://image", "published": "false", "access_token": "token"},
        )

    @patch.object(fb, "PAGE_ID", "123")
    @patch.object(fb, "ACCESS_TOKEN", "token")
    @patch.object(fb, "_upload_image_to_page", return_value="media123")
    @patch.object(fb, "_post")
    def test_post_to_facebook_page_with_image(self, mock_post, mock_upload, *_):
        mock_post.return_value = {"id": "post456"}
        post_id = fb.post_to_facebook_page("hello", "http://image")
        self.assertEqual(post_id, "post456")
        mock_upload.assert_called_once_with("http://image")
        expected_data = {
            "message": "hello",
            "access_token": "token",
            "attached_media[0]": "{\"media_fbid\": \"media123\"}",
        }
        mock_post.assert_called_once_with(
            "https://graph.facebook.com/123/feed",
            expected_data,
        )


if __name__ == "__main__":
    unittest.main()
