from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pool

import uvicorn
from fastapi import FastAPI
from loguru import logger

from app.bot.bot import bot_idle
from app.config import openapi_config
from app.initializer import init


def start():
    app = FastAPI(
        title=openapi_config.name,
        version=openapi_config.version,
        description=openapi_config.description,
    )
    ProcessPoolExecutor(max_workers=2).submit(bot_idle)
    init(app)
    return app
