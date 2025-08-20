import audio_post_workflow
from unittest.mock import patch, call


def test_audio_post_workflow_correction_and_link():
    with patch('audio_post_workflow.OpenAIService') as MockOpenAI, \
         patch('audio_post_workflow.TelegramService') as MockTelegram, \
         patch('audio_post_workflow.FacebookService') as MockFacebook:

        openai_instance = MockOpenAI.return_value
        openai_instance.generate_post_versions.return_value = ['v1', 'v2']
        openai_instance.correct_text.return_value = 'v1 corrigé'

        telegram_instance = MockTelegram.return_value
        telegram_instance.start.return_value = None
        telegram_instance.wait_for_voice_message.side_effect = ['texte', '']
        telegram_instance.ask_options.return_value = 'v1'
        telegram_instance.ask_yes_no.side_effect = [True, False]
        telegram_instance.ask_text.return_value = 'https://lien'
        telegram_instance.ask_groups.return_value = []

        facebook_instance = MockFacebook.return_value

        audio_post_workflow.main()

        facebook_instance.post_to_facebook_page.assert_called_once_with('v1 corrigé https://lien', None)

        send_calls = telegram_instance.send_message.call_args_list
        assert send_calls[1:4] == [
            call('v1 corrigé'),
            call('Texte confirmé'),
            call('https://lien'),
        ]
