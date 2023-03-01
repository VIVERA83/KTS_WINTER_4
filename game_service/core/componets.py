from typing import Optional, Union

from aiohttp import web
from core.settings import Settings


class Application(web.Application):
    """Основной класс приложения, описываем дополнительные атрибуты"""

    #  настройки приложения
    settings: Optional["Settings"] = None
    #  ассессоры
    store: Optional["Store"] = None
    # подключенные БД
    postgres: Optional["PostgresDatabase"] = None


class Request(web.Request):
    @property
    def app(self) -> "Application":
        return super().app()


class View(web.View):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def store(self) -> "Store":
        return self.request.app.store

    @property
    # TODO: назначить тип возвращаемых данных
    def data(self):
        if self.request.method == "GET":
            return self.request.get("querystring", {})
        return self.request.get("data", {})
