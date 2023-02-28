from aiohttp_apispec import setup_aiohttp_apispec
from core.middlewares import setup_middlewares
from core.routes import setup_routes

from vk_api_sevice.core.componets import Application
from vk_api_sevice.core.logger import setup_logging
from vk_api_sevice.core.settings import Settings
from vk_api_sevice.store import setup_store

app = Application()


def make_app() -> "Application":
    """Место сборки приложения, подключения бд, роутов, и т.д"""
    app.settings = Settings()
    setup_logging(app)
    setup_routes(app)
    setup_aiohttp_apispec(app, title="bot", swagger_path="/docs")
    setup_middlewares(app)
    setup_store(app)
    return app
