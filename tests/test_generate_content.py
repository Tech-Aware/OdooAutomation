import unittest
from unittest.mock import patch, MagicMock

from config.openai_utils import generate_post_versions, generate_illustrations


class TestGenerateContent(unittest.TestCase):
    @patch('config.openai_utils.chat_gpt')
    def test_generate_post_versions(self, mock_chat):
        mock_chat.return_value = "Version 1\nVersion 2\nVersion 3"
        result = generate_post_versions("Mon texte")
        self.assertEqual(result, ["Version 1", "Version 2", "Version 3"])

    @patch('config.openai_utils.openai.images.generate')
    def test_generate_illustrations(self, mock_image):
        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(url=f"url{i}") for i in range(1, 4)]
        mock_image.return_value = mock_resp
        result = generate_illustrations("Une maison")
        self.assertEqual(result, ["url1", "url2", "url3"])


if __name__ == '__main__':
    unittest.main()
