import json

from fastapi import APIRouter, File
from starlette.responses import JSONResponse

from app.ml.models.tortoise.ml import Dataset

router = APIRouter()


@router.post('/upload_dataset/', response_class=JSONResponse)
async def upload_dataset(file: bytes = File(...)):
    data: dict = json.loads(file.decode())
    await Dataset.create(name=data['name'], data=data['messages'])
    return {'status': 'OK'}
