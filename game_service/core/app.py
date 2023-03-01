"""Модуль сборки приложения"""
from aiohttp_apispec import setup_aiohttp_apispec
from core.componets import Application
from core.middlewares import setup_middlewares
from core.routes import setup_routes
from core.settings import Settings
from core.logger import setup_logging
from store import setup_store

app = Application()


def make_app() -> "Application":
    """Место сборки приложения, подключения бд, роутов, и т.д"""
    app.settings = Settings()
    setup_logging(app)
    setup_store(app)
    setup_routes(app)
    setup_aiohttp_apispec(app, title="chat", swagger_path="/docs")
    setup_middlewares(app)
    return app
