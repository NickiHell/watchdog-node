import random
from datetime import datetime
from functools import partial
from logging import Handler
from typing import Tuple

from loguru import logger
from telegram import Update
from telegram.ext import Filters, MessageHandler, Updater

from app.ml.classes.sberbank import SberbankSmallGPT3


class DumdBot:
    def __init__(self, token: str, model: SberbankSmallGPT3 = None):
        """Инициализация
        :param token: Токен для BotApi
        :param model_name: Название модели из HuggingFace
        :param model_wrapper: Функция которая принимает аргументы и запускает модель ???
        """
        self._token: str = token
        self._model: SberbankSmallGPT3 = model
        self._updater: Updater = Updater(self._token)
        self._dispatcher = self._updater.dispatcher

    def reply(self, update, _):
        random.seed(datetime.now().timestamp())
        message: str = getattr(update, 'message', {'text': ''})['text'] or ''
        private_chat: bool = update.effective_chat.type == 'private'
        pinged = update.message.bot['username'] in message
        if any((pinged, private_chat, random.randint(0, 35) == 5)):
            message: str = message if private_chat else message.replace(f'@{update.message.bot["username"]}',
                                                                        '').strip()
            answer: str = self._model(message=message, max_length=random.randint(64, 128))
            update.message.reply_text(answer.replace(message, ''))
            logger.info(f'{update.message.bot["username"]} - {update.effective_chat.full_name}: {message}  -> {answer}')

    def _make_handlers(self, handlers_and_func: Tuple[Tuple[Handler, callable]] = None):
        for handler, func in handlers_and_func:
            self._dispatcher.add_handler(handler(func))

    def __call__(self, *args, **kwargs):
        handlers = (
            (partial(MessageHandler, Filters.text & (~Filters.command)), self.reply),
        )
        self._make_handlers(handlers)
        self._updater.start_polling(allowed_updates=Update.ALL_TYPES)
        self._updater.idle()
