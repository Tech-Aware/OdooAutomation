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
        task = asyncio.create_task(service._ask_images(images))
        await asyncio.sleep(0)
        service._callback_future.set_result("1")
        return await task

    result = loop.run_until_complete(runner())
    assert result is images[1]
    assert app.bot.send_photo.await_count == 2
    loop.close()
