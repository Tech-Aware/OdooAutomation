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
from config.log_config import log_execution


class TelegramService:
    """Service d'interaction via Telegram basé sur python-telegram-bot."""

    @log_execution
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
        # Les commandes (préfixées par /) sont traitées comme du texte afin de
        # permettre la gestion personnalisée dans le workflow principal.
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & filters.User(self.allowed_user_id),
                self._text_handler,
            )
        )
        self.app.add_handler(
            MessageHandler(
                filters.PHOTO & filters.User(self.allowed_user_id),
                self._photo_handler,
            )
        )
        self.app.add_handler(CallbackQueryHandler(self._callback_handler))
        self.loop: asyncio.AbstractEventLoop | None = None
        self._voice_future: asyncio.Future[str] | None = None
        self._text_future: asyncio.Future[str] | None = None
        self._callback_future: asyncio.Future[str] | None = None
        self._photo_future: asyncio.Future[BytesIO] | None = None
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Gestion du bot
    # ------------------------------------------------------------------
    @log_execution
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _run() -> None:
            self.logger.info("Démarrage du bot Telegram (polling)...")
            asyncio.set_event_loop(asyncio.new_event_loop())
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.app.initialize())
            self.loop.run_until_complete(self.app.start())
            # Lorsque le bot a été configuré avec un webhook pour recevoir les
            # mises à jour, ``get_updates`` (polling) renverra une erreur tant que
            # ce webhook reste actif. On le supprime donc explicitement avant de
            # démarrer le polling afin que les messages de l'utilisateur soient
            # bien reçus durant le workflow interactif.
            self.loop.run_until_complete(
                self.app.bot.delete_webhook(drop_pending_updates=True)
            )
            self.loop.run_until_complete(
                self.app.updater.start_polling(drop_pending_updates=True)
            )
            self.loop.run_forever()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        while self.loop is None:
            time.sleep(0.1)

    @log_execution
    def stop(self) -> None:
        """Arrête le bot Telegram et remet en place le webhook si nécessaire."""
        if not self.loop:
            return

        async def _stop() -> None:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            if config.TELEGRAM_WEBHOOK_URL:
                await self.app.bot.set_webhook(url=config.TELEGRAM_WEBHOOK_URL)

        asyncio.run_coroutine_threadsafe(_stop(), self.loop).result()
        self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread:
            self._thread.join()
        self.loop = None
        self._thread = None

    # ------------------------------------------------------------------
    # Envoi de messages
    # ------------------------------------------------------------------
    @log_execution
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

    @log_execution
    def wait_for_voice_message(self) -> str:
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        return asyncio.run_coroutine_threadsafe(self._wait_voice(), self.loop).result()

    # ------------------------------------------------------------------
    # Gestion des photos
    # ------------------------------------------------------------------
    async def _photo_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not (update.message and update.message.photo):
            return
        if self._photo_future is None or self._photo_future.done():
            return
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        data = await file.download_as_bytearray()
        self._photo_future.set_result(BytesIO(data))

    async def _wait_photo(self, timeout: float | None = None) -> BytesIO:
        assert self.loop is not None
        self._photo_future = self.loop.create_future()
        return await asyncio.wait_for(self._photo_future, timeout)

    @log_execution
    def ask_photo(self, prompt: str, timeout: float | None = None) -> BytesIO:
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        self.send_message(prompt)
        try:
            return asyncio.run_coroutine_threadsafe(
                self._wait_photo(timeout), self.loop
            ).result()
        except asyncio.TimeoutError as err:
            raise TimeoutError from err

    @log_execution
    def ask_user_images(self, timeout: float | None = None) -> List[BytesIO]:
        images: List[BytesIO] = []
        while True:
            images.append(self.ask_photo("Envoyez une image", timeout=timeout))
            if not self.ask_yes_no("Ajouter une autre image ?", timeout=timeout):
                break
        return images

    # ------------------------------------------------------------------
    # Attente d'un message texte ou vocal
    # ------------------------------------------------------------------
    async def _wait_message(self, timeout: float | None = None) -> str:
        """Attend la première entrée reçue, texte ou vocale."""
        assert self.loop is not None
        self._voice_future = self.loop.create_future()
        self._text_future = self.loop.create_future()
        done, pending = await asyncio.wait(
            [self._voice_future, self._text_future],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=timeout,
        )
        if not done:
            for fut in pending:
                fut.cancel()
            raise asyncio.TimeoutError
        result = next(iter(done)).result()
        for fut in pending:
            fut.cancel()
        return result

    @log_execution
    def wait_for_message(self, timeout: float | None = None) -> str:
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        try:
            return asyncio.run_coroutine_threadsafe(
                self._wait_message(timeout), self.loop
            ).result()
        except asyncio.TimeoutError as err:
            raise TimeoutError from err

    # ------------------------------------------------------------------
    # Gestion des messages textes
    # ------------------------------------------------------------------
    async def _text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not (update.message and update.message.text):
            return
        if self._text_future is None or self._text_future.done():
            return
        self._text_future.set_result(update.message.text)
    
    @log_execution
    def ask_text(self, prompt: str, timeout: float | None = None) -> str:
        """Envoie ``prompt`` et attend une réponse texte ou vocale."""
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        self.send_message(prompt)
        try:
            return asyncio.run_coroutine_threadsafe(
                self._wait_message(timeout), self.loop
            ).result()
        except asyncio.TimeoutError as err:
            raise TimeoutError from err
    
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

    async def _ask(
        self, prompt: str, options: List[str], timeout: float | None = None
    ) -> str:
        """Affiche les options numérotées puis propose un clavier de choix."""
        assert self.loop is not None
        self._callback_future = self.loop.create_future()

        # Mapping pour récupérer l'option complète à partir de l'index choisi
        mapping = {str(i): opt for i, opt in enumerate(options)}

        # Construction du message listant toutes les options
        message_text = f"{prompt}\n\n" + "\n\n".join(
            f"{i+1}. {opt}" for i, opt in enumerate(options)
        )

        # Clavier contenant uniquement des boutons numérotés
        keyboard = [
            [InlineKeyboardButton(str(i + 1), callback_data=str(i))]
            for i in range(len(options))
        ]

        # Envoi du message avec toutes les options
        await self.app.bot.send_message(
            chat_id=self.allowed_user_id, text=message_text
        )

        # Envoi du message avec les boutons de choix
        await self.app.bot.send_message(
            chat_id=self.allowed_user_id,
            text="Choisissez une option :",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        answer_key = await asyncio.wait_for(self._callback_future, timeout)
        return mapping[answer_key]

    @log_execution
    def ask_options(
        self, prompt: str, options: List[str], timeout: float | None = None
    ) -> str:
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        try:
            return asyncio.run_coroutine_threadsafe(
                self._ask(prompt, options, timeout), self.loop
            ).result()
        except asyncio.TimeoutError as err:
            raise TimeoutError from err

    @log_execution
    def ask_yes_no(self, prompt: str, timeout: float | None = None) -> bool:
        response = self.ask_options(prompt, ["Oui", "Non"], timeout=timeout)
        return response == "Oui"

    @log_execution
    def ask_list(
        self, prompt: str, options: List[str], timeout: float | None = None
    ) -> List[str]:
        """Permet de sélectionner plusieurs éléments dans ``options``."""
        selected: List[str] = []
        available = list(options)
        while available:
            choice = self.ask_options(
                f"{prompt} ou Terminer", available + ["Terminer"], timeout=timeout
            )
            if choice == "Terminer":
                break
            selected.append(choice)
            available.remove(choice)
        return selected

    async def _ask_images(
        self, prompt: str, images: List[BytesIO], timeout: float | None = None
    ) -> BytesIO:
        """Affiche des images avec un bouton de choix et renvoie l'image choisie."""
        assert self.loop is not None
        self._callback_future = self.loop.create_future()
        mapping = {str(i): img for i, img in enumerate(images)}
        await self.app.bot.send_message(
            chat_id=self.allowed_user_id, text=prompt
        )
        for i, img in mapping.items():
            img.seek(0)
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Choisir", callback_data=i)]]
            )
            await self.app.bot.send_photo(
                chat_id=self.allowed_user_id,
                photo=InputFile(img, filename=f"illustration_{i}.png"),
                reply_markup=keyboard,
            )
        answer_key = await asyncio.wait_for(self._callback_future, timeout)
        return mapping[answer_key]

    @log_execution
    def ask_image(
        self, prompt: str, images: List[BytesIO], timeout: float | None = None
    ) -> BytesIO:
        """Demande à l'utilisateur de choisir une image parmi celles fournies."""
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        try:
            return asyncio.run_coroutine_threadsafe(
                self._ask_images(prompt, images, timeout), self.loop
            ).result()
        except asyncio.TimeoutError as err:
            raise TimeoutError from err

    async def _send_with_buttons(
        self, text: str, options: List[str], timeout: float | None = None
    ) -> str:
        """Envoie ``text`` avec des boutons inline et retourne le choix."""
        assert self.loop is not None
        self._callback_future = self.loop.create_future()
        mapping = {str(i): opt for i, opt in enumerate(options)}
        keyboard = [
            [InlineKeyboardButton(opt, callback_data=str(i))]
            for i, opt in enumerate(options)
        ]
        await self.app.bot.send_message(
            chat_id=self.allowed_user_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        answer_key = await asyncio.wait_for(self._callback_future, timeout)
        return mapping[answer_key]

    @log_execution
    def send_message_with_buttons(
        self, text: str, options: List[str], timeout: float | None = None
    ) -> str:
        """Envoie un message et attend le choix d'un bouton parmi ``options``."""
        if not self.loop:
            raise RuntimeError("Le bot Telegram n'est pas démarré")
        try:
            return asyncio.run_coroutine_threadsafe(
                self._send_with_buttons(text, options, timeout), self.loop
            ).result()
        except asyncio.TimeoutError as err:
            raise TimeoutError from err
