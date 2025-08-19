import asyncio
import threading
import time
from io import BytesIO
from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config


class TelegramService:
    """Service d'interaction via Telegram basé sur python-telegram-bot."""

    def __init__(self, logger, openai_service: Optional["OpenAIService"] = None) -> None:
        self.logger = logger
        self.openai_service = openai_service
        self.allowed_user_id = config.TELEGRAM_USER_ID
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        self.app.add_handler(
            MessageHandler(
                filters.VOICE & filters.User(self.allowed_user_id), self._voice_handler
            )
        )
        self.app.add_handler(CallbackQueryHandler(self._callback_handler))
        self.loop: asyncio.AbstractEventLoop | None = None
        self._voice_future: asyncio.Future[str] | None = None
        self._callback_future: asyncio.Future[str] | None = None
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Gestion du bot
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _run() -> None:
            self.logger.info("Démarrage du bot Telegram (polling)...")
            asyncio.set_event_loop(asyncio.new_event_loop())
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.app.initialize())
            self.loop.run_until_complete(self.app.start())
            self.loop.run_until_complete(self.app.updater.start_polling())
            self.loop.run_forever()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        while self.loop is None:
            time.sleep(0.1)

    # ------------------------------------------------------------------
    # Envoi de messages
    # ------------------------------------------------------------------
    def send_message(self, text: str) -> None:
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        asyncio.run_coroutine_threadsafe(
            self.app.bot.send_message(chat_id=self.allowed_user_id, text=text),
            self.loop,
        )

    # ------------------------------------------------------------------
    # Gestion des messages vocaux
    # ------------------------------------------------------------------
    async def _voice_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not (update.message and update.message.voice):
            return
        if self._voice_future is None or self._voice_future.done():
            return
        file = await context.bot.get_file(update.message.voice.file_id)
        data = await file.download_as_bytearray()
        text = ""
        if self.openai_service:
            text = self.openai_service.transcribe_audio(bytes(data))
        self._voice_future.set_result(text)

    async def _wait_voice(self) -> str:
        assert self.loop is not None
        self._voice_future = self.loop.create_future()
        return await self._voice_future

    def wait_for_voice_message(self) -> str:
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        return asyncio.run_coroutine_threadsafe(self._wait_voice(), self.loop).result()

    # ------------------------------------------------------------------
    # Questions avec boutons
    # ------------------------------------------------------------------
    async def _callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user and update.effective_user.id != self.allowed_user_id:
            return
        if self._callback_future and not self._callback_future.done():
            self._callback_future.set_result(update.callback_query.data)
        await update.callback_query.answer()
        await update.callback_query.edit_message_reply_markup(None)

    async def _ask(self, prompt: str, options: List[str]) -> str:
        assert self.loop is not None
        self._callback_future = self.loop.create_future()
        mapping = {str(i): opt for i, opt in enumerate(options)}
        keyboard = [
            [InlineKeyboardButton(opt, callback_data=str(i))]
            for i, opt in mapping.items()
        ]
        await self.app.bot.send_message(
            chat_id=self.allowed_user_id,
            text=prompt,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        answer_key = await self._callback_future
        return mapping[answer_key]

    def ask_options(self, prompt: str, options: List[str]) -> str:
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        return asyncio.run_coroutine_threadsafe(
            self._ask(prompt, options), self.loop
        ).result()

    def ask_yes_no(self, prompt: str) -> bool:
        response = self.ask_options(prompt, ["Oui", "Non"])
        return response == "Oui"

    def ask_groups(self) -> List[str]:
        groups = []
        data = config.load_group_data()
        options = list(data.keys())
        options.append("Terminer")
        while True:
            choice = self.ask_options("Choisissez un groupe ou Terminer", options)
            if choice == "Terminer":
                break
            groups.append(choice)
        return groups

    async def _ask_images(self, images: List[BytesIO]) -> BytesIO:
        """Affiche des images avec un bouton de choix et renvoie l'image choisie."""
        assert self.loop is not None
        self._callback_future = self.loop.create_future()
        mapping = {str(i): img for i, img in enumerate(images)}
        for key, img in mapping.items():
            idx = int(key)
            file = InputFile(img, filename=f"illustration_{idx}.png")
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Choisir", callback_data=key)]]
            )
            await self.app.bot.send_photo(
                chat_id=self.allowed_user_id,
                photo=file,
                caption=f"Illustration {idx}",
                reply_markup=keyboard,
            )
        answer_key = await self._callback_future
        return mapping[answer_key]

    def ask_image(self, images: List[BytesIO]) -> BytesIO:
        """Demande à l'utilisateur de choisir une image parmi celles fournies."""
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        return asyncio.run_coroutine_threadsafe(
            self._ask_images(images), self.loop
        ).result()
