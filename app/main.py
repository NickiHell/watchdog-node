import os
from concurrent.futures import ProcessPoolExecutor

from dotenv import load_dotenv
from fastapi import FastAPI
from transformers import GPT2LMHeadModel

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
    token_choir = os.getenv('TOKEN_SCARLET_CHOIR')
    token_citadel = os.getenv('TOKEN_CITADEL')

    citadel_model = SberbankSmallGPT3('Nicki/citadel')
    scarlet_choir_model = SberbankSmallGPT3('Nicki/scarlet-choir')

    citadel_bot = DumdBot(token_citadel, citadel_model)
    scarlet_choir_bot = DumdBot(token_choir, scarlet_choir_model)

    with ProcessPoolExecutor(max_workers=4) as pool:
        pool.submit(citadel_bot())
        pool.submit(scarlet_choir_bot())

    init(app)
    return app
