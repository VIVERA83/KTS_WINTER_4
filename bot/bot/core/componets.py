from typing import Optional

from aiohttp import web
from core.settings import Settings
from store import Store
from store.rabbitmq.rabbitmq_accessor import RabbitMQ

from bot.workers.dispatcher import Bot


class Application(web.Application):
    """Основной класс приложения, описываем дополнительные атрибуты"""

    #  настройки приложения
    settings: Optional["Settings"] = None
    #  ассессоры
    store: Optional["Store"] = None
    # брокер сообщений
    rabbitmq: Optional["RabbitMQ"] = None
    # bot
    bot: Optional["Bot"] = None


class Request(web.Request):
    @property
    def app(self) -> "Application":
        return super().app()


class View(web.View):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def bot(self) -> "Bot":
        return self.request.app.bot

    @property
    def data(self) -> dict:
        if self.request.method == "GET":
            return self.request.get("querystring", {})
        return self.request.get("data", {})
