"""Telegram bot service using Flask webhooks."""

import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
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

@app.post("/webhook")
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    if update.effective_user and update.effective_user.id == config.TELEGRAM_USER_ID:
        bot_app.update_queue.put_nowait(update)
    return "ok"

async def set_webhook(url: str) -> None:
    """Register the webhook URL with Telegram."""
    await bot_app.bot.set_webhook(url)
