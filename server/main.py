import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from server.apps.bots.classes.bots import DumdBot
from server.apps.ml.classes.sberbank import SmallGPT3
from server.config import openapi_config
from server.initializer import init


def start():
    app = FastAPI(
        title=openapi_config.name,
        version=openapi_config.version,
        description=openapi_config.description,
    )

    load_dotenv()
    token_choir = os.getenv('TOKEN_SCARLET_CHOIR')

    scarlet_choir_model = SmallGPT3('Nicki/scarlet-choir')

    scarlet_choir_bot = DumdBot(token_choir, scarlet_choir_model)

    loop = asyncio.get_event_loop()

    loop.create_task(scarlet_choir_bot())

    init(app)
    return app
