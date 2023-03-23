import logging
from typing import TYPE_CHECKING, Optional, Union

from aiohttp import web
from core.settings import Settings
from store import GameDatabase, Store

if TYPE_CHECKING:
    from game.schemas import game_objects


class Application(web.Application):
    """Основной класс приложения, описываем дополнительные атрибуты"""

    #  настройки приложения
    settings: Optional["Settings"] = None
    #  ассессоры
    store: Optional["Store"] = None
    # подключенные БД
    postgres: Optional["GameDatabase"] = None


class Request(web.Request):
    @property
    def app(self) -> "Application":
        return super().app()


class View(web.View):
    @property
    def logger(self) -> logging.Logger:
        return self.request.app.logger

    @property
    def request(self) -> Request:
        return super().request

    @property
    def store(self) -> "Store":
        return self.request.app.store

    @property
    # TODO: назначить тип возвращаемых данных
    def data(self) -> "game_objects":
        if self.request.method == "GET":
            return self.request.get("querystring", {})
        return self.request.get("data", {})
