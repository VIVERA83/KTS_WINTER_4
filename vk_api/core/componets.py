from typing import Optional

from aiohttp import web

from vk_api.core.settings import Settings
from vk_api.store import Store


class Application(web.Application):
    """Основной класс приложения, описываем дополнительные атрибуты"""

    #  настройки приложения
    settings: Optional["Settings"] = None
    #  ассессоры
    store: Optional["Store"] = None


class Request(web.Request):
    @property
    def app(self) -> "Application":
        return super().app()


class View(web.View):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def data(self) -> dict:
        if self.request.method == "GET":
            return self.request.get("querystring", {})
        return self.request.get("data", {})
