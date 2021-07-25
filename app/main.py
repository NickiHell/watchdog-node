import os
from concurrent.futures import ProcessPoolExecutor

from dotenv import load_dotenv
from fastapi import FastAPI

from app.bot.classes.bots import DumdBot
from app.config import openapi_config
from app.initializer import init
from app.ml.classes.sberbank import SberbankSmallGPT3


def start():
    app = FastAPI(
        title=openapi_config.name,
        version=openapi_config.version,
        description=openapi_config.description,
    )

    load_dotenv()
    token = os.getenv('TOKEN')
    model = SberbankSmallGPT3('sberbank-ai/rugpt3small_based_on_gpt2')
    model()
    bot = DumdBot(token, model)

    with ProcessPoolExecutor(max_workers=2) as pool:
        pool.submit(bot())

    init(app)
    return app
