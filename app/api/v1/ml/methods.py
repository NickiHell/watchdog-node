from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter()


@router.get("", response_class=JSONResponse)
async def get():
    pass
