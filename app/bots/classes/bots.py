import asyncio
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.types import ChatType
from loguru import logger

from app.ml.classes.sberbank import SmallGPT3


class DumdBot:
    def __init__(self, token: str, model: SmallGPT3 = None):
        self._token: str = token
        self._model: SmallGPT3 = model
        self._loop = asyncio.get_event_loop()
        self._bot = Bot(token=self._token)
        self._dispatcher = Dispatcher(self._bot)

    async def _post_cat_pic(self, message: types.Message):
        random.seed(datetime.now().timestamp())
        media = types.MediaGroup()
        media.attach_photo(f'http://theoldreader.com/kittens/{random.randint(200, 600)}/{random.randint(200, 600)}',
                           'Random cat.')
        await message.reply_media_group(media=media)

    async def ping_pong(self, message: types.Message):
        await types.ChatActions.typing(3)
        await message.answer('pong')

    async def reply_private(self, message: types.Message):
        await types.ChatActions.typing(3)
        await message.answer(await self._loop.run_in_executor(None, self._model, message.text))

    async def reply_supergroup(self, message: types.Message):
        bot_info = await self._bot.get_me()
        pinged: bool = bot_info['username'] in message.text
        if any((pinged, random.randint(0, 100) == 5, message.reply_to_message)):
            await types.ChatActions.typing(3)
            answer: str = await self._loop.run_in_executor(None, self._model, message.text)
            answer: str = answer.replace(f'@{bot_info["username"]}', '') if pinged else answer
            await message.answer(answer)

    async def _morning(self):
        while True:
            await asyncio.sleep(1)
            morning = datetime.now().replace(hour=9)
            if morning - datetime.now() < timedelta(minutes=1):
                logger.info(f'Good morning {morning - datetime.now()}')
                chat_id: int = -1001304348662
                text: str = await self._loop.run_in_executor(None, self._model, 'Доброе утро!')
                # await self._bot.send_message(chat_id, f'Доброе утро {text}')

    async def _make_handlers(self):
        self._dispatcher.register_message_handler(self._post_cat_pic, Text(contains='cat', ignore_case=True))
        self._dispatcher.register_message_handler(self.ping_pong, Text(contains='ping', ignore_case=True))
        self._dispatcher.register_message_handler(self.reply_private, chat_type=[ChatType.PRIVATE])
        self._dispatcher.register_message_handler(self.reply_supergroup, chat_type=[ChatType.SUPERGROUP])

    async def __call__(self, *args, **kwargs):
        await self._morning()
        await self._make_handlers()
        try:
            await self._dispatcher.start_polling()
        finally:
            await self._bot.close()
