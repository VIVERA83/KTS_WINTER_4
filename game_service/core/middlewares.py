import typing

from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware
from core.utils import error_handler

if typing.TYPE_CHECKING:
    from core.componets import Application, Request


@middleware
async def error_handling_middleware(request: "Request", handler):
    try:
        return await handler(request)
    except Exception as error:
        return await error_handler(error, request, handler)


def setup_middlewares(app: "Application"):
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(validation_middleware)
