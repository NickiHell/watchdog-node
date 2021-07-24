from app.core.routers.nodes import router as nodes_router
from app.utils.api.router import TypedAPIRouter

nodes_router = TypedAPIRouter(router=nodes_router, prefix="/nodes", tags=["nodes"])
