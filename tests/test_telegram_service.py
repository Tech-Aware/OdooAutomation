import asyncio
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from services.telegram_service import TelegramService


@patch("services.telegram_service.Application")
def test_ask_image_returns_selected_image(mock_app):
    builder = MagicMock()
    builder.token.return_value = builder
    app = MagicMock()
    app.add_handler = MagicMock()
    app.bot.send_photo = AsyncMock()
    app.bot.send_message = AsyncMock()
    builder.build.return_value = app
    mock_app.builder.return_value = builder

    service = TelegramService(MagicMock())
    loop = asyncio.new_event_loop()
    service.loop = loop

    images = [BytesIO(b"a"), BytesIO(b"b")]

    async def runner():
        task = asyncio.create_task(service._ask_images("prompt", images))
        await asyncio.sleep(0)
        service._callback_future.set_result("1")
        return await task

    result = loop.run_until_complete(runner())
    assert result is images[1]
    assert app.bot.send_photo.await_count == 2
    assert app.bot.send_message.await_count == 1
    loop.close()


@patch("services.telegram_service.Application")
def test_ask_list_collects_choices(mock_app):
    builder = MagicMock()
    builder.token.return_value = builder
    app = MagicMock()
    builder.build.return_value = app
    mock_app.builder.return_value = builder

    service = TelegramService(MagicMock())
    service.ask_options = MagicMock(side_effect=["a", "b", "Terminer"])

    result = service.ask_list("prompt", ["a", "b", "c"])
    assert result == ["a", "b"]
    assert service.ask_options.call_count == 3


@patch("services.telegram_service.Application")
def test_ask_text_returns_user_input(mock_app):
    builder = MagicMock()
    builder.token.return_value = builder
    app = MagicMock()
    app.add_handler = MagicMock()
    builder.build.return_value = app
    mock_app.builder.return_value = builder

    service = TelegramService(MagicMock())
    service.send_message = MagicMock()
    loop = asyncio.new_event_loop()
    service.loop = loop

    async def runner():
        task = asyncio.create_task(asyncio.to_thread(service.ask_text, "prompt"))
        while service._text_future is None:
            await asyncio.sleep(0)
        service._text_future.set_result("answer")
        return await task

    result = loop.run_until_complete(runner())
    assert result == "answer"
    service.send_message.assert_called_once_with("prompt")
    loop.close()
