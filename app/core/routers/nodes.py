from fastapi import APIRouter
from starlette.responses import HTMLResponse, JSONResponse

router = APIRouter()


async def random_task():
    return {'result': 999 * 999}


@router.get("/get", description="Get all nodes'", response_description="Some", response_class=JSONResponse)
async def get():
    # random_task()
    return JSONResponse({})
