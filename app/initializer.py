from fastapi import FastAPI
from fastapi_admin.app import app as admin_app
from tortoise.contrib.fastapi import register_tortoise

from app.api.router import TypedAPIRouter
from app.config import tortoise_config


def init(app: FastAPI) -> None:
    """
    Init routers and etc.
    :return:
    """
    app.mount("/admin", admin_app)
    init_routers(app)
    init_db(app)


def init_db(app: FastAPI) -> None:
    """
    Init database models.
    :param app:
    :return:
    """
    register_tortoise(
        app,
        db_url=tortoise_config.db_url,
        generate_schemas=tortoise_config.generate_schemas,
        modules=tortoise_config.modules,
    )


def init_routers(app: FastAPI) -> None:
    from app.api.v1 import routers

    routers = [router for router in routers if isinstance(router, TypedAPIRouter)]

    for router in routers:
        app.include_router(**router.dict())
