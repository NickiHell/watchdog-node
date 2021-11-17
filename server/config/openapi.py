"""OpenAPI-schema"""
from server.config.base import BaseSettings

OPENAPI_API_NAME = "WatchDog API"
OPENAPI_API_VERSION = "0.1"
OPENAPI_API_DESCRIPTION = ""


class OpenAPISettings(BaseSettings):
    name: str
    version: str
    description: str

    @classmethod
    def generate(cls):
        return OpenAPISettings(
            name=OPENAPI_API_NAME,
            version=OPENAPI_API_VERSION,
            description=OPENAPI_API_DESCRIPTION,
        )
