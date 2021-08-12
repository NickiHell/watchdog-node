from app.api import TypedAPIRouter
from app.api.v1.bots.methods import router as bots_router
from app.api.v1.ml.methods import router as ml_router

bots_router = TypedAPIRouter(router=bots_router, prefix="/v1/bots", tags=["v1"])
ml_router = TypedAPIRouter(router=ml_router, prefix="/v1/ml", tags=["v1"])

routers = [
    bots_router,
    ml_router,
]
