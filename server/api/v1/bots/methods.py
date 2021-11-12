from fastapi import APIRouter
from starlette.responses import JSONResponse

from server.apps.bots.models.tortoise.bots import Bot

router = APIRouter()


@router.get("", response_class=JSONResponse)
async def get_bots():
    bots = await Bot.all()
    return [x.__dict__() for x in bots]


@router.get("/{bot_id}", response_class=JSONResponse)
async def get_bot(bot_id: int):
    bot = await Bot.get(id=bot_id)
    return bot.__dict__()
