import asyncio
import json
import random
from datetime import datetime, timedelta

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.types import ChatType

from server.apps.ml.classes.sberbank import SmallGPT3


class DumdBot:
    def __init__(self, token: str, model: SmallGPT3 = None):
        self._token: str = token
        self._model: SmallGPT3 = model
        self._loop = asyncio.get_event_loop()
        self._bot = Bot(token=self._token)
        self._dispatcher = Dispatcher(self._bot)

    async def _post_cat_pic(self, message: types.Message):
        random.seed(datetime.now().timestamp())
        text = await self._loop.run_in_executor(None, self._model, 'Однаждый философ сказал')
        url = f'http://theoldreader.com/kittens/{random.randint(200, 600)}/{random.randint(200, 600)}'
        await types.ChatActions.upload_photo(2)
        media = types.MediaGroup()
        media.attach_photo(url, text)
        await message.reply_media_group(media=media)

    async def ping_pong(self, message: types.Message):
        await types.ChatActions.typing(3)
        await message.answer('pong')

    async def _get_khv_weather(self, message: types.Message):
        api_key = 'cccef59c25b3f18570a7d8347005c413'
        url = "http://api.openweathermap.org/data/2.5/weather?" + "appid=" + api_key + "&q=" + 'Khabarovsk'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.text()
                data = json.loads(data)
                await message.answer(
                    f'Погода в Хабаровске: \n'
                    f'Температура: {(data["main"]["temp"] - 273, 15)[0]:.1f}C \n'
                    f'Влажность: {data["main"]["humidity"]}% \n'
                    f'Давление: {data["main"]["pressure"]} мм рт. ст. \n'
                    f'Скорость ветра: {data["wind"]["speed"]} м/с \n',
                    reply=True
                )

    async def reply_private(self, message: types.Message):
        await types.ChatActions.typing(3)
        await message.answer(await self._loop.run_in_executor(None, self._model, message.text))

    async def reply_supergroup(self, message: types.Message):
        random.seed(datetime.now().timestamp())
        bot_info = await self._bot.get_me()
        pinged: bool = bot_info['username'] in message.text
        replied = message.reply_to_message
        conditions: bool = any((
            pinged,
            replied and replied.from_user.id == bot_info.id,
            random.randint(1, 45) == 5
        ))
        if conditions:
            await types.ChatActions.typing(3)
            answer: str = await self._loop.run_in_executor(None, self._model, message.text)
            answer: str = answer.replace(f'@{bot_info["username"]}', '') if pinged else answer
            await message.answer(answer)

    async def _morning(self):
        while True:
            await asyncio.sleep(45)
            morning = datetime.now().replace(hour=9, minute=0, second=0)
            if abs(datetime.now() - morning) < timedelta(minutes=1):
                chat_id: int = -1001304348662
                text: str = await self._loop.run_in_executor(None, self._model, 'Доброе утро!')
                await self._bot.send_message(chat_id, f'Доброе утро {text}')

    async def _make_handlers(self):
        self._dispatcher.register_message_handler(self._get_khv_weather, Text(contains='погода', ignore_case=True))
        self._dispatcher.register_message_handler(self._post_cat_pic, Text(contains='cat', ignore_case=True))
        self._dispatcher.register_message_handler(self.ping_pong, Text(contains='ping', ignore_case=True))
        self._dispatcher.register_message_handler(self.reply_private, chat_type=[ChatType.PRIVATE])
        self._dispatcher.register_message_handler(self.reply_supergroup, chat_type=[ChatType.SUPERGROUP])

    async def __call__(self, *args, **kwargs):
        await self._make_handlers()
        self._loop.create_task(self._morning())
        try:
            await self._dispatcher.start_polling()
        finally:
            await self._bot.close()
