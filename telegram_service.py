"""Telegram bot service using Flask webhooks."""

import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import config

app = Flask(__name__)
bot_app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

async def send_message(text: str) -> None:
    """Send a text message to the configured Telegram user."""
    await bot_app.bot.send_message(chat_id=config.TELEGRAM_USER_ID, text=text)

async def ask_options(question: str, options: list[str]) -> str:
    """Ask a question with inline button options and return user's choice."""
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()

    async def _callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user and update.effective_user.id == config.TELEGRAM_USER_ID:
            future.set_result(update.callback_query.data)
            await update.callback_query.answer()
            await update.callback_query.edit_message_reply_markup(None)
            bot_app.remove_handler(handler)

    keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
    handler = CallbackQueryHandler(_callback)
    bot_app.add_handler(handler)
    await bot_app.bot.send_message(
        chat_id=config.TELEGRAM_USER_ID,
        text=question,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return await future

async def wait_for_voice_message(openai_service) -> str:
    """Wait for a voice message and return its transcription."""
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()

    async def _voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user and update.effective_user.id == config.TELEGRAM_USER_ID:
            file = await update.message.voice.get_file()
            data = await file.download_as_bytearray()
            text = openai_service.transcribe_audio(bytes(data)) if openai_service else ""
            future.set_result(text)
            bot_app.remove_handler(handler)

    handler = MessageHandler(filters.VOICE, _voice)
    bot_app.add_handler(handler)
    await bot_app.bot.send_message(
        chat_id=config.TELEGRAM_USER_ID, text="Envoyez un message vocal"
    )
    return await future

async def ask_yes_no(question: str) -> bool:
    """Ask a yes/no question and return True if user answers yes."""
    choice = await ask_options(question, ["Oui", "Non"])
    return choice == "Oui"

async def ask_groups() -> list[str]:
    """Ask for a comma-separated list of Facebook groups."""
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()

    async def _text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user and update.effective_user.id == config.TELEGRAM_USER_ID:
            future.set_result(update.message.text)
            bot_app.remove_handler(handler)

    handler = MessageHandler(filters.TEXT & ~filters.COMMAND, _text)
    bot_app.add_handler(handler)
    await bot_app.bot.send_message(
        chat_id=config.TELEGRAM_USER_ID,
        text="Groupes Facebook (séparés par des virgules) :",
    )
    text = await future
    return [g.strip() for g in text.split(",") if g.strip()]

@app.post("/webhook")
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    if update.effective_user and update.effective_user.id == config.TELEGRAM_USER_ID:
        bot_app.update_queue.put_nowait(update)
    return "ok"

async def set_webhook(url: str) -> None:
    """Register the webhook URL with Telegram."""
    await bot_app.bot.set_webhook(url)
