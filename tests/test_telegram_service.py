import asyncio
import threading
import time
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from services.telegram_service import TelegramService


@patch("services.telegram_service.Application")
def test_start_deletes_webhook_before_polling(mock_app):
    builder = MagicMock()
    builder.token.return_value = builder
    app = MagicMock()
    app.add_handler = MagicMock()
    app.initialize = AsyncMock()
    app.start = AsyncMock()
    app.bot.delete_webhook = AsyncMock()
    app.updater.start_polling = AsyncMock()
    app.updater.stop = AsyncMock()
    app.stop = AsyncMock()
    app.shutdown = AsyncMock()
    builder.build.return_value = app
    mock_app.builder.return_value = builder

    service = TelegramService(MagicMock())
    service.start()
    while service.loop is None:
        time.sleep(0.1)
    time.sleep(0.1)

    service.stop()

    app.bot.delete_webhook.assert_awaited_once_with(drop_pending_updates=True)
    app.updater.start_polling.assert_awaited_once()


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


@patch("services.telegram_service.Application")
def test_ask_text_accepts_voice_input(mock_app):
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
        while service._voice_future is None:
            await asyncio.sleep(0)
        service._voice_future.set_result("transcribed")
        return await task

    result = loop.run_until_complete(runner())
    assert result == "transcribed"
    service.send_message.assert_called_once_with("prompt")
    loop.close()


@patch("services.telegram_service.Application")
def test_ask_text_or_return_handles_return(mock_app):
    builder = MagicMock()
    builder.token.return_value = builder
    app = MagicMock()
    app.add_handler = MagicMock()
    app.bot.send_message = AsyncMock()
    builder.build.return_value = app
    mock_app.builder.return_value = builder

    service = TelegramService(MagicMock())
    loop = asyncio.new_event_loop()
    service.loop = loop

    async def runner():
        task = asyncio.create_task(
            asyncio.to_thread(service.ask_text_or_return, "prompt")
        )
        while service._callback_future is None:
            await asyncio.sleep(0)
        service._callback_future.set_result("0")
        return await task

    result = loop.run_until_complete(runner())
    assert result is None
    assert app.bot.send_message.await_count == 1
    loop.close()


@patch("services.telegram_service.Application")
def test_send_message_with_buttons_returns_choice(mock_app):
    builder = MagicMock()
    builder.token.return_value = builder
    app = MagicMock()
    app.add_handler = MagicMock()
    app.bot.send_message = AsyncMock()
    builder.build.return_value = app
    mock_app.builder.return_value = builder

    service = TelegramService(MagicMock())
    loop = asyncio.new_event_loop()
    service.loop = loop

    async def runner():
        task = asyncio.create_task(
            asyncio.to_thread(
                service.send_message_with_buttons, "post", ["a", "b"]
            )
        )
        while service._callback_future is None:
            await asyncio.sleep(0)
        service._callback_future.set_result("1")
        return await task

    result = loop.run_until_complete(runner())
    assert result == "b"
    assert app.bot.send_message.await_count == 1
    loop.close()


@patch("services.telegram_service.Application")
def test_stop_stops_polling_and_thread(mock_app):
    builder = MagicMock()
    builder.token.return_value = builder
    app = MagicMock()
    app.add_handler = MagicMock()
    app.updater.stop = AsyncMock()
    app.stop = AsyncMock()
    app.shutdown = AsyncMock()
    app.bot.set_webhook = AsyncMock()
    builder.build.return_value = app
    mock_app.builder.return_value = builder

    service = TelegramService(MagicMock())

    loop = asyncio.new_event_loop()

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    thread = threading.Thread(target=run_loop)
    thread.start()
    service.loop = loop
    service._thread = thread

    service.stop()

    app.updater.stop.assert_awaited_once()
    app.stop.assert_awaited_once()
    app.shutdown.assert_awaited_once()
    thread.join(timeout=1)
    assert not thread.is_alive()
